# Repository Agent Map

## Authority

- Read `README.md` for the repository and installer contract.
- Read `docs/README.md` for current decisions and active implementation plans.
- Reusable engineering guidance lives under `references/engineering/`.
- First-party skills live under `skills/`; do not change behavioral cases as
  part of an unrelated implementation.

## Conditional AO Delivery

AO is an optional environment adapter, not a property of every public clone.
Use it only when the current environment has already installed AO, explicitly
adopted this repository, and supplied local host authority. Otherwise use an
isolated worktree for pull-request-bound delivery. Ordinary local engineering
tasks continue directly under repository rules without requiring AO or a new
worktree.

For conversation-authorized implementation intended to cross a pull-request
boundary in an adopted environment, verify AO health and start a task-specific
worker before creating the implementation branch or pull request. If a pull
request already exists, mark it ready for review if it is a draft, then restore
its owning worker or claim it without takeover. Ready-for-review is only an AO
claim prerequisite.

Conversation authorization for a low-risk implementation also authorizes the
worker to request GitHub native auto-merge without a second merge
authorization, but only after required CI passes on the exact current head,
current-head review is clean, and no actionable review threads remain. Read
those gates back immediately before the request. Repository-local stricter
policy, an explicit user stop, or a high-risk, irreversible, permission,
security, secret, release, or compatibility decision withholds auto-merge and
requires escalation.

This authority applies to GitHub's native per-pull-request auto-merge after the
exact-head gate. It does not authorize always-on AO project configuration such
as `autoMerge`, whose cancellation and state-change behavior is unproven and
must remain disabled. If AO is unavailable, use an isolated worktree and report
that fallback for pull-request-bound delivery.

Before mutation, compare the assigned writable workspace and Git root with the
target's owning AO worker. Keep one writer: the controller must not patch,
stage, commit, or push an owner's sibling worktree. Send an `active` or `idle`
owner directly; hold `waiting_input` for provenance and escalate permission or
user-decision prompts. Restore a terminated owner only after authoritative
readback proves runtime release and its OS-owned containment boundary is empty;
otherwise preserve state and monitor.
Before transfer, authoritative readback must prove the former owner cannot
write, ownership is released, and runtime/containment release is complete and
empty; idle/live or cleanup-pending is not quiesced. Otherwise do not transfer.
Do not repeat rejected filesystem escalation. The owner retries same-scope
mechanical feedback within a bounded retry budget.

Classify AO observations by state owner before diagnosing them:

- sandbox state: paths and processes visible only inside the current agent
  sandbox;
- worker state: the AO-created worktree, pane, environment, and Codex home;
- daemon state: the persistent AO service, database, and project readback; and
- host state: the user service manager, filesystem, credentials, and installed
  binaries outside the worker boundary.

A mismatch between these states is diagnostic evidence, not proof that the
host is broken. Verify the state through its owning context and use local host
authority, when present, before changing persistent host configuration.

Use the accepted AO diagnosis states exactly:

- a failure observed only in the sandbox is `indeterminate`;
- active host service plus AO `ready`/`running` readback and a passing health
  probe is `daemon ready`;
- repeated failure from the authoritative host context is `unavailable`; and
- an AO doctor external integration or authentication failure is `delivery
  degraded`, not daemon unavailability. Core doctor failures remain evidence
  about daemon or host readiness and must be diagnosed by their owning state.

## Validation

Install the locked validation environment with:

```bash
pdm sync --clean
```

Before delivery, run:

```bash
pdm lock --check
pdm run check
CODEX_HOME="$(mktemp -d)" bash install.sh --dry-run
git diff --check
git diff --cached --check
git diff --check "${BASE_REF:-main}...HEAD"
git status --short
```

`pdm.lock` is the dependency authority for local and CI validation. Use an
explicit temporary `CODEX_HOME`; never overwrite the user's active Codex
installation during validation.
Run all three diff checks before delivery: the worktree, staged changes, and
the committed branch range are distinct surfaces. Set `BASE_REF` to the pull
request base SHA or an available local base branch when `main` is unavailable.
Treat unexpected status entries after validation as artifacts to remove or
classify before delivery.

## Review Guidelines

- Treat skill trigger expansion, instruction precedence, and routing changes
  as behavior changes, not documentation-only edits.
- Keep project-specific commands and checks in the owning repository rather
  than copying them into cross-project calibration guidance.
- Do not claim a workflow or harness improvement from static validation alone;
  require representative evidence for the stated improvement.
