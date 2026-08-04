# AO Host Calibration CLI Closeout

Date: 2026-08-04

Status: accepted NO-GO closeout

## Context

Pull request #46 explored a public AO host-calibration CLI. Its host-diagnosis
work clarified several portable contracts, but the implementation grew beyond
the boundary calibration should own.

The NO-GO decision was reached when the branch represented 39 commits and
11,606 added lines. Closeout readback on 2026-08-04 found the same
11,606 added lines across 41 commits, with the branch three commits behind the
current `main`; GitHub reports the pull request as conflicting. These numbers
describe delivery scope, not a quality comparison.

## Preserved Host-Diagnosis Contracts

The following contracts remain valid independent of the proposed CLI:

- Keep sandbox, worker, daemon, and host evidence distinct. Sandbox-visible
  absence or mismatch is `indeterminate`, not proof of host failure.
- A host-context diagnosis must use authoritative host-owned evidence for the
  service, AO status, process identity, and health and readiness probes before
  reporting the daemon ready or unavailable.
- Classify external integration or authentication failures as `delivery
  degraded` when the core daemon remains ready. Host-owned core failures affect
  daemon readiness, while malformed or incomplete evidence cannot establish a
  clean result.
- Host inspection is read-only and does not infer trust values, rewrite private
  profiles, deploy candidates, or change services. Private paths, addresses,
  credentials, installed state, and rollback material remain in private host
  authority.

The current portable AO runbook and rendered private host authority own these
contracts. No public host-calibration CLI is required to keep them effective.

## Decision

Do not merge, rebase, or continue the implementation from pull request #46.
The five-command CLI, profile schema and migration, renderer, verifier,
deployment-shaped candidates, and associated test surface exceed calibration's
portable guidance boundary. They also duplicate concerns better owned by AO or
private host operations.

Close #46 after this decision is merged. Retain its source branch for
provenance; do not delete it.

## Reopening Conditions

Reopen this direction only after real host-diagnosis work demonstrates the same
missing capability repeatedly. A hypothetical future need, the existing #46
implementation, or one host's private operations is insufficient evidence.

The first reopened slice must contain read-only `inspect` only. It must keep
state owners explicit, emit evidence without selecting trust or changing host
state, and prove its value on the repeated diagnostic cases that justified
reopening. Initialization, planning, rendering, verification, profile
migration, deployment artifacts, and host mutation remain out of that first
slice and require separate calibration if later evidence supports them.

## Consequences

- The accepted diagnosis contracts remain available through existing public
  guidance and private host authority.
- Calibration adds no CLI, schema, renderer, service, or deployment surface
  from #46.
- Future work starts from current `main` and fresh evidence, not by reviving or
  rebasing the oversized branch.
