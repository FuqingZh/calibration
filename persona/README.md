# Persona Context

This directory stores git-synced user persona context for Codex and other AI agents.

## Files

- `USER_PERSONA.md`: canonical subject-structure profile for 张富卿.

## Purpose

The persona profile explains why the user tends to prefer structure, restraint,
reality-contact, auditability, and direct critique. It is not an engineering rule
file and should not replace project-specific instructions.

Use it for tasks involving:

- strategic direction
- career and life planning
- long-term priorities
- communication style
- architectural judgment with personal tradeoffs
- explicit requests to reason from the user's subject structure

Do not load it by default for ordinary coding, refactoring, tests, or mechanical
implementation tasks. For those tasks, use `$global-defaults` and repository-local
instructions.

## Recommended Codex setup

Add this short index to `~/.codex/AGENTS.md`, adjusting the path if this repository
is cloned elsewhere:

```markdown
## User Persona Context

The user's git-synced persona profile is located at:
`/home/being/projects/engineering-canon/persona/USER_PERSONA.md`.

Read it when the task involves strategic direction, career/life planning,
long-term priorities, architectural judgment with personal tradeoffs,
communication style, or explicit requests to reason from the user's
subject structure.

Do not load it by default for ordinary coding, refactoring, tests, or
mechanical implementation tasks. For those, follow `$global-defaults` and
repository-local instructions.
```
