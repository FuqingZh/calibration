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

## Checkpoints

Use explicit checkpoints to prevent retrospectives from turning uncertain
observations into durable rules.

- 🔴 CHECKPOINT: If evidence is missing, contradictory, sensitive, or based
  mostly on user memory, mark the retro `Status: draft` before writing.
- 🔴 CHECKPOINT: If the retro recommends promotion to project docs,
  repository-local instructions, calibration, or memory, write the
  recommendation only. Stop before editing those targets unless the user gives a
  separate explicit request.
- 🔴 CHECKPOINT: Before writing a deep retro, state the keywords that bound the
  historical search. If no credible bounded keyword set exists, fall back to
  `standard`.
- 🔴 CHECKPOINT: Before updating `.traces/index.md`, keep it a short navigation
  index. Do not convert it into a second retrospective or raw evidence log.

## Failure Table

| Trigger | Action |
|---|---|
| No git repository is available | Use only provided evidence and mark `Status: draft`; do not invent git history. |
| No active plan or goal can be found | Reconstruct expected behavior from the user request, commits, docs, and tests; label the source in `Expected`. |
| Git diff is empty but the user asks for a completed-task retro | Use recent commits and user-provided evidence; if neither exists, ask for the task boundary before writing. |
| Validation evidence is missing | Record the missing validation explicitly in `Evidence Quality`; do not claim success. |
| Evidence conflicts | Prefer checked artifacts over memory; record the conflict and mark `Status: draft`. |
| Deep mode lacks bounded keywords | Run `standard` mode and note that deep historical search was skipped. |
| `.traces/index.md` is missing | Create a minimal index with recent retros and repeated patterns only. |
| The user asks to promote a rule during the retro | Write a promotion recommendation and stop before editing long-term rule files. |
| The user asks for raw logs in the retro | Summarize and cite paths by default; use `.traces/evidence/` only when the repository already allows it or the user explicitly asks. |

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
