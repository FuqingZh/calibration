# AO Host Calibration Contract

Date: 2026-07-31

Status: in progress

## Decision

Calibration provides a stdlib-only JSON CLI for inspecting, initializing,
planning, rendering, and verifying an explicitly trusted private AO host
profile. Inspection is profile-independent and keeps sandbox, worker, daemon,
and host evidence separate. Daemon readiness requires host-owned systemd and
AO ready/running status evidence plus matching MainPID/status/health/ready
process identity and validated health and readiness payloads. Sandbox-visible
stale status or a read-only data-dir-write failure remains indeterminate and
cannot be promoted to host evidence. External doctor failures degrade delivery;
host-owned core doctor failures affect daemon readiness, and malformed doctor
output cannot establish that core checks are clean. `--context host` is the
explicit host attestation; `auto` remains sandbox-owned and indeterminate until
a separate positive host-context attestation exists.

The CLI recognizes the existing schema v1 `[ao]`, `[dashboard]`,
`[dashboard.terminal]`, and `[paths]` sections when `schema_version` is absent
or equals `1`. That document retains its existing meaning. Canonical output
uses schema v2, retains those names, and adds `ao.runtime_owner`,
`ao.process_containment`, `dashboard.mode`,
`dashboard.terminal.origin_mode`, and `storage.boundaries`. Migration and
candidate needs are explicit in `plan` and `verify` readback. Unknown keys fail
closed. Storage boundaries are structured path/kind/recursive-search values,
and desired process containment never certifies observed containment.
Fresh init identifies its in-memory profile as schema v2 before
canonicalization, so an explicitly selected v2 Origin mode is preserved.

Legacy v1 terminal validation remains distinct from v2 policy. V1 accepts its
deployed `single-user-trusted-lan` trust name, multiple exact client IPs, and a
loopback upstream ending in `/mux`. Fresh and canonical v2 profiles retain the
stricter terminal safety contract; compatibility reads do not redefine it.

Inspect JSON has a fixed top-level shape: `schema_version`, `command`,
`context`, `states`, `capabilities`, `probes`, `known_issues`, and
`next_actions`. Every probe has `id`, `owner`, `status`, and `detail`.
Daemon state is one of `not_installed`, `ready`, `unavailable`, or
`indeterminate`; delivery state is one of `not_applicable`, `ready`,
`degraded`, or `indeterminate`. AO status and doctor objects retain extension
fields while required subsets are validated independently.

Pure evaluators produce these stable issue IDs:

- `AO-HOST-CONTEXT-MISMATCH`;
- `AO-GLIBC-INCOMPATIBLE`;
- `AO-TMUX-TOO-OLD`;
- `AO-CODEX-HOME-CONFLICT`;
- `AO-DASHBOARD-MUX-NOT-PROXIED`;
- `AO-DASHBOARD-UPSTREAM-ORIGIN-REWRITE`; and
- `AO-PROCESS-CONTAINMENT-UNVERIFIED`.

## Candidate Boundary

Rendering produces review material, never deployed state. A candidate root is
new or byte-identical, directories use mode `0700`, files use mode `0600`, and
`MANIFEST.json` hashes every other file. Output contains no timestamps,
process IDs, secrets, or active-state snapshots. Runtime candidate output is
private and faithfully retains the explicit absolute paths and trusted
addresses required to reconstruct the requested host semantics. Public
portability applies to tracked source, templates, and synthetic tests.

Dashboard and Terminal output are conditional and off by default. Enabling
them requires explicit listen, CIDR, document-root, nginx, service, exact
client-IP, external-Origin, loopback-upstream, upstream-Origin, and origin-mode
inputs as applicable. The generated full nginx candidate keeps static and API
access GET-only and CIDR-restricted, while exact `/mux` requires every exact
client IP, exact Origin, GET, WebSocket Upgrade, and the proven loopback Origin
rewrite. Inspection may discover runtime facts but never chooses trust values.

## Compatibility

The new CLI is independent of `scripts/adopt_ao_repository.py`. It neither
imports nor changes that adapter, and it does not alter `install.sh`. AO source,
services, proxy state, private profiles, and installed Codex homes remain
outside this public change.

## Verification

Focused tests require 100 percent line coverage, a real schema v1 fixture,
deterministic rendering, profile and mode rejection, evidence precedence,
terminal constraints, and an isolated XDG reconstruction canary using a fake
runner. The canary executes the JSON boundary for init, inspect, plan, render,
verify, and a byte-identical second render, and validates the complete nginx
candidate when nginx is available. The canonical repository gate retains
public portability and Markdown-link checks.
