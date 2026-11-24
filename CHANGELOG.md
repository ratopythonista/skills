# Changelog

## Unreleased

- `python-release` 0.1.1 — the `secrets` job checks out full history (`fetch-depth: 0`); with the default depth, gitleaks aborts on a PR range it cannot read.
- `python-release` 0.1.0 — the delivery path: managed `ci.yml` (gate, audit, secrets), `dependabot.yml`
  (weekly `uv` + Actions, grouped patch/minor), `audit.sh` (`uv audit --locked` plus
  `.security/audit-ignores` via `--ignore-until-fixed`), `release.sh` (check, bump, changelog, annotated
  tag, push, GitHub Release with wheel+sdist for `kind = "lib"`), and the one-shot MIT `LICENSE`. PyPI is
  an opt-in recipe, never a dormant workflow.
- `python-scaffold` 1.3.0 — `--delivery-only` renders the delivery set for an existing repo (the onboarding
  runs gate and delivery in two passes), `[tool.pack-python].kind` selects app vs library, and the pack
  requirement now includes `python-release`.
- `python-standards` 1.1.0 — the **Delivery** section: one version source, Keep a Changelog, annotated
  immutable tags, release notes from the changelog, license for public repos, artifact rules, blocking
  audit, secret scan and pinned Actions.
- `python-verify` 1.1.1 — the description routes CI to `python-release`; the gate contract is unchanged.
- `pack.json` — six skills, `delivery` section, delivery files in `scaffold.generated`, and `validate.py`
  checks the new skill, its range and the delivery templates.
- `python-web` 1.1.0 — the generated `urls.py` routes `/admin/` (`admin.site.urls`). The admin app was
  already in `INSTALLED_APPS`, so a fresh project had it enabled but unreachable; a project that does not
  want the admin removes the one route.
- `python-scaffold` 1.2.0 — `--gate-only` renders only the three managed files, so an existing repo gets
  `CODING_STANDARDS.md`, `scripts/check.sh` and `scripts/size_check.py` without a second app skeleton;
  combines with `--check`, `--dry-run` and `--force`, and `pack.json` lists the flag.
- `python-standards` 1.0.0 — the normative text: 10 sections, section anchors, the managed
  `CODING_STANDARDS.md` body, one keep block, semver by obligation, and the three profile override slots.
- `python-testing` 1.0.0 — test mechanics: placement ladder, Django/HTMX fixtures, Playwright e2e against
  Granian, 90% line+branch coverage, and the test skeleton now owned by this skill.
- `python-web` 1.0.0 — the Django 6.1 + HTMX + Tailwind + Granian profile: stack, layout, settings, HTMX
  conventions, Tailwind build, e2e boundary, and the `dependencies`/`structure`/`pydantic` overrides.
- `python-scaffold` 1.1.0 — composes templates from `python-web` and `python-testing`, materializes
  `CODING_STANDARDS.md` with the `pack-python` stamp, the three overrides and a preserved keep block, and
  refuses a partial pack by name.
- `python-verify` 1.1.0 — the gate runs `pytest --cov` with the 90% line+branch floor; coverage config lives
  in `pyproject.toml` and the drift check covers `CODING_STANDARDS.md`.
- `pack.json` — all five skills implemented, `standards` format/overrides and `verify.coverage` added;
  `scripts/validate.py` checks the standards template, the override slots and the coverage floor.
- Templates moved to their semantic owners: Django config in `python-web`, test skeleton in
  `python-testing`, standards body in `python-standards`; `python-scaffold` keeps only the generic
  `.gitignore` and `.python-version`.

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
