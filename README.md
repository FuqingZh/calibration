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
- `skills/calibration/SKILL.md`: default Codex engineering skill entrypoint, including architecture and implementation design judgment
- `skills/retrospect/SKILL.md`: user-invoked evidence-driven retrospective and lesson-refinement skill
- `skills/writing-code-docs/SKILL.md`: language-aware, Python-calibrated code documentation for public APIs and durable workflow boundaries
- `references/engineering/principles.md`: stable cross-project engineering principles
- `references/engineering/naming/`: naming and interface conventions, split by decision surface
- `references/engineering/discipline/`: refactoring, debugging, verification,
  repository-harness, and evaluation decisions
- `references/engineering/design/`: codebase design and boundary judgment
- `references/engineering/docs_index.md`: navigation for longer specifications
- `references/engineering/docs/`: reusable long-form specifications and patterns
- `evaluations/ai-native-implementation/`: writable repository fixtures,
  deterministic contracts, and the blind-review rubric for calibration
  behavior comparison
- `docs/README.md`: current decision, evaluation, and implementation-plan map
- `scripts/adopt_ao_repository.py`: optional plan/apply and readback gate for a
  repository using an already installed, CLI-capable AO
- `scripts/calibrate_ao_host.py`: read-only inspection and deterministic
  candidate renderer for an explicitly trusted private AO host profile
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

Install an isolated AO worker home with only first-party managed skills and
global instructions:

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
installs symlink managed first-party and vendored skills. AO worker installs
only managed first-party skills. Existing `AGENTS.md` content is backed up
before replacement when it differs.

## Development

Install the locked validation environment:

```bash
pdm sync --clean
```

Run the same repository quality gate used by GitHub Actions:

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

## AO Host Calibration

The stdlib-only host calibration CLI emits JSON for every command:

```bash
python scripts/calibrate_ao_host.py inspect
python scripts/calibrate_ao_host.py init \
  --profile /private/config/calibration/host.toml \
  --trust-model untrusted \
  --codex-home /private/codex-home \
  --data-dir /private/ao-data \
  --private-authority /private/config/calibration/AGENTS.md \
  --state-root /private/state/calibration
python scripts/calibrate_ao_host.py plan --profile /private/config/calibration/host.toml
python scripts/calibrate_ao_host.py render \
  --profile /private/config/calibration/host.toml \
  --output /private/candidate
python scripts/calibrate_ao_host.py verify \
  --profile /private/config/calibration/host.toml \
  --candidate /private/candidate
```

`inspect` needs no profile, accepts `--context auto|host|sandbox`, and defaults
its profile-free loopback probes to port 3001. `init` requires an explicit trust
model and private reconstruction paths, and keeps terminal access disabled
unless all terminal constraints are supplied.
`plan` and `verify` are read-only. `render` writes only a new deterministic
candidate tree, or accepts an existing byte-identical tree; it does not operate
services or active host configuration.

## Intent

- Keep reusable Codex skill entrypoints in `skills/`; keep architecture/design judgment in `calibration` unless it needs a distinct interaction mode.
- Keep narrow topics such as naming and project-doc placement as references unless they need a distinct interaction mode.
- Keep engineering source documents in `references/engineering/`.
- Keep AO optional and keep private host configuration outside this repository.
- Treat `~/.codex/AGENTS.md` as a local generated file; update the template in
  this repository, then rerun `install.sh`.
- Keep project-specific exceptions in each repository's local docs.
- Prefer one source of truth over duplicated guidance.

## Managed Skills

The installer also manages selected first-party skills:

- `retrospect`: evidence-driven retrospective and lesson-refinement mode for completed work and cross-stage patterns
- `writing-code-docs`: language-aware, Python-calibrated code documentation for public APIs and durable workflow boundaries

The managed third-party optional skills are:

- `brainstorming`: exploratory design mode for ambiguous work
- `grilling`: adversarial stress-test mode for plans and designs
- `writing-great-skills`: reference for writing and editing skills predictably

Third-party skills are vendored under `thirdparty/skills/`. The installer does
not download them from the network. Local patches and source notes are tracked
in `thirdparty/PATCHES.md` and `thirdparty/sources.tsv`.

`test-prompts.json` files are behavioral evaluation inputs. Their presence does
not prove an optimization or regression result until the prompts have been run
under a stated model, reasoning effort, and comparison method.

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
