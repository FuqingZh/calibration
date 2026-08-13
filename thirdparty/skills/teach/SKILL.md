---
name: teach
description: User-invoked stateful teaching for a skill or concept in an explicitly selected personal learning workspace, with a session-only no-write mode.
---

# Teach

Teach one bounded capability at a time. Ground every lesson in the learner's
mission, current capability, trusted sources, retrieval practice, and a tight
feedback loop.

## Establish The Learning Boundary

Resolve these locations separately before reading or writing anything:

- **skill source**: the directory containing this file, its format references,
  and bundled assets; treat it as read-only;
- **project context**: the current engineering repository, code, or team
  documentation used as teaching evidence; treat it as read-only by default;
  and
- **learning workspace**: a personal directory or repository explicitly
  selected by the user for persistent learner state.

Never infer that the current directory or the installed skill source is the
learning workspace. For persistent mode, confirm the exact learning-workspace
path and verify that it is not the skill source, current engineering Git root,
or a directory inside that Git root. After first confirmation, create
`.teach-workspace.yaml` containing `kind: personal-learning` and `version: 1`;
that marker is durable evidence for later sessions. Ask before adopting an
existing unmarked workspace.

When no learning workspace has been selected, offer either:

1. persistent teaching in a separate personal learning workspace; or
2. session-only teaching in the conversation.

In session-only mode, create or edit no files, including project documents,
lessons, notes, records, or assets. Continue teaching in the conversation.

## Persistent Workspace State

Keep all learner-specific state relative to the confirmed learning workspace:

- `MISSION.md`: the learner's concrete reason and observable goal; use
  [MISSION-FORMAT.md](./MISSION-FORMAT.md).
- `RESOURCES.md`: current trusted sources and communities; use
  [RESOURCES-FORMAT.md](./RESOURCES-FORMAT.md).
- `learning-records/*.md`: demonstrated knowledge, prior capability, corrected
  misconceptions, and mission changes; use
  [LEARNING-RECORD-FORMAT.md](./LEARNING-RECORD-FORMAT.md).
- `lessons/*.html`: short, self-contained lessons.
- `reference/*.html` and `GLOSSARY.md`: compressed material for later recall;
  use [GLOSSARY-FORMAT.md](./GLOSSARY-FORMAT.md) for the glossary.
- `assets/*`: reusable lesson components.
- `NOTES.md`: personal teaching preferences, review cues, and temporary working
  notes.

Create directories and files lazily. Never promote these personal artifacts to
team-authoritative project documentation.

## Start Or Resume

For a marked existing workspace, read `MISSION.md`, `RESOURCES.md`, `NOTES.md`,
the glossary, and the learning-record inventory. Inspect the latest relevant
records, lesson titles, and reusable assets before choosing the next step. Use
that state to resume; do not restart a generic curriculum. Confirm material
contradictions or a changed goal with the user before rewriting prior state.

Before the first lesson, establish both:

1. **mission**: the concrete outcome, success evidence, and constraints; and
2. **starting capability**: what the learner can already explain or do.

Use at least one small diagnostic question or task instead of relying only on a
self-rating. In persistent mode, write the confirmed mission and the assessed
starting point only after workspace confirmation. In session-only mode, keep
them in the conversation. Do not create the first lesson until both are clear
enough to select the learner's zone of proximal development.

## Ground Current Knowledge

Gather lesson claims from high-trust sources. Prefer current primary sources,
official documentation, standards, peer-reviewed work, and recognized experts.
Verify facts that may have changed, and record the publisher, title, URL,
applicable version or date, and check date in `RESOURCES.md`. Label historical
material as historical context. When a current authoritative source cannot be
found, state the gap instead of presenting parametric knowledge as verified.

Use community knowledge for practical wisdom only when useful to the mission.
Respect a learner who declines community participation.

## Run One Tight Lesson Loop

For each lesson:

1. Choose one tangible win tied to the mission and define the stopping
   condition.
2. Teach only the knowledge required for that win, with citations near claims.
3. Ask the learner to retrieve or apply it without copying the explanation.
4. Give immediate, specific feedback and let the learner retry.
5. Record knowledge only after the learner demonstrates it; coverage alone is
   not learning.
6. Stop when the win is demonstrated or when confusion, fatigue, or a missing
   prerequisite makes another small lesson the better next step.

Use conversation-native teaching in session-only mode. In persistent mode,
save a short lesson as `lessons/NNNN-dash-case-name.html` when a reusable lesson
artifact helps. Keep it readable and printable, link its sources, and reuse
workspace assets rather than duplicating components.

For multiple-choice HTML exercises, preserve answer identity with stable data
attributes and randomize displayed option order at runtime. Copy
[assets/quiz.js](./assets/quiz.js) into the learning workspace when needed and
load it with `defer`; do not encode a recurring correct-answer position. Keep
option length and formatting comparable so they do not reveal the answer.

Build storage strength with retrieval practice. Suggest a concrete future
review cue and interleave related skills when useful, but do not claim that the
skill automatically schedules or delivers spaced reviews. At the beginning of
a later session, check recorded review cues and demonstrated learning before
choosing new material.

## Change The Mission Deliberately

Confirm a mission change with the user before editing `MISSION.md`. Record why
the change matters in a new learning record so later sessions can distinguish a
changed goal from forgotten context.

## Promote Team-Neutral Knowledge Explicitly

Enter a project-document workflow only when the user explicitly asks to make a
result durable for the project or team. Keep personal mission, preferences,
mastery, review cues, and session notes in the learning workspace. Distill only
team-neutral, source-backed material, then follow the target repository's own
documentation authority and validation rules.

Route the promoted result by its primary role:

- guided path from a known starting state to a capability -> tutorial;
- steps for one known task -> how-to guide;
- stable current system concepts or structure -> architecture;
- verified third-party or external behavior -> compatibility record; and
- controlled or high-risk operation -> runbook.

Use `$calibration` when this routing or the durability boundary requires
substantive engineering judgment.

## Finish A Session

State the teaching mode, the selected workspace when persistent, the lesson win
and evidence, the sources checked, and one next lesson or review cue. Report
only files actually written. In session-only mode, explicitly report that no
filesystem state was created.
