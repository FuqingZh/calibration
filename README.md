# engineering-canon

Cross-project engineering source of truth for Codex skills, engineering
references, naming rules, and reusable structural specifications.

## Layout

- `install.sh`: local installer for Codex global entry and skill symlinks
- `codex/AGENTS.md.template`: canonical template for `~/.codex/AGENTS.md`
- `skills/global-defaults/SKILL.md`: default Codex engineering skill entrypoint, including architecture and implementation design judgment
- `skills/personal-strategy/SKILL.md`: persona-backed strategy and planning skill
- `references/engineering/principles.md`: stable cross-project engineering principles
- `references/engineering/naming.md`: naming and interface conventions
- `references/engineering/docs_index.md`: navigation for longer specifications
- `references/engineering/docs/`: reusable long-form specifications and patterns
- `references/persona/USER_PERSONA.md`: git-synced subject-structure profile for strategic and communication context

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
with the current repository path and symlinks managed skills from `skills/`
into `~/.codex/skills/`. Existing `AGENTS.md` content is backed up before
replacement when it differs.

## Intent

- Keep reusable Codex skill entrypoints in `skills/`; keep architecture/design judgment in `global-defaults` unless it needs a distinct interaction mode.
- Keep narrow topics such as naming and project-doc placement as references unless they need a distinct interaction mode.
- Keep engineering source documents in `references/engineering/`.
- Keep the user persona context in `references/persona/`; it is not an engineering rule file.
- Treat `~/.codex/AGENTS.md` as a local generated file; update the template in
  this repository, then rerun `install.sh`.
- Keep project-specific exceptions in each repository's local docs.
- Prefer one source of truth over duplicated guidance.
