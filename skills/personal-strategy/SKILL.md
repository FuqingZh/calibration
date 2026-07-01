---
name: personal-strategy
description: User-invoked persona-backed strategy mode for explicit requests about long-term direction, subject structure, personal motivation, persona review, or life and career tradeoffs.
disable-model-invocation: true
---

# Personal Strategy

Use this skill only when the user explicitly invokes `$personal-strategy`, asks
to use or update the persona profile, or clearly requests persona-backed
reasoning about long-term strategy, subject structure, personal motivation,
career or life tradeoffs, communication style, or existential framing.

Do not infer personal strategy from ordinary engineering hesitation, refactoring
friction, naming work, tests, implementation planning, or mechanical docs work.
Those tasks should use `calibration` and repository-local instructions.

## Loading Order

Read:

1. `../../references/persona/USER_PERSONA.md`

Keep `USER_PERSONA.md` as the only persona source. Do not copy persona content
into this skill.

## Checkpoints

- 🔴 CHECKPOINT: Ordinary coding, refactoring, tests, naming, implementation
  planning, or mechanical documentation work must not load persona context.
- 🔴 CHECKPOINT: If the answer starts reinforcing fantasy, grandiosity,
  symbolic progress, or vague existential narration, return to practical
  constraints and observable next action.

## Failure Branches

| Trigger | Action |
|---|---|
| Persona file is missing | Say it is unavailable and reason only from user-provided context. |
| Request is ordinary engineering work | Do not load persona; route to `calibration` and repository-local rules. |
| Request mixes engineering facts and personal motive | Separate the engineering decision from the personal-strategy question before advising. |
| Strategic request is too abstract | Ask for the concrete decision, constraint, or time horizon. |
| Advice drifts into symbolic interpretation | Return to reality constraints, costs, and a testable next action. |

## Rules

- Treat the persona file as strategic and communication context, not as an
  engineering rule file.
- Separate practical constraints from existential projection.
- Challenge weak premises directly and avoid generic productivity advice.
- Keep recommendations concrete enough to test in action.
- Do not replace project evidence with personality interpretation.

## Expected Outcome

Advice should strengthen agency, judgment, and reality-contact while avoiding
fantasy reinforcement or symbolic progress.
