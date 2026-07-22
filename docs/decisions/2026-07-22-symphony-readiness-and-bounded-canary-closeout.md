# Symphony Readiness and Bounded Canary Closeout

Date: 2026-07-22

Status: Closed at Slice 1 (`NO-GO`)

## Context

Version 1.5 reopened the Symphony path only far enough to test a pinned engine
and the current server before creating credentials, a tracker fixture, a
listener, or a persistent installation. The plan was merged by
[pull request #14](https://github.com/FuqingZh/calibration/pull/14) as
`5f2ce8c5c5f15ee24113c62c18b2769b07c50448`. Its stable check was
`validate-skills`. Pull-request run
[`29889815958`](https://github.com/FuqingZh/calibration/actions/runs/29889815958)
succeeded on head `483577a8d7ff52cfb1896de7e930bc3f8c80851d`; post-merge
`main` run
[`29890209666`](https://github.com/FuqingZh/calibration/actions/runs/29890209666)
succeeded on the merge commit.

An independent Agent review found no blocking issue before merge. Automatic
Codex Review was still represented only by an `eyes` reaction after a bounded
five-minute wait, so it was not counted as a successful review. Thirty-five
seconds after merge it returned three P2 findings. All three were valid and
the implementation plan is corrected by this closeout change:

1. both the upstream live E2E and the foreground smoke must run inside the
   dedicated OS or container identity, not only the second step;
2. the issue-only tracker/status identity must remain separate from the
   code-push/pull-request identity as well as the staging identity; and
3. critical or high findings in any dependency executed by readiness checks
   must stop those checks, with audit occurring before tasks compile or start
   dependency or application modules. Resolution and audit necessarily
   evaluate the project's `mix.exs`.

The delayed review confirms the existing repository delivery loop's rule to
keep pending work explicit until the owning platform reports a terminal result.
For this pull request, an `eyes` reaction meant only that Codex accepted the
work; a submitted review with comments or a no-finding reaction was terminal.
Those are observations about this GitHub integration, not a new cross-project
harness rule defined by this closeout.

## Decision

Close v1.5 at the first readiness gate with `NO-GO`. Do not install or run the
pinned Symphony revision as a persistent service and do not proceed to the
GitHub scratch, bounded host, `bio_plot_platform` no-product, or E03/E04
slices.

This is not evidence that Symphony orchestration is ineffective. It is
evidence that the evaluated upstream lock and the current host test surface do
not satisfy the predeclared safety and full-validation gates. A diagnostic
lock-only update indicates a likely upstream remediation path, but it is not a
reviewed or published Symphony revision and is not an installation candidate.

## Probe Boundary and Identity

The probe used only temporary roots under
`/tmp/symphony-readiness-1f3219bb-20260722` and
`/tmp/symphony-lockprobe-1f3219bb-20260722`. Tool, Mix, Hex, cache, and Codex
homes were redirected into those roots. The real Codex App Server handshake
used an empty isolated `CODEX_HOME`; it did not copy authentication, start a
model turn, or contact a tracker.

The probe ran inside the current Codex filesystem and process sandbox but
under the host `fqzhang` Unix identity. It therefore does not prove the
dedicated worker identity required by later slices. The exploratory sequence
also compiled and ran focused tests before the automatic review clarified the
stricter audit-before-execution ordering. No credential, listener, or real
repository was exposed, but that sequence does not satisfy the corrected
future gate and must not be reused as its passing evidence.

## Source and Toolchain Readback

- Evaluated Symphony source:
  [`1f3219bb1ea5f69a1305dc594e79b0db57c113c5`](https://github.com/openai/symphony/commit/1f3219bb1ea5f69a1305dc594e79b0db57c113c5),
  verified against the then-current upstream `main` and checked out detached.
- Upstream `elixir/mix.lock` remained unchanged, with SHA-256
  `f707a715e6a4e91fc865c1c78d286a5211759a94659caa87e6cd6bad12a6f90c`.
- `mise` `2026.7.11` was bootstrapped from a checksummed binary; its SHA-256
  was `904896399722568d66589a45d928dee1094c03a4a1746176aeb42bf3c5f11233`.
- The pinned project toolchain was Erlang/OTP 28 and Elixir 1.19.5 compiled
  with OTP 28.
- The real protocol probe used `codex-cli 0.144.1`.
- The host supplied Git 2.27.0. A temporary diagnostic environment supplied
  Git 2.51.2 without changing the host installation.

## Passing Evidence

- The focused GitHub adapter suite passed: 8 tests, 0 failures.
- The focused Symphony protocol test passed: 1 test, 0 failures, 51 excluded.
  That test uses upstream's fake Codex executable and verifies the larger
  initialize/thread/turn sequence.
- A separate real `codex app-server` initialize/initialized handshake returned
  `symphony-readiness-probe/0.144.1` and the expected isolated Codex home. It
  intentionally stopped before authentication, thread creation, or a model
  turn.
- In the upstream `make all` sequence, dependency setup, escript build,
  format checking, and Credo/spec lint completed before coverage tests failed.
- Changing only the diagnostic probe's lockfile through normal dependency
  resolution made `mix hex.audit` pass and preserved passing GitHub adapter and
  focused protocol tests.

These results establish source compatibility for narrow surfaces. They do not
override the dependency or full-suite failures below.

## First Blocking Gate: Dependency Audit

The unchanged upstream lock failed `mix hex.audit` with 26 current findings:
14 high, 9 medium, and 3 low. The table groups every advisory identifier and
shows the clean version selected by the diagnostic lock resolution. The last
column is a tested clean resolution, not a claim that it is the minimum fixed
version for every grouped advisory.

| Package | Locked | Findings | Advisory identifiers | Diagnostic clean resolution |
| --- | --- | --- | --- | --- |
| `bandit` | 1.10.3 | 4 high, 3 medium | `GHSA-rf5q-vwxw-gmrf`, `GHSA-9q9q-324x-93r2`, `GHSA-pf94-94m9-536p`, `GHSA-q6v9-r226-v65f`, `GHSA-frh3-6pv6-rc8j`, `GHSA-c67r-gc9j-2qf7`, `GHSA-375f-4r2h-f99j` | 1.12.0 |
| `decimal` | 2.3.0 | 1 medium | `GHSA-rhv4-8758-jx7v` | 3.1.1 |
| `phoenix` | 1.8.4 | 2 high, 1 medium | `GHSA-628h-q48j-jr6q`, `GHSA-6983-jfq8-485w`, `GHSA-63mc-hw7g-86rr` | 1.8.9 |
| `req` | 0.5.17 | 1 high, 1 low | `GHSA-655f-mp8p-96gv`, `GHSA-px9f-whj3-246m` | 0.6.3 |
| `mint` | 1.7.1 | 4 high, 3 medium, 1 low | `GHSA-8pf6-g464-h6h9`, `GHSA-2p26-p43x-fhp8`, `GHSA-mjqx-c6f6-7rc2`, `GHSA-c59h-fq4p-r36r`, `GHSA-qrfr-wh4c-3qhw`, `GHSA-g586-ccqf-7x4r`, `GHSA-2pg6-44cx-c49v`, `GHSA-x3x7-96vm-6h2w` | 1.9.3 |
| `plug` | 1.19.1 | 2 high, 1 medium, 1 low | `GHSA-95qv-c9g9-rm63`, `GHSA-wpmj-jh88-rpgm`, `GHSA-j43x-5hjq-rgxf`, `GHSA-468c-vq7p-gh64` | 1.20.3 |
| `hpax` | 1.0.3 | 1 high | `GHSA-jj2p-32j7-whj2` | 1.0.4 |

The high findings include unauthenticated memory-exhaustion and denial-of-
service paths in the HTTP server and outbound HTTP client stack. Loopback
binding would reduce exposure but would not make the original lock pass and
would not address malicious or oversized tracker responses. No finding was
ignored or allowlisted.

## Full Upstream Gate

The unchanged upstream source also failed `make all` at coverage:

- 296 tests ran, with 3 failures and 6 skipped;
- `workspace bootstrap can be implemented in after_create hook` failed because
  the host Git 2.27.0 does not support the upstream `git init -b` command;
- `normal worker exit schedules active-state continuation retry` failed its
  remaining-delay lower bound; and
- `abnormal worker exit increments retry attempt progressively` failed its
  remaining-delay lower bound.

The workspace-hook test passed when rerun with temporary Git 2.51.2. The two
timing assertions remained unstable with the newer Git and with a reduced
scheduler count. Because coverage failed, the official gate stopped before
Dialyzer. The result is a host/toolchain incompatibility plus timing fragility,
not a product-behavior verdict, but it is not a green upstream gate.

## Diagnostic Lock-only Probe

Normal `mix deps.update --all` changed only `elixir/mix.lock`: 22 dependency
entries were updated. The diagnostic lock selected the clean versions shown
above, `mix hex.audit` returned zero advisories, and the two focused suites
continued to pass.

This probe establishes that current version constraints can resolve to a clean
lock without an application-source change. It does not establish full-suite,
Dialyzer, release, or live GitHub compatibility. The lock was neither committed
to calibration nor pushed to OpenAI's repository, and no private Symphony fork
was created.

## External-state Readback

No persistent Symphony program, configuration, state directory, service unit,
listener, BEAM process, dashboard, scratch repository, tracker token, or
worker credential was created. `FuqingZh/symphony-canary` remained absent.
No `bio_plot_platform` issue, workflow, branch, pull request, repository
content, Actions configuration, ruleset, staging state, or E03/E04 task was
changed.

The only persistent host mutation was hardening
`/home/fqzhang/.config/gh/hosts.yml` from mode 755 to mode 600. Its contents and
authentication were not copied into the probe, and the broad GitHub CLI OAuth
identity was not used as a Symphony credential.

## Reopen Conditions

Reopen with a new plan or explicit successor only when all of the following
are available:

1. a new verified upstream Symphony commit contains a reviewed dependency
   refresh, or the user separately authorizes contribution of such a change;
2. dependency resolution and `mix hex.audit` run first inside a disposable
   constrained build identity, and no critical or high advisory remains in a
   dependency the readiness checks or runtime would execute; every medium or
   lower finding also has a recorded applicability decision and explicit risk
   acceptance before the gate is treated as passing;
3. the official full gate, including Dialyzer, passes in the intended worker
   environment with a supported Git version and the retry-timing behavior
   understood or corrected;
4. both the upstream GitHub live E2E and the foreground orchestrator smoke run
   inside the same tested dedicated OS or container identity;
5. a fine-grained issue-only tracker/status credential is provisioned
   separately from any code-push/pull-request credential and any staging
   credential; and
6. the scratch repository passes claim, stop, resume, terminal cleanup, and
   unauthorized-write checks before any persistent service or real-repository
   canary is created.

These conditions govern re-entry into generic host and scratch readiness; they
do not replace the cumulative repository gates in the 2026-07-21 adoption
closeout. Before any `bio_plot_platform` no-product or E03/E04 run, that
repository must still provide a stable tracker object linked to its existing
acceptance authority, a repository-owned `WORKFLOW.md` defining task
selection, isolated workspace ownership, validation, status reporting, and
cleanup, and a no-product task that proves claim, resume, report, stop, and
cleanup. E03/E04 remains closed until both the generic and repository-specific
conditions pass.

Until then, Symphony remains a candidate implementation for a reusable
cross-repository continuation capability, not an installed global service.
Scheduled Tasks, a custom orchestrator, wider autonomous gardening, and
auto-merge remain outside this decision.
