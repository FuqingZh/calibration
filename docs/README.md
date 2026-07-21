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

## Current Boundary

There is no active calibration-optimization plan. The v1.2 successor plan
closed after Stage B, the v1.1 plan is a closed predecessor, and the earlier
agent-harness collaboration plan is superseded. Future work should apply the
accepted principles in real projects and bring back repeated evidence; do not
continue tuning calibration wording without a concrete cross-project failure.

Slice 4 bounded pilots remain inactive. Reopen a pilot only through a separate
project decision with a concrete need and verification path, not as a default
continuation of the closed evaluation plans.
