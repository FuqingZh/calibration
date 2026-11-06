# Workflow Artifact Contracts

Use the workflow engine's native artifact model and the repository's producer
and consumer contracts. Consult the relevant engine or format documentation
when its behavior matters.

Document only the handoff details consumers rely on: artifact identity,
discovery, format, schema, file versus dataset shape, partitioning, and lifecycle.
Keep temporary implementation outputs separate from supported consumer inputs.
Naming prefixes, directory layouts, manifest formats, and configuration languages
belong to the owning workflow.

Preserve existing consumer contracts when changing artifact names or locations;
use [verification discipline](../discipline/verification.md) for compatibility
and handoff checks.
