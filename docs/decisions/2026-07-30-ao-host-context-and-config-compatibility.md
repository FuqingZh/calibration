# AO Host Context And Codex-Home Compatibility

Version: v1.0
Date: 2026-07-30
Status: accepted

## Decision

Diagnoses that depend on resources outside an agent sandbox must verify the
relevant fact from an authoritative host context. Sandbox-visible absence or a
mismatch between sandbox, worker, daemon, and host state is evidence for a
hypothesis, not proof that persistent host state is missing or broken.

AO repository guidance names those four state owners. The current-host runbook
owns their concrete verification, repair, and backfill procedure. Existing
opted-in repositories receive the classification when they next cross a normal
pull-request boundary rather than through an unaudited bulk rewrite.

The accepted diagnosis state machine is:

- sandbox-only failure: `indeterminate`;
- active host service, AO `ready`/`running`, and passing `healthz`: `daemon
  ready`;
- repeated authoritative host failure: `unavailable`; and
- doctor external integration or authentication failure: `delivery degraded`,
  not daemon unavailable. Core doctor failures remain classified by the state
  they test.

The AO Codex-home validator now treats `config.toml` as extensible
configuration. It requires these invariants:

- `[features].apps` is exactly `false`;
- `[features].plugins` is exactly `false`; and
- no top-level `mcp_servers` key exists.

TUI state, additional top-level metadata, and additional feature keys are
compatible. Validation is read-only and must not normalize or rewrite a
compatible file.

## Rationale

The previous exact-key check coupled adoption to one minimal configuration
shape. Codex can persist unrelated TUI state and add compatible metadata or
feature keys, so exact equality produced false incompatibility without
improving the AO isolation boundary. Conversely, MCP server configuration is a
top-level capability surface and remains explicitly excluded from the isolated
AO home.

The host-context rule addresses the same class of ownership error at diagnosis
time: an observation made in a restricted context cannot establish the state
of a resource owned by a broader context.

## Evidence

Focused tests cover missing or enabled required features, top-level MCP server
rejection, compatible TUI and metadata state, extra feature keys, and
byte-for-byte preservation of accepted configuration.

The representative writable case `W05` requires an agent to reconcile a stale
sandbox report with an authoritative host-context probe and record the owning
state rather than declaring the host configuration missing. `W01` remains the
bounded local-repair regression control.

Both fresh candidate runs passed with Codex CLI 0.144.1, `gpt-5.6-sol`, medium
reasoning, a workspace-write sandbox, a fresh workspace, and an isolated Codex
home:

| Case | Representative behavior | Result |
| --- | --- | --- |
| W05 host-context diagnosis | Ran `python -m scripts.query_host_context`; recorded exact sandbox, host, feature, health, and raw doctor evidence in structured JSON; classified the daemon as `ready` and delivery as `degraded`; changed only `DIAGNOSIS.json` | Pass in 56.41 s |
| W01 bounded local repair | Preserved the one-file repair boundary, changed only `src/normalize.py`, and passed `python -m unittest -q` | Pass in 29.93 s |

The structured W05 contract compares all required evidence and classifications
exactly, so negated prose does not cause a false rejection and contradictory
host values cannot produce a false pass. The deterministic result hashes are
`b4bb1af92648668763ae7864e8b18c656fcaecdf957442c85b00cb0d64e6111e`
for W05 and
`45a70278e4dd7c44b23f79fb149ac658459c6ef81db1b0841161f6340966b76f`
for W01. Raw trajectories, workspaces, and isolated homes remain temporary
private evidence.

## Compatibility And Limits

- This decision does not permit Apps, Plugins, or top-level MCP servers in the
  isolated AO Codex home.
- It does not modify the live `/home/fqzhang/.ao/codex-home/config.toml`.
- It does not claim that arbitrary future Codex keys are safe; only keys
  outside the three owned invariants are tolerated by this validator.
- Host verification may still be unavailable to a worker. In that case the
  correct result is a bounded diagnosis with the exact host-side check still
  required, not an inferred host mutation.
- W05 is a synthetic single-turn fixture with a repository-provided host probe.
  It does not establish real-service recovery, repeated-failure classification,
  cross-model behavior, or production delivery reliability.
- W01 supplies only a bounded regression check for local repair behavior; it
  does not measure broader instruction interference.
