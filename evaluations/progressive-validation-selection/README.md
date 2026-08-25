# Progressive validation selection evaluation

## Current evaluation authority

The frozen 14-pair protocol below is historical background. Do not use it to
accept, reject, tune, or migrate the candidate. The current formal authority is
[`docs/testing/20260825-v2.1-progressive-validation-relative-replacement-test-plan.md`](../../docs/testing/20260825-v2.1-progressive-validation-relative-replacement-test-plan.md): it compares relative net improvement against the current effective baseline while preserving repository-owned mandates, uses fresh outcome-only P01/P02/P03/P04/P05/P10 runs, and treats common failure as inherited debt.

Its G0 preflight at `ff16714999465ad1acbd130dbb9711725584544f`, Codex 0.148.0,
found that `codex exec --json` has no structured, correlated approval event.
The revised protocol intentionally skips approval statistics and does not parse
error-message prose. `Approve for me` remains enabled identically in both arms;
the comparison uses 24 initial runs and no more than 36 runs. See the
[`outcome-only scope decision`](../../docs/decisions/2026-08-25-progressive-validation-outcome-only-approval-scope.md).

This frozen evaluation compares validation-selection behavior without treating
command count as a quality signal. Deterministic command reconciliation decides
whether each declared proof obligation was covered; blinded judges assess only
the quality of diagnosis and reporting.

## Inputs and boundaries

`cases/` contains the public task prompts and command contracts. `fixtures/`
contains synthetic, case-relative repositories. Their `AGENTS.md` files name
the real fixture authorities and commands but do not disclose oracle labels.
The runner assigns `CALIBRATION_EVAL_RUN_ID`; repository wrappers may emit
begin and end `CALIBRATION_CHECK_EVENT` records for diagnostics, but those
workspace-controlled records never establish that a check ran or what it
returned. Runner post-run verification is a separate phase and does not emit
or trust workspace event records.

Executor runs require Linux `bwrap` and a read-mostly mount namespace. The
prepared workspace is writable only at the case's pre-existing
`allowed_changes` files; `.git` and every other original fixture file are
read-only. The trusted Codex process receives a minimal root containing only
system and pinned runtime files, its workspace, isolated `CODEX_HOME`, output
directory, and a runner-private runtime read-only bind containing dual broker
FIFOs. Model-generated commands use a fixed named permission profile with
`network=false` that denies all reads below `/output`; that profile remains the
generic executor-command network boundary. The shell wrapper preserves
filesystem, environment, and FIFO isolation but does not add
`bwrap --unshare-net`. A runner-owned no-model preflight directly probes
named-profile denial, including for a direct executable, rather than assuming
every command happens to use a shell. The source repository, evaluation cases,
rubric, and user home are absent. There is no unconfined fallback: a missing
boundary, a dirty input workspace, an output path inside the workspace, or a
missing allowed target invalidates the run.

PATH shims send an exact candidate command through a runner-owned dual-FIFO
broker transport. The request FIFO is executor write-only and the response FIFO
is executor read-only; an advisory transaction lock serializes cooperating shim
pairs. Each single-write request is at most `PIPE_BUF`; every response carries
`protocol_version` and `request_id` and is bounded by size and timeout limits.
Because the response FIFO must be readable by the executor shim under the same
UID, a malicious executor can steal a response and cause a request-ID mismatch
or timeout; this fails closed as harness-invalid/DoS. Response writes remain
denied by mode `0400` and the read-only bind. For every accepted response, the
runner generates a random 64-hex receipt; only after fully validating that
response does the shim emit the receipt. The oracle matches runner-memory
receipts to actual aliases in order, without placing a token in the public
result. A stolen response therefore lacks its receipt and is harness-invalid
even if its error code collides with a legitimate nonzero exit. The broker does
not trust a
caller-supplied family, identity, working directory, or exit status. It selects
the fixed case and workspace itself, executes at most the configured canonical
command inside its own fresh `bwrap --unshare-net` check sandbox, and records
the real exit in runner memory. An executor can bypass the advisory lock and
directly write an exact canonical request, which can execute that real fixed
check and create a runner event. It cannot forge a valid reconciled result or
event: every runner-memory broker event must match exactly one runner-captured
raw command, and every executed raw alias must match exactly one broker event;
missing, extra, reordered, bypassed, ambiguous, or unmatched raw/event evidence
invalidates the run.

For shell compounds, the oracle retains operators and records only children
that their `&&`, `||`, or `;` control flow actually executes. Broker events
supply each invocation's real exit code. The aggregate parent-shell exit code
and wrapper stdout are never used as child-process truth.

P08 and H04 explicitly classify their probe as `executor_sandbox`. A nonzero
broker event establishes only that the authoritative host boundary was not
available to the executor; the final contract must still report
`not_yet_verified` and cannot turn that event into host-success evidence.

Raw trajectories, isolated Codex homes, authentication material, unredacted
tool captures, and the schema-validated per-run `result.json` are private
artifacts. The private result retains `raw_command` so the deterministic oracle
can be audited. A separately generated public projection must omit raw commands
and may contain only their hashes, normalized family/exit observations,
scorecards, contamination records, and the bounded decision.

