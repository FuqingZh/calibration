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
5. `decisions/2026-07-21-repository-engineering-capability-adoption-closeout.md`
   for the closed proportional adoption pilots, the bounded Symphony `NO-GO`,
   and the separate `biofetch` CI result.
6. `decisions/2026-07-22-symphony-readiness-and-bounded-canary-closeout.md`
   for the current pinned-engine readiness result, dependency and full-suite
   blockers, and explicit reopen conditions.
7. `implementation-plan/20260722-v1.5-symphony-readiness-and-bounded-canary-implementation-plan.md`
   for the closed gate definitions and the post-review safety corrections.

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
- `decisions/2026-07-21-repository-engineering-capability-adoption-closeout.md`:
  accepted v1.4 proportional adoption behavior with a bounded `bio_plot`
  Symphony `NO-GO` and a repository-owned `biofetch` CI increment.
- `decisions/2026-07-22-symphony-readiness-and-bounded-canary-closeout.md`:
  closed v1.5 at Slice 1 after the pinned lock failed dependency audit and the
  upstream full gate remained red on the current host.
- `implementation-plan/20260722-v1.5-symphony-readiness-and-bounded-canary-implementation-plan.md`:
  closed successor whose later scratch-repo and repository canary slices did
  not open.

## Current Boundary

The v1.3 repository-delivery feedback loop and v1.4 proportional adoption plan
are accepted and closed. The v1.5 Symphony readiness and bounded-canary plan
is also closed at Slice 1 with `NO-GO`; it did not change calibration guidance
or reopen wider orchestration.

The v1.5 ephemeral probe established narrow source and protocol compatibility,
but the pinned dependency lock failed security audit and upstream `make all`
did not pass. It therefore stopped before a scratch tracker, persistent
installation, or repository-owned no-product-change canary. E03/E04 remains
closed until the latest closeout's gates pass.

The closeout does not authorize bulk environment provisioning, mandatory
per-repository configuration, auto-merge, or project-specific operating rules
inside calibration. Another Symphony canary requires the 2026-07-22 closeout's
explicit host and scratch reopen conditions. A `bio_plot_platform` or E03/E04
canary additionally requires the cumulative repository gates retained by the
2026-07-21 adoption closeout.
