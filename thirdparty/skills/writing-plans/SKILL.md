---
name: writing-plans
description: User-invoked implementation planning mode for approved specs, requirements, or multi-step engineering work.
disable-model-invocation: true
---

# Writing Plans

Use this skill only when the user explicitly invokes it or asks for an
implementation plan. It is an optional planning mode, not a default continuation
after brainstorming.

The goal is to write a plan that another competent engineer or agent can execute
without rediscovering the codebase context.

## Inputs

Before writing the plan, identify:

- the approved spec, requirement, or user request being planned
- repository-local instructions and active docs that constrain the work
- files likely to be created, modified, or deleted
- verification commands and final user-visible artifacts
- compatibility, API, CLI, schema, data, or documentation risks

If the input spans multiple independent subsystems, propose separate plans or
plan sections before writing detailed tasks.

## Plan Shape

A useful implementation plan includes:

- goal and non-goals
- assumptions and constraints
- affected files and boundaries
- task list ordered by dependency
- per-task implementation notes
- per-task verification or review gate
- final verification checklist
- risks and rollback or follow-up notes when relevant

Use the repository's normal plan or docs location. Do not force
`docs/superpowers/plans/`.

## Task Granularity

A task is the smallest unit that carries its own review and verification gate.
Split tasks when one could be rejected while a neighboring task is still valid.
Fold setup, config, docs, and fixtures into the task whose deliverable needs
them.

Prefer exact paths, commands, interfaces, expected outputs, and decision points.
Avoid placeholders such as `TBD`, `TODO`, `handle edge cases`, or `write tests`
without specifying the behavior to test.

## Local Policy

- Do not force TDD when the repository or task shape calls for a different
  validation path, but every behavior change still needs appropriate tests or
  smoke checks.
- Do not force per-task commits. Commit when the user asks, the current task
  includes commit/push, or repository workflow requires it.
- Do not force subagent execution or Superpowers execution skills. Handoff to
  the active environment's normal implementation process.
- Preserve project-local planning conventions over this skill's defaults.

## Self-Review

Before claiming the plan is ready, check:

1. Coverage: every accepted requirement maps to a task or an explicit non-goal.
2. Buildability: each task gives enough file, interface, and command detail to
   execute without guessing.
3. Consistency: names, types, paths, and task dependencies line up across the
   whole plan.
4. Verification: the plan proves final behavior, not only intermediate edits.
5. Placeholders: no vague TODOs or generic instructions remain.

For a separate reviewer pass, use `plan-document-reviewer-prompt.md` as a
starting prompt, adjusted to the current repository context.
