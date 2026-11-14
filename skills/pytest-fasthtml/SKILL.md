---
name: pytest-fasthtml
description: Test mechanics for Python/FastHTML apps — where a test belongs (unit, integration, e2e), fixtures, async handlers, HTMX requests, Playwright, and the uv/ruff commands. Use when writing, running or reviewing tests for a pytest + FastHTML app, or when a card's Skills line names pytest-fasthtml.
license: MIT
metadata:
  version: 0.1.0
---

# Testing pytest + FastHTML

This skill fixes **mechanics**: where a test lives, how to build fixtures, how to exercise HTMX, and how to
run the suite. Coverage judgement belongs to `testing-strategy`; the red-green loop belongs to `tdd`.

Paths below assume the project lives in `python/` (package `app` in the examples); adjust the package name,
keep the layout.

## Placement

Climb the ladder and stop at the first rung that proves the behaviour:

| # | What it proves | Layer | Tool |
| :--- | :--- | :--- | :--- |
| 1 | pure logic: a handler/component returns the right FT | unit | plain pytest |
| 2 | real route + form + session, without a browser | integration | `TestClient` over the app |
| 3 | real interaction (HTMX in the browser, JS, CSS) | e2e | Playwright |
| 4 | a live third party (payment, OAuth) | **not a test** | record the gap |

- An e2e for a pure-logic defect is slow and points at the page instead of the function.
- Every test must go red **for the right reason** and survive a refactor of the implementation.

## Layout

```
python/
  app/main.py            # create_app() + the ASGI app
  app/                   # domain, store, views
  tests/conftest.py      # shared fixtures
  tests/test_<module>.py # one file per module
  tests/e2e/conftest.py  # live_server
  tests/e2e/test_<flow>.py
```

Import the app through its real entrypoint (`app.main.create_app`); never assemble a parallel app just for
the test.

## Fixtures

`create_app()` must return a fresh app with its own store and state. One fixture per test, never a mutated
singleton across tests:

```python
# tests/conftest.py
import pytest
from starlette.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    with TestClient(create_app()) as test_client:  # `with` runs lifespan
        yield test_client


@pytest.fixture
def htmx():
    return {"HX-Request": "1"}
```

- The shortest scope that works; no global state shared between tests.
- Database or files: `tmp_path`, never the developer's path.
- `TestClient` outside a `with` does not run `lifespan` — use the context manager whenever the app needs
  startup or shutdown.

## Unit: a pure handler

Top-level views registered by a `register(app)` / `@rt` are directly callable:

```python
from fastcore.xml import to_xml

from app.views import render_card


def test_render_card_shows_score():
    html = to_xml(render_card(name="ana", score=3))
    assert "ana" in html
    assert ">3<" in html
```

Calling the handler returns FT: the page wrapper (`<html>`, head, body) only happens when the app renders,
so assert content markers, not `<html>`. Never wildcard-import FastHTML.

Decide on the HTMX header without HTTP: FastHTML injects `HtmxHeaders` into the handler.

```python
from fasthtml.core import HtmxHeaders


def test_board_page_chrome_without_htmx():
    html = to_xml(render_board(htmx=HtmxHeaders()))
    assert "My tournaments" in html


def test_board_bare_list_for_htmx():
    html = to_xml(render_board(htmx=HtmxHeaders(request="1")))
    assert "My tournaments" not in html
```

## Integration: `TestClient`

`TestClient` calls the ASGI app synchronously (the calls are **not** awaitables):

```python
def test_save_returns_fragment(client, htmx):
    response = client.post("/save", data={"name": "ana"}, headers=htmx)
    assert response.status_code == 200
    assert "<html" not in response.text  # fragment, not a full page
    assert "ana" in response.text


def test_save_full_page_without_htmx(client):
    response = client.post("/save", data={"name": "ana"})
    assert "<html" in response.text
```

- Assert the contract (status, fragment vs page, headers), not the whole tag tree.
- In `client.post`, use `data=` for form-urlencoded; `json=` only when the route reads JSON.
- HTMX response headers (`HX-Trigger`, `HX-Redirect`, `HX-Location`) are part of the contract: check
  `response.headers`.
- Form validation: the handler must re-render the message and create no state. Test both sides (accept and
  reject).

## Async

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

- `pytest-asyncio` is a dev dependency; in `strict` mode async fixtures need `@pytest_asyncio.fixture`.
- An async route handler: prefer driving it through `TestClient` (synchronous, covers the real ASGI path).
  Direct `await` only for logic that never passes through the router.
- No `sleep` for synchronisation: use fixtures or events.

## HTMX

- `HX-Request` is always `"true"` when the request comes from htmx; `HX-Target` / `HX-Trigger` say which
  element fired it.
- Test both branches of the handler (fragment and full page) — that is where regressions live. On the HTTP
  response, a request without `HX-Request` is wrapped in `<html>…`; with it, the fragment goes bare
  (restored history is the exception).
- FastHTML's `Redirect` is htmx-aware: with `HX-Request` it answers `HX-Redirect` and no 3xx; without the
  header it answers `303`. Test the header the flow actually emits.
- `follow_redirects=False` when you want to observe the 303.
- Do not simulate htmx in Python: for the behaviour of an `hx-*` attribute in the browser, drop to the e2e
  rung.

## E2E with Playwright

`tests/e2e/conftest.py` starts the app once per test and hands over the URL:

```python
def test_card_moves_on_click(page, live_server):
    page.goto(live_server)
    page.get_by_role("button", name="Move").click()
    expect(page.get_by_text("in progress")).to_be_visible()
```

- `pytest-playwright` provides `page` / `context`; `--headed`, `--browser` on the CLI.
- Mark the file with `pytestmark = pytest.mark.e2e`; the project default excludes that marker.
- Run `uv run playwright install chromium` once if the cache is empty.
- Prefer role/label/text selectors; `data-testid` only where there is no semantics.
- Data comes from the UI, never from a hidden seed.

## Commands

```bash
cd python
uv run pytest -q                 # default suite (unit + integration)
uv run pytest -k test_name       # red-green of one test
uv run pytest -m e2e             # real browser
uv run ruff check . && uv run ruff format --check .
```

- Never bare `pytest`: outside `uv`'s pinned environment the result does not count.
- In a repo with `mise`, the canonical path is `mise run test` (which is `uv run pytest`).

## Anti-patterns

- `from fasthtml.common import *` in app or test code.
- Mocking FastHTML/Starlette to "isolate" a route — `TestClient` already is the isolation.
- `sleep`, real network, writes outside `tmp_path`.
- Asserting a giant HTML string when the contract is "has the form" / "does not have it".
- E2E for pure logic; a unit test for a bug that only reproduces in the browser.

## Lessons from a real run

- **Mute every guard.** Swap `casefold()` for identity, `has_scores` for truthiness,
  `get_active_tournament()` for `list_tournaments()[-1]`, the `Form(action=...)` for a `Div`, and confirm
  the test goes red. If the suite stays green, coverage is missing.
- **Derived ids need a uniqueness test.** Two teams in the same tournament with a fixed id pass twenty
  tests and break the round-robin.
- **The e2e server scope is a decision, not a detail.** In-memory state → start the app per test;
  session state → isolate it. Document the real scope in the README and in the skill.
- **QA evidence is a contract:** cite the head, the count, and the line the artefacts actually contain. A
  claim without the matching log or PNG becomes a Review finding.
- **A PR with more than 100 files breaks `gh pr view --json files`** (it truncates at 100) and halts the
  merge gate; keep evidence lean or page through `gh api`.
