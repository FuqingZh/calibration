# Repository Agent Harness

Use this reference when an agent repeatedly stalls, rediscovers the same
operation, lacks feedback, or cannot reliably navigate and complete work in a
repository.

The goal is to identify the missing repository capability and place it at the
lowest durable layer that can provide it. Do not default to adding prompt text.

## Missing Capability Diagnosis

| Observed gap | Prefer |
| --- | --- |
| Facts or authority are hard to find | repository map, current docs, or generated reference |
| A repeated operation is hard to execute | repository script, tool, or stable command |
| Correctness cannot be decided | test, grader, acceptance fixture, or explicit contract |
| Runtime state cannot be observed | logs, metrics, traces, screenshots, or inspectable artifacts |
| A boundary is repeatedly violated | lint, structural test, schema, or typed interface |
| A task cannot survive interruption or handoff | durable task state, isolated workspace, or orchestration |

Confirm the gap from actual failures, review feedback, or repeated task
evidence. A longer instruction is not a substitute for a missing capability.

## Placement Ladder

Place each learned capability with the owner able to keep it current and, when
possible, enforce it:

| Knowledge or capability | Owner |
| --- | --- |
| Temporary observation | current task or `.traces/` |
| Stable project fact or boundary | project documentation |
| Repeated project operation | repository script or tool |
| Mechanically decidable invariant | test, lint, schema check, or CI |
| Representative output-quality problem | evaluation case and rubric |
| Cross-project engineering judgment | calibration |
| Private direction or personal progress | private planning or memory surface |

Memory and conversation may identify where to look, but current repository,
environment, and external-system evidence remain authoritative.

## Repository Capability Adoption

When asked to assess or improve a repository for agent-led engineering, begin
with its delivery goal, local authority, current feedback loop, and a
representative task. Do not begin from a universal maturity model or a fixed
set of artifacts.

Treat named tools and artifacts as possible means unless the user or an
accepted contract requires that exact artifact. Assess the capability they
serve before creating them.

### Ruff quality-gate baseline

When a Python repository uses Ruff or is choosing a Python lint gate, inspect
and follow its repository-local Ruff contract first. Do not replace an existing
rule selection with a shared default.

When no repository-local Ruff rule contract exists and Ruff is an appropriate
fit, recommend the stable high-signal fallback `E`, `F`, `I`, `UP`, `B`, `SIM`,
and `RUF`. Do not enable `S`, `ANN`, `D`, `PL`, `ALL`, or preview rules by
default. Treat broader or preview selections as repository-specific policy
choices that need their own evidence and migration decision.

Make adoption actionable through the repository-owned configuration and
canonical validation entrypoint. Inspect the resulting violations, fix only
deterministic first-party issues introduced by the selected rules, preserve
behavior, and keep vendored or generated exclusions under repository authority.

Consider only capabilities that are material to the repository's work:

- finding current authority and repository-specific operating constraints;
- setting up, executing, and deciding deterministic verification;
- delivering through pull-request validation, independent review, and bounded
  feedback repair when pull requests are the repository's delivery path;
- starting and observing the real runtime when correctness depends on
  application behavior;
- preserving, resuming, or orchestrating task state when actual task volume
  requires it; and
- promoting repeated failures into the owning test, constraint, operation, or
  document.

Classify each considered capability from current evidence as present, missing,
or not applicable. Leave an adequate capability unchanged. For a missing
capability, add the smallest durable increment with its repository or external
control-plane owner. Do not replace a not-applicable capability with ceremony.
For example, a library or CLI does not need a UI, staging deployment,
observability stack, or orchestrator merely because an application repository
might benefit from them.

An assessment request is read-only. When adoption is authorized, implement
reversible repository-local gaps without asking the user for discoverable
facts; retain the human-authority and external-control-plane boundaries below.
Do not assign a generic maturity score, require identical `AGENTS.md`, CI,
runtime, or workflow files, or promote repository-local implementation details
into calibration.

## `AGENTS.md` Contract

Treat `AGENTS.md` as an operational map for an agent entering a repository or
subtree. Include only repository-specific information needed to find authority
and execute work, such as:

