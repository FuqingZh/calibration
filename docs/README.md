# Calibration Documentation

This directory records calibration-specific decisions, evaluations, and active
implementation plans. Reusable cross-project engineering guidance lives under
`references/engineering/`.

## Read First

1. `../README.md` for the active repository surface and installer contract.
2. `decisions/2026-07-20-agent-harness-and-evaluation-closeout.md` for the
   rejected Slice 2 candidate, completed blind evaluation, and closed pilot
   gate.
3. `decisions/2026-07-20-skill-optimization-evaluation-closeout.md` for the
   accepted prior skill baseline and earlier evaluation limitations.
4. `decisions/2026-07-20-agent-contribution-and-task-isolation.md` for commit
   identity, PR ownership, Worktree, and task-boundary decisions.
5. `decisions/2026-07-20-agent-harness-and-evaluation-ownership.md` for the
   repository-harness and behavior-evaluation ownership boundary.
6. `implementation-plan/20260720-v1.1-agent-harness-evaluation-implementation-plan.md`
   for the closed execution record and successor handoff.

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
  harness and evaluation ownership decision.
- `decisions/2026-07-20-agent-harness-and-evaluation-closeout.md`: rejected
  Slice 2 behavior candidate and current Slice 3 evaluation record.

## Plan Status

The latest plan is
`implementation-plan/20260720-v1.1-agent-harness-evaluation-implementation-plan.md`.
It closed after Slice 3 rejected the evaluated candidate, so Slice 4 bounded
pilots are not active. The next task must choose a narrow reversal or corrected
successor and complete a new evaluation before reopening pilots. The earlier
agent-harness collaboration plan remains superseded after its static validation
slice completed in pull request #4.
