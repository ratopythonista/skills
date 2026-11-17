#!/usr/bin/env python3
"""Generate a Python project from the pack's canonical templates.

Deterministic: no network, no clock, no randomness. The same profile, project and
package always render the same bytes. Stdlib only, Python 3.12.

    scaffold.py --profile web --project torneios --target ../python
    scaffold.py --profile web --target ../python --check
"""

from __future__ import annotations

import argparse
import difflib
import keyword
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = SKILL_DIR.parent
TEMPLATES_DIR = SKILL_DIR / "templates"
TOKEN_RE = re.compile(r"\{\{([A-Z_]+)\}\}")
SEMVER_RE = re.compile(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?$")
RANGE_RE = re.compile(r"(>=|<=|>|<|==)\s*(\d+(?:\.\d+){0,2})")

TOKENS = {"PROJECT", "PACKAGE", "PACKAGE_CLASS"}
EXECUTABLE = {"manage.py"}
EXECUTABLE_PREFIXES = ("scripts/",)
MANAGED = {Path("scripts/check.sh"), Path("scripts/size_check.py")}


class ScaffoldError(Exception):
    """A user-facing refusal; the message names exactly what to fix."""


@dataclass(frozen=True)
class Rendered:
    path: Path
    content: bytes
    mode: int


def parse_frontmatter(path: Path) -> tuple[dict[str, str], dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ScaffoldError(f"{path}: missing frontmatter")
    try:
        end = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration as exc:
        raise ScaffoldError(f"{path}: unterminated frontmatter") from exc
    top: dict[str, str] = {}
    meta: dict[str, str] = {}
    section = top
    for line in lines[1:end]:
        if not line.strip():
            continue
        if line.startswith((" ", "\t")):
            key, _, value = line.strip().partition(":")
            if section is meta and key and value:
                section[key.strip()] = value.strip().strip("\"'")
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if key == "metadata" and not value:
            section = meta
            continue
        section = top
        top[key] = value
    return top, meta


def semver(text: str, *, where: str) -> tuple[int, int, int]:
    match = SEMVER_RE.match(text.strip())
    if match is None:
        raise ScaffoldError(f"{where}: `{text}` is not MAJOR.MINOR.PATCH")
    return int(match.group(1)), int(match.group(2) or 0), int(match.group(3) or 0)


def satisfies(version: str, spec: str, *, where: str) -> bool:
    current = semver(version, where=where)
    clauses = RANGE_RE.findall(spec)
    if not clauses:
        raise ScaffoldError(f"{where}: cannot parse range `{spec}`")
    for operator, raw in clauses:
        target = semver(raw, where=where)
        if operator == ">=" and not current >= target:
            return False
        if operator == "<=" and not current <= target:
            return False
        if operator == ">" and not current > target:
            return False
        if operator == "<" and not current < target:
            return False
        if operator == "==" and not current == target:
            return False
    return True


def require_verify() -> Path:
    verify = SKILLS_DIR / "python-verify"
    skill = verify / "SKILL.md"
    if not skill.is_file():
        raise ScaffoldError(
            "python-verify is not installed next to python-scaffold; "
            "install the pack as a set (npx skills add ratopythonista/skills)"
        )
    _, own_meta = parse_frontmatter(SKILL_DIR / "SKILL.md")
    own_version = own_meta.get("version", "")
    spec = own_meta.get("requires", "")
    if not spec:
        raise ScaffoldError("python-scaffold/SKILL.md: metadata.requires is missing")
    _, verify_meta = parse_frontmatter(skill)
    verify_version = verify_meta.get("version", "")
    if not satisfies(verify_version, spec, where="python-verify/SKILL.md"):
        raise ScaffoldError(
            f"python-verify {verify_version} is outside python-scaffold {own_version}'s "
            f"range `{spec}`; install a compatible pack"
        )
    return verify


def package_class(package: str) -> str:
    return "".join(part.capitalize() for part in package.split("_")) + "Config"


def normalize_package(project: str) -> str:
    candidate = re.sub(r"[^a-zA-Z0-9]+", "_", project).strip("_").lower()
    if not candidate:
        candidate = "app"
    if candidate[0].isdigit():
        candidate = f"app_{candidate}"
    return candidate


def validate_package(package: str) -> None:
    if not package.isidentifier() or keyword.iskeyword(package):
        raise ScaffoldError(f"`{package}` is not a valid Python package name")


def read_target_config(target: Path) -> dict[str, str]:
    pyproject = target / "pyproject.toml"
    if not pyproject.is_file():
        return {}
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ScaffoldError(f"{pyproject}: invalid TOML ({exc})") from exc
    pack = data.get("tool", {}).get("pack-python", {})
    project = data.get("project", {})
    found = {
        "project": project.get("name", "") if isinstance(project, dict) else "",
        "package": pack.get("package", "") if isinstance(pack, dict) else "",
        "profile": pack.get("profile", "") if isinstance(pack, dict) else "",
    }
    return {key: value for key, value in found.items() if isinstance(value, str) and value}


def render_text(text: str, tokens: dict[str, str], *, where: str) -> str:
    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in tokens:
            raise ScaffoldError(f"{where}: unknown token `{{{{{name}}}}}`")
        return tokens[name]

    rendered = TOKEN_RE.sub(replace, text)
    leftover = TOKEN_RE.search(rendered)
    if leftover is not None:
        raise ScaffoldError(f"{where}: unresolved token `{leftover.group(0)}`")
    return rendered


def output_name(relative: Path, package: str) -> Path:
    parts = [package if part == "__package__" else part for part in relative.parts]
    return Path(*parts)


def mode_for(relative: Path) -> int:
    posix = relative.as_posix()
    if posix in EXECUTABLE or posix.startswith(EXECUTABLE_PREFIXES):
        return 0o755
    return 0o644


def template_files(profile: str) -> list[Path]:
    root = TEMPLATES_DIR / profile
    if not root.is_dir():
        available = sorted(path.name for path in TEMPLATES_DIR.iterdir() if path.is_dir())
        raise ScaffoldError(f"unknown profile `{profile}`; available: {', '.join(available)}")
    return sorted(path for path in root.rglob("*") if path.is_file())


def render(profile: str, project: str, package: str, verify: Path) -> list[Rendered]:
    validate_package(package)
    tokens = {
        "PROJECT": project,
        "PACKAGE": package,
        "PACKAGE_CLASS": package_class(package),
    }
    rendered: list[Rendered] = []
    for source in template_files(profile):
        relative = source.relative_to(TEMPLATES_DIR / profile)
        target = output_name(relative, package)
        text = source.read_text(encoding="utf-8")
        content = render_text(text, tokens, where=str(source)).encode("utf-8")
        rendered.append(Rendered(target, content, mode_for(target)))

    for external in ("check.sh", "size_check.py"):
        source = verify / "templates" / external
        if not source.is_file():
            raise ScaffoldError(f"python-verify is missing templates/{external}")
        relative = Path("scripts") / external
        content = source.read_text(encoding="utf-8").encode("utf-8")
        rendered.append(Rendered(relative, content, 0o755))

    seen: set[Path] = set()
    for item in rendered:
        if item.path in seen:
            raise ScaffoldError(f"two templates render to `{item.path}`")
        seen.add(item.path)
    return sorted(rendered, key=lambda item: item.path.as_posix())


def diff_for(path: Path, current: bytes, expected: bytes) -> str:
    old = current.decode("utf-8", errors="replace").splitlines(keepends=True)
    new = expected.decode("utf-8", errors="replace").splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(old, new, fromfile=f"a/{path}", tofile=f"b/{path}", n=3)
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", help="project profile (web)")
    parser.add_argument("--project", help="project name (default: target directory name)")
    parser.add_argument("--package", help="top-level package (default: project, normalized)")
    parser.add_argument("--target", type=Path, default=Path("."), help="write root (default: .)")
    parser.add_argument("--check", action="store_true", help="re-render and diff; write nothing")
    parser.add_argument("--dry-run", action="store_true", help="list files; write nothing")
    parser.add_argument("--force", action="store_true", help="overwrite managed files")
    args = parser.parse_args(argv)

    if args.check and args.dry_run:
        parser.error("--check and --dry-run are mutually exclusive")
    if args.check and args.force:
        parser.error("--check and --force are mutually exclusive")

    target: Path = args.target
    disk = read_target_config(target)
    project = args.project or disk.get("project")
    package = args.package or disk.get("package")
    profile = args.profile or disk.get("profile")
    if not profile:
        parser.error("--profile is required for a fresh target (no [tool.pack-python] found)")
    if not project:
        project = target.resolve().name
    if not package:
        package = normalize_package(project)

    try:
        verify = require_verify()
        rendered = render(profile, project, package, verify)
    except ScaffoldError as exc:
        print(f"scaffold: {exc}", file=sys.stderr)
        return 2

    if args.dry_run:
        for item in rendered:
            suffix = " [managed]" if item.path in MANAGED else ""
            print(item.path.as_posix() + suffix)
        return 0

    if args.check:
        drift = False
        for item in rendered:
            if item.path not in MANAGED:
                continue
            destination = target / item.path
            current = destination.read_bytes() if destination.is_file() else b""
            if current == item.content:
                continue
            drift = True
            print(diff_for(item.path, current, item.content), end="")
        if drift:
            return 1
        return 0

    conflicts = [
        item.path
        for item in rendered
        if item.path in MANAGED
        and (target / item.path).is_file()
        and (target / item.path).read_bytes() != item.content
    ]
    if conflicts and not args.force:
        print(
            "scaffold: refusing to overwrite managed files without --force:\n  "
            + "\n  ".join(path.as_posix() for path in conflicts),
            file=sys.stderr,
        )
        return 3

    written = 0
    unchanged = 0
    kept = 0
    for item in rendered:
        destination = target / item.path
        if destination.is_file() and destination.read_bytes() == item.content:
            unchanged += 1
            continue
        if destination.is_file() and item.path not in MANAGED:
            kept += 1
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(item.content)
        destination.chmod(item.mode)
        written += 1

    print(
        f"scaffold: {written} written, {unchanged} unchanged, {kept} project-owned kept "
        f"({profile}, {package})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
