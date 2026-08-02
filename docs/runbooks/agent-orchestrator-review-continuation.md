# Portable Agent Orchestrator Integration Guide

Status: current public integration guidance

## Boundary

Calibration has four layers:

1. reusable engineering references;
2. skills that expose those references as model interaction entrypoints;
3. AO as an optional environment adapter; and
4. private host configuration outside the public repository.

The references and public skills work without AO and without a private host
profile. AO installation and upgrades belong to upstream AO Desktop.
Calibration does not install, fork, rebuild, patch, or replace AO.

Private host paths, credentials, service-manager details, network addresses,
and recovery commands belong in local authority. The generated global
`AGENTS.md` may point to that authority for explicit AO or host-operation tasks
only. Skills and references must not discover private host configuration
directly.

## Portable Containment Boundary

An AO worker's assigned task workspace is its default filesystem discovery and
mutation boundary. Do not recursively search a parent aggregation root that
contains sibling worktrees, sessions, repositories, or unrelated user data.
Resolve the assigned workspace first and make any additional repository or
external path explicit.

On remote mounts, network filesystems, and large shared filesystems, narrow
the search root and require a traversal-aware bound such as selected
subdirectories or maximum depth. Also bound file type, file size, result count,
and concurrency where supported. Private mount topology, exclusions, and
host-specific safe paths belong to rendered local authority and are consulted
only for explicit host-operation tasks.

This is a portable operating invariant; process containment is not current AO
behavior established by this guide. A service-manager scope for each worker
and its descendants is proposed to upstream AO as defense in depth. Until
upstream implements and documents that behavior, repository and
generated-agent boundaries remain the active controls; calibration ships no
service unit or deployed host artifact.

Process release is a distinct invariant. An orchestrator may treat worker
termination as complete or mark its runtime released only after the worker's
OS-owned containment boundary is empty. A worker or session may enter a
terminated state while cleanup remains pending. Terminal, tmux, shell,
harness-session, or orchestrator-session disappearance is not proof that
descendant processes have exited. An incomplete release remains observable and
retryable, with enough worker and containment identity retained for cleanup
and authoritative emptiness verification.

Current AO does not yet enforce per-worker systemd scopes. Those scopes remain
an upstream proposal for supplying the required OS-owned containment boundary;
this guide defines the release contract without claiming that mechanism is
deployed.

## State Ownership And Diagnosis

Classify every observation by its owner:

- **sandbox state**: paths and processes visible only inside the current agent
  sandbox;
- **worker state**: the AO-created worktree, pane, environment, and Codex home;
- **daemon state**: AO service, database, project configuration, and API
  readback; and
- **host state**: the service manager, filesystem, credentials, networking, and
  installed binaries outside the worker boundary.

A mismatch between owners is evidence, not proof that the host is broken.
Verify through the owning context before changing persistent state.

Use these outcomes:

- a failure observed only in the sandbox is `indeterminate`;
- active host service plus AO `ready` or `running` readback and a passing
  health probe is `daemon ready`;
- repeated failure from authoritative host context is `unavailable`; and
- an external integration or authentication failure is `delivery degraded`
  when the core daemon remains ready.

If AO is unavailable or local authority cannot be verified, use an isolated
worktree only for new or unowned pull-request-bound work. Existing AO-owned
pull requests defer to the ownership-preservation rule in Pull-Request
Delivery.

## Repository Adoption

For an already installed, CLI-capable AO, repository adoption progresses
through four distinct states:

1. **registered**: AO has a project record;
2. **configured**: persisted settings match the repository's accepted profile;
3. **runtime-ready**: host service, AO status, and diagnostics pass; and
4. **continuation-proven**: a real pull request demonstrates that actionable CI
   or review feedback returns to the owning worker and the correction can be
   pushed.

Do not report adoption complete at registration, configuration, or static
health. `scripts/adopt_ao_repository.py` remains an optional compatible
plan/apply helper for its supported Linux user-service profile. Its apply path
expects `systemd --user`, AO doctor checks, and compatible tmux prerequisites;
it is not a universal Desktop adapter. Other platforms install and operate AO
through upstream Desktop directly. The helper never claims the real event loop
has passed and must preserve its existing CLI contract.

Before any mutation, determine whether the repository, worktree, or branch is
already AO-owned. If so, the controller remains read-only regardless of whether
a pull request exists or the task is PR-bound. Without authority, preserve the
owned state. With authority and implementation authorization, continue only
when continuation is proven or the current task is the explicitly bounded
canary. Before owner lookup and handoff through the state rules below, verify
authoritative AO core health is `daemon ready`; otherwise preserve the owned
state. Read-only review, analysis, and discussion requests remain read-only.

Conversation authorization is sufficient issue intake. Issue-tracker intake,
automatic work discovery, and a separate orchestrator session are not
prerequisites. Normal automatic AO lifecycle routing requires the four-stage
assessment to be `continuation-proven`; an explicitly bounded canary may route
only its current task. When continuation is unproven and this is not that
canary, truly unowned new work uses isolated-worktree fallback, while existing
AO-owned work preserves its branch, worktree, and feedback without owner
lookup, restore, claim, or spawn. Only after the proof gate, for truly unowned
new implementation, start a task-specific
owning worker, immediately perform authoritative session readback, and hand the
task through normal activity-state routing; only that owner creates the branch
or pull request. If an existing draft is already AO-owned, perform owner lookup
and handoff first, then its owning worker marks it ready. If a draft is
unclaimed, its authorized current writer marks it ready, then claim or spawn
without takeover only after authoritative verification proves every
controller, human, or non-AO writer is quiesced and cannot write. No AO owner
does not prove the pull request is unowned. Otherwise preserve state, do not
claim or spawn, and escalate. After that gate, claim or spawn, then perform
fresh authoritative readback and normal activity-state routing.

