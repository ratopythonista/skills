# Changelog

## Unreleased

- `python-verify` 1.0.0 — the merge gate: canonical `verify_commands` (`uv sync --frozen` + `bash
  scripts/check.sh`), the `check.sh` template, and `size_check.py` (warn at 200, fail at 250, explicit
  `# size-check: allow <reason>` exceptions).
- `python-scaffold` 1.0.0 — deterministic `web` profile (Django 6.1 + HTMX + Tailwind standalone + Granian,
  src-layout, `uv` lock, `django-types`), one-shot project files, managed gate files, `--check`/`--dry-run`/
  `--force`, and compatibility refusal against `python-verify`.
- `pack.json` — the shared manifest for skill ranges, verify commands, size policy and generated files;
  `scripts/validate.py` now checks skills against it and CI watches it.

## 0.1.0 — 2026-11-14

- `pytest-fasthtml` 0.1.0 — first publication. Test mechanics for pytest + FastHTML: placement ladder, fresh
  app per test, `TestClient` and lifespan, async, HTMX request/response headers, Playwright e2e, the
  `uv`/`ruff` commands, anti-patterns, and the lessons of a real board run (mutable guards, derived ids,
  server scope, QA evidence, the 100-file `gh pr view` truncation).
