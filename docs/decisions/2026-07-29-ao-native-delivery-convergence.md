# AO-Native Delivery Convergence

Date: 2026-07-29

Status: Accepted and deployed on the current host

## Decision

The current-host delivery path converges on upstream AO, GitHub, and AO's
Dashboard:

- AO v0.11.1 is the Dashboard compatibility target. The host runtime is the
  minimal `0.11.1-calibration.9` review-continuation fork described below.
- AO's durable Dashboard notifications are the only attention-event surface.
  No email, chat, webhook, Linear, or other external notifier is part of the
  accepted path.
- The current conversation and explicit implementation authorization are the
  work-intake authority. This is conversation-authorized issue intake; AO
  creates or continues the worker from that authorization. GitHub pull requests
  are the delivery, CI, review, and merge fact source. Linear integration is
  deferred and is not an execution prerequisite.
- A narrow operator-gated GitHub auto-merge happy path may be used only for
  explicitly classified low-risk pull requests.

The historical Linear decisions, plans, canary evidence, wrapper, and credential
rollback copy remain available for audit. They are not current authority.

## Upstream v0.11.1 And Minimal-Fork Evidence

The accepted source is upstream tag `v0.11.1`, commit
`2f6d98f272afa2cd9ea142511fe3a9197d94d2c6`. GitHub reported the tag as a
verified commit and the release AppImage SHA-256 as
`a2997ef52ad4414581454cef320d2ad0b44062cccfde46be05fa4dd7e3ae1bee`.

The exact AppImage passed that digest check. Its isolated Xvfb launch did not
start a daemon on this host: the packaged daemon requires GLIBC 2.32 and 2.34,
while the host provides GLIBC 2.28. `backend/internal/cli/start.go` also confirms
that `ao start` only resolves and opens Electron; it does not provide a
standalone Web Dashboard listener. The v0.11.1 remote-access documentation and
the executable headless behavior therefore do not establish upstream-native
headless Dashboard support on this host.

The original exact tag source was built locally with the release metadata:

```text
0.11.1 commit 2f6d98f272afa2cd9ea142511fe3a9197d94d2c6 built 2026-07-29T03:21:29Z
```

