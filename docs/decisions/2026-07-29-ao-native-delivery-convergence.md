# AO-Native Delivery Convergence

Date: 2026-07-29

Status: Accepted and deployed on the current host

## Decision

The current-host delivery path converges on upstream AO, GitHub, and AO's
Dashboard:

- AO v0.11.1 is the host runtime and Dashboard compatibility target.
- AO's durable Dashboard notifications are the only attention-event surface.
  No email, chat, webhook, Linear, or other external notifier is part of the
  accepted path.
- The current conversation and explicit implementation authorization are the
  work-intake authority. This is conversation-authorized issue intake; AO
  creates or continues the worker from that authorization. GitHub pull requests
  are the delivery, CI, review, and merge fact source. Linear integration is
  deferred and is not an execution prerequisite.
- A narrow fail-closed GitHub auto-merge policy may be used only for explicitly
  classified low-risk pull requests.

The historical Linear decisions, plans, canary evidence, wrapper, and credential
rollback copy remain available for audit. They are not current authority.

## Upstream v0.11.1 Evidence

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

The exact tag source was built locally with the release metadata:

```text
0.11.1 commit 2f6d98f272afa2cd9ea142511fe3a9197d94d2c6 built 2026-07-29T03:21:29Z
```

The installed `/home/fqzhang/.local/bin/ao` SHA-256 is
`b6249d803dd3c3ad8a315783dd3443f0ed0771f5d73d094267ff2f79b0f08bb0`.
Focused upstream CLI, daemon, HTTP, mobile-LAN, notification, and SQLite tests
passed in an environment scrubbed of the active AO worker variables. A broader
run also passed those surfaces and most adapters, but inherited live-session
variables made CLI hook expectations fail; that contaminated run is not used as
release acceptance evidence.

After cutover, `ao status --json` reported ready and healthy on loopback port
3001, `ao doctor --json` reported zero failures, and systemd reported the
service enabled and active with no drop-ins.

## Trusted-LAN Dashboard Compatibility Boundary

Because the release has no supported standalone Web Dashboard on this host, the
deployed LAN surface is a small compatibility adapter, not an upstream-native
headless feature.

- Renderer source: the renderer extracted from the digest-verified v0.11.1
  AppImage.
- API source: the exact locally built v0.11.1 binary above.
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
The service health endpoint reports:

```json
{"status":"ok","mode":"read-only","renderer":"0.11.1","api":"127.0.0.1:3001"}
```

A LAN-bound read returned persisted Dashboard notifications and their unread
count. An isolated headless Chrome run loaded the packaged assets, projects,
sessions, and notification stream; nginx also recorded the renderer's
background agent-refresh POST being rejected with HTTP 403. Reads sourced from
the trusted interface returned 200, while the same root, health, and API reads
sourced from the host's `192.168.10.13` interface returned 403. These readbacks
establish the bounded status/attention use case; they do not establish full
Electron feature parity.

The managed compatibility artifacts are:

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

## Fail-Closed Low-Risk Auto-Merge Policy

Auto-merge is denied unless every condition below is true:

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
6. GitHub's auto-merge request is enabled only after conditions 1-5 are read
   back. Any uncertainty, API failure, head change, new review, failed check, or
   scope expansion cancels or withholds auto-merge.
7. AO records status and attention in its Dashboard only. AO does not override
   branch rules, merge queues, GitHub permissions, or a human stop decision.

This is an allowlist, not a default. Pull requests outside it remain
human-merged. PR #24 is explicitly outside this decision and remains untouched.
PR #36 is superseded by this convergence and may be closed without merging only
after the replacement pull request exists.

### Disposable real-PR canary

[PR #37](https://github.com/FuqingZh/calibration/pull/37) changed only
`docs/canary/ao-native-auto-merge-20260729.md`. Before auto-merge was requested,
GitHub read back the exact head
`5e1627f063dc5238aeb6758b02cebf5282eb1892` as mergeable and current, the
required `validate-skills` check passed on that head, the PR was not draft, and
the GraphQL review-thread readback returned zero unresolved threads.

`gh pr merge 37 --auto --squash` then merged the PR at
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
