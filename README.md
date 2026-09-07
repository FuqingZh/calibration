# calibration

An engineering calibration system for code, agents, judgment, and delivery.

`calibration` keeps cross-project engineering principles, naming rules, design
judgment, verification discipline, Codex skill entrypoints, and managed local
setup in one repository. Skills are one presentation layer of the system, not
the system itself. AO is an optional environment adapter; private host
configuration remains outside the public repository.

## Layout

- `install.sh`: local installer for Codex global entry and skill symlinks
- `codex/AGENTS.md.template`: canonical template for `~/.codex/AGENTS.md`
- `skills/calibration/`: self-contained default Codex engineering skill,
  including its routed engineering references
- `skills/closeout/SKILL.md`: explicitly invoked whole-conversation documentation and handoff entrypoint
- `skills/retrospect/`: self-contained user-invoked evidence-driven
  retrospective and lesson-refinement skill
- `skills/writing-code-docs/SKILL.md`: language-aware, Python-calibrated code documentation for public APIs and durable workflow boundaries
- `skills/calibration/references/principles.md`: stable cross-project engineering principles
- `skills/calibration/references/naming/`: naming and interface conventions,
  split by decision surface
- `skills/calibration/references/discipline/`: refactoring, debugging, verification,
  repository-harness, and evaluation decisions
- `skills/calibration/references/design/`: codebase design and boundary judgment
- `skills/calibration/references/docs_index.md`: navigation for longer specifications
- `skills/calibration/references/docs/`: reusable long-form specifications and patterns
- `evaluations/ai-native-implementation/`: writable repository fixtures,
  deterministic contracts, and the blind-review rubric for calibration
  behavior comparison
- `evaluations/teach-adaptation/`: sanitized fixtures, outputs, arm mapping,
  and blind judgment for the bounded `teach` adoption comparison
- `docs/README.md`: current decision, evaluation, and implementation-plan map
- `scripts/adopt_ao_repository.py`: optional plan/apply and readback gate for a
  repository using an already installed, CLI-capable AO
- `thirdparty/`: vendored optional skills and their source/patch records
- `pyproject.toml` and `pdm.lock`: locked repository validation environment and
  the canonical local/CI task entrypoints

## Install

Preview local Codex integration:

```bash
bash install.sh --dry-run
```

Install or refresh the local Codex entry:

```bash
bash install.sh
```

The default `standard` profile preserves the existing installation behavior:

```bash
bash install.sh --profile standard
```

Install an isolated AO worker home with first-party managed skills and global
instructions:

```bash
bash install.sh --profile ao-worker --codex-home /path/to/worker-home
```

`ao-worker` requires an explicit non-root `--codex-home`. The installer does
not read or modify `config.toml`, `auth.json`, Apps, Plugins, or MCP state.

When adopting previously hand-installed optional skills for the first time, use
`--force` after reviewing `--dry-run --force` so the installer can replace those
local directories with managed symlinks.

The installer renders `codex/AGENTS.md.template` into the selected Codex home
with the current repository path and a conditional pointer to private host
authority at `$XDG_CONFIG_HOME/calibration/AGENTS.md`, or
`$HOME/.config/calibration/AGENTS.md` when `XDG_CONFIG_HOME` is unset. Standard
installs symlink managed first-party skills and standard-only optional vendored
skills. AO worker installs only managed first-party skills; optional third-party
skills remain excluded. Existing
`AGENTS.md` content is backed up before replacement when it differs.

## Development

Install the locked validation environment:

```bash
pdm sync --clean
```

Select validation proportionally to the affected behavior and contracts. Run
the smallest relevant checks unless repository policy or the changed surface
requires the complete gate. The complete repository quality gate used by
GitHub Actions is:

```bash
pdm lock --check
pdm run check
```

The gate runs Ruff, Pyright, rumdl, first-party Markdown link validation,
ShellCheck, pytest with 100% line coverage for repository-owned Python tools,
and the skill validator. Installer behavior tests always use isolated temporary
`CODEX_HOME` directories; the development gate does not modify the active
Codex installation. Ruff linting uses the explicit stable baseline `E`, `F`,
`I`, `UP`, `B`, `SIM`, and `RUF`; preview rules are not enabled.

