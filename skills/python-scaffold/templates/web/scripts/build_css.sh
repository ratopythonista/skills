#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
BIN="${TAILWIND_BIN:-.tools/tailwindcss}"
if [ ! -x "$BIN" ]; then
  echo "tailwindcss not found at $BIN; run scripts/fetch_tailwind.sh or set TAILWIND_BIN" >&2
  exit 2
fi
"$BIN" -i src/{{PACKAGE}}/static/input.css -o src/{{PACKAGE}}/static/app.css --minify
