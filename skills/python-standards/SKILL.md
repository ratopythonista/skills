---
name: python-standards
description: The normative Python standards for the pack. Use when writing or reviewing Python code, when a repo needs CODING_STANDARDS.md, when `/code-review` asks which rule a diff violates, or when a card's Skills line names python-standards.
license: MIT
metadata:
  version: 1.0.0
---

# Standards — the normative layer

This skill owns the **text** of the pack's Python standard. The canonical file is
[`templates/CODING_STANDARDS.md`](templates/CODING_STANDARDS.md); `python-scaffold` materializes it as
`CODING_STANDARDS.md` at the project root. Do not keep a second copy of the rules in a repo.

The generated file is the norm of the repo. If it disagrees with this skill, the repo file wins; if it
disagrees with a profile skill, the repo file also wins. A conflict between skills is a defect in the
lower-precedence skill, fixed at the source.

## Precedence

```text
CODING_STANDARDS.md of the repo > python-standards > python-web > procedure
```

`python-scaffold`, `python-verify` and `python-testing` are procedure. Only this skill and the profile
fragment are normative.

## The file

- One `CODING_STANDARDS.md` per Python repo, next to `pyproject.toml`.
- English. `/code-review` reads it as the Standards axis and cites a section anchor.
- Sections, in order: Environment & tooling; Dependencies; Structure; Naming; Typing;
  Pydantic & configuration; Testing policy; Size & smells; Prose & UI copy; Minimal change.
- Each rule is imperative and self-contained. A rule that needs a recipe belongs in the skill that owns
  the procedure, not here.

## Managed blocks

The scaffold writes the file. Only two regions survive regeneration:

| Region | Owner | Behavior |
| :--- | :--- | :--- |
| `<!-- pack-python:keep -->` … `<!-- /pack-python:keep -->` | the repo | preserved byte for byte; one block, at the end |
| `<!-- pack-python:override rule=... -->` … `<!-- /pack-python:override -->` | the profile skill | generated, never edited locally |

The stamp is a single HTML comment at the top with `format`, `managed-by`, `profile` and the
`name@version` of each applied skill. No hash, no timestamp. `scaffold.py --check` is the drift check.

A profile may override only the rules declared in the pack manifest. In the web profile that is
`dependencies`, `structure` and `pydantic`. Any other marker is a defect.

## Changing the standard

Semver in `metadata.version` follows the obligation, not the byte count:

- **major** — remove or rename a rule or anchor, make a requirement incompatible, raise the Python
  floor, change the keep/override schema.
- **minor** — add a rule, a section or an override slot; add a default dependency.
- **patch** — clarify, fix an example, correct wording without changing the obligation.

Change the template first, bump the version, update `pack.json` and `CHANGELOG.md`, then regenerate the
projects. A project that cannot be regenerated is a migration, not a silent drift.

## Anti-patterns

- Copying the rules into `README.md`, an `AGENTS.md` or a second standards file.
- Editing generated sections of `CODING_STANDARDS.md`; the next `--check` fails and the edit is lost.
- Adding a rule that only one profile can satisfy; that is a profile override, not a base rule.
- Bumping the version for a typo without updating the changelog.
