# Implementation Plan

## Use When

Use this type to turn a settled requirement or accepted direction into a
decision-complete execution plan.

## Method Reference

Use a dependency-aware task graph with one independently reviewable outcome and
verification gate per slice. Keep the plan grounded in the accepted design and
repository rules.

## Local Requirements

- Prefer project `docs/implementation-plans/`, or the repository-local planning
  location when one already exists.
- Persist or commit the plan only when explicitly requested or required by
  repository workflow.
- Ground the plan in the settled requirement or design, repository-local
  instructions, current implementation, affected contracts, expected artifacts,
  and available verification paths.
- If a material product, architecture, interface, or compatibility decision
  remains open, return it to design discussion before completing the plan.
- Use separate plans for independent subsystems that can be implemented and
  accepted on their own.
- State affected files or components and the boundary each one owns before
  decomposing tasks.
- Preserve established repository boundaries unless the settled design
  explicitly changes them.
- For each slice, state applicable predecessors, interfaces, invariants,
  slice-local non-goals, verification, acceptance, and durable evidence.
- State cross-slice dependencies using consistent paths, names, types, schemas,
  and compatibility assumptions.
- Include goal, non-goals, assumptions, risks, compatibility concerns,
  rollback or cleanup notes, final verification, and intended review splits.
- Do not invent unstable details merely to make the plan appear complete.

## Complete When

An implementer can follow the task graph without inferring requirements,
recovering design intent, or resolving interfaces, dependencies, or acceptance
criteria left open by the plan.