The Codex controller process retains the authentication file needed to start a
turn. Model-generated commands run only under the named permission profile
`/output=deny` with `network=false`. Their shell wrapper retains filesystem,
environment, and FIFO isolation without an additional `bwrap --unshare-net`
boundary. This does not claim the outer Codex process has no network access or
cannot read its authentication material. Before every slot, a temporary broker
FIFO round trip must finish with zero retained events and zero errors, then its
transport is closed and recreated fresh. C01 separately proves the actual Codex
command-tool, shell-wrapper, FIFO, and broker path; it does not replace the
runner's no-model direct-executable permission-profile preflight.

## Run protocol

Use the same model, reasoning effort, tools, permissions, prompt, turn budget,
and a fresh workspace and `CODEX_HOME` for both arms. Counterbalance arm order.
Before the 14-case comparison begins, run the independent live canary C01 once
from the separately frozen controller source. C01 is a real `codex exec` turn,
not a no-model permission-profile probe: it must run its one broker-normalized
shell check through the actual FIFO path with exit zero, leave the fixture
unchanged, and report `VERIFICATION_STATUS: verified_ready`. Its private ledger
belongs under the run root's `canary/` directory. A missing or failed C01 proof
blocks every smoke slot; C01 is not an arm, is not part of `case_ids`, and does
not contribute to the 14x2 smoke or repeated-comparison metrics.

The first recovery C01 did not meet that contract: under `network=false`, its
AF_UNIX broker transport was denied before a broker event, despite Codex and
workspace verification exiting zero. It correctly ended
`blocked_by_sandbox_permission_error`; no smoke slot started and it supplies no
candidate comparison result. That early invalid evidence is retained only as
diagnostic history.

The FIFO recovery controller commit
`03830f7bf7a78dd730320109e348578c61c4db79` produced a valid replacement C01:
`verified=true`, result SHA-256
`23f9ac2b87d606f5313408e3b5d781e73e4533dc16565508f28b80e000132d0a`.
It released the 28-slot smoke, which completed 28/28 slots with zero failed.
`smoke-status` returned `reject` for deterministic critical failure; the public
summary is `decision=reject`, `reason=deterministic critical failure`,
`runs=28`. The candidate had 7 valid and 7 critical runs; the baseline had 4
valid and 9 critical runs with `comparable_overvalidation=1`.

Candidate improvements were P01, P02, P05, and P10; regressions were P03 and
P04. Both arms were valid on P07, P09, and H04, and critical on P06, P08, H01,
H02, and H03. Critical categories cover execution, workspace safety,
required-check/proof coverage, and final-answer contract failures. Partial gains
do not offset deterministic critical failures. STOP: no repeats, judges,
activation, or migration are authorized.

For the outcome-only v2.1 comparison, run two initial paired repetitions for
P01, P02, P03, P04, P05, and P10. `run-smoke` executes those 24 slots.
`smoke-status` reports conflicts without treating a candidate task failure as
an automatic veto. Run `run-tiebreaks` only when that status names conflicting
cases; it executes the frozen third pair for those cases and no others. The
maximum is 36 runs. Approval activity is not collected or inferred.

The batch controller freezes exact clean commits, source archives, fixture and
runner hashes, the Codex CLI version, model controls, and the complete schedule
before a model call. It archives its current controller commit separately for
C01, then records the canary only in its independent private ledger. `run-one`
accepts only an authorized frozen slot identifier after verified C01
completion; it
derives the case, arm archive, model, and effort from the private manifest and
writes exclusive start, completion, or failure records. `smoke-status`
recomputes result hashes and classifications for all 24 initial slots. Missing
evidence remains `not_yet_verified`; a baseline selection-only forbidden check
and the same candidate outcome are classified symmetrically as comparable
overvalidation, but no execution, workspace, required-check, or final-answer
failure is reclassified as overvalidation.

The third repetition is a conflict breaker, not a default. A run is invalid,
rather than replaced silently, when its capture, events, source hashes, or
isolation checks fail. Common paired failure is inherited debt; ordinary
candidate-only failure is a loss, while only a realized candidate-only narrow
veto stops the comparison.

The holdouts H01--H04 remain outside instruction authoring and smoke tuning.
They exercise executable prose, authority precedence, generated-output
verification, and an unavailable host-only probe respectively.

## Result interpretation

The deterministic oracle dominates proof coverage and command-selection
failures. Two blind judges use independently randomized A/B labels and never
see source, arm, target, or expected-oracle identity. A tie or a one-judge
preference disagreement is retained as bounded qualitative evidence; it does
not manufacture a consensus. Rollout is blocked for a qualitative regression
only when both judges prefer the baseline on the same case and identify the
same critical dimension.

`fixture-manifest.json` freezes the lexical SHA-256 inventory of every case,
fixture file, and public scoring input. It excludes private results and the
manifest itself; its root-tree hash is derived from the same ordered mapping.
