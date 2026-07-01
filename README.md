# calibration

A personal engineering calibration system for code, agents, judgment, and
delivery.

`calibration` keeps the user's cross-project engineering principles, naming
rules, design judgment, verification discipline, Codex skill entrypoints, and
managed local setup in one repository. Skills are one presentation layer of the
system, not the system itself.

## Layout

- `install.sh`: local installer for Codex global entry and skill symlinks
- `codex/AGENTS.md.template`: canonical template for `~/.codex/AGENTS.md`
- `skills/calibration/SKILL.md`: default Codex engineering skill entrypoint, including architecture and implementation design judgment
- `skills/personal-strategy/SKILL.md`: persona-backed strategy and planning skill
- `references/engineering/principles.md`: stable cross-project engineering principles
- `references/engineering/naming/`: naming and interface conventions, split by decision surface
- `references/engineering/discipline/`: refactor, debugging, and verification gates
- `references/engineering/design/`: codebase design and boundary judgment
- `references/engineering/docs_index.md`: navigation for longer specifications
- `references/engineering/docs/`: reusable long-form specifications and patterns
- `references/persona/USER_PERSONA.md`: git-synced subject-structure profile for strategic and communication context
- `thirdparty/`: vendored optional skills and their source/patch records

## Install

Preview local Codex integration:

```bash
bash install.sh --dry-run
```

Install or refresh the local Codex entry:

```bash
bash install.sh
```

When adopting previously hand-installed optional skills for the first time, use
`--force` after reviewing `--dry-run --force` so the installer can replace those
local directories with managed symlinks.

The installer renders `codex/AGENTS.md.template` into `~/.codex/AGENTS.md`
with the current repository path and symlinks managed first-party skills from
`skills/` and managed vendored skills from `thirdparty/skills/` into
`~/.codex/skills/`. Existing `AGENTS.md` content is backed up before
replacement when it differs.

## Intent

- Keep reusable Codex skill entrypoints in `skills/`; keep architecture/design judgment in `calibration` unless it needs a distinct interaction mode.
- Keep narrow topics such as naming and project-doc placement as references unless they need a distinct interaction mode.
- Keep engineering source documents in `references/engineering/`.
- Keep the user persona context in `references/persona/`; it is not an engineering rule file.
- Treat `~/.codex/AGENTS.md` as a local generated file; update the template in
  this repository, then rerun `install.sh`.
- Keep project-specific exceptions in each repository's local docs.
- Prefer one source of truth over duplicated guidance.

## Managed Optional Skills

The installer also manages selected user-invoked third-party skills:

- `brainstorming`: exploratory design mode for ambiguous work
- `grilling`: adversarial stress-test mode for plans and designs
- `writing-great-skills`: reference for writing and editing skills predictably

These skills are vendored under `thirdparty/skills/`. The installer does not
download them from the network. Local patches and source notes are tracked in
`thirdparty/PATCHES.md` and `thirdparty/sources.tsv`.

## Rename Note

`calibration` replaces the old `engineering-canon` repository name and the old
`global-defaults` skill name. The migration is intentionally not
backward-compatible: use the installer to remove retired local skill links and
install the current `$calibration` entrypoint.
