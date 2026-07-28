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

- Current deployed fork:
  `https://github.com/FuqingZh/agent-orchestrator.git`
- Current deployed fork `main` commit:
  `68496903141232718c23b8f13f4efede2d6f7b58`
- Merged worker-environment fix head:
  `4c241b1447b4c5c303593ac0a94386cc3dfd3261`
- Current `/home/fqzhang/.local/bin/ao` SHA-256:
  `ce2df0db2e6ad7f1eb65906a04b900620941ba716d0ad1b14378db9db1387d91`
- Pre-reproducible Phase 3 `/home/fqzhang/.local/bin/ao` SHA-256:
  `ec19ff3a87a15a04eb3d9d647397c2cc32a820da19448cc93b6fe4f423cc4016`
- Pre-security-fix rollback:
  `/home/fqzhang/.ao/backups/phase3-runtimeenv-68496903/ao-before-runtimeenv`,
  SHA-256
  `2fbd3af959a1135c7d0b3cefeb0c5597b3f68a53c39e5102c418f5db302f9a16`

The current deployment supersedes the original patched canary artifact below.
Retain the older inputs and the pre-reproducible Phase 3 binary for
reconstruction and rollback evidence.

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

### Current Phase 3 fork

Start from the calibration checkout, preserve its root for later managed
artifact installation, then clone the AO fork:

```bash
CALIBRATION_ROOT="$(git rev-parse --show-toplevel)"
AO_BUILD_ROOT="$(mktemp -d)"
git clone --no-checkout https://github.com/FuqingZh/agent-orchestrator.git \
  "${AO_BUILD_ROOT}/source"
git -C "${AO_BUILD_ROOT}/source" fetch \
  origin refs/heads/main:refs/remotes/origin/main
git -C "${AO_BUILD_ROOT}/source" rev-parse refs/remotes/origin/main
git -C "${AO_BUILD_ROOT}/source" ls-remote origin refs/heads/main
AO_DEPLOYED_COMMIT=68496903141232718c23b8f13f4efede2d6f7b58
git -C "${AO_BUILD_ROOT}/source" cat-file -e \
  "${AO_DEPLOYED_COMMIT}^{commit}"
git -C "${AO_BUILD_ROOT}/source" merge-base --is-ancestor \
  "${AO_DEPLOYED_COMMIT}" refs/remotes/origin/main
```

On the observed checkout, `git fetch origin main` updated only `FETCH_HEAD`;
the explicit refspec above durably updates `refs/remotes/origin/main`.
At cutover, both remote readbacks reported
`68496903141232718c23b8f13f4efede2d6f7b58`. On a later rebuild, fork `main`
may have advanced; the gates are that the exact deployed commit remains
available from the fork and is an ancestor of its current `main`, not that
`main` still equals the historical deployment. Then build the pinned commit:

```bash
git -C "${AO_BUILD_ROOT}/source" checkout --detach \
  68496903141232718c23b8f13f4efede2d6f7b58
cd "${AO_BUILD_ROOT}/source/backend"
go test ./...
mkdir -p "${AO_BUILD_ROOT}/bin"
go build -trimpath -buildvcs=false \
  -o "${AO_BUILD_ROOT}/bin/ao" ./cmd/ao
printf '%s  %s\n' \
  ce2df0db2e6ad7f1eb65906a04b900620941ba716d0ad1b14378db9db1387d91 \
  "${AO_BUILD_ROOT}/bin/ao" |
  sha256sum --check -
```

With Go 1.26.4 on `linux/amd64`, the expected SHA-256 is
`ce2df0db2e6ad7f1eb65906a04b900620941ba716d0ad1b14378db9db1387d91`.
Two independent builds from the merge commit produced this same hash with
`-trimpath -buildvcs=false`. Earlier source tree `e9505779` demonstrated that
`-buildvcs=false` alone retained worktree-dependent output. Both flags are
therefore part of the canonical deployment command. Another supported Go
toolchain or target may produce a different hash and requires its own
toolchain-qualified build, test, and installed-hash evidence.

Install the verified artifact as `fqzhang`, preserving the currently installed
binary first:

