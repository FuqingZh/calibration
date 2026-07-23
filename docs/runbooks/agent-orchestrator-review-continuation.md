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

exec /lib64/ld-linux-x86-64.so.2 \
  --library-path /home/fqzhang/micromamba/envs/gwas-cli/lib \
  /home/fqzhang/micromamba/envs/gwas-cli/bin/tmux "$@"
```

Install it with mode `0755`. The loader flag supplies libraries only to the
tmux process. Do not export `LD_LIBRARY_PATH` from this wrapper or put it on the
AO service: a tmux server inherits that variable and forwards it into new
worker panes, where it changed Git/curl certificate discovery and broke real
worker pushes. If an older tmux server was launched with the variable, remove
it before creating another worker:

```bash
/home/fqzhang/.local/lib/ao/bin/tmux \
  set-environment -g -u LD_LIBRARY_PATH
```

The current `fqzhang` shell also uses tmux 3.5 by linking
`/home/fqzhang/.local/bin/tmux` to `../lib/ao/bin/tmux`. This is a user
convenience, not an AO requirement.

Create the state directory before systemd opens the append-only log, then
create `/home/fqzhang/.config/systemd/user/agent-orchestrator.service`:

```bash
install -d -m 0700 /home/fqzhang/.ao
```

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
StandardOutput=append:%h/.ao/daemon.log
StandardError=append:%h/.ao/daemon.log
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

The append-only user log is the first diagnostic surface for an HTTP
`INTERNAL_ERROR`. Inspect the matching request id before retrying a failed
spawn; AO may have rolled back the worktree while leaving an empty branch.

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

## Adopt An Opted-In Repository

Repository adoption is not a single boolean. Use these states:

1. `registered`: AO has a project record;
2. `configured`: configuration readback matches the accepted profile;
3. `runtime-ready`: the persistent service and diagnostics pass; and
4. `continuation-proven`: a real pull request proves review feedback returns to
   the original worker, which can push the correction.

The repository-owned initializer validates these boundaries and is
non-mutating unless `--apply` is present. Run it from the calibration
checkout:

```bash
cd /home/fqzhang/project/calibration
python scripts/adopt_ao_repository.py \
  --path /absolute/path/to/repository \
  --name repository-name \
  --default-branch main \
  --session-prefix repository-name \
  --codex-home /home/fqzhang/.ao/codex-home \
  --permission bypass-permissions \
  --json
```

Inspect that plan, then add `--apply` to execute the same explicit request.

`chatgpt-codex-connector` is the login AO observes through GraphQL; the REST
surface may display `chatgpt-codex-connector[bot]`.

The current single-user host explicitly accepts `bypass-permissions` for
repositories that opt into this AO service. This is not a portable default:
another host, owner, or trust boundary must choose its own permission setting.
The initializer requires the permission argument so that this decision cannot
be inherited silently.

The command enables and starts the persistent user service, verifies AO status
and doctor output, creates or reuses the project, merges the required profile
with configuration fields modeled by the pinned AO CLI, and validates the
repository path and configuration readback. `ao project set-config` replaces a
typed whole object, so this initializer does not promise to preserve fields
outside that CLI schema; inspect an existing project's configuration before
using it with a newer or plugin-extended AO build. The command also requires the
isolated Codex home, configuration, and authentication file to retain private
permissions. It stops at `runtime-ready`.
It never claims the real event loop has passed.

Before registration, the initializer confirms that `.codex` is absent or a
real directory in the repository, never a symlink. Its equivalent guard is:

```bash
if [ -L .codex ] || { [ -e .codex ] && [ ! -d .codex ]; }; then
  echo '.codex must be absent or a non-symlinked directory' >&2
  exit 1
fi
```

A tracked regular file named `.codex` prevents the Codex adapter from creating
`.codex/hooks.json`; a symlink could make that provisioning write outside the
worktree. Remove either through the repository's normal pull-request path
rather than changing it inside a failed AO worktree.

After runtime setup, commit a small repository-local `AGENTS.md` increment
which records that the repository has adopted AO on this host and tells an
implementation agent to start or claim the task-specific worker before
creating a branch or pull request. Do not copy this runbook into the target
repository. Issue-tracker intake and a separate orchestrator session are not
required for a task authorized in conversation.

Use this shape, replacing the project id:

```markdown
## AO Delivery

This repository has opted into the accepted user-level AO service as
`repository-name`. For conversation-authorized implementation intended to
cross a pull-request boundary, verify AO health and start a task-specific
worker before creating the implementation branch or PR. If a PR already
exists, mark it ready for review if it is a draft, then restore its owning
worker or claim it with `--no-takeover`. Ready-for-review is only an AO claim
prerequisite; leave merge and risk decisions to the user. If AO is unavailable,
use an isolated worktree and report that fallback.
```

This entry makes task intake discoverable; it does not itself prove the event
loop or authorize bulk enrollment.

The installed AO build does not claim a GitHub Draft pull request: it returns
`PR_NOT_OPEN` even though GitHub reports the draft's state as `OPEN`. Keep
unfinished work draft, then mark it ready for review before AO claim or spawn
with `--claim-pr`. Ready-for-review triggers CI/review ownership; it does not
authorize merge. A stacked pull request may be ready while its base remains
open, provided merge order stays explicit.

## Verification

Run after installation, restart, configuration, or upgrade:

```bash
systemctl --user is-enabled agent-orchestrator.service
systemctl --user is-active agent-orchestrator.service
ao status --json
ao project get repository-name --json
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

Passing this section establishes `runtime-ready`, not
`continuation-proven`.

Also confirm that
`/home/fqzhang/.local/lib/ao/bin/tmux show-environment -g LD_LIBRARY_PATH`
reports an unknown variable and that a newly created worker can fetch and push
without a per-command certificate override.

A complete behavior revalidation also requires a disposable pull request with
an anchored Automatic Codex Review finding. Confirm that the finding reaches
the original worker, the worker commits the correction, repository validation
passes, and auto-merge remains off. Static status readback alone does not prove
the GitHub event loop. Only after this canary may the repository be called
`continuation-proven` or fully adopted.

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
