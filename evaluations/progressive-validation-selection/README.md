# Progressive validation selection evaluation

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
directory, and a read-only runner broker endpoint. Model-generated commands use
a fixed named permission profile that denies all reads below `/output` and
disables network access; that named profile owns generic executor-command
network denial. The shell wrapper preserves filesystem, environment, and
read-only broker-endpoint isolation but does not add `bwrap --unshare-net`. A
runner-owned no-model preflight directly probes named-profile denial, including
for a direct executable, rather than assuming every command happens to use a
shell. The source repository, evaluation cases, rubric, and user home are
absent. There is no unconfined fallback: a missing boundary, a dirty input
workspace, an output path inside the workspace, or a missing allowed target
invalidates the run.

PATH shims send an exact candidate command to a runner-owned broker. The broker
does not trust a caller-supplied family, identity, working directory, or exit
status. It selects the fixed case and workspace itself, executes a configured
canonical command inside its own fresh `bwrap --unshare-net` check sandbox, and
records the real exit in runner memory. A direct socket request can only trigger
that real check. Every broker event must match exactly one runner-captured raw
command, and every executed raw alias must match exactly one broker event;
missing, extra, reordered, bypassed, or ambiguous evidence invalidates the run.

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
`/output=deny` with network disabled. Their shell wrapper retains filesystem,
environment, and broker isolation without an additional `bwrap --unshare-net`
boundary. This does not claim the outer Codex process has no network access or
cannot read its authentication material. C01 separately proves the actual
Codex command-tool, shell-wrapper, and broker path; it does not replace the
runner's no-model direct-executable permission-profile preflight.

## Run protocol

Use the same model, reasoning effort, tools, permissions, prompt, turn budget,
and a fresh workspace and `CODEX_HOME` for both arms. Counterbalance arm order.
Before the 14-case comparison begins, run the independent live canary C01 once
from the separately frozen controller source. C01 is a real `codex exec` turn,
not a no-model permission-profile probe: it must run its one broker-normalized
shell check with exit zero, leave the fixture unchanged, and report
`VERIFICATION_STATUS: verified_ready`. Its private ledger belongs under the run
root's `canary/` directory. A missing or failed C01 proof blocks every smoke
slot; C01 is not an arm, is not part of `case_ids`, and does not contribute to
the 14x2 smoke or repeated-comparison metrics.

Run one smoke repetition for each of the 14 comparison cases only. Continue
only if both arms preserve authority and workspace safety and satisfy
deterministic mandatory obligations.

The batch controller freezes exact clean commits, source archives, fixture and
runner hashes, the Codex CLI version, model controls, and the complete schedule
before a model call. It archives its current controller commit separately for
C01, then records the canary only in its independent private ledger. `run-one`
accepts only a frozen smoke slot identifier after verified C01 completion; it
derives the case, arm archive, model, and effort from the private manifest and
writes exclusive start, completion, or failure records. `smoke-status`
recomputes result hashes and classifications for all 28 smoke slots. Missing
evidence remains `not_yet_verified`; a baseline selection-only forbidden check
may remain comparable, but no execution, workspace, required-check, or final-
answer failure is reclassified as overvalidation.

For every eligible arm and every primary or holdout case, record exactly three
valid runs. A run is invalid, rather than replaced silently, when its capture,
events, source hashes, or blind packet leak checks fail. A candidate critical
failure stops that case from contributing an efficiency comparison.

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
