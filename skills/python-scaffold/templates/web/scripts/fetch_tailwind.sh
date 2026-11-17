#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
VERSION="${TAILWIND_VERSION:-v4.3.5}"
case "$(uname -s)-$(uname -m)" in
  Darwin-arm64) ASSET="tailwindcss-macos-arm64" ;;
  Darwin-x86_64) ASSET="tailwindcss-macos-x64" ;;
  Linux-x86_64) ASSET="tailwindcss-linux-x64" ;;
  Linux-aarch64) ASSET="tailwindcss-linux-arm64" ;;
  *)
    echo "unsupported platform: $(uname -s)-$(uname -m); install tailwindcss and set TAILWIND_BIN" >&2
    exit 2
    ;;
esac
mkdir -p .tools
curl -fsSL "https://github.com/tailwindlabs/tailwindcss/releases/download/${VERSION}/${ASSET}" \
  -o .tools/tailwindcss
chmod +x .tools/tailwindcss
echo "tailwindcss ${VERSION} -> .tools/tailwindcss"
