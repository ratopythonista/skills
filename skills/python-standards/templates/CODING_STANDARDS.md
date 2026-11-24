# Coding Standards — {{PROJECT}}

These are the standards this repo is written to. `/code-review` reads this file to judge whether a
diff conforms; cite the section anchor when flagging a violation.

## Environment & tooling

- **Python 3.12.** Pinned in `.python-version` and declared as the floor in `pyproject.toml`
  (`requires-python = ">=3.12"`). Do not use syntax or stdlib features newer than 3.12.
- **uv is the only entry point.** Never call `python`, `pip`, `pytest`, `ruff`, or `ty` directly;
  run them through `uv run`. The locked environment (`uv.lock`) is the only environment.
- **The gate is two commands:** `uv sync --frozen` and `bash scripts/check.sh`. Every command must
  work from a clean checkout, with no `.venv`, no global tool, and no network beyond the locked
  wheels. A local task runner is allowed as a convenience, never as a gate dependency.
- **ruff owns lint and format.** Config lives in `pyproject.toml`: line length 100, target
  `py312`, rules `E`, `W`, `F`, `I`, `UP`, `B`, `SIM`, `C4`, `RUF`; ignore `E501`; double quotes.
  Do not hand-format; run `uv run ruff format` and `uv run ruff check --fix`.
- **ty owns types.** Config lives in `[tool.ty.environment]`; the check is `uv run ty check src`.
  A type error is a hard violation, not a judgement call.
- **No unexplained suppression.** A `# noqa` or `# type: ignore` carries a one-line reason on the
  same line or the line above. Suppression without a reason is a violation.
- **The standard applies to every Python file in the repo**, including scripts and tests, unless a
  rule names an exception.

## Dependencies

- **The standard library comes first; the platform comes before custom code.** Reach for a
  dependency only when the stdlib or the platform genuinely lacks the capability.
- **Default stack:** `pydantic` for DTOs and validation, `pydantic-settings` for configuration,
  `httpx` for outbound HTTP, `pytest` for tests, `ruff` and `ty` as dev tools. A project installs
  only what it uses; the list is a default, not a shopping list.
- **Every dependency outside the default stack needs a one-line justification**: what the stdlib or
  platform cannot do, and why the cost is worth it. "It is convenient" is not a justification.
- **One library per job.** Do not add a second HTTP client, settings library, validator, or test
  runner.
- **Add with `uv add`; commit `pyproject.toml` and `uv.lock` together.** Never hand-edit `uv.lock`;
  a lock that drifts from the manifest fails `uv sync --frozen`.
- **Logging uses the stdlib `logging` module** unless the profile declares a concrete need for a
  library. No module-level `basicConfig` in importable code; configure once at the entrypoint.
- **Retries stay at a boundary that can transiently fail.** No generic retry decorator around
  arbitrary code; name the failure mode and the bound.

<!-- pack-python:slot=dependencies -->

## Structure

- **src-layout.** Source lives in `src/<package>/`; never import the package from the repo root.
  Tests live in `tests/`.
- **Folders by domain, not by technical layer.** A domain owns its models, services, routes, and
  persistence. A top-level `utils/`, `helpers/`, or `common/` is not a domain; if it grows, split it
  by the concepts it actually serves.
- **One package is one deep module.** The public interface lives in the package `__init__.py`
  (re-export); callers import the package, never its internals. Internals are small files split by
  cohesion. Do not create one-class-per-file modules or pass-through re-exports that pretend to be
  modules.
- **One module has one responsibility.** If a module accumulates unrelated reasons to change, split
  it. Do not split by line count alone.
- **Large static strings and assets live in files**, read once at import through
  `Path(__file__).resolve()` relative paths. The read is cwd-independent and fails fast at import
  when the file is missing. Dynamic markup built from them uses `string.Template`.
