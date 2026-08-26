# Progressive Validation Selection Early Invalid Evidence And Valid Smoke Rejection

Date: 2026-08-24
Status: historical v2.0 rejection; early invalid evidence retained

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
`2280.179936625529` seconds. The smoke status presentation as `reject` is
therefore incorrect: the shared executor failure invalidates the evidence before
it can evaluate either arm.

The first recovery used controller commit
`5e2f1dc24acd47eb269257a88b3d60096bec372c` and a fresh frozen root. Its
independent real C01 canary failed closed before any smoke slot started. Codex
exited `0`, and its workspace verification command exited `0` with no workspace
change, but the canonical check could not reach the broker: `/broker/bin/bash`
received `EPERM` while connecting to an AF_UNIX endpoint under the Codex named
profile with `network=false`. It emitted zero broker events, the oracle was
invalid, and the final status was `blocked_by_sandbox_permission_error`. The
private result's SHA-256 is
`90a8cfc229382c8ef7b0722cebbb19190dcbc2df24c644f3c93986247ec59299`.

This second result proves the C01 gate is effective: it prevented a smoke whose
canonical command path had not executed. It still supplies no comparison,
quality, safety, or activation evidence about the candidate.

Version-frozen, no-model exact probes establish the recovery constraint. With
`network=false`, the profile blocks AF_UNIX `connect`; enabling both
`network_proxy` and its feature flag still blocks AF_UNIX socket creation, while
TCP and `/output` remain denied. The current documented Unix-socket allowlist
does not alter that observed local CLI behavior. Do not relax network controls.
Under the exact outer `bwrap` and profile, a no-model probe instead completed a
runner-private runtime read-only-bind request/response FIFO round trip with its
lock, while `/output` and TCP remained denied.

## Early Invalid Evidence And FIFO Recovery

Preserve both batches as **invalid**, not as a candidate rejection. Do not run
repeats, generate judge packets, or obtain blind judgments from either result.

Replace the broker transport with a runner-private dual-FIFO protocol. The
runner-memory broker event is the sole execution truth. Each request is a
single writer's record no larger than `PIPE_BUF`; each response carries
`protocol_version` and `request_id` and is bounded by size and timeout limits.
An advisory transaction lock serializes cooperating shim request/response
pairs. The executor has write-only access to the request FIFO and read-only
access to the response FIFO, both through the runtime read-only bind; it cannot
supply an exit result. Because the response FIFO must be readable by the
executor shim under the same UID, a malicious executor can steal a response and
cause a request-ID mismatch or timeout: fail closed as harness-invalid/DoS.
Response writes remain denied by mode `0400` and the read-only bind.
For every accepted response, the runner generates a random 64-hex receipt; only
after fully validating that response does the shim emit the receipt. The oracle
matches runner-memory receipts to actual aliases in order, without placing a
token in the public result. A stolen response therefore lacks its receipt and is
harness-invalid even if its error code collides with a legitimate nonzero exit;
the aggregate shell exit remains non-authoritative for child checks.

The broker accepts only exact canonical argv, fixes the case and workspace,
executes at most that one real fixed check through its inner
`bwrap --unshare-net`, and records the resulting event in runner memory.
Reconcile raw command capture and events one-to-one and in order. Missing,
extra, reordered, bypassed, or ambiguous evidence invalidates the run. An
executor can bypass the advisory lock and directly write an exact canonical
request, which can execute the real fixed check and create a runner event; it
still cannot forge a valid reconciled result or event, because an extra or
unmatched raw/event pair invalidates the run. It cannot request an arbitrary
command or invent an exit result.

Before every slot, preflight the exact transport with a temporary broker round
trip that produces zero retained events and zero errors, then close and recreate
it fresh. C01 must separately demonstrate the actual canonical Codex,
shell-wrapper, FIFO, and broker path before any smoke slot can start. Retain the
named `network=false` profile, model hard timeouts, output isolation, and the
inner networkless check sandbox. Recovery does not change prompts, skills,
cases, fixtures, expected outcomes, or the candidate comparison contract.

## Valid Smoke Result And Decision

The FIFO recovery controller commit was
`03830f7bf7a78dd730320109e348578c61c4db79`. Its C01 live canary is
`verified=true`, with result SHA-256
`23f9ac2b87d606f5313408e3b5d781e73e4533dc16565508f28b80e000132d0a`.
It released a 28-slot smoke: all 28 completed, zero failed, and
`smoke-status` returned `reject` for deterministic critical failure. The public
summary decision is `reject`, reason `deterministic critical failure`, with
`runs=28`.

| Arm | Valid | Critical | Other comparable result |
| --- | ---: | ---: | --- |
| Candidate | 7 | 7 | — |
| Baseline | 4 | 9 | `comparable_overvalidation=1` |

The candidate improved P01, P02, P05, and P10, but regressed P03 and P04.
Both arms were valid on P07, P09, and H04; both were critical on P06, P08,
H01, H02, and H03. Critical outcomes include execution, workspace-safety,
required-check/proof-coverage, and final-answer contract failures. Partial
gains do not offset any deterministic critical failure.

Therefore reject the candidate. STOP: do not run repeats or judges; do not
activate, canary, roll out, or migrate the candidate. The two earlier batches
remain invalid diagnostic evidence and are not reinterpreted as this rejection.

## Alternatives Considered

- Treat the first 28 critical outcomes as a candidate rejection. Rejected
  because the common sandbox failure happened before broker evidence and
  invalidates both arms equally.
- Treat C01's process exit or clean workspace as a canary success. Rejected
  because zero broker events prove the canonical check did not execute.
- Relax `network=false` or enable the network proxy for broker access. Rejected
  because the exact local probes still deny AF_UNIX and because network denial
  remains a required model-command boundary.
- Remove all nested isolation. Rejected because the CommandBroker inner
  networkless `bwrap` remains required; only the incompatible socket transport
  is replaced.

## Consequences

The first-batch ledger and failed first-recovery C01 remain invalid diagnostic
evidence only. The later valid smoke rejects the candidate; no repeat, judge,
activation, real-repository canary, rollout, or migration is authorized.

That consequence is retained for the v2.0 protocol only. The later corrected
[v2.2 relative comparison](2026-08-25-progressive-validation-relative-replacement-acceptance.md)
separates task outcome from evidence parsing and supersedes this rejection for
current progressive-validation authority.