## Pull-Request Delivery

The portable flow is:

```text
controller -> owning worker -> commit and push -> exact-head CI
           -> current-head review -> same-scope fix by owning worker
           -> no actionable review threads -> merge authority
```

Before mutation, the controller compares its assigned writable workspace and
Git root with the pull request's worktree and owning AO worker. A difference is
a workspace capability mismatch, not AO unavailable or daemon unavailability.
The controller does not patch, stage, commit, or push in the sibling worktree
and does not repeat a rejected filesystem escalation. Inspect
`session.isTerminated` first, then `session.activity.state`; `session.status` is
derived board or SCM state, not the activity source of truth. Route an owner in
`active` or `idle` activity with `ao send`. Hold `waiting_input` and inspect its
provenance: escalate a permission or user-decision prompt, and send only when
authoritative evidence proves it is an ordinary idle prompt within already
granted authority. Route a terminated owner only after authoritative readback
confirms runtime release and its OS-owned containment boundary is empty, using
`ao session restore`; then perform fresh authoritative readback, apply the
normal resulting activity-state routing, and use `ao send` only when permitted.
Otherwise preserve state and monitor.
Route an unclaimed ready pull request to an existing owner with
`ao session claim-pr <session> <pr> -p <project> --no-takeover`, or to a new
owner with `ao spawn --claim-pr ... --no-takeover`. After claim or spawn,
perform fresh authoritative readback and apply the normal owner-state routing;
use `ao send` only when that routing permits it. If
`session.isTerminated=false` and `session.activity.state=exited`, use the
existing REST resume-agent boundary; there is no CLI resume command defined by
this contract. Route `session.activity.state=blocked` to human authority.
Thereafter the controller performs readback only.

The owning worker commits, pushes, observes CI and review, fixes same-scope
mechanical feedback, and autonomously retries only idempotent transient network
operations and polling. Every retry loop has an explicit attempt or deadline
budget, exponential backoff, and honors `Retry-After`. Stop on head or scope
change, cancellation, a non-transient authentication or permission failure, or
budget exhaustion. If an external write times out with unknown outcome, first
perform authoritative readback and deduplication, then retry only when the
intended state is absent. On stop, preserve observable state and report
the actual stop reason instead of looping or requesting repeated approval. Use
`delivery degraded` only for the corresponding external integration or
authentication failure while the core daemon remains ready.

Explicit ownership transfer first requires the former owner to be quiesced and
maintains one writer. Quiesced means authoritative readback shows the former
owner cannot write, normally because it is terminated and ownership is
released, and that runtime release is complete with an empty containment
boundary. A merely idle or live owner, or a terminated owner with cleanup
pending, is not quiesced. Until all conditions hold, preserve state and do not
transfer, claim, or spawn. If only the owner cannot be restored or claimed,
preserve the branch, worktree, pull-request, and feedback state for later
continuation; do not cross-write from the controller. If authoritative host
evidence establishes AO is unavailable, use the normal isolated-worktree
fallback only for new or unowned pull-request-bound work. For an existing
AO-owned pull request, especially one with dirty state, preserve the branch,
worktree, pull-request, and feedback state and wait for AO or owner restoration.
Transfer is allowed only when a real enforceable containment or write-authority
revocation mechanism is available and authoritatively verified; otherwise do
not transfer, because process, tmux, session, or writer absence is not
equivalent proof.
Security, compatibility,
irreversible, secret, and genuine permission decisions still require human
authority. Low-risk GitHub native auto-merge may use authority already granted
by its exact-head contract; deploy always requires separate explicit authority
unless a distinct deployment contract grants it.

Read every gate against the exact current head. An already AO-owned draft routes
to its owner before that owner marks it ready. An unclaimed draft's authorized
current writer marks it ready before the quiescence-gated claim.

Conversation authorization for a low-risk implementation may include GitHub
native per-pull-request auto-merge without a second merge authorization, but
only after required CI passes on the exact current head, current-head review is
clean, and no actionable review threads remain. Repository-local stricter
policy, an explicit stop, or a high-risk, irreversible, permission, security,
secret, release, or compatibility decision withholds auto-merge.

GitHub per-pull-request auto-merge is distinct from AO project `autoMerge`.
Always-on project configuration has different cancellation and state-change
semantics and remains disabled unless separately proven and accepted.

## Dashboard Terminal Boundary

Dashboard Terminal is off by default. Enabling an existing-session terminal is
a control-surface decision; it does not authorize REST mutations or standalone
shell creation.

A trusted, single-user private LAN may opt in only when all of these constraints
are enforced together:

- an exact client IP allowlist;
- an exact allowed WebSocket `Origin`;
- an exact `/mux` route; and
- a loopback-only upstream.

Origin checking is defense in depth, not authentication. Multi-user,
dynamic-address, public, or otherwise untrusted-network deployments require
authentication. Never expose terminal access to a shared subnet or the public
Internet merely because read-only Dashboard routes are available there.

Deployment commands, service units, proxy configurations, credentials, and
network values remain private host authority. This public guide intentionally
contains no deployable host artifact.
