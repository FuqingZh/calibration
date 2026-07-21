# Repository Engineering Capability Adoption Closeout

Date: 2026-07-21

Status: Accepted with limitations

## Context

Version 1.4 added a proportional repository-capability adoption entrypoint to
the accepted delivery feedback loop. It required agents to start from local
authority, the current delivery path, and a representative task; classify only
material capabilities as present, missing, or not applicable; and add the
smallest evidenced gap with its durable owner.

Pull request #11 delivered that entrypoint and merged to `main` as
`e8d1f60e3ba9bc27b0a1d56ac207dda5149208c0`. The two live checks then used
`bio_plot_platform` as an application and orchestration candidate and
`biofetch` as a Go CLI transfer case.

## Decision

Retain the v1.4 adoption guidance and close the implementation plan. The two
checks support its proportional capability classification, but they do not
establish that Symphony orchestration is ready or effective in the current
server environment.

- Record a bounded `NO-GO` for the `bio_plot_platform` Symphony canary. Do not
  run E03/E04 through an unverified engine and do not build a custom
  substitute.
- Retain `bio_plot_platform` unchanged. Its product staging and rollback
  contracts are useful application capabilities, not substitutes for task
  claiming, isolated engineering workspaces, or a least-privilege execution
  identity.
- Treat `biofetch` runtime UI, staging, Kubernetes, and Symphony as not
  applicable. Retain its existing authority, test contract, CLI observability,
  and failure-classification behavior unchanged.
- Accept one `biofetch` delivery gap: its documented test, vet, and build gate
  had no GitHub Actions execution or pre-merge check. Correct that gap only in
  `biofetch`; do not promote its workflow into a calibration template.

The result is deliberately asymmetric. A no-change or `NO-GO` result is valid
when evidence supports it, while a concrete repository-local gap still
receives a small enforceable fix.

## Slice 1 Delivery

- Candidate pull request: calibration #11
- Merged commit: `e8d1f60e3ba9bc27b0a1d56ac207dda5149208c0`
- Stable check: `validate-skills`
- Successful `main` run: GitHub Actions run `29815042589`
- Installed global skill source: the repository `skills/calibration` tree at
  the merged commit

Activation was read back from the installed symlink and repository blob
identities before either live repository check began. Existing user changes in
the calibration primary worktree were left untouched.

## `bio_plot_platform` Gate Result

Repository revision:
`607dbe639bce996f0de6a79ff5e0e9b2bf7931b8`.

E03 and E04 are current repository-owned acceptance cases. Their expected
heatmap and correlation-matrix behavior, observed failures, and next validation
steps are recorded in:

- `docs/testing/20260706-v1.0-ai-plotting-workbench-sample-acceptance-test-plan.md`;
- `docs/testing/20260716-v1.0-openwebui-e01-e20-staging-smoke.md`;
- `scripts/run_openwebui_repetition_gate.py`; and
- `tests/test_openwebui_repetition_gate.py`.

That acceptance authority satisfied only part of the orchestration gate. The
canary stopped before execution because all of the following were unavailable:

1. a stable tracker object that Symphony could claim, resume, and report;
2. a repository-owned `WORKFLOW.md` defining that task and its execution
   contract;
3. an installed, running, and handshake-tested Symphony engine with a
   per-issue workspace root;
4. a least-privilege persistent credential boundary for the engineering agent;
   and
5. an engine-owned status and cleanup surface proven on this host.

The GitHub repository contained no issue for E03/E04. Existing E03/E04 labels
inside tests and documents are acceptance case identifiers, not schedulable
tracker state. The available Kubernetes administration identity was also too
broad to serve as a canary execution boundary.