That upstream binary was superseded after the real PR #38 canary showed that
COMMENTED reviews were not refreshed when provider `UpdatedAt` advanced. The
deployed minimal fork is based directly on `2f6d98f` and ends at
[`ed191f7cb48f33e4915cf0dbfbb3eb2916ca5d13`](https://github.com/FuqingZh/agent-orchestrator/commit/ed191f7cb48f33e4915cf0dbfbb3eb2916ca5d13).
Its eleven-commit patch stack is limited to COMMENTED-review refresh and
actionability, lifecycle-message confirmation, persisted launch-permission
facts and their migration, and reliable Codex paste submission. It contains no
Linear or Symphony intake.

The installed binary reports:

```text
0.11.1-calibration.9 commit ed191f7c built 2026-07-29T10:49:00Z
```

Its SHA-256 is
`0f0adb964c91ae9c9ef0655b0615fc932b07fe1c808fef084e6a265a94c67ad0`.
That digest is specific to the recorded `go1.26.4 linux/amd64` build toolchain
and release flags; reconstruction with another toolchain or flag set requires
its own artifact digest and evidence.
Focused upstream CLI, daemon, HTTP, mobile-LAN, notification, and SQLite tests
passed in an environment scrubbed of the active AO worker variables. A broader
run also passed those surfaces and most adapters, but inherited live-session
variables made CLI hook expectations fail; that contaminated run is not used as
release acceptance evidence.

After cutover, `ao status --json` reported ready and healthy on loopback port
3001, `ao doctor --json` reported zero failures, and systemd reported the
service enabled and active with no drop-ins.

At `2026-07-29T08:37:48Z`, upstream v0.11.1 refreshed PR #38 as mergeability
blocked while reporting `review: none` and `reviewComments: false`, and it did
not automatically continue the owning worker. Calibration.8 later discovered
and pasted a fresh review payload automatically, but left it in the Codex
composer. The operator manually sent `Right` then `Enter` at
`2026-07-29T10:47:15.618543016Z`; that activation does not prove automatic
submission. Calibration.9 was deployed at `2026-07-29T10:49:53Z` to end the
paste burst before submitting. A fresh review-thread event with no manual
terminal key remains the closure gate. No general watcher, issue intake,
negative cancellation behavior, Linear, or Symphony is established.

## Trusted-LAN Dashboard Compatibility Boundary

Because the release has no supported standalone Web Dashboard on this host, the
deployed LAN surface is a small compatibility adapter, not an upstream-native
headless feature.

- Renderer source: the renderer extracted from the digest-verified v0.11.1
  AppImage.
- API source: the exact locally built `0.11.1-calibration.9` binary above.
- Loopback API: fixed `127.0.0.1:3001`, unchanged and not directly exposed.
- Dashboard: fixed `http://192.168.30.205:31080`.
- Network allowlist: `192.168.30.0/24` only.
- Methods: GET and HEAD only.
- Explicitly unavailable: terminal multiplexing, daemon controls, project
  mutation, session mutation, notification mutation, and all other POST, PUT,
  PATCH, or DELETE operations.
- Transport: plaintext HTTP on a user-approved trusted LAN. Do not route this
  listener to another subnet, the Internet, or an untrusted Wi-Fi network.

The compatibility shim supplies the Electron-only read interfaces that the
packaged renderer expects and points its API reads to the same-origin proxy.
The nginx-only liveness endpoint reports:

```json
{"status":"live","component":"ao-dashboard-readonly-nginx","renderer":"0.11.1"}
```

`/dashboard-health` separately proxies AO's `/readyz`; it returns success only
while the Dashboard's AO dependency is ready. A LAN-bound read returned
persisted Dashboard notifications and their unread count. An isolated headless
Chrome run loaded the packaged assets, projects, sessions, and notification
stream; nginx also recorded the renderer's background agent-refresh POST being
rejected with HTTP 403. Reads sourced from the trusted interface returned 200,
while the same root, liveness, health, and API reads sourced from the host's
`192.168.10.13` interface returned 403. These readbacks establish the bounded
status/attention use case; they do not establish full Electron feature parity.

The managed compatibility artifacts are:

- `../runbooks/artifacts/agent-orchestrator-v0.11.1.service`
- `../runbooks/artifacts/ao-dashboard-readonly.nginx.conf`
- `../runbooks/artifacts/ao-dashboard-readonly.service`
- `../runbooks/artifacts/ao-dashboard-readonly-shim.js`
- `../runbooks/artifacts/ao-dashboard-readonly-health.json`

## Linear Retirement

The cutover replaced the complete `calibration` project configuration without a
Linear provider, project, or assignee. AO normalizes the empty tracker value as
`"trackerIntake": {}`. The Linear systemd drop-in was removed from the active
unit in the same transaction as the upstream binary install; the effective
service has no drop-ins and the daemon environment contains no
`AO_LINEAR_API_KEY` or `AO_LINEAR_OAUTH_TOKEN`.

The active root `WORKFLOW.md` Linear intake definition is removed. Historical
plans retain its former contents and behavior evidence, but no repository-root
workflow can make Linear appear to be a current intake authority.

The credential itself was not printed, committed, or revoked incidentally. A
mode-0600 rollback copy and the old binary, wrapper, unit, AppImage, database,
project readback, and hashes are retained under the mode-0700 local backup
directory:

```text
/home/fqzhang/.ao/backups/native-dashboard-20260729T160000
```

The superseded Linear plans remain historical evidence. Re-enabling Linear
requires a new decision; no Linear repair or availability condition blocks the
current GitHub/AO path.

## Verified Low-Risk Auto-Merge Happy Path

Request GitHub auto-merge only when every condition below has already been read
back as true on the exact current head:

1. The pull request is explicitly created as a disposable canary or classified
   low-risk by the repository owner.
2. The diff changes only documentation, comments, test-only fixtures, or a
   similarly reversible non-runtime surface. Dependency, workflow, permission,
   secret, release, installer, skill behavior, host configuration, generated
   lockfile, and production-code changes are excluded.
3. The pull request is not draft, has no merge conflict, and is current with its
   base branch.
4. Every repository-required check passes on the exact head SHA.
5. Every review thread is resolved, no review requests changes, and no required
   review is pending.
6. Immediately before the request, repeat the head SHA, draft, mergeability,
   required-check, review-decision, and unresolved-thread reads. Any
   uncertainty or failed read withholds the request.
7. AO records status and attention in its Dashboard only. AO does not override
   branch rules, merge queues, GitHub permissions, or a human stop decision.

This is an allowlist, not a default. Pull requests outside it remain
human-merged. PR #24 is explicitly outside this decision and remains untouched.
PR #36 is superseded by this convergence and may be closed without merging only
after the replacement pull request exists.

No custom watcher, pending-request monitor, automatic cancellation path, or
negative head-change/check-failure/review-arrival behavior was implemented or
proven. If any state changes after the exact read-back gate, GitHub's native
branch rules and auto-merge behavior are the only enforcement. Operators must
not rely on AO to cancel a pending request. This decision accepts only the
verified already-green happy path.

### Disposable real-PR canary

[PR #37](https://github.com/FuqingZh/calibration/pull/37) changed only
`docs/canary/ao-native-auto-merge-20260729.md`. Before auto-merge was requested,
GitHub read back the exact head
`5e1627f063dc5238aeb6758b02cebf5282eb1892` as mergeable and current, the
required `validate-skills` check passed on that head, the PR was not draft, and
the GraphQL review-thread readback returned zero unresolved threads.

Only after those reads, `gh pr merge 37 --auto --squash` merged the PR at
`2026-07-29T08:08:01Z` as commit
`08118596387e531e31d21bdfe1772ba19d455a55`. The replacement delivery PR
removes the marker, leaving the policy and evidence while discarding the
canary-only file.

## Rollback

To roll back the host:

1. Stop and disable `ao-dashboard-readonly.service`.
2. Restore the saved AO binary and service unit from the backup directory.
3. Restore `linear.conf.disabled` as the active drop-in only if Linear
   reactivation has been separately approved.
4. Restore the saved complete project configuration if the rollback requires
   the old tracker boundary.
5. Reload systemd, restart AO, and require installed hashes, effective unit,
   project configuration, `ao status --json`, and `ao doctor --json` to match
   the selected rollback state.

Do not restore the Linear credential wrapper by itself. Binary, database,
project configuration, unit, and credential boundary must be treated as one
versioned state.