- a compact repository or subtree map;
- links to current architecture, testing, planning, and deployment authority;
- environment entrypoints and canonical verification commands;
- repository-specific review guidance when external agents cannot inherit a
  developer's global instructions;
- external resources, dangerous operations, and permission boundaries;
- repository-local exceptions to broader defaults.

Keep root and nested scopes explicit. Point to `docs/README.md` when the
repository has one. Do not copy architecture prose, test matrices, temporary
task state, generic engineering guidance, or source articles into
`AGENTS.md`. A repository with no useful local increment may omit it.

## Implementation Task Intake

Treat a repository task as initiated when the user authorizes implementation
or delivery, for example by asking the agent to implement, modify, fix, execute
an accepted plan, or publish the resulting change. A request to analyze,
review, discuss, or write a plan remains read-only unless it also authorizes
the change.

At intake, discover the repository's current delivery path and whether the
current host and repository already have an accepted continuation
orchestrator. When they do, and the authorized task is intended to cross a
pull-request CI or review boundary, route it to that orchestrator without
requiring the user to name the tool again:

- start a task-specific worker in an isolated workspace for new work;
- claim or restore the owning worker when a pull request already exists; and
- retain human authority for high-risk, irreversible, permission, security,
  secret, release, compatibility, and other materially underdetermined
  decisions.

### Low-risk GitHub native auto-merge

Conversation authorization for a low-risk implementation includes permission
to request GitHub native auto-merge without a second merge authorization; a
repository-local stricter policy wins. Request it only after reading back that
required CI passes on the exact current head, current-head review is clean, and
no actionable review threads remain. Withhold the request after an explicit
user stop or when the work requires a high-risk, irreversible, permission,
security, secret, release, or compatibility decision.

This is a per-pull-request GitHub control armed only after the exact-head gate.
It is not permission to enable always-on AO project `autoMerge` or a reaction
that automatically merges approvals. Those AO configuration paths lack proven
head-change, failure, review-arrival, and cancellation behavior. Those
unproven AO paths remain disabled unless a separate repository decision
establishes them.

Use only an already accepted repository, host, identity, and permission
configuration. Do not silently register every repository, enable
permissionless execution on another host, or introduce an orchestrator merely
because implementation was authorized. If the accepted orchestrator is
unavailable or the repository has not adopted it, continue through the normal
isolated-Worktree delivery path and report that bounded fallback instead of
asking the user to diagnose infrastructure.

## Orchestrator Containment

Treat each task workspace as the default filesystem discovery and mutation
boundary. An orchestrated worker must not recursively enumerate an aggregation
root that contains sibling worktrees, sessions, repositories, or unrelated
user data merely because that root is reachable. Resolve the assigned
repository and task workspace first, run discovery from that boundary, and
name any additional repository or external path before accessing it.

This is a portable orchestrator invariant, independent of a particular service
manager or host layout. Repository instructions and orchestration adapters
should make the assigned workspace discoverable and keep mutations scoped to
it. Process-level enforcement, such as a service-manager scope that constrains
descendant processes, is a stronger defense in depth when the upstream
orchestrator supports it; documentation must not describe a proposed
containment mechanism as current AO behavior.

A **workspace capability mismatch** exists when the controller's assigned
writable workspace or Git root does not contain the target change, while an AO
worker owns the target repository, worktree, branch, or pull request. Before
mutation, compare the assigned writable workspace and resolved Git root with
the target and its owning AO worker. On mismatch, the controller remains
read-only: it must not apply patches, stage, commit, or push in a sibling
worktree, and it must not loop on rejected filesystem escalation. Restore and
send the owner only after authoritative readback proves runtime release and an
empty containment boundary; otherwise preserve state and monitor. Use the
controller only for orchestration and readback.