```bash
AO_CUTOVER_BACKUP="/home/fqzhang/.ao/backups/phase3-trimpath-$(date +%Y%m%d%H%M%S)"
install -d -m 0700 "${AO_CUTOVER_BACKUP}"
install -m 0755 /home/fqzhang/.local/bin/ao \
  "${AO_CUTOVER_BACKUP}/ao-pre-reproducible"
install -m 0755 "${AO_BUILD_ROOT}/bin/ao" /home/fqzhang/.local/bin/ao
sha256sum /home/fqzhang/.local/bin/ao
systemctl --user restart agent-orchestrator.service
```

The installed hash must match the expected value above. Then run every
host-context, wrapper, worker-environment, and Linear smoke check in
Verification before accepting the cutover.

### Rollback-only original patched canary

This procedure reconstructs the superseded upstream canary only. Do not use it
to rebuild the current Phase 3 fork. Run from a clean checkout of this
calibration repository when rollback requires that historical artifact:

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

These historical commands intentionally retain the original
`-buildvcs=false`-only flags used for the recorded
`25fab37d...`/`5bd25fd...` canary artifacts. Adding `-trimpath` produces
different binaries and must not be used when comparing against those hashes.
The retained installed artifacts are the hash authority; rebuilding on another
path or toolchain requires separate source, patch, test, and launch review.

### No standalone canary binary install

