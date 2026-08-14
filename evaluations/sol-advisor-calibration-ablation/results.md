# Sol Advisor And CAL-MIN Ablation Results

Date: 2026-08-13
Status: complete; bounded same-model comparison

## Decision

Reject `CAL-MIN` as tested, and do not enable Sol Advisor by default for a
bounded local repair with a clear repository oracle. Keep the current
conditional Calibration route: ordinary local work should not load Calibration
merely because the skill is installed.

This result does not reject a shorter ambient AO safety kernel by itself. The
tested `C1` bundle combined shorter always-loaded text with a mandatory
route-once capsule. That bundle caused one Calibration route in every `C1` run,
and the routed context cost more than the ambient text it removed. Any later
candidate must isolate a shorter AO kernel while retaining the current
no-route behavior for clear local work.

## Result Summary

All 12 official arms passed the same correctness and scope gate:

- the real base-R worker reproduction and all nine assertions passed;
- only `src/wgcna_worker.R` changed;
- no critical failure, AO route, scope artifact, rework fingerprint, or
  compaction occurred; and
- every repetition's normalized prompt matrix differed only at the registered
  Calibration or Advisor message indexes.

The values below are medians across three counterbalanced repetitions. Total
tokens are input plus output. Cached input is already part of input, and
reasoning output is already part of output, so neither is added twice.

| Arm | Wall seconds | First effective edit | Total tokens | Commentary |
| --- | ---: | ---: | ---: | ---: |
| `C0-A0` current Calibration, no Advisor | 81.5 | 48.8 | 120,035 | 4 |
| `C1-A0` CAL-MIN, no Advisor | 115.6 | 75.9 | 188,523 | 5 |
| `C0-A1` current Calibration and Advisor | 478.2 | 163.5 | 1,127,823 | 8 |
| `C1-A1` CAL-MIN and Advisor | 532.7 | 245.3 | 1,403,815 | 9 |

Paired median deltas retain the registered direction: candidate arm minus
reference arm.

| Contrast | Wall seconds | First effective edit | Total tokens | Commentary |
| --- | ---: | ---: | ---: | ---: |
| CAL-MIN without Advisor | +34.1 | +33.2 | +70,326 | +1 |
| CAL-MIN with Advisor | +51.0 | +43.4 | +34,654 | 0 |
| Advisor with current Calibration | +402.6 | +119.5 | +1,007,788 | +4 |
| Advisor with CAL-MIN | +408.0 | +169.2 | +1,223,051 | +4 |

`CAL-MIN` increased wall time and time to first effective edit in all six
paired comparisons across both Advisor strata. Its token delta with Advisor
varied, but two of three repetitions and the paired median were higher. Without
Advisor, all three token deltas were higher. It therefore fails the registered
adoption gate.

Sol Advisor preserved correctness but added an implementation role, a fresh
review role, and 3-13 observable collaboration waits per arm. Every Advisor
contrast was slower and used more total tokens in all three repetitions. No
quality difference remained for the Advisor to recover: every no-Advisor arm
already produced the same one-file verified repair with zero critical failures.

## Routing Findings

The result supports a narrower routing policy:

- `C0-A0` correctly performed zero Calibration and zero AO routes in all three
  runs even though the frozen Calibration skill was installed.
- `C1` performed exactly one Calibration route, one decision capsule, and 2-5
  engineering-reference loads per run. The capsule prevented scope churn, but
  the current baseline also had zero scope churn without paying that route.
- Every Advisor arm used two exact native roles. Their persisted turn context
  recorded `gpt-5.6-sol` with `max` reasoning for both implementation and
  review.
- Sol Advisor 0.5.0's orchestration skill exceeded the main prompt context
  limit in every Advisor run and was then read explicitly. The host also
  broadened the requested reviewer isolation to `workspace-write`; parent
  before-and-after checks confirmed no review mutation. These are protocol
  deviations and additional reasons not to make the workflow a local default.

## Luna Boundary

The separate Sol-to-Luna arm was not run. The runtime exposed exact model and
effort inside native Advisor role sessions, but the parent `codex exec` event
stream did not expose a backend build identity. The registered model-routing
gate therefore remained closed. More importantly, the primary comparison found
no quality deficit for a cheaper executor to preserve: the efficiency problem
in this fixture was the mandatory routing and review workflow itself.

## Evidence And Limits

[`runs.json`](runs.json) contains all 12 per-run values, paired deltas, prompt
hashes, final-diff hashes, exact role identities, and protocol deviations. The
pilot run is excluded from the official comparison because it discovered and
corrected two harness issues before registration was enforced: dynamic message
IDs in prompt hashes and incomplete subagent token aggregation.

The official runtime fixture tree also contained one Git-ignored CPython
bytecode cache created by the oracle preflight. It was not tracked or changed
by any arm. `runs.json` records both that exact runtime-tree hash and the
cleaned, distributable source-tree hash rather than silently treating them as
identical.

Raw trajectories, isolated Codex homes, auth symlinks, and mutable workspaces
were private runtime material and are not committed. The public bundle is
therefore sufficient to check the frozen inputs, fixture, arithmetic, and
reported decision, but not to reconstruct every raw model event independently.
No qualitative trajectory score was used, so no blind-judge claim is made.

This is one synthetic, bounded, cross-language repair with a deterministic
oracle. It does not establish Advisor value for consequential architecture,
security, migration, or ambiguous compatibility work, and it observed no real
context compaction. Advisor use remains an explicit high-complexity option,
not a general default.
