---
name: closeout
description: User-invoked task closeout that preserves missing durable context, hands off the next executable action, and archives the current task without expanding authority.
---

# Closeout

Leave the next task a trustworthy starting point, not a second transcript.

Explicit invocation of `$closeout` authorizes only the minimal repository
documentation edits needed to preserve missing durable task context and native
archival. There is no read-only or audit mode. If the required context is
already durable or reliably reconstructable, make no artificial file change.

## Establish State

Read the task and the most specific repository authority. When relevant, verify
drift-prone Git and pull-request state, checks, ownership, and external writes
from their authoritative sources. Treat an external write with an unknown
outcome as pending until authoritative readback resolves it.

## Persist Only What Must Survive

Preserve only accepted decisions, contracts, blockers, and next actions that
must survive the task and are neither recorded nor reliably reconstructable.
Update the existing owning documentation instead of copying transcripts, Git
history, check output, or other reconstructable evidence. Validate every file
you write under the repository's own rules.

A documentation edit in an uncommitted worktree is not yet durable. Before
archival, verify that every new edit has reached the durable repository state
allowed by the existing delivery contract. Use only delivery operations that
contract already authorizes. If a commit, push, pull request, merge, or another
delivery step is required but is not already authorized or completed, list it
under `Open` and leave the task unarchived.

Keep hypotheses, unresolved choices, and unconfirmed lessons in the handoff;
do not promote them into durable project truth. Route substantive engineering
judgment through `$calibration`. Never perform `$retrospect` unless it is
separately invoked.

## Report And Archive

Report these fields:

- `State`: the task and delivery state verified now
- `Completed`: finished work and validation
- `Persisted`: durable context written, or `none` when no edit was needed
- `Open`: remaining blockers, decisions, permissions, or uncertain outcomes
- `Next`: one executable next action

Archive only when every new documentation edit is verified durable and no
operation, permission request, user decision, or unknown external write
remains. Otherwise leave the task unarchived and make the open state and next
action explicit.

Invocation does not authorize commit, push, merge, ownership transfer, another
task, or next-phase work beyond the already authorized delivery contract.
