#!/usr/bin/env bash
# Dependency audit: OSV for the locked environment, plus the repo's accepted advisories.
# Accepted IDs live in .security/audit-ignores, one per line, and expire once a fix exists.
set -euo pipefail
cd "$(dirname "$0")/.."

args=()
if [ -f .security/audit-ignores ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%%#*}"
    line="$(printf '%s' "$line" | tr -d '[:space:]')"
    [ -n "$line" ] || continue
    args+=(--ignore-until-fixed "$line")
  done < .security/audit-ignores
fi

exec uv audit --locked --preview-features audit-command ${args[@]+"${args[@]}"}