Explicit ownership transfer requires the former owner to be quiesced and must
preserve exactly one writer. Quiesced means authoritative readback proves the
former owner cannot write, normally because it is terminated and ownership is
released, and proves complete runtime release with an empty containment
boundary. An idle or live owner, or a terminated owner with cleanup pending,
is not quiesced; preserve state and do not transfer. Within the same authorized
scope, the owner
autonomously retries mechanical CI and review repairs and only idempotent
transient network operations or polling. Retry loops require an explicit
attempt or deadline budget, backoff, and `Retry-After`; they stop on head or
scope change, cancellation, non-transient authentication or permission
failure, or budget exhaustion. For an external write with unknown outcome,
authoritative readback and deduplication must prove the intended state absent
before retry. On stop, preserve observable state and report delivery degraded
instead of looping or requesting repeated approval.

Security, compatibility, irreversible, secret, and genuine permission
decisions remain human authority. The existing low-risk GitHub native
auto-merge contract may preauthorize merge; deploy requires separate explicit
authority unless a distinct deployment contract exists. A workspace
capability mismatch is not evidence that AO is unavailable.

True AO unavailability may use the normal isolated-worktree fallback. For an
existing pull request, that fallback is still an ownership transfer: require
authoritative proof that the former owner is quiesced and preserve one writer.
If that proof is unavailable, preserve state rather than cross-write.

## Orchestrator Process Release

Treat process release as a separate portable lifecycle invariant. An
orchestrator may treat worker termination as complete or mark its runtime
released only after the OS-owned containment boundary assigned to that worker
is empty. A worker or session may enter a terminated state while cleanup
remains pending. A terminal, tmux pane, shell, harness session, or orchestrator
session disappearing is not proof that descendant processes have exited.

When the containment boundary is not empty or cannot be authoritatively read,
keep the incomplete release observable and retryable. Preserve enough worker
identity and containment state for the owning control plane to retry cleanup
and verify emptiness; do not silently convert a partial teardown into a
released state.

This is a portable release contract, not a claim about current enforcement.
Per-worker systemd scopes are one proposed upstream mechanism for providing an
OS-owned boundary. Current AO does not yet enforce those scopes.

## Accepted Orchestrator Repository Adoption

For an explicitly opted-in repository on a host whose orchestrator, identity,
and permission profile are already accepted, distinguish these states:

1. **registered**: the orchestrator has a project record for the repository;
2. **configured**: persisted configuration readback matches the accepted host
   profile and repository branch/session settings;
3. **runtime-ready**: the persistent service is enabled and active, daemon
   status is ready, and orchestrator diagnostics pass; and
4. **continuation-proven**: a real pull request demonstrates that actionable
   CI or review feedback returns to the original worker and that the worker can
   push its correction.

Do not report repository adoption as complete at registration, configuration,
or a passing static health check. Use the portable AO guide plus conditional
private host authority instead of inventing permission, identity, or service
defaults. Record the repository-specific adoption fact and task-intake
entrypoint in the repository's own `AGENTS.md` through its normal delivery
path. Keep any accepted continuation service alive beyond the initiating
conversation.

For conversation-authorized work, neither issue-tracker intake nor a separate
orchestrator session is a prerequisite. Start or claim the task-specific
worker before creating its implementation branch or pull request. Until the
real-event canary passes, label the repository `runtime-ready`, keep AO project
`autoMerge` off, and retain the normal isolated-Worktree fallback.

## Repository Delivery Feedback Loop

When a repository change is intended to land through a pull request:

1. Discover the repository-owned setup, validation, and delivery commands,
   together with the current CI and review feedback surfaces.
2. Use existing platform defaults and automatic setup before adding custom
   configuration.
3. Classify an observed setup, validation, review, or environment failure
   before changing the harness. When an existing check correctly identifies an
   implementation defect, fix the product code; the feedback capability is
   already working. Do not preconfigure every repository.
4. Only treat the failure as a missing capability when the repository cannot
   reliably discover, execute, decide, or observe what delivery requires. Then
   place the smallest fix with its durable owner: a repository command or
   script, a mechanical test or CI check, a useful repository-specific
   `AGENTS.md` increment, or the external platform that owns the capability.
5. Prefer one repository-owned entrypoint that local agents, CI, cloud
   environments, and developers can reuse.
