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
- Durable validation strategy and acceptance evidence:
  `test-plan.md`
- Reproducible performance, numerical, or scale measurement:
  `benchmark-record.md`
- Guided learning from a starting state to a new capability:
  `tutorial.md`
- One concrete task for a competent reader:
  `how-to-guide.md`
- Controlled or high-risk operational procedure:
  `runbook.md`
- Verified external or third-party behavior and safe adaptation:
  `compatibility-record.md`
- Task-level expectation-versus-actual learning: `$retrospect`

## Non-Types

- `AGENTS.md` is a scoped operational map, not a durable document type; its
  content boundary is defined by the [repository harness](../../discipline/harness.md).
- PR body is a review artifact. Generate it at PR time from the implementation
  plan, actual diff, and verification results.
- Archive is a lifecycle state, not a document type. Archived documents keep
  their original type and move under the repository's existing archive
  convention.

## Authority

Repository-local documentation conventions override these defaults.

Use `../workflow/project_docs_architecture/20260805-v1.1-project-docs-architecture.md`
for project `docs/` layout, file naming, README navigation, and archive
lifecycle rules.

Use `$retrospect` for `.traces/` layout, retrospective format, evidence
handling, and promotion rules. Retrospect owns its supporting references; do
not cross-read another skill's internals.

For tutorial and how-to method guidance, use the linked Diataxis references in
the corresponding type files. External methods inform authoring; they do not
silently change the local contract.
