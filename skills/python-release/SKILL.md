---
name: python-release
description: The Python delivery path. Defines the managed CI workflow, the dependency-audit and secret-scan jobs, the release script, the changelog and tag contract, and the GitHub Release. Use when cutting a release, wiring CI or Dependabot, adding a license, recording an audit exception, or when a card's Skills line names python-release.
license: MIT
metadata:
  version: 0.1.0
  requires: python-verify>=1.1,<2.0
---

# Release — the Python delivery path

`python-scaffold` renders every file here; this skill is the semantic owner.
A fix lands here first, then in the generated projects.

## What this skill owns

| File | Kind | Contents |
| :--- | :--- | :--- |
| `.github/workflows/ci.yml` | managed | `gate`, `audit`, `secrets` jobs |
| `.github/dependabot.yml` | managed | weekly `uv` and `github-actions` updates |
| `scripts/audit.sh` | managed | `uv audit --locked` plus the repo's exceptions |
| `scripts/release.sh` | managed | check, bump, changelog, tag, push, release |
| `LICENSE` | one-shot | MIT, written only when missing |
| `.security/audit-ignores` | project-owned | advisory IDs accepted while no fix exists |

Managed files are compared by `scaffold.py --check`; change the skill, never the generated file.
The one-shot `LICENSE` and the ignore list belong to the repo.

## The delivery contract

- **One version source:** `[project].version` in `pyproject.toml`.
- **A release is a changelog entry:** `CHANGELOG.md` uses Keep a Changelog; `scripts/release.sh` refuses an empty `## [Unreleased]`.
- **A tag is `vX.Y.Z` and annotated**, cut from `main` after the checks pass. Never move or delete a published tag.
- **GitHub Release notes are the changelog section**, never a second document.
- **Apps release without artifacts; libraries attach wheel and sdist.** `[tool.pack-python].kind` decides: `"app"` (default) or `"lib"`.
- **Public repos ship `LICENSE` and `[project].license`.** The generated MIT text names `<project> contributors`; the year is omitted so the scaffold stays deterministic.

## CI

`ci.yml` runs on push to `main` and on pull requests, with `contents: read`:

| Job | Steps |
| :--- | :--- |
| `gate` | `uv sync --frozen`, `bash scripts/check.sh`; for `kind = "lib"`, `uv build` |
| `audit` | `bash scripts/audit.sh` |
| `secrets` | `gitleaks/gitleaks-action@v3` |

The gate job is the same two commands the board runs; the workflow is a second caller, never a second definition.

The `secrets` job needs `pull-requests: write` for the action's PR comment. Organizations need a `GITLEAKS_LICENSE`; personal accounts do not.

Private repositories on a personal GitHub Free account cannot require checks (rulesets need Pro); the board's gate remains the enforcement there.

## Audit

`scripts/audit.sh` runs `uv audit --locked` (OSV) and passes one `--ignore-until-fixed <ID>` per line of `.security/audit-ignores`.
The ignore expires by construction: once the advisory has a fix, the audit fails again.
Record each ID with a comment naming the advisory and the reason; delete the line when the dependency is updated.

`uv audit` is experimental in uv 0.13; the script passes `--preview-features audit-command` to silence the warning and keep the job output readable.

## Release

`bash scripts/release.sh <patch|minor|major>`:

1. refuses a dirty tree, a branch other than `main`, or a `main` behind `origin/main`;
2. runs `uv sync --frozen` and `bash scripts/check.sh`;
3. bumps `[project].version`, moves `## [Unreleased]` into `## [X.Y.Z] - <date>`, runs `uv lock`;
4. commits `release: vX.Y.Z`, creates the annotated tag, pushes `main` and the tag;
5. creates the GitHub Release with the changelog section as notes; for `kind = "lib"`, builds first and attaches `dist/*`.

A release needs a human: run it from a checkout of `main`, never from a lane.
The board merges the release commit; the tag follows it.

## PyPI (opt-in)

The pack publishes to GitHub Releases.
A repo that decides to publish to PyPI adds a workflow with `id-token: write` and `uv publish --trusted-publishing automatic`, and configures the PyPI trusted publisher for that repo and workflow.
Do not add the workflow before the decision: a dormant publisher is surface without a consumer.

## Changing this skill

- **major** — change a managed path, the tag or changelog contract, or the CI job names.
- **minor** — add a file, a job or a rule; add an opt-in recipe.
- **patch** — clarify, fix an example, correct wording.

Bump `metadata.version`, update `pack.json` and `CHANGELOG.md`, then regenerate.
