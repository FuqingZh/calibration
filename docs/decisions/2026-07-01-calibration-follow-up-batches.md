# Calibration Follow-up Batches

Date: 2026-07-01

## Purpose

This document records the remaining decisions from the calibration skill
architecture discussion and turns them into execution batches.

The rename, naming split, third-party skill vendoring, and installer takeover
are complete. The remaining work is to make the default `calibration` skill a
more precise router and to finish cleaning up optional skill management.

## Status

Implemented on 2026-07-01 in three semantic batches:

- discipline references
- design references and default routing
- optional skill cleanup and third-party source traceability

`writing-plans` and `darwin-skill` remain intentionally uninstalled because
they were not selected as managed optional skills for this pass.

## Batch 1: Discipline References

Create `references/engineering/discipline/` with a short router and three
operational references:

- `refactor.md`: refactor, migration, split, extraction, import cleanup,
  suppression cleanup, and convergence gates
- `debugging.md`: concrete repro, red loop, root-cause proof, and fix validation
- `verification.md`: evidence required before claiming completion, including
  fresh command output, readback checks, live smoke, and final artifact paths

Rationale: these references address the failure mode where temporary transition
debt such as broad imports or suppression comments survives after the immediate
mechanical change.

## Batch 2: Design References and Default Routing

Create `references/engineering/design/` with:

- `README.md`: router for architecture, module, interface, abstraction, and
  boundary decisions
- `codebase.md`: codebase-design vocabulary and judgment checks such as deep
  modules, interface, locality, leverage, and deletion tests

Then update `skills/calibration/SKILL.md` so it reads `principles.md` first and
loads topic routers only when the current task requires them:

- `naming/README.md` for naming decisions
- `discipline/README.md` for refactor, debugging, and verification tasks
- `design/README.md` for architecture, module, interface, and abstraction tasks
- `docs_index.md` only for long-form specifications and project-doc routing

## Batch 3: Optional Skill Cleanup and Source Traceability

Clean up optional skill management:

- retire the stale `grill-me` skill in favor of `grilling`
- keep `brainstorming`, `grilling`, and `writing-great-skills` user-invoked
- keep `writing-plans` uninstalled unless explicitly requested later
- keep `darwin-skill` uninstalled unless skill self-improvement work needs it
- add upstream commit or import ref fields to third-party source records where
  available
- decide whether to patch the brainstorming visual companion from
  `.superpowers/brainstorm` to `.calibration/brainstorm` or leave it documented
  as upstream asset behavior

## Completion Criteria

The follow-up is complete when:

- all accepted reference routers exist
- `calibration` no longer defaults to reading unrelated routing indexes
- stale optional skill names are removed from local Codex state or explicitly
  documented as unmanaged and out of scope
- third-party source records are precise enough to audit future updates
- `bash install.sh --dry-run` passes
- the repository is committed and pushed
