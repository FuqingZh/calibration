# Whole-Conversation Closeout

Status: implemented locally; behavior improvement remains unmeasured.

## Problem And Decision

The user invokes closeout before archiving a conversation to preserve important
undocumented discussion. The old minimal-handoff contract could focus on the
latest task and treat recoverable chat as a substitute for project documents.

Closeout now inventories the full accessible conversation, reconciles every
important topic with actual documents, and fills only missing or stale content.
Later corrections supersede earlier conclusions. Important hypotheses and
unresolved choices are documented with status and a next action, not promoted
to established facts. Recent-message views and compaction summaries do not
prove full history coverage; material retrieval gaps must be disclosed.

The report contains Coverage, Documents, and Open, then returns control to the
user without automatic archival or an archive confirmation prompt. Invoking
closeout alone does not authorize archival; a separate explicit archive
instruction is required. Recorded future work does
not prevent archival. Saved, validated, reread local files satisfy local-only
persistence; uncommitted state is disclosed. Existing explicit pre-archive
delivery gates, live operations, unknown writes, and actual pending authority
requests remain blockers. This changes the previous unconditional commit-like
durability gate; it grants no additional Git or external-write authority.

## Boundary With Retrospect

Closeout organizes established discussion and preserves confirmed lessons.
Retrospect investigates causes, expectation-versus-outcome differences, and
new lessons or rule proposals. Neither automatically invokes the other.
Retrospect retains its separately requested persistence boundary.

## Validation Scope

Behavioral prompts cover early topics, compaction, chat-only decisions, later
corrections, no automatic archival, documented future decisions, explicit
delivery gates, and missing
archive capability. They are evaluation inputs, not executed behavior evidence.
Static validation checks package structure, metadata, Markdown, and references.
No claim is made that the revised skill has already eliminated real-session
omissions; representative full-history execution remains an open check.
