# Implementation Plan

Use this type for turning an accepted direction or concrete requirement into
execution slices.

## Where It Lives

Prefer project `docs/implementation-plan/`, or the repository-local planning
location if one already exists.

## Required Content

- Goal, non-goals, and assumptions.
- Affected modules, boundaries, APIs, CLIs, schemas, or docs.
- Execution slices in the intended order.
- Verification plan, including tests, smoke checks, real-data checks, or manual
  acceptance where relevant.
- Risks, compatibility concerns, and rollback or cleanup notes.
- Intended commit or PR split when work should be reviewed in batches.

## Do Not Include

- Current architecture truth that belongs in `architecture-overview.md`.
- Unsettled alternatives that still require a `design-proposal.md`.
- PR body prose. Generate PR body later from the plan, actual diff, and
  verification results.
- Raw logs or execution transcripts.

## Complete When

Another engineer or agent can execute the work without making new structural
decisions, and can tell how completion will be verified.
