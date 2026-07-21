# Calibration Documentation

This directory records calibration-specific decisions, evaluations, and active
implementation plans. Reusable cross-project engineering guidance lives under
`references/engineering/`.

## Read First

1. `../README.md` for the active repository surface and installer contract.
2. `decisions/2026-07-20-agent-harness-and-evaluation-ownership.md` for the
   accepted repository-harness and behavior-evaluation ownership boundary.
3. `decisions/2026-07-21-harness-successor-evaluation-closeout.md` for the
   rejected v1.2 candidate and why its result remains historical evidence
   rather than the current optimization agenda.
4. `decisions/2026-07-21-repository-delivery-feedback-loop.md` and
   `implementation-plan/20260721-v1.3-repository-delivery-feedback-loop-implementation-plan.md`
   for the active evidence-driven delivery-loop candidate and smoke gate.

## Decision Status

- `decisions/2026-07-01-calibration-rename-and-skill-architecture.md`:
  implemented historical architecture decision.
- `decisions/2026-07-01-calibration-follow-up-batches.md`: superseded batch
  record.
- `decisions/2026-07-01-document-types-retrospect-and-evaluation.md`: partially
  superseded historical decision.
- `decisions/2026-07-03-writing-docstrings-skill-design.md`: superseded by
  `writing-code-docs`.
- `decisions/2026-07-20-skill-optimization-evaluation-closeout.md`: accepted
  prior skill baseline and earlier evaluation limitations.
- `decisions/2026-07-20-agent-contribution-and-task-isolation.md`: current
  collaboration decision.
- `decisions/2026-07-20-agent-harness-and-evaluation-ownership.md`: current
  accepted harness and evaluation ownership boundary; the pull request #5 and
  #7 behavior candidates were rejected separately.
- `decisions/2026-07-20-agent-harness-and-evaluation-closeout.md`: rejected
  Slice 2 behavior candidate and current Slice 3 evaluation record.
- `decisions/2026-07-21-harness-successor-evaluation-closeout.md`: rejected
  pull request #7 successor and current staged evaluation record.
- `decisions/2026-07-21-repository-delivery-feedback-loop.md`: active candidate
  for failure-driven repository delivery feedback; acceptance is pending two
  real cloud smoke tasks.

## Current Boundary

The v1.3 repository-delivery feedback-loop candidate is the only active plan.
It responds to a concrete cloud execution failure and must pass read-only smoke
validation in two real repositories before acceptance. The rejected v1.2
candidate remains closed and is not its behavioral baseline.

Broader project pilots, orchestrator work, bulk environment provisioning, and
per-repository scheduled tasks remain inactive.
