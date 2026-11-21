---
name: python-scaffold
description: Deterministic generator for Python project skeletons from the pack templates. Use when creating a new Python repo or web app, when regenerating the managed check.sh/size_check.py, or when a card's Skills line names python-scaffold.
license: MIT
metadata:
  version: 1.1.0
  requires: python-standards>=1.0,<2.0; python-verify>=1.1,<2.0; python-testing>=1.0,<2.0; python-web>=1.0,<2.0
---

# Scaffold — deterministic project generation

`scripts/scaffold.py` renders a project from the pack's templates. It is stdlib-only, Python 3.12, and
writes nothing outside `--target`. The generator owns **files**, never prose: every `SKILL.md` is authored by
hand.

The templates are composed from the skill that owns each artifact:

| Source | Owns |
| :--- | :--- |
| `python-scaffold/templates/<profile>` | generic project files (`.gitignore`, `.python-version`) |
| `python-web/templates/<profile>` | Django config, stack, Tailwind, Granian |
| `python-testing/templates/<profile>` | test skeleton, e2e fixture |
| `python-verify/templates` | `check.sh`, `size_check.py` |
| `python-standards/templates` | `CODING_STANDARDS.md` body |
| `python-web/templates/overrides` | the three profile override blocks |

A missing skill is an error (exit 2), never a half-configured project.

## Command

```bash
python3 .agents/skills/python-scaffold/scripts/scaffold.py \
  --profile web --project torneios --package torneios --target python/
```

| Flag | Meaning |
| :--- | :--- |
| `--profile` | template set; `web` is the only profile today |
| `--project` | distribution name written to `pyproject.toml` (default: target directory name) |
| `--package` | top-level package under `src/` (default: project, normalized to an identifier) |
| `--target` | write root; never escaped |
| `--dry-run` | print the rendered paths with `[managed]` marks; write nothing |
| `--check` | re-render the **managed** files and diff; exit 1 on drift |
| `--force` | overwrite managed files that drifted |

`--check` and `--dry-run` are mutually exclusive, and `--force` cannot be combined with `--check`.

## Determinism contract

- No network, no clock, no randomness, no locale. Same profile + project + package → same bytes.
- UTF-8, LF, one final newline; files written in sorted path order.
- Tokens are `{{PROJECT}}`, `{{PACKAGE}}`, `{{PACKAGE_CLASS}}`; the path token `__package__` becomes the
  package name. An unknown or unresolved token is an error, never a silently literal `{{...}}`.
- A second run writes nothing. Re-running with the same inputs reports `0 written`.
- The generator refuses a pack outside its `metadata.requires` ranges (exit 2) or a missing skill, naming
  the skill (exit 2). A partial pack is an error, not a half-configured project.
- The stamp and every managed file are rendered from the installed skill versions; a version bump changes
  the bytes and `--check` reports the drift.

## Managed vs project-owned

Only the generated contract files are re-rendered and drift-checked; the rest are one-shot bootstrap:

| Kind | Paths | Re-run behavior |
| :--- | :--- | :--- |
| managed | `scripts/check.sh`, `scripts/size_check.py`, `CODING_STANDARDS.md` | compared by `--check`; overwritten only with `--force` |
| project-owned | `pyproject.toml`, `manage.py`, `settings.py`, `urls.py`, views, templates, tests | created when missing; never overwritten once present |

This is deliberate. Adding a dependency belongs in `pyproject.toml`, and a byte-for-byte regeneration would
erase it. The managed files have one semantic owner each and no local edits worth preserving, except the
`CODING_STANDARDS.md` keep block:

- `scripts/check.sh` and `scripts/size_check.py` come from `python-verify`.
- `CODING_STANDARDS.md` is the body from `python-standards`, plus the three `python-web` overrides and a
  stamp with every applied skill version.
- `--check` preserves the local `<!-- pack-python:keep -->` block byte for byte; anything outside it is
  drift.

## Web profile

Stack: Django 6.1, HTMX (vendored client), `django-htmx`, Tailwind standalone, Granian, `uv` with a lock,
src-layout. Generated layout:

```
.python-version             3.12
pyproject.toml              Django/HTMX/Granian; dev: pytest, pytest-cov, pytest-django, Playwright, ruff, ty, django-types
CODING_STANDARDS.md         generated norm; keep block at the end (owned by python-standards + python-web)
manage.py                   DJANGO_SETTINGS_MODULE=<package>.settings
scripts/check.sh            canonical gate (owned by python-verify)
scripts/size_check.py       200 warns, 250 fails (owned by python-verify)
scripts/fetch_tailwind.sh   downloads the pinned standalone binary to .tools/
scripts/build_css.sh        compiles src/<package>/static/input.css -> app.css
scripts/serve.sh            Granian on 127.0.0.1:8000
src/<package>/              settings, URLs, ASGI app, views, templates, static
tests/                      pytest-django unit/integration; tests/e2e has the Playwright smoke
```

The home page renders a shell and one HTMX fragment (`hx-get` → `pong`). That is enough to prove the
server-side wiring without inventing product behaviour.

## After generation

```bash
uv lock                         # once; commits uv.lock
uv sync --frozen                # what the board runs
uv run playwright install chromium
bash scripts/fetch_tailwind.sh  # once per machine/CI
bash scripts/build_css.sh       # after template/class changes; commit app.css
bash scripts/serve.sh           # http://127.0.0.1:8000
```

`uv lock` is not part of the scaffold: resolving the dependency graph needs the network and a clock the
generator does not have. The lock is the first deliberate project action.

`app.css` is generated but committed, so a fresh clone renders without running Tailwind. Rebuild it whenever a
template changes; the gate does not compile CSS.

## What the scaffold does not do

- It does not configure CI, credentials, deploy, or the super-board (onboarding owns those).
- It does not create the virtualenv, the lock, the database, or browser binaries.
- It does not edit files outside `--target`.

## Anti-patterns

- Editing generated `check.sh` in place instead of fixing `python-verify/templates/check.sh`.
- Adding a dependency and then running `--force`: it regenerates the managed gate only, but a hand-edited
  pyproject is still yours to keep.
- Using `--check` as a project-wide "no changes allowed" gate: it checks managed files, not your product.
- Copying templates into the repo as a second source of truth.
