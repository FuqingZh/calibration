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
- Resolve material product, architecture, interface, or compatibility choices
  in design discussion. For a technical assumption that can be tested, define
  a bounded investigation slice with its question, expected evidence, and
  decision criteria; make dependent implementation conditional on its outcome.
- Use separate plans for independent subsystems that can be implemented and
  accepted on their own.
- State affected files or components and the boundary each one owns before
  decomposing tasks.
- Preserve established repository boundaries unless the settled design
  explicitly changes them.
- For each slice, state applicable predecessors, interfaces, invariants,
  slice-local non-goals, verification, acceptance, and durable evidence.
- For correctness-critical or design-determining behavior, give representative
  inputs or states and observable acceptance results, preferably by referencing
  existing checks. Schedule necessary validation before work that depends on
  its conclusions.
- State cross-slice dependencies using consistent paths, names, types, schemas,
  and compatibility assumptions.
- Include goal, non-goals, assumptions, risks, compatibility concerns,
  rollback or cleanup notes, final verification, and intended review splits.
- Do not invent unstable details merely to make the plan appear complete.

## Complete When

An implementer can start the ready slices without inferring requirements or
recovering design intent. Interfaces, dependencies, and acceptance criteria are
settled for those slices; unresolved technical assumptions have bounded
investigations and explicit conditions for starting dependent implementation.
