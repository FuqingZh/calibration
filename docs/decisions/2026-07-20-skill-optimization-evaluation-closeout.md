# Skill Optimization Evaluation Closeout

Date: 2026-07-20

Status: Accepted with limitations

## Decision

Retain the evaluated candidate as the next calibration baseline. The observed
behavior supports regression acceptance under the current cases, but it does
not establish blinded comparative superiority.

## Evaluation Scope

- Baseline: repository commit `5e50f96`
- Candidate: the frozen dirty-worktree source installed into arm B; its
  behavior-bearing files are committed in `5e50f96..1addeb2`
- Model: `gpt-5.6-sol`
- Reasoning effort: `medium`
- Matrix: 13 cases, 3 repetitions, and 2 arms
- Codex CLI: `0.144.1`
- Frozen candidate source-tree SHA-256:
  `2bb3c1a6c1defa41ceff0cba468ac50876c8fabb09b0364e6f14be084a2672f2`
- Case definition SHA-256:
  `5bfc09b1364de44c21c6c711079a20d526dcd7ef2071d604a4eee2377c245a0e`

The harness used isolated Codex homes, frozen synthetic fixtures, fresh
sessions, read-only workspaces, disabled web search, and neutral arm labels.
Raw model outputs and the private arm map remain in the local temporary
evaluation workspace and are not repository artifacts.

The committed range differs from the frozen source only by a later
documentation-only expansion in the superseded `writing-docstrings` decision
record. Skill bodies, metadata, references, and runtime instructions match the
evaluated source.

## Results

- 78 of 78 sessions completed successfully.
- The sessions produced 90 turns and 39 blind comparison packages.
- Non-blind rubric review found no critical regression in the candidate.
- `brainstorming` retained its implementation gate, one-question limit, 2-3
  mutually exclusive approaches, explicit recommendation, approval wait, and
  Design Checkpoint. The candidate reached the checkpoint earlier on average.
- `grilling` did not show a stable comparative gain. The baseline already
  covered its central single-turn behavior, while the cases did not exercise
  the candidate's confirmation gate or stopping condition.
- The runner's timeout, heartbeat, resume-integrity, and continuation behavior
  is covered by five passing local tests.

## Limitations

The blind scorecard contains all 39 pair rows, but its preference, critical
failure, required-behavior, and notes fields are unfilled. The result therefore
supports retaining the candidate, not a claim that it won a completed blind
comparison or achieved statistical significance.

The fixed third turn in the `brainstorming` case also asked the candidate to
repeat design work after it had already reached a checkpoint. Treat the earlier
checkpoint as an observed behavior, but do not use the later turn as an
unbiased quality comparison.

## Follow-up

Before changing the skill bodies again:

1. Stop a `brainstorming` case at its first Design Checkpoint, or use a later
   turn only to verify that the skill still waits for approval.
2. Add multi-turn `grilling` cases covering user confirmation, dependent
   decisions, no action before confirmation, and the final stopping summary.
3. Add `writing-code-docs` cases that penalize combining several public
   consequences into one overloaded example and that assess caller-facing
   example length.
4. Reject an evaluation closeout when expected scorecard fields are blank.
5. Use this accepted candidate, rather than `5e50f96`, as the baseline for the
   next optimization round.

Execution is tracked in
`../implementation-plan/20260720-v1.1-agent-harness-evaluation-implementation-plan.md`.
