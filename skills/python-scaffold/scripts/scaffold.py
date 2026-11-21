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
MANAGED = {
    Path("scripts/check.sh"),
    Path("scripts/size_check.py"),
    Path("CODING_STANDARDS.md"),
}
PACK_ORDER = (
    "python-standards",
    "python-scaffold",
    "python-verify",
    "python-testing",
    "python-web",
)
KEEP_START = b"<!-- pack-python:keep -->"
KEEP_END = b"<!-- /pack-python:keep -->"
REQUIRE_RE = re.compile(r"^([a-z0-9-]+)\s*(.+)$")
PROFILE_SKILLS = {
    "web": ("python-web", "python-testing"),
}
OVERRIDE_SLOTS = ("dependencies", "structure", "pydantic")


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


def skill_frontmatter(name: str) -> tuple[Path, dict[str, str]]:
    skill = SKILLS_DIR / name / "SKILL.md"
    if not skill.is_file():
        raise ScaffoldError(
            f"{name} is not installed next to python-scaffold; "
            "install the pack as a set (npx skills add ratopythonista/skills)"
        )
    return skill, parse_frontmatter(skill)[1]


def check_requires(owner: str, spec: str, versions: dict[str, str]) -> None:
    for clause in spec.split(";"):
        clause = clause.strip()
        if not clause:
            continue
        match = REQUIRE_RE.match(clause)
        if match is None:
            raise ScaffoldError(f"{owner}/SKILL.md: cannot parse requirement `{clause}`")
        name, range_ = match.group(1), match.group(2).strip()
        if name not in versions:
            raise ScaffoldError(f"{owner} requires {name}, which is not installed")
        if not satisfies(versions[name], range_, where=f"{owner} requires {name}"):
            raise ScaffoldError(
                f"{name} {versions[name]} is outside {owner}'s range `{range_}`; "
                "install a compatible pack"
            )


def require_pack(profile: str) -> dict[str, str]:
    versions: dict[str, str] = {}
    for name in PACK_ORDER:
        _, meta = skill_frontmatter(name)
        version = meta.get("version", "")
        semver(version, where=f"{name}/SKILL.md")
        versions[name] = version
    for name in ("python-scaffold", "python-web", "python-testing"):
        _, meta = skill_frontmatter(name)
        check_requires(name, meta.get("requires", ""), versions)
    if profile not in PROFILE_SKILLS:
        raise ScaffoldError(f"unknown profile `{profile}`; available: web")
    return versions


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


def profile_roots(profile: str) -> list[Path]:
    roots: list[Path] = []
    generic = TEMPLATES_DIR / profile
    if generic.is_dir():
        roots.append(generic)
    for owner in PROFILE_SKILLS[profile]:
        root = SKILLS_DIR / owner / "templates" / profile
        if not root.is_dir():
            raise ScaffoldError(f"{owner} is missing templates/{profile}")
        roots.append(root)
    if not roots:
        raise ScaffoldError(f"unknown profile `{profile}`; available: web")
    return roots


def template_files(profile: str) -> list[tuple[Path, Path]]:
    return [
        (root, path)
        for root in profile_roots(profile)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    ]


def stamp(versions: dict[str, str], profile: str) -> str:
    lines = [
        "<!-- pack-python",
        "  format: 1",
        "  managed-by: pack-python",
        f"  profile: {profile}",
        "  skills:",
    ]
    lines.extend(f"    - {name}@{versions[name]}" for name in PACK_ORDER)
    lines.append("-->")
    return "\n".join(lines) + "\n"


def render_standards(profile: str, versions: dict[str, str], tokens: dict[str, str]) -> bytes:
    source = SKILLS_DIR / "python-standards" / "templates" / "CODING_STANDARDS.md"
    if not source.is_file():
        raise ScaffoldError("python-standards is missing templates/CODING_STANDARDS.md")
    text = render_text(source.read_text(encoding="utf-8"), tokens, where=str(source))
    for slot in OVERRIDE_SLOTS:
        marker = f"<!-- pack-python:slot={slot} -->"
        if profile == "web":
            override = SKILLS_DIR / "python-web" / "templates" / "overrides" / f"{slot}.md"
            if not override.is_file():
                raise ScaffoldError(f"python-web is missing templates/overrides/{slot}.md")
            replacement = render_text(
                override.read_text(encoding="utf-8"), tokens, where=str(override)
            ).strip()
            text = text.replace(marker, replacement)
        else:
            text = text.replace(marker, "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return (stamp(versions, profile) + "\n" + text).encode("utf-8")


def keep_block(data: bytes) -> bytes | None:
    start = data.find(KEEP_START)
    if start < 0:
        return None
    end = data.find(KEEP_END, start)
    if end < 0:
        return None
    return data[start : end + len(KEEP_END)]


def with_keep(rendered: bytes, destination: Path) -> bytes:
    """Replace the template keep block with the target's local block, if present."""
    if not destination.is_file():
        return rendered
    local = keep_block(destination.read_bytes())
    if local is None:
        return rendered
    start = rendered.find(KEEP_START)
    if start < 0:
        return rendered
    end = rendered.find(KEEP_END, start)
    if end < 0:
        return rendered
    return rendered[:start] + local + rendered[end + len(KEEP_END) :]


def expected_content(item: Rendered, target: Path) -> bytes:
    if item.path != Path("CODING_STANDARDS.md"):
        return item.content
    return with_keep(item.content, target / item.path)


def render(
    profile: str, project: str, package: str, versions: dict[str, str]
) -> list[Rendered]:
    validate_package(package)
    tokens = {
        "PROJECT": project,
        "PACKAGE": package,
        "PACKAGE_CLASS": package_class(package),
    }
    rendered: list[Rendered] = []
    for root, source in template_files(profile):
        relative = source.relative_to(root)
        target = output_name(relative, package)
        text = source.read_text(encoding="utf-8")
        content = render_text(text, tokens, where=str(source)).encode("utf-8")
        rendered.append(Rendered(target, content, mode_for(target)))

    for external in ("check.sh", "size_check.py"):
        source = SKILLS_DIR / "python-verify" / "templates" / external
        if not source.is_file():
            raise ScaffoldError(f"python-verify is missing templates/{external}")
        relative = Path("scripts") / external
        content = source.read_text(encoding="utf-8").encode("utf-8")
        rendered.append(Rendered(relative, content, 0o755))

    rendered.append(
        Rendered(Path("CODING_STANDARDS.md"), render_standards(profile, versions, tokens), 0o644)
    )

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
        versions = require_pack(profile)
        rendered = render(profile, project, package, versions)
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
            expected = expected_content(item, target)
            if current == expected:
                continue
            drift = True
            print(diff_for(item.path, current, expected), end="")
        if drift:
            return 1
        return 0

    conflicts = [
        item.path
        for item in rendered
        if item.path in MANAGED
        and (target / item.path).is_file()
        and (target / item.path).read_bytes() != expected_content(item, target)
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
        expected = expected_content(item, target)
        if destination.is_file() and destination.read_bytes() == expected:
            unchanged += 1
            continue
        if destination.is_file() and item.path not in MANAGED:
            kept += 1
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(expected)
        destination.chmod(item.mode)
        written += 1

    print(
        f"scaffold: {written} written, {unchanged} unchanged, {kept} project-owned kept "
        f"({profile}, {package})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
