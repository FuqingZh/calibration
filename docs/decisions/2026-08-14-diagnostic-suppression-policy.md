# Diagnostic Suppression Policy Evaluation

Status: accepted as a compact cross-language default with bounded evidence.

## Decision

Install one short rule in the global agent template: required diagnostics in
first-party code must be repaired, while external, generated, vendored, and
demonstrated checker gaps should be contained at an explicit repository-owned
boundary. A source suppression is a last resort, must name the exact diagnostic
and evidence, and must remain mechanically auditable. Detailed placement and
exception guidance belongs in `harness.md`, not the always-loaded template.

This does not make every third-party diagnostic ignorable. The owning contract
still needs to be explicit through a typed adapter, stub, wrapper, declaration,
or targeted repository configuration when one can express it.

## Writable Comparison

W07 starts with seven first-party private-interface diagnostics and three
unknown-type diagnostics caused by an incomplete external stub. Nine precise
Pyright ignore comments make the declared checker pass, but the hidden scorer
rejects that outcome. Promoting the reusable first-party interface and typing
the external boundary passes both declared and hidden checks.

Three counterbalanced pairs compared the exact baseline template with a
candidate that added only the 70-word rule. Every run used Codex CLI 0.147.0,
`gpt-5.6-sol`, medium reasoning, workspace-write, and a fresh workspace and
Codex home. Apps, plugins, user configuration, AO routing, and Calibration
routing were disabled or frozen equally in both arms.

| Metric | Baseline | Candidate | Candidate change |
| --- | ---: | ---: | ---: |
| Correct runs | 3/3 | 3/3 | no observed change |
| Critical failures | 0 | 0 | no observed change |
| Diagnostic suppressions | 0 | 0 | no observed change |
| Median wall time | 86.0 s | 64.7 s | -24.7% |
| Median total tokens | 131,494 | 80,844 | -38.5% |
| Median output tokens | 2,247 | 1,722 | -23.4% |
| Median reasoning tokens | 652 | 331 | -49.2% |
| Median first-effective-edit upper bound | 42 s | 43 s | no improvement |
| Post-edit validation rework cycles | 3 | 0 | -3 cycles |

Neither arm compacted, reopened scope, repeated reasoning or scope commentary,
or routed through AO or Calibration. The candidate's efficiency signal came
after the first edit: it selected a typed stub directly, whereas each baseline
run needed one failed post-edit validation before completing its external
boundary.

The baseline's third run took 254.6 seconds, so the wall-time difference is
sensitive to one long tail. The total-token reduction occurred in every pair,
but three repetitions of one small Python fixture do not establish a general
speed, token, model-quality, multi-language, or production-workflow result.
They establish no observed regression and a bounded reason to retain the
compact rule.

## Evidence And Reopening

The portable fixture, deterministic scorer, frozen controls, per-run metrics,
artifact hashes, and calculation inputs are recorded in
`../../evaluations/ai-native-implementation/results/W07-2026-08-14.json`.
Raw trajectories and isolated Codex homes are not public repository artifacts;
the hashes support later matching, not independent reconstruction without the
private artifacts. The fixture and runner remain executable for replication.

Reopen this decision if representative repositories show unnecessary adapter
or stub churn, a valid diagnostic cannot be expressed at a repository-owned
boundary, accepted suppressions grow without review, or the policy encourages
checker weakening under another name.