- **Tests mirror the source tree**: one file per module under test
  (`tests/test_<module>.py`); shared fixtures in `tests/conftest.py`. Comment-separated sections
  inside one test file are a smell; split by cohesion.
- **Samples are optional.** When present, they live in `samples/`, read configuration from the
  environment with development defaults, never hard-code secrets, and have no role in the gate. A
  sample that drifts from the code it mirrors says so in its docstring.

<!-- pack-python:slot=structure -->

## Naming

- **Casing follows the object:** `snake_case` for modules, packages, functions, and variables;
  `PascalCase` for classes, exceptions, and type aliases; `UPPER_SNAKE` for module-level constants.
- **Private names start with `_`.** A name without the underscore is part of the module's contract.
- **No abbreviations outside established domain vocabulary.** `http`, `url`, `id`, and `db` are
  fine; `usr`, `cfg`, `mgr`, `tmp` are not. When the domain already names the concept, use that
  word.
- **Booleans read as predicates:** `is_active`, `has_items`, `can_publish`. Avoid `flag`, and avoid
  negation in the name (`not_found` is a state, `is_not_found` is a double negative).
- **Tests describe behaviour:** `test_<unit>_<expected_behaviour>`, for example
  `test_parse_config_rejects_empty_stage_list`. No numbered suffixes and no implementation names.
- **Same concept, same name.** If the repo has a glossary or context file, its term wins across
  modules, tests, and docs. A synonym for an existing concept is a naming defect.
- **Package names are short lowercase identifiers**; underscores are allowed only when they make
  the name readable. The distribution name may use hyphens.

## Typing

- **All new code is fully annotated:** function parameters and return types, module-level constants
  whose type is not obvious, and dataclass/TypedDict fields.
- **Prefer precise types over `Any`.** If a third-party type is genuinely unknown, isolate it at the
  boundary and narrow it immediately with `isinstance` or explicit `None` guards.
- **`ty check` must pass**, and it runs inside the gate. Fix the code or the annotation; do not
  silence the checker.
- **`cast` is a boundary tool.** Use it only where the runtime contract was just verified, and say
  why in a comment.

## Pydantic & configuration

- **Pydantic is the default** for DTOs, schemas, and validated boundaries. A profile may declare a
  different mechanism for its own boundary, but Pydantic remains the default elsewhere.
- **Every field declares `Field(..., description=...)`.** The description is mandatory; it feeds
  documentation, validation errors, and downstream contracts.
- **Fields carry a default whenever one is meaningful.** Write
  `Field(default=None, description=...)` with a precise `X | None` type. A required field is an
  explicit exception whose description says why no safe default exists.
- **Optional fields stay precisely typed.** Never use a bare `str` holding the string `"None"`.
- **One small `BaseSettings` class per concern**, with `SettingsConfigDict(extra="ignore")` and
  plain defaults. Do not build a fat settings class, and do not scatter `os.getenv` through the
  code.
- **Inject settings; do not import a global singleton deep in the call graph.** The entrypoint
  builds the settings object and passes it down.

<!-- pack-python:slot=pydantic -->

## Testing policy

- **pytest runs through `uv run pytest`.** Configuration lives in `[tool.pytest.ini_options]` with
  `testpaths = ["tests"]`. The gate runs the suite from a clean checkout.
- **One test file per module under test.** Every non-trivial branch gets at least one test. A bug
  fix adds a regression test that fails before the fix and passes after it.
- **Test names describe behaviour**, not implementation: `test_<unit>_<expected_behaviour>`.
- **Tests are deterministic and fast.** No network calls, no writes outside `tmp_path`, no sleeps
  for timing, no dependence on execution order.
- **E2E is marked and excluded by default.** Browser flows carry the `e2e` marker, stay out of
  `check.sh`, and run in the QA lane where a browser is available.
