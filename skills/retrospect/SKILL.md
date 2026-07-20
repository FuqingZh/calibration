---
name: retrospect
description: User-invoked evidence-driven retrospective mode for completed work, failures, repeated patterns, and cross-stage experience.
---

# Retrospect

Follow the evidence until the real lesson has a name.

A name is earned when its evidence, boundary, risk, and future action are clear
enough for an informed outsider to question and reuse it. Keep unsupported
causes as hypotheses rather than polishing them into lessons.

Let checked evidence, rather than chronology or moral judgment, determine the
lesson.

## Method

- establish the task, failure, or period under review
- reconstruct what was expected and what actually happened
- inspect the relevant plans, changes, validation, artifacts, feedback, and
  history
- separate checked evidence from memory, interpretation, and open questions
- identify the consequential difference between expectation and reality

For a local execution delta, produce a concrete rule for the next similar task.
For a repeated or cross-stage pattern, name its boundary, evidence, risk, and
consequence for future action.

## Depth

Use `standard` by default and inspect evidence directly tied to the review.

Use `deep` for repeated failures, high-risk or customer-facing delivery,
production-adjacent work, broad changes, or cross-stage direction and portrait
reviews. Bound searches with terms from the task, symptom, file, plan, test,
command, or artifact. Fall back to `standard` when no credible search boundary
exists.

Summarize evidence and cite its location rather than copying raw logs or long
conversation transcripts.

## Stop

Stop when the user has confirmed the lesson's evidence, boundary, risk, and
future action, or when missing or conflicting evidence has been recorded as an
explicit hypothesis with its verification gap.

Remain in retrospective mode until that point. Write files, promote rules, or
take implementation or commit action only after a separate explicit request.

## Persistence

When the user later asks to persist a confirmed task-level lesson, follow
`references/engineering/docs/document-types/trace-retro.md` and
`references/engineering/docs/workflow/task_traces_and_retros/20260527-v1.0-task-traces-and-retros.md`.

For a direction, portrait, or cross-stage review, use the repository's
document-type routing or the path specified by the user.

Recommend promotion to project documentation, repository instructions,
calibration, or memory only after the lesson is stable.

Use `$grilling` before facts exist to stress-test a plan. Use `$retrospect`
after facts exist to discover what the evidence can carry forward.
