#!/usr/bin/env python3
"""Validate every skill in this repo: frontmatter, name/dir agreement, single-line description, links.

Stdlib only: the registries parse SKILL.md frontmatter line by line, so this checks the subset they rely on.
    python3 scripts/validate.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
ALLOWED = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)")

problems: list[str] = []


def frontmatter(text: str, path: Path) -> tuple[dict[str, str], dict[str, str]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        problems.append(f"{path}: does not start with a `---` frontmatter block")
        return {}, {}
    end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if end is None:
        problems.append(f"{path}: frontmatter block is never closed")
        return {}, {}
    top: dict[str, str] = {}
    meta: dict[str, str] = {}
    section = top
    for line in lines[1:end]:
        if not line.strip():
            continue
        if line.startswith((" ", "\t")):
            key, _, value = line.strip().partition(":")
            if section is meta and key and value:
                section[key.strip()] = value.strip().strip('"\'')
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if key == "metadata" and not value:
            section = meta
            continue
        section = top
        top[key] = value
    return top, meta


def check_skill(path: Path) -> None:
    name = path.parent.name
    text = path.read_text(encoding="utf-8")
    top, meta = frontmatter(text, path)

    for key in top:
        if key not in ALLOWED:
            problems.append(f"{path}: frontmatter key `{key}` is not in {sorted(ALLOWED)}")

    got = top.get("name", "")
    if got != name:
        problems.append(f"{path}: `name: {got}` does not match its directory `{name}`")
    if len(name) > 64 or not NAME_RE.match(name):
        problems.append(f"{path}: `{name}` is not a valid skill name (lowercase, hyphens, ≤64)")

    desc = top.get("description", "")
    if not desc:
        problems.append(f"{path}: `description` is missing or empty")
    else:
        if desc.startswith((">", "|")):
            problems.append(f"{path}: `description` is a block scalar; keep it on one line")
        if ": " in desc:
            problems.append(f"{path}: `description` contains ': ' — line-based parsers truncate it")
        if len(desc) > 1024:
            problems.append(f"{path}: `description` is {len(desc)} chars (max 1024)")

    version = meta.get("version", "")
    if not SEMVER_RE.match(version):
        problems.append(f"{path}: `metadata.version` is `{version}`; expected MAJOR.MINOR.PATCH")

    for target in LINK_RE.findall(text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        if not (path.parent / target.split("#")[0]).exists():
            problems.append(f"{path}: link target `{target}` does not exist")


def check_display_config() -> None:
    path = ROOT / "skills.sh.json"
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        problems.append(f"{path}: invalid JSON ({exc})")
        return
    groups = data.get("groupings")
    if not isinstance(groups, list) or not groups:
        problems.append(f"{path}: `groupings` must be a non-empty array")
        return
    for group in groups:
        if not str(group.get("title", "")).strip():
            problems.append(f"{path}: a grouping has no title")
        skills = group.get("skills") or []
        if not skills:
            problems.append(f"{path}: grouping `{group.get('title')}` lists no skills")
        for skill in skills:
            if not (SKILLS / skill / "SKILL.md").exists():
                problems.append(f"{path}: grouping `{group.get('title')}` names unknown skill `{skill}`")


def main() -> int:
    files = sorted(SKILLS.glob("*/SKILL.md"))
    if not files:
        problems.append(f"{SKILLS}: no skills found")
    for path in files:
        check_skill(path)
    check_display_config()
    for problem in problems:
        print(problem)
    print(f"{len(files)} skill(s) checked, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
