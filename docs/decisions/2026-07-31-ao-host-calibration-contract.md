# AO Host Calibration Contract

Date: 2026-07-31

Status: accepted

## Decision

Calibration provides a stdlib-only JSON CLI for inspecting, initializing,
planning, rendering, and verifying an explicitly trusted private AO host
profile. Inspection is profile-independent and keeps sandbox, worker, daemon,
and host evidence separate. Sandbox-visible stale paths or read-only failures
cannot override an active user service plus passing `healthz` and `readyz`
probes. AO status is evidence but is not a readiness prerequisite. A doctor
data-dir-write failure caused by a read-only sandbox is a known issue, not a
daemon failure.

The CLI recognizes the existing schema v1 `[ao]`, `[dashboard]`,
`[dashboard.terminal]`, and `[paths]` sections when `schema_version` is absent
or equals `1`. That document retains its existing meaning. Canonical output
uses schema v2, retains those names, and adds `ao.runtime_owner`,
`ao.process_containment`, `dashboard.mode`,
`dashboard.terminal.origin_mode`, and `storage.boundaries`. Migration and
candidate needs are explicit in `plan` and `verify` readback. Unknown keys fail
closed.

## Candidate Boundary

Rendering produces review material, never deployed state. A candidate root is
new or byte-identical, directories use mode `0700`, files use mode `0600`, and
`MANIFEST.json` hashes every other file. Output contains no timestamps,
process IDs, secrets, or active-state snapshots. Runtime candidate output is
private and faithfully retains the explicit absolute paths and trusted
addresses required to reconstruct the requested host semantics. Public
portability applies to tracked source, templates, and synthetic tests.

Terminal output is conditional and off by default. It requires a trusted
single-user model, exact client IP, exact Origin, exact `/mux` location,
GET-and-Upgrade handling, a loopback upstream, and a read-only API boundary.
Origin rewriting remains rejected without paired pre-change and post-change
probe evidence.

## Compatibility

The new CLI is independent of `scripts/adopt_ao_repository.py`. It neither
imports nor changes that adapter, and it does not alter `install.sh`. AO source,
services, proxy state, private profiles, and installed Codex homes remain
outside this public change.

## Verification

Focused tests require 100 percent line coverage, a real schema v1 fixture,
deterministic rendering, profile and mode rejection, evidence precedence,
terminal constraints, and an isolated XDG reconstruction canary using a fake
runner. The canary executes init, inspect, plan, render, verify, and a
byte-identical second render. The canonical repository gate retains public
portability and Markdown-link checks.
