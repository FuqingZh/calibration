# Document Types

This directory is a routing layer for engineering documents. It helps decide
which document type to write, where it belongs, and the minimum contract it must
satisfy.

It is not a template library. Do not load every file by default. Select the one
type file that matches the current phase.

## Selection

- Current system facts, boundaries, and contracts:
  `architecture-overview.md`
- Not-yet-approved architecture or implementation direction:
  `design-proposal.md`
- Settled high-impact choice with important alternatives and consequences:
  `decision-record.md`
- Execution slices, affected boundaries, verification, and risks:
  `implementation-plan.md`
- Task-level expectation-versus-actual learning:
  `trace-retro.md`

## Non-Types

- `AGENTS.md` is a scoped operational map for agents, not a durable engineering
  document type. It should point to current authority and executable commands
  instead of duplicating project documentation.
- PR body is a review artifact. Generate it at PR time from the implementation
  plan, actual diff, and verification results.
- Archive is a lifecycle state, not a document type. Archived documents keep
  their original type and move under the repository's existing archive
  convention.

## Authority

Repository-local documentation conventions override these defaults.

Use `../workflow/project_docs_architecture/20260527-v1.0-project-docs-architecture.md`
for project `docs/` layout, file naming, README navigation, and archive
lifecycle rules.

Use `../workflow/task_traces_and_retros/20260527-v1.0-task-traces-and-retros.md`
for `.traces/` layout, retrospective format, evidence handling, and promotion
rules.