Rebuilding the historical canary does not authorize replacing either installed
binary by itself. To restore that canary, use the complete earlier-upstream
procedure under [Rollback verification](#rollback-verification). That procedure
first stops and verifies deactivation of the service, preserves the active
deployment locally, disables the Linear drop-in, restores the matching
binary/database/unit set, reloads systemd, and verifies rollback-specific
hashes and service state.

## Host Runtime Install

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
ExecStart=%h/.local/bin/ao daemon
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

### Phase 3 Linear credential override

The current host adds Linear access without placing a credential in the base
unit or repository. Store the credential only at
`/home/fqzhang/.config/agent-orchestrator/linear-api-key`, mode `0600`, inside
the mode `0700` directory `/home/fqzhang/.config/agent-orchestrator`.

The mode `0755` wrapper
`/home/fqzhang/.local/lib/ao/bin/ao-daemon-with-linear` is managed from
[`artifacts/ao-daemon-with-linear`](artifacts/ao-daemon-with-linear). Install
the exact repository artifact:

```bash
install -D -m 0755 \
  "${CALIBRATION_ROOT}/docs/runbooks/artifacts/ao-daemon-with-linear" \
  /home/fqzhang/.local/lib/ao/bin/ao-daemon-with-linear
sha256sum /home/fqzhang/.local/lib/ao/bin/ao-daemon-with-linear
```

The expected wrapper SHA-256 is
`bb5421301d09df0c3fa9176dffb1fbb5170cb02d897610b0137a155cb4c08090`.
The complete source is retained rather than described only in prose so
reconstruction and audit use identical fail-closed behavior.
The wrapper clears `AO_LINEAR_OAUTH_TOKEN` before exec so the reviewed
file-backed `AO_LINEAR_API_KEY` is the only active Linear credential source.
Root installed this exact artifact. The previous wrapper is retained at
`/home/fqzhang/.ao/backups/wrapper-6635e31/ao-daemon-with-linear.before`,
with SHA-256
`0531d973a0cd690b03b52530388cf138e5a4b54899167a341ca0d1a5ff88d2d7`.
After restart, AO reported ready and healthy at PID `3727219`, doctor reported
zero failures, effective `ExecStart` named the wrapper, `DropInPaths` named the
active `linear.conf`, and all nine pre-existing tmux pane PIDs were unchanged.
The installed wrapper, AO binary, and drop-in hashes matched the documented
values. A values-never-printed daemon environment-name boolean check reported
exactly `API_KEY_PRESENT=yes` and `OAUTH_TOKEN_PRESENT=no`.

The active mode `0644` drop-in is managed from
[`artifacts/linear.conf`](artifacts/linear.conf) and installed at
`/home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf`
inside a mode `0700` directory:

```bash
install -d -m 0700 \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d
install -m 0644 \
  "${CALIBRATION_ROOT}/docs/runbooks/artifacts/linear.conf" \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf
sha256sum \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf
systemctl --user daemon-reload
systemctl --user restart agent-orchestrator.service
```

The expected drop-in SHA-256 is
`be96ac3b7e948656c7c747e641201d7d989dbc3eec4886d16b548a7bc9c685df`.
The reload and restart are required so effective `ExecStart` uses the wrapper.

Do not record the credential value in Git, shell transcripts, the systemd
unit, or diagnostic output. The file is read-only operational input; this
deployment does not authorize writes to Linear.

The wrapper necessarily supplies the credential to the daemon process. AO must
filter both `AO_LINEAR_API_KEY` and `AO_LINEAR_OAUTH_TOKEN` from every tmux pane
environment. The AO-side fix head was
[`4c241b1447b4c5c303593ac0a94386cc3dfd3261`](https://github.com/FuqingZh/agent-orchestrator/commit/4c241b1447b4c5c303593ac0a94386cc3dfd3261)
in agent-orchestrator
[pull request #10](https://github.com/FuqingZh/agent-orchestrator/pull/10).
Its focused, race, full lint, vet, Linux build, and Windows build validation
passed; fresh Automatic Review reported no major issues and its two P1 threads
were resolved. PR #10 merged as
`68496903141232718c23b8f13f4efede2d6f7b58`.

Two independent builds from the merge commit matched at SHA-256
`ce2df0db2e6ad7f1eb65906a04b900620941ba716d0ad1b14378db9db1387d91`,
and that binary is installed. After restoring the drop-in and restarting,
effective unit readback named the wrapper, AO was ready and healthy, doctor had
zero failures, and all nine pre-existing tmux pane PIDs were unchanged. A fresh
AO worker pane ran a boolean presence check that never printed values, reported
exactly `LINEAR_ENV_CLEAN`, and was terminated. This is the accepted evidence
that both Linear credential variables are absent from a newly AO-created
pane's ambient environment.

This is environment-hygiene evidence, not worker-secret isolation. AO and its
workers run as the same `fqzhang` user with `bypass-permissions`; a worker with
that authority can read the mode `0600` credential file or inspect same-user
process state through host interfaces allowed by the operating system. True
isolation from workers requires privilege separation: run the credentialed
daemon under a distinct account or security boundary that workers cannot read
or inspect. Do not claim the current single-user deployment prevents a
malicious or fully privileged worker from obtaining the credential.

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
sha256sum \
  /home/fqzhang/.local/bin/ao \
  /home/fqzhang/.local/lib/ao/bin/ao-daemon-with-linear \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf
```

After the final Phase 3 security-fix cutover,
`/home/fqzhang/.local/bin/ao` must report:

```text
ce2df0db2e6ad7f1eb65906a04b900620941ba716d0ad1b14378db9db1387d91
```

The SHA-256
`2fbd3af959a1135c7d0b3cefeb0c5597b3f68a53c39e5102c418f5db302f9a16`
identifies the pre-security-fix Phase 3 binary, while `ec19ff3a...` identifies
the pre-reproducible binary. Both belong in rollback evidence.

Run these checks as `fqzhang` through the same `systemd --user` manager used by
the deployment. Confirm the effective wrapper and drop-in rather than relying
on a shell invocation:

```bash
systemctl --user cat agent-orchestrator.service
systemctl --user show agent-orchestrator.service \
  -p FragmentPath -p DropInPaths -p ExecStart -p ActiveState -p UnitFileState
stat -c '%A %a %U:%G %n' \
  /home/fqzhang/.config/agent-orchestrator \
  /home/fqzhang/.config/agent-orchestrator/linear-api-key \
  /home/fqzhang/.local/lib/ao/bin/ao-daemon-with-linear \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf
sha256sum \
  /home/fqzhang/.local/lib/ao/bin/ao-daemon-with-linear \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf
```

A check run as another user, outside the user manager, or with a separately
constructed environment does not verify the deployed service context.
The wrapper hash must be
`bb5421301d09df0c3fa9176dffb1fbb5170cb02d897610b0137a155cb4c08090`.
The enabled drop-in hash must be
`be96ac3b7e948656c7c747e641201d7d989dbc3eec4886d16b548a7bc9c685df`.

Expected current readback:

- service: `enabled`, `active`, and daemon `ready`;
- effective `ExecStart`:
  `/home/fqzhang/.local/lib/ao/bin/ao-daemon-with-linear`;
- `DropInPaths`:
  `/home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf`;
- active drop-in:
  `/home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf`,
  mode `0644`;
- run file: `/home/fqzhang/.ao/running.json`;
- data directory: `/home/fqzhang/.ao/data`;
- worker agent: `codex`;
- worker `CODEX_HOME`: `/home/fqzhang/.ao/codex-home`;
- permissions: `bypass-permissions`;
- bot review allowlist: `chatgpt-codex-connector`; and
- `ao doctor --json`: zero failures and tmux 3.5 or later.

Passing this section establishes `runtime-ready`, not
`continuation-proven`.

A passing Phase 3 Linear smoke is also narrower than a real Linear intake
loop. The bounded smoke below validates only the credential and read-only
Linear API identity path; it does not exercise AO's tracker adapter. The
installed binary hash, effective service wiring, AO health, focused AO tests,
and fresh-worker environment acceptance are separate evidence. None of these
proves sustained polling, durable claims, issue-to-worker creation, restart
recovery, or complete processing of a real Linear issue. Require a separately
authorized real-project canary before describing Linear intake as end-to-end
proven.

### Bounded read-only Linear smoke

Inputs:

- the mode `0600` credential file
  `/home/fqzhang/.config/agent-orchestrator/linear-api-key`;
- network access to `https://api.linear.app/graphql`; and
- `curl` plus Python 3.

Run this non-mutating identity query. The command never prints the credential:

```bash
set +x
set -euo pipefail
LINEAR_SMOKE_RESPONSE="$(mktemp)"
trap 'rm -f "${LINEAR_SMOKE_RESPONSE}"' EXIT
LINEAR_SMOKE_KEY=
IFS= read -r LINEAR_SMOKE_KEY < \
  /home/fqzhang/.config/agent-orchestrator/linear-api-key ||
  [ -n "${LINEAR_SMOKE_KEY}" ]
printf 'header = "Authorization: %s"\n' "${LINEAR_SMOKE_KEY}" |
  curl -q --config - --fail-with-body --silent --show-error \
  --connect-timeout 10 --max-time 30 \
  -H 'Content-Type: application/json' \
  --data '{"query":"query AOViewer { viewer { id } }"}' \
  https://api.linear.app/graphql > "${LINEAR_SMOKE_RESPONSE}"
unset LINEAR_SMOKE_KEY
python - "${LINEAR_SMOKE_RESPONSE}" <<'PY'
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text())
if payload.get("errors"):
    raise SystemExit("Linear returned GraphQL errors")
viewer_id = payload.get("data", {}).get("viewer", {}).get("id", "")
if not isinstance(viewer_id, str) or not viewer_id.strip():
    raise SystemExit("missing Linear viewer id")
print("linear-read-only-smoke: PASS")
PY
rm -f "${LINEAR_SMOKE_RESPONSE}"
trap - EXIT
```

Success requires HTTP success, valid JSON, no GraphQL `errors`, a non-empty
`data.viewer.id`, and the final line `linear-read-only-smoke: PASS`. The query
has no mutation and does not enable tracker intake, create a worker, or alter a
Linear object. Strict shell mode makes any missing credential, transport
failure, invalid JSON, or explicit validation failure return nonzero and block the
deployment claim.

This verifies the credential and read-only Linear API path. The installed AO
hash, effective service command, wrapper hash, daemon readiness, and
worker-environment checks separately verify that the intended AO artifact and
host wiring are active.

### Worker environment secret gate

After installing or upgrading, create a new disposable AO worker so AO creates
the tmux pane:

```bash
ao spawn \
  --project calibration \
  --name linear-env-smoke \
  --harness codex \
  --prompt 'Run only this boolean environment check without printing values:
if env | sed -n "s/=.*//p" |
  grep -Eq "^AO_LINEAR_(API_KEY|OAUTH_TOKEN)$"; then
  echo LINEAR_ENV_LEAK
else
  echo LINEAR_ENV_CLEAN
fi
Report the single result line and stop.'
```

Record the returned session id, confirm the worker reports exactly
`LINEAR_ENV_CLEAN`, then read back and terminate it:

```bash
ao session get SESSION_ID --project calibration --json
ao session kill SESSION_ID --project calibration
```

The check prints only a boolean result, never variable values. It verifies
ambient environment hygiene, not privilege separation or credential
inaccessibility. The accepted test ran while the active wrapper supplied the
real credential to the daemon, so it exercised filtering rather than passing
against an uncredentialed service. The fresh worker reported exactly
`LINEAR_ENV_CLEAN` and was terminated.

The pane-only result was not sufficient to establish server-start hygiene:
the pane launch command also unsets both variables, so it can mask a credential
retained by the persistent tmux server. Recovery from a later shared-server
loss supplied the required fresh-server sample without another restart. The
wrapper-credentialed daemon remained PID `3727219`, started
`2026-07-28 10:04:17 +08:00`; its values-never-printed environment-name check
reported only `AO_LINEAR_API_KEY`. The first restoring tmux client created the
default server at `2026-07-28 10:53:15 +08:00`, PID `4012975`, socket
`/tmp/tmux-1009/default`. Its process environment and `show-environment -g`
persistent environment both reported no
`AO_LINEAR_API_KEY` or `AO_LINEAR_OAUTH_TOKEN`. The server contained only
session `calibration-8` (`$0`, tmux creation time
`2026-07-28T10:53:16+08:00`), with one pane, PID `4012976`; that pane's
environment also reported neither name. No variable values were printed.

This closes the current fresh-server ambient and persistent-environment gate.
It also confirms the deployed fork's tmux-client environment filtering, not
only its pane-command scrubbing. Do not restart the shared tmux server merely
to repeat this check. Revalidate from an observed fresh server after an AO or
tmux upgrade, or during a separately authorized maintenance window after all
workers are drained and their Git state is preserved.

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

## Headless Dashboard Boundary

The pinned AO `0.10.3` desktop package contains the dashboard renderer, but
`ao start` fetches and opens an Electron Desktop App. It is not a supported
command for starting a standalone Web Dashboard on this headless server.

An isolated browser canary unpacked the installed AppImage renderer, served it
on loopback port `31080`, and connected it through a read-only proxy on
loopback port `31081`. The board rendered the real AO projects, sessions, pull
requests, and continuation states. The proxy allowed GET requests and rejected
POST, PUT, PATCH, and DELETE, including the renderer's automatic agent-refresh
request. The application processes used approximately 45 MB RSS, or about
65 MB including the temporary Codex sandbox wrappers, with idle CPU near zero.

The canary also identified an earlier headless AppImage launch with no display
or listener consuming approximately one CPU core. That process was terminated;
the AO daemon and API remained healthy. Both temporary Web services were then
stopped. No Web Dashboard service, listener, proxy, extracted renderer, or
startup contract was retained.

Do not run `ao start` on this headless host. Use `ao status --json`, project and
session readback, the loopback AO API, and the owning Codex or GitHub surfaces
for current status. Reconsider a persistent browser dashboard only when it
materially reduces attention cost and a maintained AO release exposes a
supported remote-Web contract; do not promote the isolated extraction into a
custom production frontend.

## Stop Or Remove

To stop the service without deleting state:

```bash
systemctl --user disable --now agent-orchestrator.service
```

Do not remove `/home/fqzhang/.ao` as part of an ordinary upgrade. It contains
the SQLite project and session state needed for diagnosis and continuation.
Delete that state only as an explicit destructive cleanup after inspecting
active sessions and preserving any required worktree or pull-request state.

## Phase 3 Rollback Artifacts

The previous credential wrapper is retained at
`/home/fqzhang/.ao/backups/wrapper-6635e31/ao-daemon-with-linear.before`.
Its SHA-256 is
`0531d973a0cd690b03b52530388cf138e5a4b54899167a341ca0d1a5ff88d2d7`.
It does not clear `AO_LINEAR_OAUTH_TOKEN`; restoring it requires separately
ensuring that variable is absent and rerunning daemon and worker environment
checks.

The immediate pre-security-fix binary is retained at
`/home/fqzhang/.ao/backups/phase3-runtimeenv-68496903/ao-before-runtimeenv`.
Its SHA-256 is
`2fbd3af959a1135c7d0b3cefeb0c5597b3f68a53c39e5102c418f5db302f9a16`.
Restoring it also requires disabling the Linear drop-in because that binary
does not contain the accepted worker-environment filtering fix.

The immediate pre-Phase-3 set is retained under
`/home/fqzhang/.ao/backups/phase3-c5ed22df/`:

- `ao`
- `ao-phase3-before-typed-nil-fix`
- `ao.db`
- `agent-orchestrator.service`

The concrete pre-reproducible Phase 3 binary is retained at
`/home/fqzhang/.ao/backups/phase3-repro-7238619/ao-before-trimpath`, with
verified SHA-256
`ec19ff3a87a15a04eb3d9d647397c2cc32a820da19448cc93b6fe4f423cc4016`.

The retained service in this immediate set starts
`/home/fqzhang/.local/bin/ao daemon`, so the retained `ao` is its matching
executable and no `ao-daemon` copy is required for this set.

The earlier upstream-canary set is retained under
`/home/fqzhang/.local/lib/ao/backups/20260726-upstream-9f8c085f/`:

- `ao`
- `ao-daemon`
- `ao.db`
- `agent-orchestrator.service`

This earlier service starts `/home/fqzhang/.local/bin/ao-daemon`. Restore it
only with the matching
`/home/fqzhang/.local/lib/ao/backups/20260726-upstream-9f8c085f/ao-daemon`,
whose SHA-256 is
`5bd25fd1647c4c6eb2e22b35aa9f257c0d76d23c5ed0fa42c5bed32745e290e8`.

### Rollback verification

Do not reuse the current Phase 3 hash or wrapper expectations for a rollback.
For the immediate pre-security-fix binary, disable the Linear drop-in, restore
the retained executable, and verify the base service:

```bash
set -euo pipefail
systemctl --user stop agent-orchestrator.service
if systemctl --user is-active --quiet agent-orchestrator.service; then
  echo "agent-orchestrator.service remained active after stop" >&2
  exit 1
fi
ROLLBACK_SAVE="/home/fqzhang/.ao/backups/rollback-$(date +%Y%m%d%H%M%S)"
install -d -m 0700 "${ROLLBACK_SAVE}"
install -m 0600 /home/fqzhang/.ao/data/ao.db "${ROLLBACK_SAVE}/ao.db"
install -m 0755 /home/fqzhang/.local/bin/ao "${ROLLBACK_SAVE}/ao"
install -m 0600 \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service \
  "${ROLLBACK_SAVE}/agent-orchestrator.service"
install -m 0755 \
  /home/fqzhang/.local/lib/ao/bin/ao-daemon-with-linear \
  "${ROLLBACK_SAVE}/ao-daemon-with-linear"
install -m 0644 \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf \
  "${ROLLBACK_SAVE}/linear.conf"
install -m 0755 \
  /home/fqzhang/.ao/backups/phase3-runtimeenv-68496903/ao-before-runtimeenv \
  /home/fqzhang/.local/bin/ao
if [ -e /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf ]; then
  mv \
    /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf \
    /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf.disabled
fi
systemctl --user daemon-reload
systemctl --user start agent-orchestrator.service
sha256sum /home/fqzhang/.local/bin/ao
systemctl --user show agent-orchestrator.service \
  -p DropInPaths -p ExecStart -p ActiveState
ao status --json
```

Expected results are binary SHA-256
`2fbd3af959a1135c7d0b3cefeb0c5597b3f68a53c39e5102c418f5db302f9a16`,
empty `DropInPaths`, effective `ExecStart` ending in `ao daemon`, active
service state, and ready AO status. This is a binary-only rollback: no matching
database was retained in `phase3-runtimeenv-68496903`, so it deliberately keeps
the current database after preserving a recovery copy.

For the immediate pre-Phase-3 set, restore its matching `ao` and base unit,
keep the Linear drop-in disabled, then verify:

```bash
set -euo pipefail
systemctl --user stop agent-orchestrator.service
if systemctl --user is-active --quiet agent-orchestrator.service; then
  echo "agent-orchestrator.service remained active after stop" >&2
  exit 1
fi
ROLLBACK_SAVE="/home/fqzhang/.ao/backups/rollback-$(date +%Y%m%d%H%M%S)"
install -d -m 0700 "${ROLLBACK_SAVE}"
install -m 0600 /home/fqzhang/.ao/data/ao.db "${ROLLBACK_SAVE}/ao.db"
install -m 0755 /home/fqzhang/.local/bin/ao "${ROLLBACK_SAVE}/ao"
install -m 0600 \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service \
  "${ROLLBACK_SAVE}/agent-orchestrator.service"
install -m 0755 \
  /home/fqzhang/.local/lib/ao/bin/ao-daemon-with-linear \
  "${ROLLBACK_SAVE}/ao-daemon-with-linear"
install -m 0644 \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf \
  "${ROLLBACK_SAVE}/linear.conf"
if [ -e /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf ]; then
  mv \
    /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf \
    /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf.disabled
fi
install -m 0755 /home/fqzhang/.ao/backups/phase3-c5ed22df/ao \
  /home/fqzhang/.local/bin/ao
install -m 0600 /home/fqzhang/.ao/backups/phase3-c5ed22df/ao.db \
  /home/fqzhang/.ao/data/ao.db
install -m 0600 \
  /home/fqzhang/.ao/backups/phase3-c5ed22df/agent-orchestrator.service \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service
systemctl --user daemon-reload
systemctl --user start agent-orchestrator.service
sha256sum /home/fqzhang/.local/bin/ao
systemctl --user show agent-orchestrator.service \
  -p DropInPaths -p ExecStart -p ActiveState
ao status --json
```

Expected results are binary SHA-256
`4e23bde24054b18a4c443f463542e50fde11ac2e11ff552209b62ba269674981`,
empty `DropInPaths`, effective `ExecStart` ending in `ao daemon`, active
service state, and ready AO status.

For the earlier upstream canary, restore both historical binaries and its
matching unit:

```bash
set -euo pipefail
systemctl --user stop agent-orchestrator.service
if systemctl --user is-active --quiet agent-orchestrator.service; then
  echo "agent-orchestrator.service remained active after stop" >&2
  exit 1
fi
ROLLBACK_SAVE="/home/fqzhang/.ao/backups/rollback-$(date +%Y%m%d%H%M%S)"
install -d -m 0700 "${ROLLBACK_SAVE}"
install -m 0600 /home/fqzhang/.ao/data/ao.db "${ROLLBACK_SAVE}/ao.db"
install -m 0755 /home/fqzhang/.local/bin/ao "${ROLLBACK_SAVE}/ao"
if [ -e /home/fqzhang/.local/bin/ao-daemon ]; then
  install -m 0755 /home/fqzhang/.local/bin/ao-daemon \
    "${ROLLBACK_SAVE}/ao-daemon"
fi
install -m 0600 \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service \
  "${ROLLBACK_SAVE}/agent-orchestrator.service"
install -m 0755 \
  /home/fqzhang/.local/lib/ao/bin/ao-daemon-with-linear \
  "${ROLLBACK_SAVE}/ao-daemon-with-linear"
install -m 0644 \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf \
  "${ROLLBACK_SAVE}/linear.conf"
if [ -e /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf ]; then
  mv \
    /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf \
    /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf.disabled
fi
install -m 0755 \
  /home/fqzhang/.local/lib/ao/backups/20260726-upstream-9f8c085f/ao \
  /home/fqzhang/.local/bin/ao
install -m 0755 \
  /home/fqzhang/.local/lib/ao/backups/20260726-upstream-9f8c085f/ao-daemon \
  /home/fqzhang/.local/bin/ao-daemon
install -m 0600 \
  /home/fqzhang/.local/lib/ao/backups/20260726-upstream-9f8c085f/ao.db \
  /home/fqzhang/.ao/data/ao.db
install -m 0600 \
  /home/fqzhang/.local/lib/ao/backups/20260726-upstream-9f8c085f/agent-orchestrator.service \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service
systemctl --user daemon-reload
systemctl --user start agent-orchestrator.service
sha256sum /home/fqzhang/.local/bin/ao \
  /home/fqzhang/.local/bin/ao-daemon
systemctl --user show agent-orchestrator.service \
  -p DropInPaths -p ExecStart -p ActiveState
ao status --json
```

Expected hashes are
`25fab37d7279e72d0e3c2295630c1eb47ed4ff4f54c08b02e4125ca3b9efcdeb`
for `ao` and
`5bd25fd1647c4c6eb2e22b35aa9f257c0d76d23c5ed0fa42c5bed32745e290e8`
for `ao-daemon`. `DropInPaths` must be empty, effective `ExecStart` must end in
`ao-daemon`, the service must be active, and AO status must be ready.

To roll back, stop the service, preserve the current binary, database, base
unit, wrapper, and drop-in in a new dated backup, then restore one internally
consistent retained set. Remove or disable the Linear drop-in when restoring a
build that does not support Linear and run the matching rollback verification
above. Do not delete or revoke the Linear credential as an incidental rollback
step; that is a separate explicit security action.

## Upgrade Rule

Never update from a moving branch or pull-request head in place. Build a new
pinned candidate, run the focused tests, compare project-config compatibility,
and repeat the real-event canary before replacing the installed binaries. If
upstream includes either local fix, drop only the corresponding patch after
confirming equivalent coverage.
