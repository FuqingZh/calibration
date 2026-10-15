# Calibration Documentation

Calibration is in stable maintenance mode. This index separates current
authority, recorded open work, and historical evidence.

## Start Here

1. Read the [repository README](../README.md) for installation and development.
2. Use the [calibration router](../skills/calibration/SKILL.md) to select reusable
   references; long-form guidance has one [document router](../skills/calibration/references/docs_index.md).
3. Follow [AGENTS.md](../AGENTS.md) for repository validation and contribution rules.

## Public Architecture

Reusable references live inside the owning skills, which provide model
interaction entrypoints. Repository tools own setup and validation. Private host
configuration stays outside this repository and is read only for explicit host
operations. Calibration does not provide an orchestrator integration.

## Current Authority

| Need | Source |
| --- | --- |
| Repository and installer contract | [README](../README.md) |
| Cross-project judgment and routing | [Principles](../skills/calibration/references/principles.md), [skill router](../skills/calibration/SKILL.md) |
| Repository capability and delivery placement | [Harness](../skills/calibration/references/discipline/harness.md) |
| Completion and external-result evidence | [Verification](../skills/calibration/references/discipline/verification.md) |
| Agent and workflow comparisons | [Evaluation](../skills/calibration/references/discipline/evaluation.md) |
| Document layout and lifecycle | [Project docs architecture](../skills/calibration/references/docs/workflow/project_docs_architecture/20260805-v1.1-project-docs-architecture.md) |
| Durable implementation-plan contract | [Implementation plans](../skills/calibration/references/docs/document-types/implementation-plan.md) |
| Explicit conversation closeout | [Closeout skill](../skills/closeout/SKILL.md) |

The installer and skill sources define active behavior. Adoption rationale,
completed comparisons, and superseded protocols are indexed in the
[historical records](archive/README.md), with their original evidence limits.
Completed evaluations do not establish general model or cross-client quality.

## Recorded Open Work

- [Project docs convergence](implementation-plans/20260805-v1.0-project-docs-architecture-convergence-implementation-plan.md):
  local slices are complete; the recorded downstream owner migration remains
  pending. This index does not verify another repository's current state.
- [Body compression trial](decisions/2026-09-20-calibration-body-compression-and-routing.md):
  the three adopted bodies remain current; metadata candidates and real-work
  performance remain unverified.
- [Coding-protocol retirement trial](decisions/2026-09-07-coding-protocol-runtime-retirement-trial.md):
  the runtime entry remains retired; retained source supports restoration.

## Validation

[AGENTS.md](../AGENTS.md#validation) owns proportional check selection and the
complete gate; `pdm.lock` owns validation dependencies. The existing PDM tasks
remain the local and CI entrypoints. The [check-routing assessment](decisions/20261011-v1.0-check-routing-and-nx-decision-record.md)
records why Nx is not adopted in this cleanup.

## Historical Evidence

Use the [archive index](archive/README.md) for completed plans, corrected or
superseded comparisons, adoption decisions, and old AO guidance. Historical
records stay at their existing paths for link compatibility. Raw evidence,
manifests, hashes, provenance, and compatibility cleanup remain preserved.