## Intent

- Keep reusable Codex skill entrypoints in `skills/`; keep architecture/design judgment in `calibration` unless it needs a distinct interaction mode.
- Keep narrow topics such as naming and project-doc placement as references unless they need a distinct interaction mode.
- Keep every first-party skill's source documents inside that skill directory;
  calibration's engineering references live in `skills/calibration/references/`.
- Keep AO optional and keep private host configuration outside this repository.
- Treat `~/.codex/AGENTS.md` as a local generated file; update the template in
  this repository, then rerun `install.sh`.
- Keep project-specific exceptions in each repository's local docs.
- Prefer one source of truth over duplicated guidance.

## Managed Skills

The installer also manages selected first-party skills:

- `closeout`: explicitly invoked whole-conversation documentation gap filling and unresolved-context handoff
- `retrospect`: evidence-driven retrospective and lesson-refinement mode for completed work and cross-stage patterns
- `writing-code-docs`: language-aware, Python-calibrated code documentation for public APIs and durable workflow boundaries

The managed third-party optional skills are:

- `brainstorming`: exploratory design mode for ambiguous work
- `grilling`: adversarial stress-test mode for plans and designs
- `teach`: explicitly invoked teaching with session-only mode or isolated
  personal learning state

`coding-protocol` is archived from runtime installation for a reversible trial.
Both profiles remove only its symlink owned by this repository, preserving
foreign links and directories even with `--force`. Its pinned source, body,
metadata, references, and licenses remain under `thirdparty/`.
The [trial and restoration instructions](docs/decisions/2026-09-07-coding-protocol-runtime-retirement-trial.md)
record its evidence limits and rollback. Other optional third-party skills
remain standard-only and explicitly invoked.

Third-party skills are vendored under `thirdparty/skills/`. The installer does
not download them from the network. Local patches and source notes are tracked
in `thirdparty/PATCHES.md` and `thirdparty/sources.tsv`.

Optional GitHub workflow integrations are not vendored or managed by this
installer. When available, ordinary actionable pull-request feedback routes to
`github:gh-address-comments`, and failing GitHub Actions checks route to
`github:gh-fix-ci`. They provide mechanics without granting write or scope
authority. When unavailable, use repository- or platform-native tooling rather
than silently installing a provider or invoking calibration for routine work.

`test-prompts.json` files are behavioral evaluation inputs. Their presence does
not prove an optimization or regression result until the prompts have been run
under a stated model, reasoning effort, and comparison method.

The installed `teach` adaptation has bounded regression-acceptance evidence in
`docs/decisions/2026-08-13-teach-adaptation-evaluation.md`, with reconstructable
sanitized evidence under `evaluations/teach-adaptation/`. It does not claim a
general improvement in teaching effectiveness or token use.

`writing-great-skills` is archived: its source and license remain vendored for
provenance, but neither profile installs it. Refreshing an installation removes
only its symlink owned by this repository and preserves foreign links.

`writing-plans` remains vendored for source and provenance review but is no
longer installed as a runtime skill. Codex Plan Mode plus the
implementation-plan reference owns planning behavior. `darwin-skill` is
retired and no longer vendored; `thirdparty/sources.tsv` retains its immutable
upstream refs, and the installer still removes links it owns under the retired
name while preserving foreign links.

The stale `grill-me` skill name is retired in favor of `grilling`. Existing
unmanaged `grill-me` directories are removed only when running the installer
with `--force`.

`writing-docstrings` is retired in favor of the language-aware
`writing-code-docs` skill. The installer removes the old symlink only when it
still points to this repository's retired first-party path.

## Rename Note

`calibration` replaces the old `engineering-canon` repository name and the old
`global-defaults` skill name. The migration is intentionally not
backward-compatible: use the installer to remove retired local skill links and
install the current `$calibration` entrypoint.
