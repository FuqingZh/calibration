# engineering-canon

Cross-project engineering source of truth for global defaults, naming rules,
and reusable structural specifications.

## Layout

- `install.sh`: local installer for Codex global entry and skill symlink
- `codex/AGENTS.md.template`: canonical template for `~/.codex/AGENTS.md`
- `global-defaults/SKILL.md`: Codex skill entrypoint
- `global-defaults/references/principles.md`: stable cross-project engineering principles
- `global-defaults/references/naming.md`: naming and interface conventions
- `global-defaults/references/docs_index.md`: navigation for longer specifications
- `global-defaults/docs/`: reusable long-form specifications and patterns
- `persona/USER_PERSONA.md`: git-synced subject-structure profile for strategic and communication context

## Install

Preview local Codex integration:

```bash
bash install.sh --dry-run
```

Install or refresh the local Codex entry:

```bash
bash install.sh
```

The installer renders `codex/AGENTS.md.template` into `~/.codex/AGENTS.md`
with the current repository path and symlinks `global-defaults/` into
`~/.codex/skills/global-defaults`. Existing `AGENTS.md` content is backed up
before replacement when it differs.

## Intent

- Keep cross-project engineering defaults in `global-defaults/`.
- Keep the user persona context in `persona/`; it is not an engineering rule file.
- Treat `~/.codex/AGENTS.md` as a local generated file; update the template in
  this repository, then rerun `install.sh`.
- Keep project-specific exceptions in each repository's local docs.
- Prefer one source of truth over duplicated guidance.
