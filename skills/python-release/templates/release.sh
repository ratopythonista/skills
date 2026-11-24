#!/usr/bin/env bash
# Cut a release from main: check, bump, changelog, annotated tag, push, GitHub Release.
# usage: bash scripts/release.sh <patch|minor|major>
set -euo pipefail
cd "$(dirname "$0")/.."

LEVEL="${1:-}"
case "$LEVEL" in
  patch|minor|major) ;;
  *) echo "usage: bash scripts/release.sh <patch|minor|major>" >&2; exit 2 ;;
esac

[ "$(git rev-parse --abbrev-ref HEAD)" = "main" ] || {
  echo "release: run from main, not $(git rev-parse --abbrev-ref HEAD)" >&2
  exit 2
}
[ -z "$(git status --porcelain)" ] || {
  echo "release: the working tree must be clean" >&2
  exit 2
}
git fetch --quiet origin main
[ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ] || {
  echo "release: main must match origin/main" >&2
  exit 2
}

uv sync --frozen
bash scripts/check.sh

current=$(uv run --frozen python - <<'PY'
import tomllib

print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])
PY
)

new=$(uv run --frozen python - "$LEVEL" "$current" <<'PY'
import sys

level, current = sys.argv[1], sys.argv[2]
major, minor, patch = (int(part) for part in current.split("."))
if level == "major":
    major, minor, patch = major + 1, 0, 0
elif level == "minor":
    minor, patch = minor + 1, 0
else:
    patch += 1
print(f"{major}.{minor}.{patch}")
PY
)

uv run --frozen python - "$new" <<'PY'
import datetime
import re
import sys

version = sys.argv[1]

path = "pyproject.toml"
text = open(path, encoding="utf-8").read()
text, count = re.subn(
    r'(?m)^(version = )"[^"]+"', rf'\g<1>"{version}"', text, count=1
)
if count != 1:
    raise SystemExit("release: pyproject.toml has no [project] version line")
open(path, "w", encoding="utf-8").write(text)

path = "CHANGELOG.md"
text = open(path, encoding="utf-8").read()
marker = "## [Unreleased]"
start = text.find(marker)
if start < 0:
    raise SystemExit("release: CHANGELOG.md has no '## [Unreleased]' section")
body = text[start + len(marker):]
next_section = body.find("\n## [")
entry = (body if next_section < 0 else body[:next_section]).strip()
if not entry:
    raise SystemExit("release: '## [Unreleased]' is empty; write the release notes first")
tail = "" if next_section < 0 else body[next_section:]
section = f"## [{version}] - {datetime.date.today().isoformat()}"
text = text[:start] + marker + "\n\n" + section + "\n\n" + entry + "\n" + tail
if not text.endswith("\n"):
    text += "\n"
open(path, "w", encoding="utf-8").write(text)
PY

uv lock

notes=$(awk -v ver="$new" 'index($0, "## [" ver "]") == 1 {on=1; next} on && /^## \[/ {exit} on' CHANGELOG.md)

git add pyproject.toml uv.lock CHANGELOG.md
git commit -m "release: v$new"
git tag -a "v$new" -m "v$new"
git push origin HEAD
git push origin "v$new"

kind=$(uv run --frozen python -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb")).get("tool", {}).get("pack-python", {}).get("kind", "app"))')
if [ "$kind" = "lib" ]; then
  uv build
  gh release create "v$new" --verify-tag --title "v$new" --notes "$notes" dist/*
else
  gh release create "v$new" --verify-tag --title "v$new" --notes "$notes"
fi

echo "released v$new"
