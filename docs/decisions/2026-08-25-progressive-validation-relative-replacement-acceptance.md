# Progressive Validation Relative-Replacement Acceptance

Date: 2026-08-25
Status: accepted for the bounded repository comparison

## Decision

Accept candidate `5a94f5826c99f6e748a2d712851874b604471a23` over frozen baseline
`0f21f880383859f060156db6ce69d08eff73ed44` as the repository's current
progressive-validation authority for the tested scope. The candidate preserved
all observed task success, evidence integrity, required checks, and ordering
totals while eliminating five forbidden complete-gate invocations. It won two
cases, lost none, and tied one.

This decision does not claim that the candidate is universally better, more
correct, or faster. It is bounded to Codex CLI 0.148.0, `gpt-5.6-sol` at medium
reasoning, the frozen permission/sandbox configuration, and P02, P03, and P05.

## Immutable evidence

The clean controller commit was
`e3d771fa0d89cc8f098997b20c60158b6f4d192b`. The frozen local private root is
`/tmp/calibration-progressive-v22d.A87QAk`; it is retained as append-only local
evidence and is not committed. Freeze verification and post-run readback both
passed. C01 was `verified`, with result SHA-256
`6310a39be25e5bc4097f91d7e864f4d04b709dceb431171aec6a68d2d0cba021`.

The batch completed 12 initial slots. P05 alone had conflicting first-two
paired outcomes, so only its frozen third pair ran. All 14 slots completed and
none failed.

| Arm | Task valid | Evidence valid | Required missing | Ordered missing | Forbidden events | Elapsed total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 7/7 | 7/7 | 0 | 2 | 5 | 495.06 s |
| Candidate | 7/7 | 7/7 | 0 | 2 | 0 | 524.22 s |

| Case | Paired result | Reason |
| --- | --- | --- |
| P02 | Candidate win, 2:0 | Both tasks succeeded; candidate omitted the forbidden complete gate in both repetitions. |
| P03 | Tie, both pairs tied | Both arms preserved required structural and behavior-sample proof without forbidden checks. |
| P05 | Candidate win, 2:1 | The third pair resolved the conflict; candidate avoided the complete gate and was precise in the deciding run. |

The controller returned `state=complete`, `decision=accept`, two candidate
wins, zero baseline wins, and one tie. Independent aggregation reproduced the
same task, evidence, ordering, forbidden-event, and elapsed totals.

## Interpretation

The test establishes a validation-selection gain, not a task-correctness gain:
both arms completed every task. It also does not establish an elapsed-time
gain. Candidate mean time was 74.89 seconds versus 70.72 seconds for baseline,
about 5.9% slower. Time is secondary under the frozen rule and cannot erase the
earlier-dimensional improvement, but it remains a real limitation.

One run per arm retained heuristic command-normalization warnings in the
detailed oracle. Their broker events and delivery receipts reconciled exactly,
so both evidence layers remained valid. This confirms the corrected boundary:
parser uncertainty stays auditable without being mistaken for task failure or
forged evidence.

## Invalid diagnostic attempts

Three fresh roots preceded the valid batch. They remain immutable and are not
pooled:

- controller `4983906f…`: one completed slot, then selection-contract errors
  were found to contaminate evidence integrity;
- controller `824303cd…`: three completed slots, then a valid read-only
  `find -exec` command exposed parser noise; and
- controller `8bb4c00d…`: two completed slots, then shell control syntax
  exposed the remaining heuristic-warning boundary.

Each stopped with one started-only slot. Every correction passed focused and
complete gates and used a newly frozen root. No result, ledger, or slot was
rewritten or reused.

## Consequences

The candidate implementation is already present in the repository history, so
no additional behavior patch is required. The historical v2.0 rejection and
v2.1 inconclusive run remain diagnostic background but no longer own current
authority. Approval telemetry remains out of scope.

This evaluation did not run the installer against the user's active Codex home
and did not modify downstream repository rules. Any cross-repository pilot or
local-rule cleanup remains a separate, reversible rollout with its own
repository authority and readback.
