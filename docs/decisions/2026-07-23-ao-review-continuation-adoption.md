# AO Review Continuation Adoption

Date: 2026-07-23

Status: historical public summary

## Decision

Adopt a bounded review-continuation adapter for repositories that explicitly
opt in to an already installed AO. A conversation-authorized implementation may
start a task-specific worker, and actionable pull-request feedback may return
to the owning worker.

Repository adoption is not complete until a real event proves continuation.
Registered, configured, and runtime-ready are necessary intermediate states.
Ready-for-review is a claim prerequisite, not proof that the event loop works.

## Public Boundary

AO installation, patches, binary hashes, service definitions, credentials,
host paths, and recovery evidence are private host authority. The current
portable contract lives in
[`../runbooks/agent-orchestrator-review-continuation.md`](../runbooks/agent-orchestrator-review-continuation.md).
