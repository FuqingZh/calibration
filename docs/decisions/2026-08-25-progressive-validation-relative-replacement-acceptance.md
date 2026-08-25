# Progressive Validation Relative-Replacement Decision

Date: 2026-08-25
Status: inconclusive; replacement not accepted

## Decision

Retain frozen baseline `0f21f880383859f060156db6ce69d08eff73ed44` as
the current progressive-validation authority. Candidate
`5a94f5826c99f6e748a2d712851874b604471a23` did not prove a net improvement
under the corrected relative rule: P05 favored the candidate, P03 favored the
baseline, and P02 tied.

This decision supersedes the earlier acceptance interpretation. Audit found
that the earlier fixtures credited a literal `\\n` artifact in P02, used a
phrase-only behavior sample in P03, and failed to require preservation of all
consumer fields in P05. Those defects changed the compared behavior and made
the earlier result unsuitable for replacement.

## Immutable evidence

The final clean controller commit was
`6265d90f9851ff8c9278b297dde542ff51eab1b2`. The immutable local evidence root
is `/tmp/calibration-progressive-v22-conclusive.PglcjF`; it remains private,
append-only evidence and is not committed. Freeze verification and post-run
readback passed. C01 was `verified`, with result SHA-256
`eead4f3377978778b769414fdd26949875876593973d73dc3456fe4e0564971d`.

All 12 initial slots completed. P03 alone had conflicting first-two paired
outcomes, so only its frozen third pair ran. All 14 slots completed and none
failed.

| Arm | Runs | Task valid | Evidence valid | Required missing | Ordered missing | Forbidden events | Elapsed total | Mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 7 | 7 | 7 | 0 | 2 | 5 | 439.60 s | 62.80 s |
| Candidate | 7 | 7 | 7 | 0 | 2 | 3 | 448.03 s | 64.00 s |

| Case | Paired result | Interpretation |
| --- | --- | --- |
| P02 | Tie | Both arms satisfied the corrected generated-artifact contract. |
| P03 | Baseline win | The baseline selected the required behavior proof more precisely across the deciding repetitions. |
| P05 | Candidate win | The candidate preserved the full consumer contract while avoiding unnecessary validation. |

The controller returned `state=complete`, `decision=inconclusive`, one
candidate win, one baseline win, and one tie. Independent readback reproduced
the same totals.

## Interpretation

The candidate showed a real reduction in forbidden checks, from five to three,
without losing aggregate task success or required-check totals. That narrower
gain is offset by the baseline win on P03 under the frozen rule. Candidate mean
elapsed time was also slightly higher, but elapsed time was a secondary
diagnostic and did not decide the result.

The result therefore says neither implementation is uniformly better on the
tested behaviors. It does not justify replacing the baseline, activating the
candidate globally, or migrating downstream repositories.

## Invalid diagnostic attempts

Two corrected-run roots remain immutable diagnostics and are not pooled with
the result:

- `/tmp/calibration-progressive-v22-review.sLEU6u` used controller
  `331990e…` and stopped after an over-broad `gate` substring heuristic
  misclassified evidence; and
- `/tmp/calibration-progressive-v22-final.uV2MXa` used controller
  `a24ced9…` and stopped after multiline shell syntax exposed a remaining
  parser boundary.

Each correction was committed and validated before a fresh root was frozen.
No result, ledger, or slot was rewritten or reused.

## Consequences

The candidate branch and evaluation artifacts remain reviewable evidence, but
the candidate must not be merged as the replacement. The remote default branch
continues to represent the baseline. Harness and fixture corrections may be
adopted separately only under a change that does not activate the rejected
candidate behavior.

Approval telemetry remains out of scope. No active user installation or
downstream repository was changed by the formal comparison.
