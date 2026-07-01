# Trace Retro

Use this type for task-level retrospectives: expectation versus actual outcome,
judgment errors, validation quality, and rules to carry forward.

## Where It Lives

Use project `.traces/retros/` unless repository-local trace rules say
otherwise.

## Required Content

- Expected goal, risk, validation plan, and key assumptions.
- Actual changes, validation, and result.
- Delta between expected and actual.
- Rule to carry forward.
- Whether the learning should be promoted to project docs, repository-local
  instructions, or calibration.

## Do Not Include

- Raw command logs by default.
- Long conversation transcripts.
- Current architecture truth.
- PR review summaries.
- Stable project rules that should already be promoted into `docs/` or local
  instructions.

## Complete When

The next similar task can start with a better assumption, validation path, or
rule than the original task had.
