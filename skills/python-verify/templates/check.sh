#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen ty check src
uv run --frozen python scripts/size_check.py
uv run --frozen python -m pytest
