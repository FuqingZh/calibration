---
name: retrospect
description: User-invoked evidence-driven retrospective mode for completed work, failures, repeated patterns, and cross-stage experience.
disable-model-invocation: true
---

# Retrospect

Follow the evidence until the real lesson has a name.

A name is earned only when the pattern has taken shape: its boundary, evidence,
risk, and future action are clear enough to carry the wording.

Do not polish. Do not moralize. Do not stop at a timeline when the evidence
reveals a pattern. Do not name a pattern before the evidence can carry it.

Name lessons so an informed outsider can question and reuse them without the
original context.

Prefer the smallest statement that changes future work.

Remain in retrospective mode until the lesson and its boundary are agreed. Do
not write files, promote rules, or take implementation action unless the user
explicitly asks afterward.

## Method

Start from facts:

- establish the boundary of the task, failure, or period under review
- reconstruct what was expected and what actually happened
- inspect plans, changes, validation, artifacts, feedback, and relevant history
- separate checked evidence from memory, interpretation, and open questions
- identify the consequential difference between expectation and reality

Let the evidence determine the stopping point:

- for a local execution delta, stop at a concrete rule for the next similar task
- for a repeated or cross-stage pattern, name its boundary, supporting evidence,
  risk, and consequence for future action
- when evidence is missing, contradictory, or sensitive, keep the conclusion as
  a hypothesis or `draft` and state what remains unverified

## Depth

Use `standard` by default. Inspect only evidence directly tied to the review.

Use `deep` for repeated failures, high-risk or customer-facing delivery,
production-adjacent work, broad changes, or cross-stage direction and portrait
reviews. Bound historical searches with terms taken from the task, symptom,
file, plan, test, command, or artifact. If no credible boundary exists, fall
back to `standard`; never scan history without a limit.

Summarize evidence and cite its location. Do not copy raw logs or long
conversation transcripts by default.

## After Agreement

Persist a confirmed lesson only when the user explicitly asks afterward.
Classify the document before choosing its location:

- for a task-level execution retro, follow
  `references/engineering/docs/document-types/trace-retro.md` and
  `references/engineering/docs/workflow/task_traces_and_retros/20260527-v1.0-task-traces-and-retros.md`
- for a direction, portrait, or cross-stage review, use the repository's
  document-type routing or the path specified by the user; do not force it into
  `.traces/`

Recommend promotion to project docs, repository instructions, calibration, or
memory only after the lesson is stable. Promotion, implementation, and commit
remain separate explicit actions.

Use `$grilling` before facts exist to stress-test a plan. Use `$retrospect`
after facts exist to discover what the evidence can actually carry forward.
