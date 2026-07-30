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
worktree and report that bounded fallback.

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
plan/apply adapter for an already installed AO. It never claims the real event
loop has passed and must preserve its existing CLI contract.

Conversation authorization is sufficient issue intake. Issue-tracker intake,
automatic work discovery, and a separate orchestrator session are not
prerequisites. Start a task-specific worker for new implementation, or claim
the ready-for-review pull request with the owning worker without takeover.

## Pull-Request Delivery

The portable flow is:

```text
conversation -> task-specific worker -> pull request
             -> exact-head CI -> current-head review
             -> no actionable review threads -> merge authority
```

Read every gate against the exact current head. A draft pull request must become
ready before AO claims it; ready-for-review is only a claim prerequisite.

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