- **Coverage is part of the gate:** 90% of lines and branches, measured over `src`, failing the
  gate below the threshold. Exclude `*/migrations/*`, `manage.py`, `*/settings.py`, `*/asgi.py`,
  `*/wsgi.py`, `*/apps.py`, and `tests/`. The command lives in `scripts/check.sh`; the mechanics
  (fixtures, test client, Playwright) live in `python-testing`.

## Delivery

- **One version source:** `[project].version` in `pyproject.toml`. The release tag is the same number prefixed with `v`; a second version file is a defect.
- **Every release updates `CHANGELOG.md`**, which follows Keep a Changelog. `## [Unreleased]` sits at the top; a release names it `## [X.Y.Z] - YYYY-MM-DD`. An empty Unreleased means there is no release.
- **Tags are annotated `vX.Y.Z` and cut from `main`.** A published tag is immutable: fix forward with a new patch.
- **The GitHub Release notes are the changelog section**, never a second document.
- **Public repos ship `LICENSE` and declare `[project].license`.** Private repos may omit it; the pack default is MIT.
- **Apps release without artifacts; libraries attach wheel and sdist** to the GitHub Release. PyPI publication is an explicit decision per repo, through trusted publishing.
- **CI runs the same two gate commands as the board**, plus the dependency audit and the secret scan. A second definition of the gate is a defect.
- **The dependency audit blocks the merge.** An advisory without a fix is accepted in `.security/audit-ignores` by ID, with the reason in a comment, until a fix exists.
- **Secrets are never committed.** The scanner is a backstop, not permission.
- **Actions are pinned by major version tag**, never by a branch.

## Size & smells

- **Size ceiling: 200 lines warns, 250 fails.** The check is `scripts/size_check.py`. `__init__.py`
  and `*/migrations/*` are exempt. Any other exception declares
  `# size-check: allow <reason>` in the first three lines, with a reason specific to the file.
- **Size is a signal, not a target.** Split by cohesion, not to hit a number.
- **One module, one responsibility.** Divergent Change means split.
- **Fowler smell baseline** applies as judgement calls: Mysterious Name, Duplicated Code, Feature
  Envy, Data Clumps, Primitive Obsession, Repeated Switches, Shotgun Surgery, Divergent Change,
  Speculative Generality, Message Chains, Middle Man, Refused Bequest.
- **Deletion over addition.** Remove dead code, unused parameters, commented-out blocks, and
  speculative extension points.

## Prose & UI copy

- **One Sentence Per Line (OSPL).** Every sentence starts on its own line in Markdown and docs.
  Break at sentence boundaries only, never at a column limit. Do not hard-wrap prose.
- **UI copy belongs to responsive layout, never to code width.** Labels, messages, tooltips,
  dialogs, and notifications are never chopped to satisfy a line-length rule.
- **Line breaks in UI copy are intentional.** Use an explicit break only when the visual layout
  requires one.
- **Long or multi-paragraph copy lives in templates or asset files**, not in Python component
  trees. The template keeps markup and prose out of the logic.
- **Never build HTML by concatenating unescaped strings.** Use the template engine, or escape
  explicitly at the boundary.
- **Comments explain why, not what.** Delete commented-out code; git has the history.

## Minimal change

- **The smallest change that works.** Question whether the task needs to exist at all (YAGNI);
  reach for the standard library before dependencies, and for native platform features before
  custom code.
- **No speculative abstraction.** No interface with one implementation, no factory for one product,
  no configuration for a value that never changes.
- **Fix at the root cause.** One guard in the shared function beats a guard in every caller.
- **Deletion over addition.** A change that removes a concept is usually better than one that adds
  a layer around it.
- **Complex requests ship the lazy version and surface the tradeoff** in the same response; the
  full version is built only on explicit request.
- **Deliberate shortcuts name their ceiling.** A shortcut with a known limit carries a
  `ponytail:` comment stating the limit and the upgrade path.

<!-- pack-python:keep -->
## Local additions

<!-- Add repo-specific rules here. This block is preserved by scaffold --check. -->
<!-- /pack-python:keep -->
