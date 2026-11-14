# skills

Agent skills for the Python engineering flow. One directory per skill, one `SKILL.md` per directory, MIT.

Published on [skills.sh](https://skills.sh/ratopythonista/skills) through install telemetry — installing is what
lists it.

## Install

```bash
npx skills add ratopythonista/skills                          # every skill in the repo
npx skills add ratopythonista/skills/tree/main/skills/pytest-fasthtml   # just one
```

The CLI writes the skill into your project's agent skills folder and pins it in `skills-lock.json`.

## Skills

| Skill | What it fixes |
|---|---|
| [`pytest-fasthtml`](skills/pytest-fasthtml/SKILL.md) | Test mechanics for pytest + FastHTML: where a test belongs (unit vs integration vs e2e), fixtures, async handlers, HTMX requests, Playwright, and the `uv`/`ruff` commands. |

## Layout

```
skills/<name>/SKILL.md     # one skill
skills.sh.json             # how this repo's page is grouped on skills.sh
scripts/validate.py        # frontmatter + link checks, run by CI
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
