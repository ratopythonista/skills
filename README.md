# skills

Agent skills for the Python engineering flow. One directory per skill, one `SKILL.md` per directory, MIT.

Published on [skills.sh](https://skills.sh/ratopythonista/skills) through install telemetry — installing is what
lists it.

## Install

```bash
npx skills add ratopythonista/skills                                            # every skill in the repo
npx skills add https://github.com/ratopythonista/skills/tree/main/skills/pytest-fasthtml  # just one
```

The `owner/repo` form installs the whole repo; the single-skill form needs the full URL — a bare
`ratopythonista/skills/tree/main/...` is read as an unknown repository and reports `No skills found`.

The CLI writes the skill into your project's agent skills folder (`.agents/skills/<name>`, symlinked into
`.claude/skills`) and pins it in `skills-lock.json`.

## Skills

| Skill | What it fixes |
|---|---|
| [`python-scaffold`](skills/python-scaffold/SKILL.md) | Deterministic project generation from the pack templates: `web` profile (Django 6.1 + HTMX + Tailwind + Granian), src-layout, `uv` lock, managed `check.sh` and `size_check.py`. |
| [`python-verify`](skills/python-verify/SKILL.md) | The merge gate: canonical `verify_commands`, `scripts/check.sh`, the 200/250 size check, drift and CI playbook. |
| [`pytest-fasthtml`](skills/pytest-fasthtml/SKILL.md) | Test mechanics for pytest + FastHTML: where a test belongs (unit vs integration vs e2e), fixtures, async handlers, HTMX requests, Playwright, and the `uv`/`ruff` commands. |

`pack.json` is the single source for the pack's skill ranges, canonical verify commands, size thresholds and
the generated file list. `scripts/validate.py` checks every implemented skill against it.

## Layout

```
skills/<name>/SKILL.md     # one skill
skills/<name>/scripts/     # executables the skill owns (scaffold)
skills/<name>/templates/   # canonical bytes a skill owns (scaffold, verify)
pack.json                  # pack compatibility, commands, size policy, generated files
skills.sh.json             # how this repo's page is grouped on skills.sh
scripts/validate.py        # frontmatter, links, pack consistency; run by CI
```

## Adding a skill

1. `skills/<name>/SKILL.md` — the directory name **is** the skill name; `name:` must match it.
2. Frontmatter allows only `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`.
3. `description:` is one line, plain scalar — no `>-`, no `|`, no `": "` inside it. It is what triggers the
   skill, and the registries parse it line by line.
4. Bump `metadata.version` and add a `CHANGELOG.md` entry.
5. `python3 scripts/validate.py` must pass; CI runs the same script.

## Language

English. Skill descriptions are matched by models against English task text, so a non-English description is
only ever found by its author.

## Versioning

Semantic versioning, per skill, in `metadata.version`:

- **patch** — wording, a fixed command, a broken link.
- **minor** — a new section or rule that does not invalidate existing advice.
- **major** — a rule reversed, a section removed, a rename.

The repo tag names the set (`v0.1.0`); the frontmatter names the skill. A consumer reads the frontmatter.

## License

MIT — see [LICENSE](LICENSE).
