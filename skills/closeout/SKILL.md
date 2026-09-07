---
name: closeout
description: User-invoked whole-conversation closeout that fills documentation gaps across all important topics, preserves unresolved context, and returns control to the user without automatic archival.
---

# Closeout

Leave the next task a complete, trustworthy starting point.

Explicit invocation authorizes the documentation edits needed to preserve
important conversation content, not archival. Minimize duplication, not
history coverage. Do not create a document merely to show activity.

## Cover The Conversation

Review the whole conversation unless the user explicitly narrows the scope.
Build a topic inventory from the earliest available messages, including design
discussions, decisions and their rationale, user corrections, rejected options
that explain a choice, implementation, validation, and unresolved questions.
Do not let the latest request, patch, or Git status define the inventory.

Use available history tools and their pagination to recover earlier messages.
A recent-message view or compaction summary is a navigation aid, not proof of
complete coverage. If needed, inspect this conversation's own session record
using its known identifier and a bounded path; do not search unrelated sessions.
Track the accessible history boundary. If earlier content cannot be recovered,
report the gap and complete the accessible portion without inventing history.
Do not claim full coverage with a material history gap;
an explicit user instruction may accept a closeout limited to accessible history.

## Reconcile Topics With Documents

Read the most specific repository documentation rules. For every important
topic, identify its owning document and whether it is already recorded,
needs updating, is missing, or has no lasting value. Inspect the actual document
before treating a topic as covered. Keep this inventory lightweight.

Being recoverable from chat is not being documented. Preserve missing decisions,
contracts, meaningful tradeoffs, results and their limits, blockers, and next
actions. Reference reconstructable logs and commits rather than copying them.
Update existing owning documents; add a document only when no suitable owner
exists. Do not copy the transcript or force one handoff document per topic.

Use later explicit corrections to update earlier conclusions; retain rejected
or superseded options only when their rationale remains useful. Record important
hypotheses and unresolved choices as such, with available evidence and the next
verification or decision. Do not silently turn them into accepted project facts.

Closeout organizes what the conversation established. It does not investigate
new root causes, derive new lessons, or promote new rules. Suggest `$retrospect`
when that analysis is useful; never run it without separate invocation. Preserve
lessons already confirmed in this conversation with their evidence and scope.
Route necessary cross-project engineering judgment through `$calibration`.

## Verify Persistence And State

Validate and reread the documents written. For local-only work, saved and
verified files count as persisted; disclose uncommitted changes and their paths.
Do not invent a commit, push, or merge requirement. If the existing delivery
contract explicitly requires a stronger state before archival, satisfy it only
through already-authorized operations, or report the unmet requirement and hold.

When relevant, verify Git, pull-request, ownership, and external-write state
through their authoritative sources. Resolve unknown external-write outcomes by
readback when possible. Preserve an existing owner's write boundary; if this
closeout cannot write the required documents, route to the authorized owner or
report the gap rather than claiming persistence.

## Report And Return Control

Report:

- **Coverage**: the topics reviewed and any history-access limits;
- **Documents**: what was added or updated and where, or why no edit was needed;
- **Open**: recorded hypotheses, deferred work and next actions, plus any actual
  closeout blockers and uncommitted delivery state.

Unresolved product decisions or future work do not prevent archival when their
context and next action are recorded. Archival does not mean the project is
finished. Hold for a live operation, an unresolved external write, an actual
pending authorization request, an unmet explicit delivery requirement, or a
material coverage/persistence gap. Do not turn a possible future permission
need into a pending request.

After reporting, return control to the user. Do not automatically archive or
ask for archive confirmation. Invoking `$closeout` alone does not authorize
archival. Only a separate explicit user instruction to archive authorizes that
action; apply the readiness conditions above, use the available native archive
tool, and verify its result. If it is unavailable or fails, report that the task
remains unarchived. Do not claim archival from intent alone.

Invocation does not authorize commit, push, merge, ownership transfer, another
task, or next-phase work beyond the existing delivery contract.
