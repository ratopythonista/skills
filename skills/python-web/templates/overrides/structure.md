<!-- pack-python:override rule=structure by=python-web -->
### Web profile — structure

- Django project config lives in `src/{{PACKAGE}}/`: `settings.py`, `urls.py`, `asgi.py`, `views.py`.
- Templates live in `src/{{PACKAGE}}/templates/` (`base.html`, page templates, `partials/` for HTMX fragments).
- Static assets live in `src/{{PACKAGE}}/static/` (`input.css`, committed `app.css`, vendored `htmx.min.js`).
- Tests mirror the source: `tests/test_<module>.py`; browser flows in `tests/e2e/`.
- A new domain becomes a Django app with its own `models.py`, `views.py`, `urls.py`, and templates; do not grow the project package into a layer dump.
<!-- /pack-python:override -->
