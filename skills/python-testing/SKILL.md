---
name: python-testing
description: Test mechanics for the pack's Python projects. Use when deciding where a test belongs, writing pytest fixtures for Django or HTMX, wiring Playwright e2e, running coverage, or when a card's Skills line names python-testing.
license: MIT
metadata:
  version: 1.0.0
  requires: python-standards>=1.0,<2.0; python-verify>=1.1,<2.0
---

# Testing — the mechanics

`CODING_STANDARDS.md` owns the policy: one test file per module, behaviour names, regression tests,
determinism, and the 90% line+branch coverage floor. This skill owns **how** to write and run those tests.
It does not change the policy and it does not own the gate.

## Placement ladder

| Level | What it proves | Tool |
| :--- | :--- | :--- |
| Unit | a pure function or a small object in isolation | plain `pytest`, `tmp_path` |
| Integration | a view, a template, a fragment, a form, the database | `django.test.Client` via pytest-django |
| E2E | the real server and the browser wiring | Granian + Playwright, marked `e2e` |

Move down the ladder only when the higher level is too weak or too slow. Do not test a Django form through
Playwright; do not test an HTMX swap with a mocked request object.

## Files and fixtures

- One `tests/test_<module>.py` per module under test. Shared fixtures live in `tests/conftest.py`.
- The scaffold ships a Django `client` fixture through pytest-django; do not redefine it.
- Use `tmp_path` for filesystem writes, `settings` for a per-test setting override, and `monkeypatch` for
  environment variables. Restore state automatically; no fixture leaks across tests.
- E2E lives in `tests/e2e/`. Its `server_url` fixture starts one Granian process per test on a free port,
  waits for the socket and tears it down. The `page` fixture comes from pytest-playwright.
- Test files mirror the source tree; a package gets one test file per internal module, not one giant file
  with comment-separated sections.

## Django and HTMX

- Assert the response, not the implementation: status, rendered content, redirect target, form errors.
- A fragment response must not contain `<html`; a full-page response must. That is the cheapest proof that
  an HTMX target will not duplicate the shell.
- Send `HTTP_HX_REQUEST="true"` when the view branches on `request.htmx`; otherwise the test exercises the
  full-page path by accident.
- POST views need a CSRF-aware client or the test client's default enforcement disabled explicitly; do not
  disable CSRF globally in settings.
- Prefer `reverse("name")` over hard-coded paths.

## E2E

```bash
uv run playwright install chromium
uv run pytest -m e2e
```

- `pytest-playwright` provides the browser and `page`; the project provides `server_url`.
- Mark every browser module with `pytestmark = pytest.mark.e2e`; the default `addopts` excludes it.
- Use `expect(...)` with a timeout for UI state; never `time.sleep` for timing.
- E2E stays out of `check.sh`. It belongs to the QA lane, where a browser and a human or agent can wait.

## Coverage

The gate runs coverage over `src` with branch measurement and a 90% floor. Configuration lives in
`pyproject.toml` under `[tool.coverage.*]`; the command lives in `scripts/check.sh`.

```toml
[tool.coverage.run]
branch = true
source = ["src"]
omit = [
  "*/migrations/*",
  "*/settings.py",
  "*/asgi.py",
  "*/wsgi.py",
  "*/apps.py",
  "manage.py",
]

[tool.coverage.report]
fail_under = 90
show_missing = true
```

- Exclude entrypoints and configuration, not product logic. `urls.py`, views, forms, models and services are
  measured.
- A coverage drop is a gate failure, not a report to ignore. Add the missing test or justify a new omit in
  the standard; do not lower the number silently.
- `uv run pytest --cov --cov-report=term-missing` is the local command; the gate adds the same flags.

## Commands

| Command | Use |
| :--- | :--- |
| `uv run pytest` | default suite, e2e excluded |
| `uv run pytest -m e2e` | browser flows |
| `uv run pytest --cov --cov-report=term-missing` | coverage with missing lines |
| `uv run pytest tests/test_<module>.py` | one file while iterating |

Never call `pytest` directly; the locked `uv` environment is the only environment.

## Anti-patterns

- Asserting source text, log strings or implementation details instead of behaviour.
- Mocking the ORM or the template engine; use the real integration with a test database.
- `time.sleep` for synchronization, or tests that depend on order.
- A shared mutable fixture or a module-level object that leaks state between tests.
- Testing every private helper; test through the public interface and cover the branches that matter.
- Raising the coverage omit list to make the gate green.
