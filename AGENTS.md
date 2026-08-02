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
isolated worktree only for new or unowned pull-request-bound work; an existing
AO-owned pull request follows the ownership-preservation rule below. Ordinary
local engineering tasks continue directly under repository rules without
requiring AO or a new worktree.

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
must remain disabled. If AO is unavailable, use isolated-worktree fallback only
for new or unowned pull-request-bound work. Existing AO-owned pull requests
defer to the ownership-preservation rule below.

Before any mutation, an already AO-owned repository, worktree, or branch is
subject to the single-writer guard even without a pull request or PR-bound
intent: the controller remains read-only. With installed AO, adoption, supplied
local host authority, and continuation proof or an explicitly bounded canary,
perform owner lookup and handoff through the state rules below; otherwise
preserve the owned state.

For conversation-authorized implementation intended to cross a pull-request
boundary, use AO lifecycle routing only with installed AO, an adopted
repository, supplied local host authority, and an accepted continuation-proven
orchestrator or explicitly bounded canary. Review, analysis, or discussion-only
requests remain read-only. If continuation is unproven, use the narrowed
new/unowned fallback or existing-owner preservation rule. When all gates hold,
verify AO health before lifecycle routing. Then
start a task-specific owning worker for new work that is truly unowned.
Immediately perform fresh authoritative session readback and hand the task to
that owner through normal activity-state routing; only that owner creates the
implementation branch or pull request. An existing draft pull
request must become ready before owner lookup or claim. A ready pull request
with no AO owner is not thereby unowned. Before claim or spawn, authoritative
verification must prove every controller, human, or non-AO writer is quiesced
and cannot write. Otherwise preserve state, do not claim or spawn, and
escalate; AO-owner absence alone is not proof. After that gate, claim without
takeover by an existing or new owner before owner-state lookup. Only
existing-PR claim semantics require an existing pull request. Compare the
assigned writable workspace and Git root with the owning AO worker. Without
supplied local host
authority, follow the narrowed fallback or existing-owner preservation rule and
do not perform AO lifecycle routing. Keep one writer: the controller must not patch,
stage, commit, or push an owner's sibling worktree. Inspect
`session.isTerminated` first. If true, only restore after authoritative readback
proves runtime release and an empty OS-owned containment boundary; otherwise
preserve state. After restoration, perform fresh authoritative session readback
and route or send according to the resulting non-terminated activity state.
Only when false, send `activity.state=active` or `idle` directly, hold
`waiting_input` for provenance, send only when authoritative evidence proves an
already-authorized ordinary idle prompt, and escalate permission or
user-decision prompts; route `exited` through REST resume-agent and return
`blocked` to human authority.
Before transfer, authoritative readback must prove the former owner cannot
write, ownership is released, and runtime/containment release is complete and
empty; idle/live or cleanup-pending is not quiesced. Otherwise do not transfer.
Do not repeat rejected filesystem escalation. The owner retries same-scope
mechanical feedback. Blind retries are limited to idempotent transient
operations or polling and require bounded attempts or deadline, backoff, and
`Retry-After`. Stop on head or scope change, cancellation, non-transient
authentication or permission failure, or exhaustion. For an external write
with unknown outcome, perform authoritative readback and deduplication first;
retry only when the intended state is absent. On stop, preserve observable
state and report the actual stop reason. Use `delivery degraded` only for a
corresponding external integration or authentication failure while the core
daemon remains ready.

If AO is unavailable, isolated-worktree fallback applies only to new or unowned
PR-bound work. Preserve an existing AO-owned PR's branch, worktree, and feedback
until AO or owner restoration unless a real enforceable containment or
write-authority revocation mechanism is authoritatively verified.

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
