# Calibration Documentation

This directory records calibration-specific decisions, evaluations, and active
implementation plans. Reusable cross-project engineering guidance lives under
`references/engineering/`.

## Read First

1. `../README.md` for the active repository surface and installer contract.
2. `decisions/2026-07-21-harness-successor-evaluation-closeout.md` for the
   rejected v1.2 successor, staged blind evaluation, and current pilot gate.
3. `decisions/2026-07-20-agent-harness-and-evaluation-ownership.md` for the
   accepted repository-harness and behavior-evaluation ownership boundary.
4. `implementation-plan/20260721-v1.2-harness-successor-cleanup-implementation-plan.md`
   for the closed successor plan and its Stage B failure.

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

## Plan Status

The latest plan is
`implementation-plan/20260721-v1.2-harness-successor-cleanup-implementation-plan.md`.
It closed after Stage B rejected the successor, so Slice 4 bounded pilots remain
inactive. A later task must propose a materially scoped new candidate and
complete a new evaluation before reopening pilots. The v1.1 plan remains a
closed predecessor, and the earlier agent-harness collaboration plan remains
superseded after its static validation slice completed in pull request #4.