This decision follows Symphony's own execution contract: a tracker, a
repository-owned workflow, deterministic per-issue workspaces, Codex App
Server integration, host authentication, recovery, and observable status are
runtime prerequisites, not details inferred from the existence of staging.
See the [evaluated official specification](https://github.com/openai/symphony/blob/1f3219bb1ea5f69a1305dc594e79b0db57c113c5/SPEC.md)
and [reference implementation README](https://github.com/openai/symphony/blob/1f3219bb1ea5f69a1305dc594e79b0db57c113c5/elixir/README.md).

As evaluated on 2026-07-21, official release
[`v0.0.1`](https://github.com/openai/symphony/releases/tag/v0.0.1) provided a
Linux binary but preceded the GitHub Issues adapter added by Symphony commit
[`044f204`](https://github.com/openai/symphony/commit/044f204f161038f8a12823bbf42f85f089fc77df).
The server had neither that newer source revision nor its build/runtime
dependencies. Installing an incompatible release or building an unpinned
moving branch would not satisfy the gate.

No issue, worktree, workflow, service, repository change, staging change, or
remote write was created for this failed canary.

## `biofetch` Transfer Result

Repository revision:
`2de5dd2924dd4f37feef37796c5e30c19445f0ea`.

The repository already had an explicit authority map and an offline-safe local
gate in `docs/testing/20260717-v1.0-test-contract.md`. Fresh isolated-cache
execution passed:

- `go test ./...`;
- `go vet ./...`;
- `go build -o /tmp/biofetch-adoption ./cmd/biofetch`;
- root CLI help; and
- `manifest build --help`.

GitHub readback found an active `default-branch-pr-gate`, but zero Actions
workflows, runs, and check-runs. Pull requests were therefore required without
a mechanical execution of the repository's existing delivery contract.

The smallest remedy was biofetch pull request #4 at
`002a95a133748478bc1f09dc2672f5d0b2e9b734`: one workflow reuses the existing
test, vet, and build commands with read-only repository permissions. Pull
request Actions run `29816356310` completed successfully and established the
stable check name `validate-biofetch`. Only after that real success was the same
name added to ruleset `19191969`; a subsequent API readback confirmed the
original pull-request, deletion, and non-fast-forward rules remained intact.

An independent Codex agent reviewed the workflow and ruleset increment with no
finding. Pull request #4 then merged as
`eec47579411cdb8aee9b385ef19fc293d02bd9ae`; `main` Actions run `29817336552`
passed the same `validate-biofetch` test, vet, and build job.

Automatic Codex Review completed before merge without a manual trigger. The
`chatgpt-codex-connector[bot]` account added a `+1` reaction to pull request #4
at `2026-07-21T09:03:36Z`, representing the no-finding result. Calibration
pull request #12 independently received the same automatic `+1` result at
`2026-07-21T09:20:29Z`. These readbacks verify the configured automatic review
trigger in both the private CLI repository and the public calibration
repository.

No product source, runtime environment, application-only capability, or
orchestrator was added to `biofetch`.

## Transferable Findings

1. Repository authority and material delivery capability can be evaluated
   without requiring the same artifact set in every repository.
2. Staging proves an application can be observed and rolled back; it does not
   prove an engineering orchestrator can own task continuation safely.
3. A local deterministic gate becomes a delivery gap when pull requests are
   the delivery path but the remote cannot execute or enforce it.
4. External control-plane state must be changed only through its owner and
   read back after mutation. Repository documentation cannot claim a ruleset,
   review, or runner state that GitHub did not confirm.
5. A blocked canary is evidence about missing prerequisites, not evidence that
   the proposed engine failed or succeeded.

These findings require no further calibration skill or harness change. The
current guidance already produced the intended different decisions in the two
repositories.

## Limitations

- The Symphony canary did not run, so this closeout measures adoption-gate
  behavior rather than Symphony implementation quality, recovery, throughput,
  or attention savings.
- `bio_plot_platform` supplied one blocked application case and `biofetch`
  supplied one CLI case; they do not establish broad comparative performance.
- The checks did not run a blind behavior evaluation because this stage did
  not change behavior-bearing calibration guidance.
- A no-finding Automatic Codex Review may be represented only by a pull-request
  reaction, with no review, comment, or thread object. Review-state audits must
  include issue reactions; checking only review and comment collections creates
  a false negative.
- Symphony and its adapters are an engineering preview and may change after
  the pinned observations in this record.

## Reopen Conditions

Reopen the `bio_plot_platform` canary only after current evidence confirms all
of the following:

1. a Symphony version or pinned commit supports the selected tracker;
2. the engine is installed and passes a Codex App Server handshake smoke on
   the intended host;
3. a stable E03/E04 tracker task links the existing repository acceptance
   authority;
4. a minimal repository-owned `WORKFLOW.md` defines task selection, isolated
   workspace ownership, validation, status reporting, and cleanup;
5. a least-privilege persistent identity separates GitHub implementation from
   explicitly authorized staging actions; and
6. a no-product-change task proves claim, resume, report, and cleanup before a
   real E03/E04 attempt.

Any later canary should remain one bounded task with final merge under human
authority. Wider orchestration, recurring gardening, and auto-merge remain
closed until representative evidence justifies them separately.
