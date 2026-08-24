# Progressive Validation Selection First Smoke Is Invalid

Date: 2026-08-24
Status: invalid evidence; recovery required before comparison

## Context

The first S5 progressive-validation-selection smoke used frozen baseline
`0f21f880383859f060156db6ce69d08eff73ed44` and candidate
`5a94f5826c99f6e748a2d712851874b604471a23`. The controller was the same
candidate commit. It used Codex `0.148.0`, model `gpt-5.6-sol` at `medium`
reasoning effort, and seed `42`.

The local private frozen run root is intentionally not linked or copied into
this public repository. Its public ledger reports 28 of 28 runs completed and
zero failed. However, every public result projection has `valid=false`; each
arm has 14 critical runs; every trajectory contains
`bwrap: loopback: Failed to create NETLINK_ROUTE socket: Operation not
permitted`; and every run has zero broker events. The aggregate elapsed time is
`2280.179936625529` seconds.

The smoke status currently presents this as `reject`. That presentation is
incorrect: the shared executor failure invalidates the public harness evidence
before it can evaluate either arm.

## Decision

Preserve the first-batch evidence, but classify it as **invalid**, not as a
candidate rejection. Do not run repeats, generate judge packets, or obtain
blind judgments from this batch. It makes no comparison, quality, safety, or
activation conclusion about the candidate.

The root cause is three nested network-isolation layers: the outer executor
`bwrap`, the Codex named permission profile with `network=false`, and the
executor shell wrapper's additional `bwrap --unshare-net`. The third layer's
loopback setup attempts to create a `NETLINK_ROUTE` socket, which the enclosing
permission sandbox denies. Consequently the command broker never executes and
zero broker events cannot distinguish baseline from candidate behavior.

The corrective boundary is deliberately narrow:

- Remove only the executor shell wrapper's nested `--unshare-net` boundary.
- Retain CommandBroker's inner networkless `bwrap`, its output isolation, and
  its environment and filesystem constraints.
- Enforce model-command network denial through the already real-machine-tested,
  version-frozen named permission profile instead of an independent generic
  shell network namespace.
- Before every model slot, run profile and shell preflight checks that fail
  closed. Before a 28-run batch, execute one real Codex command as a live
  canary.
- Retain model hard timeouts. Recovery may reuse only a verified completed
  prefix; it must not reinterpret or repair invalid runs.

The correction must not change prompts, skills, cases, fixtures, expected
outcomes, or the candidate comparison contract.

## Alternatives Considered

- Treat the 28 critical outcomes as a candidate rejection. Rejected because
  the common sandbox failure happened before broker evidence and invalidates
  both arms equally.
- Retry or judge the affected runs. Rejected because the batch is not eligible
  for downstream comparison stages and retrying would conceal the harness
  failure.
- Remove all nested isolation. Rejected because the CommandBroker inner
  boundary remains a required constraint; only the conflicting shell wrapper
  network namespace is removed.

## Consequences And Recovery

No candidate activation, rollback, canary, or rollout decision follows from
this smoke. The first-batch ledger remains retained as invalid diagnostic
evidence only.

After the narrow harness repair, create a new controller commit and freeze a
new run root. Verify the per-slot profile and shell preflights, run the real
Codex live canary, then start a fresh 28-run smoke. Only a valid fresh smoke may
enter the predeclared repeat and judge stages.

Reopen this decision only if the live canary or a fail-closed preflight exposes
another boundary outside the stated shell-wrapper change.
