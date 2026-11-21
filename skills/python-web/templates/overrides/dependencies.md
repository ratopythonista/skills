<!-- pack-python:override rule=dependencies by=python-web -->
### Web profile — dependencies

- Web stack: Django 6.1.x, `django-htmx`, Tailwind standalone, Granian. `django-types` is the dev stub package for `ty`.
- Runtime versions are pinned in `pyproject.toml`; Tailwind is built by `scripts/build_css.sh` and the compiled `app.css` is committed.
- Django's ORM is the persistence boundary in v1; no separate database library.
- HTMX is vendored; do not add a second frontend framework.
<!-- /pack-python:override -->
