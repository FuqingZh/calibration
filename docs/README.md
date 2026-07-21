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
4. `decisions/2026-07-21-repository-delivery-feedback-loop.md` for the accepted
   failure-driven repository delivery loop.
5. `implementation-plan/20260721-v1.4-repository-engineering-capability-adoption-implementation-plan.md`
   for the current proportional adoption work and its two repository pilots.

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
- `decisions/2026-07-21-repository-delivery-feedback-loop.md`: accepted
  failure-driven repository delivery feedback boundary; merged by PR #10.

## Current Boundary

The v1.3 repository-delivery feedback loop is accepted and closed. The active
v1.4 plan adds a proportional repository capability adoption entrypoint, then
tests it on `bio_plot` as an application/Symphony pilot and on `biofetch` as a
non-application transfer check.

These pilots do not authorize bulk environment provisioning, mandatory
per-repository configuration, auto-merge, or project-specific operating rules
inside calibration.
