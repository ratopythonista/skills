---
name: python-web
description: The Django 6.1 + HTMX + Tailwind + Granian web profile for the pack. Use when building or reviewing a Django web app with HTMX fragments, Tailwind standalone, Granian, and django-types, or when a card's Skills line names python-web.
license: MIT
metadata:
  version: 1.0.0
  requires: python-standards>=1.0,<2.0; python-testing>=1.0,<2.0; python-verify>=1.1,<2.0; python-scaffold>=1.1,<2.0
---

# Web — the Django profile

This skill owns the **web profile**: the stack, the Django layout, the settings, the HTMX conventions and
the three standard overrides. The project skeleton is materialized by `python-scaffold`; the gate is
`python-verify`; test mechanics are `python-testing`. This skill does not own the base standards.

## Stack

| Layer | Choice |
| :--- | :--- |
| Framework | Django 6.1.x |
| Interactivity | HTMX (vendored client) + `django-htmx` |
| Styling | Tailwind standalone, pinned by `TAILWIND_VERSION`, compiled to `app.css` |
| Server | Granian, ASGI interface |
| Types | `django-types` for `ty` |
| Tests | pytest + pytest-django; Playwright for e2e |

No FastAPI, no FastHTML, no Node build chain. The web profile inherits Django's ORM; persistence choices
beyond the scaffold's SQLite default are out of scope for v1.

## Layout

```text
manage.py
pyproject.toml
scripts/check.sh              managed by python-verify
scripts/size_check.py         managed by python-verify
scripts/fetch_tailwind.sh     once per machine or CI
scripts/build_css.sh          after template/class changes; commit app.css
scripts/serve.sh              Granian on 127.0.0.1:8000
src/<package>/
  settings.py  urls.py  asgi.py  views.py  apps.py
  templates/base.html  templates/home.html  templates/partials/
  static/input.css  static/app.css  static/htmx.min.js
tests/test_<module>.py
tests/e2e/conftest.py  tests/e2e/test_smoke.py
```

A new domain becomes a Django app with its own `models.py`, `views.py`, `urls.py`, templates and tests.
Do not grow the project package into a layer dump; the base Structure rule still applies.

## Settings

- Read the environment with stdlib `os.environ` in `settings.py`; keep development defaults so a fresh
  clone runs without setup.
- `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS` are the only required production knobs in
  v1. Never commit a real secret.
- `DEBUG=0` requires `collectstatic` and a front proxy for static files; the ASGI static handler is a
  development convenience.
- Do not add `pydantic-settings`; Django settings are the profile's configuration mechanism.

## HTMX and templates

- The home page is a full document; mutations and refreshes return **fragments** from
  `templates/partials/`.
- Use `hx-get`/`hx-post`, `hx-target`, `hx-swap` in templates. Do not hand-write `fetch` calls for what
  HTMX already does.
- `django-htmx` middleware is installed; use `request.htmx` when a view must branch between a full page
  and a fragment.
- POST forms carry `{% csrf_token %}`. A fragment that mutates state is still a request with the same
  CSRF rules.
- Templates escape by default. Never concatenate unescaped HTML in Python, and never mark user content
  `safe`.
- Long copy lives in templates; views pass data, not markup strings.

## Tailwind

- `scripts/fetch_tailwind.sh` downloads the pinned standalone binary to `.tools/`; it is not a runtime
  dependency.
- `scripts/build_css.sh` compiles `src/<package>/static/input.css` to `app.css`. Tailwind scans the
  templates through `@source "../templates"`.
- `app.css` is committed so a fresh clone renders without the binary. Rebuild and commit it whenever a
  template or class changes; the gate does not compile CSS.
- Do not add PostCSS, `package.json` or a Node toolchain.

## Server

- `scripts/serve.sh` runs Granian with `--interface asgi <package>.asgi:application`.
- Keep the ASGI application importable from a clean checkout; the e2e fixture starts Granian on a free
  port per test.
- Development static files are served by the ASGI handler while `DEBUG=1`; production static serving is
  out of scope.

## Tests

Policy lives in `CODING_STANDARDS.md`; mechanics live in `python-testing`. The web-specific rules:

- Use pytest-django's `client` for views and fragments; assert status, rendered content and the absence
  of the full document in a fragment response.
- Mark browser flows with `@pytest.mark.e2e`; they run outside `check.sh`.
- The e2e fixture starts one Granian process per test and tears it down; no shared server state.

## Standard overrides

The profile overrides exactly three rules, each with a generated marker:

| Rule | Override |
| :--- | :--- |
| `dependencies` | Django, `django-htmx`, Tailwind standalone, Granian; ORM as the persistence boundary |
| `structure` | Django project layout under `src/<package>/`; app per domain |
| `pydantic` | Django settings and Forms at the request boundary; Pydantic for non-form DTOs |

The override text lives in [`templates/overrides/`](templates/overrides/). `python-scaffold` inserts it
into `CODING_STANDARDS.md`; do not edit the generated file.

## Anti-patterns

- Adding a second frontend framework or a Node build chain.
- Returning a full page for an HTMX target; the swap duplicates the shell.
- Hand-editing `app.css` or `htmx.min.js`.
- Putting business logic in templates or settings.
- Adding migrations, auth, deployment or cloud configuration in v1 without a new decision.
