#!/usr/bin/env python3
"""Fail a Python file that outgrew the product-size ceiling.

Warn at 200 lines, fail at 250 by default. Files under ``migrations/`` and
``__init__.py`` are exempt; any other file can declare ``# size-check: allow
<reason>`` in its first three lines. Stdlib only, deterministic output.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_WARN = 200
DEFAULT_FAIL = 250
MARKER = "# size-check: allow"
SKIPPED_DIRS = {"__pycache__", "migrations", ".venv", ".git", "node_modules"}


def declared_exception(lines: list[str]) -> bool:
    for line in lines[:3]:
        stripped = line.strip()
        if stripped.startswith(MARKER) and stripped[len(MARKER) :].strip():
            return True
    return False


def python_files(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if root.is_file() and root.suffix == ".py":
            files.append(root)
            continue
        for path in sorted(root.rglob("*.py")):
            if path.name == "__init__.py":
                continue
            if any(part in SKIPPED_DIRS for part in path.parts):
                continue
            files.append(path)
    return sorted(files)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("src")],
        help="files or directories to scan (default: src)",
    )
    parser.add_argument("--warn", type=int, default=DEFAULT_WARN)
    parser.add_argument("--fail", type=int, default=DEFAULT_FAIL)
    args = parser.parse_args(argv)

    if args.warn > args.fail:
        parser.error("--warn must be <= --fail")

    failures: list[tuple[Path, int]] = []
    warnings: list[tuple[Path, int]] = []
    for path in python_files(args.paths):
        lines = path.read_text(encoding="utf-8").splitlines()
        if declared_exception(lines):
            continue
        count = len(lines)
        if count >= args.fail:
            failures.append((path, count))
        elif count >= args.warn:
            warnings.append((path, count))

    for path, count in warnings:
        print(
            f"size-check: warning: {path} has {count} lines "
            f"(warn {args.warn}, fail {args.fail}); split by cohesion",
            file=sys.stderr,
        )
    for path, count in failures:
        print(
            f"size-check: failure: {path} has {count} lines "
            f"(fail at {args.fail}); split it or declare '# size-check: allow <reason>'",
            file=sys.stderr,
        )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
