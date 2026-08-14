# Sol Advisor And CAL-MIN Ablation

This directory implements the registered plan in
[`docs/testing/20260813-v1.0-sol-advisor-calibration-ablation-test-plan.md`](../../docs/testing/20260813-v1.0-sol-advisor-calibration-ablation-test-plan.md).
It separates reduced always-loaded Calibration context (`C0` versus `C1`) from
actual Sol Advisor activation (`A0` versus `A1`) while holding the requested
executor model, reasoning effort, fixture, tools, and writable topology fixed.

The completed result is in [`results.md`](results.md), with machine-readable
per-run evidence in [`runs.json`](runs.json). The tested candidate and default
Advisor route were rejected for this bounded local repair; neither is installed
by this evaluation bundle.

## Frozen inputs

- `arms/C0-current.AGENTS.md` is byte-identical to
  `bcc6ad6:codex/AGENTS.md.template`.
- `arms/C1-cal-min.AGENTS.md` is the 489-word candidate: a route-once capsule,
  one scope-increment decision, five commentary events, and the four-rule AO
  safety kernel. Detailed AO lifecycle work is routed on demand.
- `fixture/` is a sanitized base-R/Python/XLSX reproduction. Its initial state
  fails because stable SampleIds are replaced by numeric row names. The oracle
  contains the real R invocation and nine assertions, including five workbook
  regressions.
- `manifest.json` pins Sol Advisor 0.5.0 at commit `676d200`, Codex CLI 0.147.0,
  Bun 1.3.13, and the requested `gpt-5.6-sol`/`max` configuration.

The A1 arms install the pinned upstream plugin into a fresh isolated Codex home,
use its MCP implementation to save project-scoped preferences and install its
three native role files, and pin every role to the same requested Sol/max
configuration as the parent. The Luna lane is explicitly disabled. This is an
Advisor workflow comparison, not a Sol-to-Luna comparison.

## Run protocol

Raw prompts, trajectories, diffs, isolated Codex homes, auth symlinks, and
mutable workspaces are private runtime material and must remain outside this
directory. The runner refuses a model workspace nested under this repository,
uses a minimal environment that excludes outer task payload variables, and
checks the model-visible prompt for inherited delegation history before every
arm.

Run the environment and source preflight first, then one fresh-context smoke per
arm. Paths below are examples and must point to disposable locations:

```bash
python3 evaluations/sol-advisor-calibration-ablation/run_smoke.py preflight \
  --codex-bin /path/to/codex \
  --bun-bin /path/to/bun \
  --advisor-source /path/to/sol-advisor-676d2007 \
  --auth-file /path/to/codex/auth.json

python3 evaluations/sol-advisor-calibration-ablation/run_smoke.py smoke \
  --codex-bin /path/to/codex \
  --bun-bin /path/to/bun \
  --advisor-source /path/to/sol-advisor-676d2007 \
  --auth-file /path/to/codex/auth.json \
  --output-root /private/non-temporary/runtime/output \
  --workspace-root /tmp/calibration-sol-advisor-workspaces
```

An empty Codex turn already has substantial fixed platform input, so the smoke
gate precedes any three-repetition run. A critical failure stops promotion to
official repetitions; it does not get averaged away. The completed comparison
did not run the separate Luna arm because the parent backend build identity
remained unavailable.

## Interpretation boundary

The runner records correctness, critical failures, time to first effective
edit, wall time, exposed token fields, observable repeated summaries,
compactions, rework fingerprints, and AO/Calibration/Advisor route counts. It
does not request hidden chain-of-thought. Token totals combine the top-level
event stream with every persisted native-role session in the fresh isolated
Codex home; cached input and reasoning output remain reported as subsets. The
CLI records the requested model configuration but did not expose a parent
backend build identity, so no Sol-versus-Luna claim follows from this result.
