---
name: python-verify
description: The Python merge gate. Defines scripts/check.sh, the canonical verify_commands, the 200/250 size check, the 90% line+branch coverage floor and the drift check, and how to keep the gate green without mise. Use when wiring a merge gate locally or in the board, when check.sh fails, or when a card's Skills line names python-verify.
license: MIT
metadata:
  version: 1.1.1
---

# Verify — the Python gate

This skill owns the **contract of `scripts/check.sh`** and the canonical `verify_commands`. The scaffold writes
the script from `templates/check.sh`; this skill is the semantic owner, so a fix lands here first, then in the
generated projects.

## Canonical `verify_commands`

At the repo root:

```json
"verify_commands": [
  "uv sync --frozen",
  "bash scripts/check.sh"
]
```

When Python lives in a subdirectory, keep the same two commands with the prefix:

```json
"verify_commands": [
  "cd python && uv sync --frozen",
  "cd python && bash scripts/check.sh"
]
```

- `uv sync --frozen` proves the lock is complete and never mutates it. A stale `uv.lock` fails here, which is
  the point.
- `bash scripts/check.sh` runs everything else. The merge gate stays two commands, so the board config never
  needs to change when a check is added.
- **No `mise`.** The gate is `uv` plus the repo's script. `mise` is a local convenience, never a gate
  dependency.
- The gate runs from a fresh worktree with the current base merged in; every command must work from a clean
  checkout. No `.venv`, no global tool, no network beyond `uv sync` fetching the locked wheels.
- E2E stays out of the gate: Playwright belongs to the QA lane, where a human or agent can wait for the
  browser.

## `scripts/check.sh`

The script is short and ordered from cheapest to most expensive:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen ty check src
uv run --frozen python scripts/size_check.py
uv run --frozen python -m pytest --cov --cov-report=term-missing
```

- `cd "$(dirname "$0")/.."` makes the script safe from any cwd, including the board's worktree.
- `--frozen` on every `uv run` keeps the gate inside `uv.lock`. A command that resolves dependencies during
  the gate hides a missing lock entry.
- Adding a check means adding a line here, not a new `verify_command`.
- The script must not write to the repo: no auto-fix, no formatter rewrite, no `collectstatic`. `ruff format
  --check` is the read-only form; `ruff check --fix` belongs to the developer loop.

## Size check — warn at 200, fail at 250

`scripts/size_check.py` scans product Python under `src/` by default and enforces the standards' file-size
signal:

- **200 lines**: warning on stderr, exit code stays 0.
- **250 lines**: failure, exit code 1, every offending file listed.
- Counted lines are `splitlines()`; the final newline does not add a line.
- Exempt by path: `__init__.py` (the package interface), anything under `migrations/` (generated), and
  `__pycache__`.
- Exempt by declaration: `# size-check: allow <reason>` in the first three lines of the file. The reason is
  mandatory; the marker is an explicit conscious exception, not a silent bypass.
- Warnings never fail a PR. A file sitting at 200–249 is a prompt to split by cohesion, not a merge blocker.

The size check reads product code, not tests or scripts. A 400-line test file is a testing-mechanics problem,
not a product-size problem.

## Coverage — 90% of lines and branches

`pytest-cov` is a dev dependency and the gate runs it over `src`:

```bash
uv run --frozen python -m pytest --cov --cov-report=term-missing
```

The floor and the exclusions live in `pyproject.toml`, not in the command:

- `[tool.coverage.run] branch = true`, `source = ["src"]`.
- Omit entrypoints and configuration only: `*/migrations/*`, `manage.py`, `*/settings.py`, `*/asgi.py`,
  `*/wsgi.py`, `*/apps.py`. `urls.py`, views, forms, models and services stay measured.
- `[tool.coverage.report] fail_under = 90`, `show_missing = true`.
- A missing test is the fix. Raising `fail_under` down or adding an omit to make the gate green is a
  standards violation, not a gate configuration.

E2E is excluded by the default marker, so coverage measures unit and integration tests. Browser flows stay
in the QA lane.

## Drift check — the scaffold regenerates byte for byte

`python-scaffold` owns `--check`. In a generated repo:

```bash
python3 .agents/skills/python-scaffold/scripts/scaffold.py --profile web --target . --check
```

`--check` re-renders every managed file in memory — `scripts/check.sh`, `scripts/size_check.py` and
`CODING_STANDARDS.md` — compares bytes and prints a unified diff. Exit 0 means the checked-in generated
files match; exit 1 means drift. `CODING_STANDARDS.md` preserves the local keep block; edits outside it are
drift. The check needs the pack installed: it reads the canonical files from `python-verify`,
`python-standards`, `python-testing` and `python-web`, so a project that vendors only the generated files
cannot run it. In CI without the pack, either install the pack in the workflow or skip the drift check and
rely on the gate; do not copy a second source of truth into the repo.

## CI

A Python repo's CI delegates to the same contract:

```yaml
- uses: astral-sh/setup-uv@v6
- run: uv sync --frozen
- run: bash scripts/check.sh
```

The lock is the cache key. Do not run `uv sync` without `--frozen` in CI: it turns a lockfile mistake into a
green build today and a broken checkout tomorrow.

## Failure playbook

| Symptom | Cause | Fix |
| :--- | :--- | :--- |
| `uv sync --frozen` fails | `pyproject.toml` changed without `uv lock` | run `uv lock`, commit `uv.lock` |
| `ruff format --check` fails | code was not formatted | run `uv run ruff format .`, commit |
| `ty check` fails on Django names | `django-types` missing or stale | add/refresh the dev dependency; do not blanket-ignore |
| size check fails at 250 | a module mixes contexts | split by cohesion; declare only a real exception |
| coverage below 90% | a branch has no test | add the missing test; do not raise the omit list |
| gate green locally, red in the worktree | untracked file or uncommitted lock | commit every generated artifact the gate reads |

## Anti-patterns

- A third `verify_command` for a new check instead of a line in `check.sh`.
- `uv run` without `--frozen` inside the gate.
- `pytest` with `--maxfail` or a narrowed selection in the gate; the gate runs the whole default suite.
- `# type: ignore`, `# noqa` or a raised size threshold used to hide a real failure.
- Copying `check.sh` into the repo by hand; generate it, then edit the template here and regenerate.
