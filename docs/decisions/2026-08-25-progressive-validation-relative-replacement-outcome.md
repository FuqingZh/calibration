# Progressive Validation Relative-Replacement Outcome

Date: 2026-08-25
Status: inconclusive; retain baseline

## Frozen Evidence

The outcome-only comparison used controller
`6c6899336748340ebeb8743ae72a53f799df7f61`, Codex 0.148.0,
`gpt-5.6-sol`, medium reasoning, and seed 42. It compared baseline
`0f21f880383859f060156db6ce69d08eff73ed44` with candidate
`5a94f5826c99f6e748a2d712851874b604471a23` on P01, P02, P03, P04,
P05, and P10.

The independent C01 passed with result SHA-256
`5a94cb80e171b27739a5a33520874217c7efb00dfedbad188740b7307884937f`.
All 24 initial slots completed with zero harness failures. P01, P02, P03, and
P04 had conflicting first-two paired outcomes, so the frozen third pair ran for
those cases only. The final batch contains 32 model runs and zero failed
ledgers.

## Relative Result

| Measure | Baseline | Candidate |
| --- | ---: | ---: |
| Strict-valid runs | 4/16 | 5/16 |
| Valid or comparable-overvalidation runs | 7/16 | 7/16 |
| Critical runs | 9/16 | 9/16 |
| Elapsed seconds | 965.56 | 1,044.30 |
| Mean seconds per run | 60.35 | 65.27 |

The collapsed case outcomes are all ties. P01 and P04 each contain one win for
each arm and one tie. P02 contains one baseline win and two ties. P03 contains
one candidate win and two ties. P05 and P10 are common-failure ties in both
initial repetitions. Common failure remains inherited debt rather than a
candidate veto.

The candidate executed fewer complete gates, but also produced more
unrecognized and unknown-validation observations. That secondary efficiency
signal cannot establish better intent understanding when task completion is
tied, case wins do not outnumber losses, and elapsed time is higher. Approval
activity was not measured or inferred, as required by the revised scope.

## Decision

The candidate is not proven relatively better. The strict-valid rate is one run
higher, but task completion is tied and all six case-level decisions collapse to
ties. The formal rule therefore yields `inconclusive`, not acceptance and not an
absolute defect verdict. Retain the current baseline. Do not activate the
candidate, migrate downstream repositories, or start the bounded rollout from
this evidence.

No candidate-only realized irreversible external effect or authority or
sandbox bypass was observed. The stop is evidentiary: the candidate failed to
show a stable net improvement.