6. Hand the pull request to mechanical validation and platform-native agent
   review. After the first remote readback confirms that those systems accepted
   the current commit, return control with the durable PR state instead of
   keeping a foreground conversation open for expected remote waits.
7. Continue asynchronous CI, review, and deployment waits through the owning
   platform or an already accepted event-driven continuation orchestrator.
   Use a background or scheduled task only when that control plane can observe
   the work and resume its owner; do not substitute an unreachable scheduler
   for server-side continuation. Wake the foreground only for actionable
   feedback, a terminal result, or a decision requiring human authority;
   keep pending work explicit rather than claiming completion.
8. Address mechanical feedback in a bounded background iteration and repeat
   until the declared checks pass. Escalate product intent, tradeoffs, risk, and
   irreversible actions rather than making the user babysit routine polling.
9. Verify external state after changing it. If the current surface cannot
   observe or modify an external control plane, report the exact authorization
   or configuration action without claiming completion.

A cloud environment is an execution surface, not the repository's source of
truth. Start with automatic setup and customize it only after a representative
task exposes a concrete gap. Keep setup logic in the repository when local,
CI, and cloud execution can share it. Keep server-only dependencies and data
behind repository-owned checks or CI runners rather than assuming a hosted
environment can reproduce them.

Treat terminal access as a control surface, even when it is presented inside a
read-only dashboard or operational viewer, and keep it off by default. A
trusted single-user private LAN may opt in only with an exact client IP, exact
WebSocket Origin, exact terminal path, and loopback upstream. Origin checking is
defense in depth, not authentication. Multi-user, dynamic-address, public, or
untrusted-network deployments require authentication. Keep read-only status and
observation routes independently constrained so adding terminal access does not
implicitly enable REST mutations, standalone shell creation, or broader
network access.

Prefer platform-native automatic review when the repository and account
support it. Put only repository-specific review guidance in the closest useful
`AGENTS.md`; do not assume that global local instructions are available in
cloud execution.

Adopt a recurring pull-request babysitter or failure-classification task only
after the operation is genuinely recurring. A foreground conversation that
repeatedly polls CI or review queues, or repeatedly reopens after mechanical
feedback, is evidence of that recurrence. Prefer one shared task covering
selected repositories over duplicated per-repository tasks, and keep schedule
state in the platform control plane rather than representing it as repository
state.

## Harness Proportionality

Start from the repository's current feedback loop. Add the smallest capability
that addresses an observed gap, verify that it changes the failure mode, and
stop when the loop is adequate. Repository category or size does not imply a
mandatory harness checklist.

## Human Escalation

Escalate only decisions that require human authority:

- product intent and priority;
- scope, interface, or compatibility tradeoffs;
- risk acceptance;
- irreversible or high-impact external operations;
- judgment that remains materially underdetermined after safe evidence
  gathering.

When escalation remains after safe evidence gathering, present the checked
evidence, the unresolved decision, and a recommendation.

## Orchestration Adoption Gate

Consider a durable `WORKFLOW.md` or Symphony-style orchestrator only when all
relevant prerequisites exist:

- parallel task volume creates material context-switching or coordination
  cost;
- agents must claim, resume, retry, or continuously advance work;
- issue or task state is stable enough to act as a state machine;
- per-task workspaces and permission boundaries are reliable;
- an actual orchestrator will execute the contract.

Without those conditions, use ordinary short-lived tasks, Worktrees, scripts,
and platform-native PR state. Do not create a decorative workflow contract.

When the gate is satisfied, prefer an existing maintained execution engine,
such as Symphony, over a custom scheduler. The engine may claim, resume, and
retry work, but it does not own repository authority, acceptance criteria,
permissions, or risk policy. Keep workflow state and environment details with
the repository or external control plane, validate one bounded representative
task before broader rollout, and do not turn local labels, deployment topology,
or access configuration into cross-project calibration rules.

## Completion

Complete a harness change only when the observed gap, selected owner, smallest
capability, and verification path are explicit. Evaluate representative
behavior separately when claiming the system became more effective.
