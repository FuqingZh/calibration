# Portable Orchestrator Containment

Version: v1.1
Date: 2026-07-31
Status: accepted

## Decision

An orchestrated task's assigned workspace is its default filesystem discovery
and mutation boundary. Workers resolve that boundary before discovery and do
not recursively enumerate a shared aggregation root containing sibling
worktrees, sessions, repositories, or unrelated user data.

Recursive discovery on remote mounts, network filesystems, and large shared
filesystems must use a narrowed root and an explicit traversal-aware bound,
such as selected subdirectories or maximum depth, with file type, file size,
result count, and concurrency also bounded where supported. Explicit
host-operation tasks may consult the conditionally rendered private host
authority to resolve private mount topology, exclusions, or safe paths.
Ordinary repository work does not load that authority.

## Workspace Ownership Amendment

Before mutation, a controller compares its assigned writable workspace and Git
root with the target and its owning AO worker. A workspace capability mismatch
means the target belongs to a sibling worker worktree outside the controller's
writable roots; it is not AO unavailable or daemon unavailability. The
controller remains read-only for that worktree: it does not patch, stage,
commit, push, or repeat rejected filesystem escalation. It restores and sends
the owner, then limits itself to external-state readback.

The owner autonomously continues commit, push, CI, review, same-scope
mechanical repair, transient network retry, and polling. Explicit ownership
transfer requires the former owner to be quiesced and preserves one writer.
Human authority remains required for security, compatibility, irreversible,
secret, genuine permission, and merge or deploy decisions not already
authorized by the low-risk native auto-merge contract.

## Process-Release Invariant

An orchestrator may treat worker termination as complete or mark its runtime
released only after the OS-owned containment boundary assigned to that worker
is empty. A worker or session may enter a terminated state while cleanup
remains pending. Terminal, tmux, shell, harness-session, or
orchestrator-session disappearance is not proof that descendant processes have
exited.

An incomplete release remains observable and retryable. The owning control
plane retains enough worker identity, containment identity, and teardown state
to retry cleanup and authoritatively verify that the boundary is empty before
publishing release.

## AO Enforcement Status

The portable discovery, mutation, and process-release rules are agent and
harness contracts. Per-worker systemd scopes that contain the worker and
descendant processes are proposed to upstream AO as defense in depth and as an
OS-owned release boundary. This is not current AO behavior. Current AO does
not yet enforce those scopes. Calibration does not patch AO, modify a deployed
service, or ship a service unit.

## Compatibility

The decision preserves the installer and repository-adoption contracts. It
adds guidance to the existing generated global instructions, without changing
template variables, installer options, AO configuration, or
`scripts/adopt_ao_repository.py`.

## Verification

Static contract evidence requires the discovery, mutation, process-release,
and workspace-ownership invariants in
the harness, generated-agent template, public AO guide, documentation map, and
this decision. Focused assertions cover an empty OS-owned containment boundary,
termination-completion semantics, non-proof from terminal or session
disappearance, and observable, retryable incomplete release. The
shared-aggregation-root prompt remains unevaluated machinery, not behavioral
evidence, and this decision makes no behavioral-improvement claim. A future
evaluation is not an active phase and may reopen only through a separately
reviewed executable protocol with the assigned worktree as its own Git root,
the synthetic sibling outside that repository, structured tool-event root
auditing, and a separate sibling mutation manifest. Public portability tests
continue to reject personal paths, private network values, and deployable AO
artifacts.

Pull request #46 is one bounded representative routing canary for the v1.1
amendment: the controller stopped cross-worktree writes, and the original owner
completed the repair, local gates, push, CI, and exact-head review with no
actionable feedback. This evidence is limited to that routing handoff and does
not establish a universal model or workflow improvement.
