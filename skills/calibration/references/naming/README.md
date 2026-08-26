# Naming

This directory is the cross-project source of truth for naming and interface
conventions.

Use this index as a router. Read only the file needed for the current naming
decision.

## Routing

| Current decision | Read |
| --- | --- |
| Public or module-level function names | `function.md` |
| Public object method names | `method.md` |
| Class, dataclass, enum, config, plan, report, or adapter type names | `type.md` |
| CLI option names | `cli.md` |
| Local variable, parameter, dictionary, and structural role names | `variable.md` |
| Loop, lambda, closure, or anonymous-function binder names | `loop.md` |
| Public-facing schema fields and exported headers | `schema.md` |
| Workflow artifact filenames | `artifact.md` |
| Git branch names | `branch.md` |

## Scope

- Public API naming
- Module-level function prefixes
- Public method boundaries
- Public CLI option naming
- Public-facing schema and export header naming
- Internal variable naming guidance
- Loop and closure binder naming guidance
- Workflow artifact filename prefixes
- Branch naming conventions

Internal variable, loop, and closure binder naming is guidance, not a merge
gate unless a repository-local rule makes it one.
