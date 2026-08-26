# Progressive Validation Relative-Replacement Approval-Observability Preflight

Date: 2026-08-25
Status: superseded for the outcome-only protocol

## Decision

Do not start the v2.1 relative-replacement model evaluation. G0 was executed at
HEAD `ff16714999465ad1acbd130dbb9711725584544f` with Codex 0.148.0 and found
that the available `codex exec --json` schema has command status/error strings
but no structured, correlated approval event. The current runner also ignores
error items, but parsing those unversioned messages would still be
insufficient. It cannot establish the approval-request, decision, target, or
bypass evidence required by the formal [v2.1 test plan](../testing/20260825-v2.1-progressive-validation-relative-replacement-test-plan.md).

The immutable official source evidence is:

- [exec_events.rs at rust-v0.148.0](https://github.com/openai/codex/blob/rust-v0.148.0/codex-rs/exec/src/exec_events.rs)
- [event_processor_with_jsonl_output.rs at rust-v0.148.0](https://github.com/openai/codex/blob/rust-v0.148.0/codex-rs/exec/src/event_processor_with_jsonl_output.rs)

The inspected CLI binary SHA-256 is
`ac2cfed85fb647d61e0150b8548102b330e4799d9d81ad5d354de701edf6b074`.

## Consequences

Record `blocked_by_approval_observability`, with zero model runs. This is
neither candidate acceptance nor rejection. No candidate wording, config,
controller, schema, fixture, harness expansion, or downstream migration is
authorized from this result.

The 2026-08-24 baseline, smoke, rejection, and recovery records are retained as
historical evidence only. They do not resolve this blocked preflight and must
not be pooled into the new relative comparison.

The user subsequently removed approval statistics from the replacement
decision. The missing structured events remain a real limitation, but the
revised protocol neither scores nor reconstructs approval activity. This record
therefore no longer blocks the outcome-only comparison; it remains the reason
approval burden is excluded.

## Unblock Boundary

G0 may be retried when a future Codex version exposes the required structured
events on the existing path. Introducing a different trusted protocol, such as
an app-server adapter, requires separately authorized work; parsing warning or
error prose does not qualify. The retry must freeze the exact candidate and
controls and begin the fresh protocol only if G0 passes. No real external
resource, secret, or irreversible external effect may be used to obtain that
evidence.
