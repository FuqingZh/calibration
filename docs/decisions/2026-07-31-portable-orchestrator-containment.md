# Portable Orchestrator Containment

Version: v1.0
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

## Process-Release Invariant

An orchestrator may mark a worker terminated or its runtime released only
after the OS-owned containment boundary assigned to that worker is empty.
Terminal, tmux, shell, harness-session, or orchestrator-session disappearance
is not proof that descendant processes have exited.

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

Static tests require the discovery, mutation, and process-release invariants in
the harness, generated-agent template, public AO guide, documentation map, and
this decision. Focused assertions cover an empty OS-owned containment boundary,
non-proof from terminal or session disappearance, and observable, retryable
incomplete release. A behavioral prompt exercises a repository below a shared
aggregation root, but remains an unevaluated prompt case rather than evidence
of changed agent behavior. Public portability tests continue to reject
personal paths, private network values, and deployable AO artifacts.
