# Agent Orchestrator Review Continuation Runbook

Date: 2026-07-23

Status: Current for the `fqzhang` user on the present Linux host

## Purpose And Boundary

This runbook reconstructs the pinned AO service that connects an actionable
GitHub Automatic Codex Review finding to the original AO-managed Codex worker.
For an individually registered repository, the same service may start or claim
a task-specific worker after a conversation explicitly authorizes
implementation and pull-request delivery. It does not install Symphony,
replace GitHub Actions or Automatic Review, enable unattended issue intake or
automatic work discovery, register every repository, or enable auto-merge.

The service is intentionally permissionless for the current single-user host.
AO calls this mode `bypass-permissions`; the Codex adapter emits
`--dangerously-bypass-approvals-and-sandbox`. Do not reuse that choice on a new
host without explicit risk acceptance from its owner.

## Pinned Inputs

- Repository: `https://github.com/AgentWrapper/agent-orchestrator.git`
- Tested upstream commit:
  `04841344c82f213b8fc0e34b713e2442f8793d2b`
- Patch 1:
  [`patches/0001-fix-refresh-commented-review-threads-on-PR-updates.patch`](patches/0001-fix-refresh-commented-review-threads-on-PR-updates.patch)
- Patch 2:
  [`patches/0002-fix-submit-long-tmux-prompts-reliably.patch`](patches/0002-fix-submit-long-tmux-prompts-reliably.patch)
- Installed `ao` SHA-256:
  `25fab37d7279e72d0e3c2295630c1eb47ed4ff4f54c08b02e4125ca3b9efcdeb`
- Installed `ao-daemon` SHA-256:
  `5bd25fd1647c4c6eb2e22b35aa9f257c0d76d23c5ed0fa42c5bed32745e290e8`

AO pull request #2872 was still open on 2026-07-23 and its head had advanced
to `da29cba9274c4eed8a6947f602675360a29fba81`. Do not substitute that or a
later head for the tested commit without rerunning validation.

## Prerequisites

The current host uses:

- Git 2.27.0 or later;
- Go 1.25.7 or later as required by the pinned AO `backend/go.mod`; the
  documented rebuild used Go 1.26.4;
- tmux 3.5 or later; AO's runtime integration uses the `window-size` option
  that the host's `/usr/bin/tmux` 2.7 does not support;
- `codex` authenticated for the `fqzhang` user;
- `gh` authenticated for the repositories AO will observe; and
- the host proxy variables available to the user service when direct model and
  GitHub access is unavailable;
- a functioning `systemd --user` manager with lingering enabled when the
  service must survive logout.

No token is copied into the repository or service unit. AO discovers the
existing user authentication at runtime.

## Rebuild

Run from a clean checkout of this calibration repository:

```bash
AO_BUILD_ROOT="$(mktemp -d)"
git clone https://github.com/AgentWrapper/agent-orchestrator.git \
  "${AO_BUILD_ROOT}/source"
git -C "${AO_BUILD_ROOT}/source" checkout \
  04841344c82f213b8fc0e34b713e2442f8793d2b
git -C "${AO_BUILD_ROOT}/source" am \
  "$PWD/docs/runbooks/patches/0001-fix-refresh-commented-review-threads-on-PR-updates.patch" \
  "$PWD/docs/runbooks/patches/0002-fix-submit-long-tmux-prompts-reliably.patch"

cd "${AO_BUILD_ROOT}/source/backend"
go test ./internal/adapters/runtime/tmux \
  ./internal/observe/scm \
  ./internal/lifecycle \
  ./internal/domain \
  ./internal/adapters/scm/github
mkdir -p "${AO_BUILD_ROOT}/bin"
go build -buildvcs=false -o "${AO_BUILD_ROOT}/bin/ao" ./cmd/ao
go build -buildvcs=false -o "${AO_BUILD_ROOT}/bin/ao-daemon" .
sha256sum "${AO_BUILD_ROOT}/bin/ao" \
  "${AO_BUILD_ROOT}/bin/ao-daemon"
```

VCS stamping is disabled because replaying mail patches creates equivalent
trees with new committer metadata. Go build IDs can still make hashes
toolchain-specific. On a different supported toolchain, a hash difference
requires source, patch, test, and launch review; it is not by itself proof of a
behavior change.

## Install

Install as the `fqzhang` user:

```bash
install -D -m 0755 "${AO_BUILD_ROOT}/bin/ao" \
  /home/fqzhang/.local/bin/ao
install -D -m 0755 "${AO_BUILD_ROOT}/bin/ao-daemon" \
  /home/fqzhang/.local/bin/ao-daemon
```

When tmux 3.5 comes from the current micromamba environment, create the wrapper
`/home/fqzhang/.local/lib/ao/bin/tmux`:

```sh
#!/bin/sh

LD_LIBRARY_PATH=/home/fqzhang/micromamba/envs/gwas-cli/lib \
  exec /home/fqzhang/micromamba/envs/gwas-cli/bin/tmux "$@"
```

