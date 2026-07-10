# Implementation Plan

Use this type for turning a settled requirement or accepted direction into a
decision-complete execution plan.

## Where It Lives

Prefer project `docs/implementation-plan/`, or the repository-local planning
location when one already exists.

Persist or commit the plan only when explicitly requested or required by
repository workflow.

## Grounding

Ground the plan in the settled requirement or design, repository-local
instructions, current implementation, affected contracts, expected artifacts,
and available verification paths.

If a material product, architecture, interface, or compatibility decision
remains open, return it to design discussion before completing the plan; do not
bury it in a task or placeholder.

Use separate plans for independent subsystems that can be implemented and
accepted on their own.

## Execution Structure

Map the affected files or components and state what each one owns before
decomposing tasks.

Preserve established repository boundaries unless the settled design explicitly
changes them.

Structure the plan as a dependency-aware task graph. Each execution slice owns
one cohesive, independently reviewable outcome and its verification gate; split
slices only where one outcome could be rejected while another remains valid.

Make independent slices and dependency gates visible without prescribing goals,
subagents, or a specific execution runtime.

For each cross-slice dependency, state what the earlier slice produces and the
later slice consumes, using consistent names, types, schemas, paths, and
compatibility assumptions.

Fold setup, configuration, fixtures, and documentation into the slice whose
outcome requires them.

Each execution slice states, where applicable:

- exact files or components affected
- interfaces and contracts created or changed
- required behavior, invariants, and slice-local non-goals
- predecessor slices and the dependency gates they must satisfy
- the verification and acceptance gate, using tests, smoke checks, real-data
  checks, artifact inspection, or manual review as appropriate
- exact commands and expected evidence when the repository already determines
  them
- user-visible or durable artifacts through which the slice proves its result

Do not invent unstable details merely to make the plan appear complete.

## Plan-Level Content

Include:

- goal, non-goals, and assumptions
- affected modules and contract surfaces
- risks, compatibility concerns, and rollback or cleanup notes
- final verification and user-visible acceptance
- intended commit or PR split when review should occur in semantic batches

Do not include:

- unsettled alternatives that belong in a design proposal
- current architecture truth that belongs in an architecture overview
- raw logs or execution transcripts
- PR body prose
- placeholders that defer material decisions to implementation

## Complete When

Complete when an implementer can follow the task graph without inferring
requirements, recovering design intent, or resolving interfaces, dependencies,
or acceptance criteria left open by the plan.
