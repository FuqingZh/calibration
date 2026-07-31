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
filesystems must be narrowed to relevant subdirectories and bounded by file
type, depth, or result count. Explicit host-operation tasks may consult the
conditionally rendered private host authority to resolve private mount
topology, exclusions, or safe paths. Ordinary repository work does not load
that authority.

## AO Enforcement Status

The portable rule is an agent and harness invariant. Per-worker systemd scopes
that contain the worker and descendant processes are proposed to upstream AO
as defense in depth; they are not current AO behavior established by this
repository. Calibration does not patch AO, modify a deployed service, or ship
a service unit.

## Compatibility

The decision preserves the installer and repository-adoption contracts. It
adds guidance to the existing generated global instructions, without changing
template variables, installer options, AO configuration, or
`scripts/adopt_ao_repository.py`.

## Verification

Static tests require the invariant in the harness, generated-agent template,
public AO guide, documentation map, and this decision. A behavioral prompt
exercises a repository located below a shared aggregation root and expects
targeted workspace discovery without recursive sibling enumeration or private
host assumptions. Public portability tests continue to reject personal paths,
private network values, and deployable AO artifacts.