Install it with mode `0755`. Do not put that micromamba `LD_LIBRARY_PATH` on
the entire AO service: it changes Git/curl certificate discovery and caused a
real worker push to fail on this host.

Create `/home/fqzhang/.config/systemd/user/agent-orchestrator.service`:

```ini
[Unit]
Description=Agent Orchestrator daemon
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=%h
Environment=PATH=%h/.local/lib/ao/bin:%h/.nvm/versions/node/v22.22.2/bin:%h/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=HTTP_PROXY=http://127.0.0.1:7897
Environment=HTTPS_PROXY=http://127.0.0.1:7897
Environment=ALL_PROXY=http://127.0.0.1:7897
Environment=NO_PROXY=localhost,127.0.0.1,::1,192.168.0.0/16,192.168.30.202,10.0.0.0/8,172.16.0.0/12
Environment=http_proxy=http://127.0.0.1:7897
Environment=https_proxy=http://127.0.0.1:7897
Environment=all_proxy=http://127.0.0.1:7897
Environment=no_proxy=localhost,127.0.0.1,::1,192.168.0.0/16,192.168.30.202,10.0.0.0/8,172.16.0.0/12
ExecStart=%h/.local/bin/ao-daemon
Restart=on-failure
RestartSec=3
UMask=0077

[Install]
WantedBy=default.target
```

Then enable it:

```bash
systemctl --user daemon-reload
systemctl --user enable --now agent-orchestrator.service
```

The explicit Node path is the current Codex installation path. The wrapper
supplies tmux 3.5 and scopes its shared libraries because the host tmux 2.7
cannot create AO sessions. The proxy values are current-host settings, not
portable defaults; omit or replace them on a host with different network
routing. A new host may use a system tmux 3.5 or later and omit the wrapper.
Update the unit and rerun `ao doctor --json` after changing the active Node,
Codex, tmux, or network configuration.

## Isolate The AO Codex Home

Create `/home/fqzhang/.ao/codex-home` with mode `0700`, link its `auth.json` to
the existing `/home/fqzhang/.codex/auth.json`, and create a mode `0600`
`config.toml`:

```toml
[features]
apps = false
plugins = false
```

The isolated home reuses authentication but not Desktop-specific Apps,
Plugins, MCP servers, or unrelated instructions. Without the explicit feature
settings, Codex defaults can still start Apps and reproduce the timeout.

## Register Calibration

The current persisted project contract is:

```bash
ao project add \
  --path /home/fqzhang/project/calibration \
  --name calibration \
  --worker-agent codex

ao project set-config calibration \
  --config-json \
  '{"env":{"CODEX_HOME":"/home/fqzhang/.ao/codex-home"},"worker":{"agent":"codex","agentConfig":{"permissions":"bypass-permissions"}},"botReviewFeedback":{"allowAuthors":["chatgpt-codex-connector"]}}' \
  --json
```

`chatgpt-codex-connector` is the login AO observes through GraphQL; the REST
surface may display `chatgpt-codex-connector[bot]`.

Register another repository only after its recurring continuation need and
validation contract are known. Give it its own project configuration instead
of assuming the `calibration` permission decision applies automatically.

## Verification

Run after installation, restart, configuration, or upgrade:

```bash
systemctl --user is-enabled agent-orchestrator.service
systemctl --user is-active agent-orchestrator.service
ao status --json
ao project get calibration --json
PATH=/home/fqzhang/.local/lib/ao/bin:/home/fqzhang/.nvm/versions/node/v22.22.2/bin:/home/fqzhang/.local/bin:/usr/local/bin:/usr/bin:/bin \
  ao doctor --json
sha256sum /home/fqzhang/.local/bin/ao \
  /home/fqzhang/.local/bin/ao-daemon
```

Expected current readback:

- service: `enabled`, `active`, and daemon `ready`;
- run file: `/home/fqzhang/.ao/running.json`;
- data directory: `/home/fqzhang/.ao/data`;
- worker agent: `codex`;
- worker `CODEX_HOME`: `/home/fqzhang/.ao/codex-home`;
- permissions: `bypass-permissions`;
- bot review allowlist: `chatgpt-codex-connector`; and
- `ao doctor --json`: zero failures and tmux 3.5 or later.

A complete behavior revalidation also requires a disposable pull request with
an anchored Automatic Codex Review finding. Confirm that the finding reaches
the original worker, the worker commits the correction, repository validation
passes, and auto-merge remains off. Static status readback alone does not prove
the GitHub event loop.

## Stop Or Remove

To stop the service without deleting state:

```bash
systemctl --user disable --now agent-orchestrator.service
```

Do not remove `/home/fqzhang/.ao` as part of an ordinary upgrade. It contains
the SQLite project and session state needed for diagnosis and continuation.
Delete that state only as an explicit destructive cleanup after inspecting
active sessions and preserving any required worktree or pull-request state.

## Upgrade Rule

Never update from a moving branch or pull-request head in place. Build a new
pinned candidate, run the focused tests, compare project-config compatibility,
and repeat the real-event canary before replacing the installed binaries. If
upstream includes either local fix, drop only the corresponding patch after
confirming equivalent coverage.
