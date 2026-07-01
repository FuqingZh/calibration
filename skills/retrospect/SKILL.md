---
name: retrospect
description: User-invoked engineering retrospective and post-mortem mode for evidence-driven task retros, root-cause review, and promotion recommendations.
disable-model-invocation: true
---

# Retrospect

Use this skill only when the user explicitly invokes `$retrospect`, asks for a
task retrospective, asks for a post-mortem, or asks to turn meaningful task
learning into `.traces/retros/`.

This skill is optional. Do not run it automatically at the end of ordinary
tasks. The `calibration` skill may suggest it after meaningful engineering
deltas such as failed assumptions, rework, validation surprises, broad
refactors, customer-facing delivery, deployment risk, repeated patterns, or
production-adjacent work.

## Purpose

Produce an evidence-driven retrospective that records:

- what was expected
- what actually happened
- where judgment, scope, validation, or execution differed
- what rule should carry forward
- whether the learning should be promoted to project docs, repository-local
  instructions, or calibration

`retrospect` writes retros and promotion recommendations only. Do not
automatically edit long-term rules, project docs, `AGENTS.md`, calibration
references, or memory. Promotion requires a separate explicit user request.

## Modes

Default to `standard` unless the user asks for `deep` or the task clearly needs
a heavier post-mortem.

- `standard`: evidence-driven task retrospective.
- `deep`: heavier post-mortem for failures, repeated regressions, high-risk
  delivery, deployments, customer-facing delivery, production-adjacent work, or
  broad cross-module changes.

## Evidence

For `standard`, collect only task-relevant evidence:

- active plan, goal, implementation-plan, or docs if present
- `git status`, `git diff`, and recent `git log`
- tests, smoke checks, validation artifacts, and user feedback
- local docs or prior traces only when directly tied to the task

For `deep`, include all standard evidence and then use keyword-limited search
through relevant prior traces, plans, memory or session summaries, failure logs,
and superseded docs. Keywords should come from the task name, failure symptom,
file paths, plan document, test name, command, or artifact path.

Do not perform unconstrained history scans.
Do not copy raw logs by default. Cite paths, commands, and short evidence
summaries instead.

## Output Location

Write the retrospective to:

```text
.traces/retros/YYYYMMDD-topic-retro.md
```

If `.traces/` is missing, create only:

```text
.traces/index.md
.traces/retros/
```

Always update `.traces/index.md` as a short navigation index. Do not create
`.traces/raw/`, `.traces/tmp/`, or `.traces/evidence/` unless the repository
already uses them or the user explicitly asks.

Mark uncertain, sensitive, or evidence-limited retros as:

```text
Status: draft
```

Use `Status: current` only when the evidence is sufficient and the retro is not
sensitive.

Do not auto-commit.

## Structure

Use these base sections for all retros:

```markdown
# <Task Or Failure Pattern>

Date:
Project:
Status:
Mode:

## Expected

- Goal:
- Risk:
- Validation plan:
- Key assumptions:

## Actual

- Changes:
- Validation:
- Result:

## Delta

- Underestimated:
- Overestimated:
- Surprise:

## Rule To Carry Forward

- Future rule:

## Promotion Recommendation

- Promote: yes/no
- Target:
- Reason:
```

For `deep` or bug/RCA retros, add only the relevant conditional sections:

```markdown
## Root Cause

## Missed Detection

## Prevention

## Stale Or Superseded Rule

## Evidence Quality
```

## Boundaries

- Use `$grilling` before implementation to stress-test a plan or design.
- Use `$retrospect` after facts exist to audit expectation versus actual,
  root cause, missed detection, and future rules.
- Use `references/engineering/docs/document-types/trace-retro.md` as the
  document-type contract.
- Use `references/engineering/docs/workflow/task_traces_and_retros/20260527-v1.0-task-traces-and-retros.md`
  for trace layout, file naming, index, evidence, and promotion rules.
