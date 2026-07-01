# Discipline

This directory contains operational engineering discipline references.

Use this index as a router. Read only the file needed for the current task.

## Routing

| Current task | Read |
| --- | --- |
| Refactor, migration, extraction, file split, import cleanup, suppression cleanup, or convergence work | `refactor.md` |
| Bug, runtime failure, failing test, unclear behavior, or root-cause analysis | `debugging.md` |
| Completion claim, release check, deployment check, generated output, external write, or user-visible artifact validation | `verification.md` |

## Scope

These files are execution gates. They should change what the agent checks before
claiming progress or completion. Keep broad principles in `../principles.md` and
long domain specifications under `../docs/`.
