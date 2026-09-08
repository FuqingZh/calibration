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

### Diagnostic suppression baseline

Classify a diagnostic by the owner of the invalid or incomplete contract, not
only by the source line where a checker reports it. A warning at a first-party
call site may still originate from incomplete external typing, generated code,
vendored code, or a demonstrated checker limitation.

For first-party code and interfaces, repair the contract or implementation. Do
not use an ignore comment, warning annotation, lint disable, type escape, or
weaker checker configuration merely to make the required check pass.

Contain an external, generated, vendored, or checker gap at its narrowest
repository-owned boundary. Prefer, as the language and repository allow, a
typed adapter, stub, wrapper, declaration, or targeted configuration exclusion
that makes the assumed contract explicit and testable. Do not edit an external
or generated source merely to satisfy a local checker.

Use a source-level suppression only when no such boundary can express a
demonstrably valid contract. Name the exact diagnostic and retain reviewable
evidence for the exception. Do not hide a first-party failure on the same line.
Blanket and file-, module-, or project-wide weakening is not an acceptable
check-passing strategy. Keep accepted exceptions mechanically discoverable,
reject unused exceptions when the checker supports it, and prevent unexplained
growth through the repository-owned validation path.

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

At intake, discover the repository's accepted delivery path. Ordinary local
engineering does not require AO, an issue tracker, or an orchestrator session.

For AO-mediated delivery, adoption, owner routing, or teardown, read the
[canonical AO integration guide](../agent-orchestrator-review-continuation.md)
before lifecycle actions. It owns the exact-head GitHub native auto-merge gates,
single-writer and release conditions, state evidence, and bounded retries.
Preserve already-owned work and do not cross-write sibling worktrees. If the
guide or its required authority is unavailable, preserve owned state; use
isolated-worktree fallback only for new or unowned pull-request-bound work.
Use native `using-ao` and CLI help for command mechanics. Do not create a second
feedback scheduler or maintain another copy of AO's state table here.

## Repository Delivery Feedback Loop

Delegation transfers execution, not responsibility for the requested outcome.
The coordinator tracks progress, routes actionable blockers, and verifies final
acceptance. A sent instruction, running worker, or intermediate success is not
completion. Use existing task state to retain the goal, acceptance criteria,
owner, outstanding work, and next observation; do not require another document.

Before ending foreground tracking of unfinished work, verify that a durable
continuation mechanism has accepted responsibility for observing the work,
resuming its owner, and delivering actionable or terminal notifications to a
reachable recipient. Otherwise continue bounded observation and authorized
follow-up, or report the exact tracking blocker when continuation is unavailable.
Do not silently make the user responsible for asking again. This accountability
does not require per-command supervision or a duplicate polling scheduler.

When a repository change is intended to land through a pull request:

Focused installed skills may own ordinary GitHub mechanics:
`github:gh-address-comments` for actionable pull-request feedback and
`github:gh-fix-ci` for failing GitHub Actions checks. If unavailable, use
repository- or platform-native tooling. These optional skills do not grant
write or scope authority, replace the current owner, or make their absence a
harness gap.

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
   review. After remote readback confirms acceptance of the current commit and
   the continuation handoff above is verified, return control with the durable
   PR state and outstanding work instead of keeping a foreground conversation
   open for expected remote waits. PR submission alone is not that handoff.
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

For review convergence, continue mechanical feedback within the current
explicitly declared and authorized pull request contract through the existing
bounded owner loop. When exact-current-head review proposes work beyond that
contract or the distinct configured review-convergence budget is exhausted,
pause remote review, preserve branch, head, worktree, owner, and feedback state,
and invoke calibration. For out-of-contract feedback, calibration first decides
to reject or escalate the feedback or to accept an authorized contract
expansion; only after acceptance does it choose among one pull request,
independent pull requests, or a dependent stack. For review-convergence budget
exhaustion, calibration makes the same topology choice from the preserved
state. Independent slices remain independent pull requests. For genuinely
dependent slices, use platform-native stacking when available; otherwise use
ordinary dependent pull requests. Exhaustion of a transport, polling, or
idempotent-operation retry budget retains its existing preserve-and-report path
and is not a topology signal. Do not impose universal LOC, file-count, or
review-round thresholds.

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

## Further reading

- [DORA: Working in small batches](https://dora.dev/capabilities/working-in-small-batches/)
- [Google Engineering Practices: Small CLs](https://google.github.io/eng-practices/review/developer/small-cls.html)
