# Calibration Documentation

This directory records calibration-specific decisions, evaluations, and active
implementation plans. Reusable cross-project engineering guidance lives under
`references/engineering/`.

## Read First

1. `../README.md` for the active repository surface and installer contract.
2. `decisions/2026-07-20-agent-harness-and-evaluation-closeout.md` for the
   rejected Slice 2 candidate, completed blind evaluation, and closed pilot
   gate.
3. `decisions/2026-07-20-agent-harness-and-evaluation-ownership.md` for the
   repository-harness and behavior-evaluation ownership boundary.
4. `implementation-plan/20260721-v1.2-harness-successor-cleanup-implementation-plan.md`
   for the active successor and evaluation gates.

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
- `decisions/2026-07-20-agent-harness-and-evaluation-ownership.md`: accepted
  harness and evaluation ownership boundary; its pull request #5 behavior
  candidate was rejected separately.
- `decisions/2026-07-20-agent-harness-and-evaluation-closeout.md`: rejected
  Slice 2 behavior candidate and current Slice 3 evaluation record.

## Plan Status

The active plan is
`implementation-plan/20260721-v1.2-harness-successor-cleanup-implementation-plan.md`.
It narrows the rejected candidate and requires staged blind evaluation before
merge. Slice 4 bounded pilots remain closed. The v1.1 plan closed after Slice 3,
and the earlier v1.0 collaboration plan remains superseded.
