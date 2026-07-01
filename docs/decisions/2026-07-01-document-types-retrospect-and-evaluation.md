# Document Types, Retrospect, And Skill Evaluation

Date: 2026-07-01

## Purpose

This document records the later decisions from the calibration refinement
thread after the repository rename and follow-up batches were completed.

The covered scope is:

- engineering document type routing
- the first-party `retrospect` skill
- first-party Darwin test prompts
- the narrowed `personal-strategy` boundary
- current user-invoked skill roles

## Document Type Routing

Add `references/engineering/docs/document-types/` as a selective routing layer
for project documentation. It is a minimum contract layer, not a template
library and not a new skill.

The core long-lived engineering document types are:

- `architecture-overview`: current system facts, boundaries, contracts, and
  read-first architecture context
- `design-proposal`: not-yet-approved change proposal with alternatives,
  unresolved questions, and a recommended approach
- `decision-record`: high-value settled decision with context, alternatives,
  consequences, and reopening conditions
- `implementation-plan`: execution slices, affected boundaries, verification,
  risks, and intended commit or PR split
- `trace-retro`: task-level retrospective under `.traces/retros/`, focused on
  expectation versus actual behavior and future calibration

`pr-description` is intentionally not a durable document type. A PR body should
be generated at review time from the implementation plan, actual diff,
verification results, and reviewer needs.

`archive` is lifecycle handling, not a document type. Archived documents retain
their original type. When a document is superseded, move it according to the
project's archive convention, update indexes and source-of-truth pointers, and
do not treat archived material as active unless a current document cites it.

Migration and refactor plans are first handled as branches of
`implementation-plan`, not separate first-version document types. Repository
local documentation conventions override calibration defaults.

## Retrospect Skill

Add `retrospect` as a first-party managed skill. It is user-invoked and may be
suggested only after meaningful engineering deltas, such as failed assumptions,
validation surprises, broad refactors, repeated regressions, production-adjacent
work, or customer-facing delivery.

`trace-retro.md` defines the durable document contract. `$retrospect` defines
the interaction and evidence-gathering workflow.

Modes:

- `standard`: evidence-driven task retrospective
- `deep`: heavier post-mortem for failures, repeated regressions, high-risk
  delivery, deployments, or broad cross-module changes

Standard evidence includes active plans or docs, git status/diff/log, tests,
smoke checks, validation artifacts, user feedback, and directly relevant local
docs or prior traces.

Deep evidence adds bounded keyword searches through prior traces, plans,
memory or session summaries, failure logs, and superseded docs. Deep mode must
not become an unconstrained history scan.

Default output is `.traces/retros/YYYYMMDD-topic-retro.md`. If `.traces/` is
missing, the skill may create only `.traces/index.md` and `.traces/retros/`.
It should keep `.traces/index.md` as a short navigation index.

The skill does not automatically edit project docs, `AGENTS.md`, calibration
rules, or memory. It writes promotion recommendations only. Long-term rule
promotion requires a separate explicit user request. It also does not
auto-commit.

Boundary with `grilling`:

- `grilling` is a pre-implementation adversarial stress test for plans,
  architecture, and implementation approaches
- `retrospect` is a post-fact audit of expectation, evidence, root cause,
  missed detection, and future rules

## Darwin Test Prompt Assets

Add Darwin-compatible `test-prompts.json` files for the first-party skills:

- `skills/calibration/test-prompts.json`
- `skills/retrospect/test-prompts.json`
- `skills/personal-strategy/test-prompts.json`

Each file contains three prompts covering the typical path, a complex or
ambiguous case, and a boundary or false-trigger case.

These files are durable evaluation assets. They do not imply that full Darwin
optimization has already been run. Do not create `results.tsv` or treat dry-run
assessment as a completed independent evaluation until an explicit evaluation
pass is requested.

## Personal Strategy Boundary

`personal-strategy` is now explicit-use only. It carries
`disable-model-invocation: true` and should not be loaded for ordinary
engineering work.

Use it only when the user explicitly invokes it or clearly asks for
persona-backed reasoning about strategy, long-term direction, personal motive,
communication style, life or career tradeoffs, subject structure, or persona
updates.

Do not use it for ordinary coding, refactoring, testing, naming,
implementation planning, or mechanical documentation work. Do not infer a
personal-strategy layer from normal engineering hesitation unless the user asks
for that layer.

`USER_PERSONA.md` remains the only persona source. The persona content should
not be copied into the skill.

`calibration` should not suggest `$personal-strategy`. Mixed requests should
separate engineering facts from personal strategy before answering.

## Current Skill Roles

`calibration` remains the default engineering router for coding, refactoring,
architecture, interface shape, naming, testing, schema, CLI, API, and project
documentation tasks.

User-invoked optional skills are intentionally narrow:

- `brainstorming`: exploratory design when the user explicitly wants divergent
  options before implementation
- `grilling`: adversarial pre-implementation review; intentionally minimal
- `writing-plans`: implementation planning for approved specs or multi-step
  engineering work
- `darwin-skill`: skill evaluation and optimization with test prompts,
  rubrics, and human checkpoints
- `writing-great-skills`: reference for writing and editing skills
- `retrospect`: post-task evidence-driven retrospective
- `personal-strategy`: persona-backed strategic reasoning only on explicit use

Installing these optional skills does not make them always-on. Their value is
in being available through the calibration installer while preserving explicit
invocation boundaries.

## Implemented Batches

The decisions above are implemented by the following current commits:

- `63ffb37` adds document type routing references
- `9333a02` adds the first-party `retrospect` skill
- `ec72084` adds first-party skill test prompts
- `0a19ebf` hardens failure branches and checkpoints
- `bf5278f` makes `personal-strategy` explicit-use only

## Open Follow-ups

Run a full Darwin evaluation only after an explicit request. Until then, the
prompt files are reviewable test assets, not proof of optimized behavior.

Future task retrospectives should be written as `.traces/retros/` artifacts
when the user invokes `$retrospect` or when a task has enough learning value to
warrant a suggested retrospective.

No further decision document is required for the current skill architecture
unless a later discussion changes the role of default routing, optional mode
skills, or repository-local documentation contracts.
