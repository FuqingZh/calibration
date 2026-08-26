# Discipline

This directory contains operational engineering discipline references.

Use this index as a router. Read only the file needed for the current task.

## Routing

| Current task | Route |
| --- | --- |
| Refactor, migration, extraction, file split, import cleanup, suppression cleanup, or convergence work | `refactor.md` |
| Bug, runtime failure, failing test, unclear behavior, or root-cause analysis | `debugging.md` |
| Completion claim, release check, deployment check, generated output, external write, or user-visible artifact validation | `verification.md` |
| Ordinary actionable GitHub pull-request feedback | Installed `github:gh-address-comments`; otherwise repository- or platform-native tooling |
| Failing GitHub Actions pull-request checks | Installed `github:gh-fix-ci`; otherwise repository- or platform-native tooling |
| Repeated agent stalls, missing repository capability, `AGENTS.md`, human escalation, or orchestration adoption | `harness.md` |
| Repeated delivery failure, missing CI or review capability, cross-contract feedback, review-convergence exhaustion, or cloud execution failure | `harness.md` |
| Repository quality-gate adoption, Python lint policy, or Ruff rule selection | `harness.md` |
| Agent, skill, harness, or workflow quality comparison on representative tasks | `evaluation.md` |

## Scope

These files are operational decision references and execution gates. They
should change what the agent diagnoses, places, evaluates, or checks before
claiming progress or completion. Keep broad principles in `../principles.md`
and long domain specifications under `../docs/`.
