# Agent Orchestrator Review Continuation Runbook

Date: 2026-07-23

Status: Current for the `fqzhang` user on the present Linux host

## Purpose And Boundary

This runbook reconstructs the AO service that connects an actionable
GitHub Automatic Codex Review finding to the original AO-managed Codex worker.
For an individually registered repository, the same service may start or claim
a task-specific worker after a conversation explicitly authorizes
implementation and pull-request delivery. It does not install Symphony,
replace GitHub Actions or Automatic Review, enable unattended issue intake or
automatic work discovery, or register every repository. Low-risk auto-merge is
governed separately by
[`../decisions/2026-07-29-ao-native-delivery-convergence.md`](../decisions/2026-07-29-ao-native-delivery-convergence.md).

The service is intentionally permissionless for the current single-user host.
AO calls this mode `bypass-permissions`; the Codex adapter emits
`--dangerously-bypass-approvals-and-sandbox`. Do not reuse that choice on a new
host without explicit risk acceptance from its owner.

## Current v0.11.1 Deployment

The current host runs upstream AO tag `v0.11.1`, commit
`2f6d98f272afa2cd9ea142511fe3a9197d94d2c6`, built locally against the host's
GLIBC 2.28 with release version metadata. The installed binary reports:

```text
0.11.1 commit 2f6d98f272afa2cd9ea142511fe3a9197d94d2c6 built 2026-07-29T03:21:29Z
```

Its SHA-256 is
`b6249d803dd3c3ad8a315783dd3443f0ed0771f5d73d094267ff2f79b0f08bb0`.
That digest is qualified to the recorded `go1.26.4 linux/amd64` toolchain; it
is not a universal digest for builds made with another Go release or target.
The base `agent-orchestrator.service` launches this binary directly. No Linear
drop-in or Linear credential variable is active. The `calibration` project
readback has an empty `trackerIntake` object with no provider, repository, or
assignee.

The upstream v0.11.1 AppImage SHA-256 is
`a2997ef52ad4414581454cef320d2ad0b44062cccfde46be05fa4dd7e3ae1bee`.
It cannot launch its bundled daemon on this host because that binary requires
GLIBC 2.32 and 2.34. `ao start` launches Electron and does not expose a
standalone Web Dashboard. Do not claim upstream-native headless support.

The accepted compatibility deployment serves the renderer extracted from that
verified AppImage at `http://192.168.30.205:31080`. Its nginx listener binds
only that address, allows only `192.168.30.0/24`, proxies only GET/HEAD to AO's
fixed loopback API at `127.0.0.1:3001`, and returns HTTP 403 for mutation
methods. `/mux` is unavailable. The persistent service is
`ao-dashboard-readonly.service`; its managed unit, nginx configuration, and
Electron compatibility shim are under `artifacts/`.

### Reconstruct and install the current runtime

This is the only current reconstruction procedure. The fork, Linear, and
headless-extraction procedures later in this runbook are historical rollback
records and must not be used to reconstruct the accepted deployment.

Capture the active state before mutation:

```bash
set -euo pipefail
CALIBRATION_ROOT="$(git rev-parse --show-toplevel)"
AO_BACKUP="/home/fqzhang/.ao/backups/native-dashboard-$(date +%Y%m%dT%H%M%S)"
install -d -m 0700 "${AO_BACKUP}"
install -m 0755 /home/fqzhang/.local/bin/ao "${AO_BACKUP}/ao.before"
install -m 0600 \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service \
  "${AO_BACKUP}/agent-orchestrator.service.before"
if test -f \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf
then
  install -m 0644 \
    /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf \
    "${AO_BACKUP}/linear.conf.before"
fi
sqlite3 /home/fqzhang/.ao/data/ao.db \
  ".backup '${AO_BACKUP}/ao.db.before'"
ao status --json >"${AO_BACKUP}/status.before.json"
ao doctor --json >"${AO_BACKUP}/doctor.before.json"
ao project get calibration --json \
  >"${AO_BACKUP}/calibration-project.before.json"
systemctl --user cat agent-orchestrator.service \
  >"${AO_BACKUP}/agent-orchestrator.effective.before.txt"
```

Fetch the exact verified source and release AppImage:

```bash
set -euo pipefail
AO_BUILD_ROOT="$(mktemp -d)"
git clone --no-checkout \
  https://github.com/Untrivial-ai/agent-orchestrator.git \
  "${AO_BUILD_ROOT}/source"
git -C "${AO_BUILD_ROOT}/source" fetch --depth 1 origin \
  refs/tags/v0.11.1:refs/tags/v0.11.1
git -C "${AO_BUILD_ROOT}/source" checkout --detach v0.11.1
test "$(git -C "${AO_BUILD_ROOT}/source" rev-parse HEAD)" = \
  2f6d98f272afa2cd9ea142511fe3a9197d94d2c6
curl -L --fail \
  -o "${AO_BUILD_ROOT}/agent-orchestrator-v0.11.1.AppImage" \
  https://github.com/Untrivial-ai/agent-orchestrator/releases/download/v0.11.1/agent-orchestrator-linux-x64.AppImage
printf '%s  %s\n' \
  a2997ef52ad4414581454cef320d2ad0b44062cccfde46be05fa4dd7e3ae1bee \
  "${AO_BUILD_ROOT}/agent-orchestrator-v0.11.1.AppImage" |
  sha256sum --check -
```

Run the focused upstream checks without inheriting an active worker identity,
then build with the release metadata:

```bash
set -euo pipefail
test "$(go version)" = "go version go1.26.4 linux/amd64"
(
  cd "${AO_BUILD_ROOT}/source/backend"
  AO_TEST_HOME="$(mktemp -d)"
  env -u AO_DATA_DIR -u AO_ISSUE_ID -u AO_PROJECT_ID \
    -u AO_RUNTIME_LAUNCH_ID -u AO_SESSION_ID \
    HOME="${AO_TEST_HOME}" \
    go test ./internal/cli ./internal/daemon ./internal/httpd/... \
      ./internal/mobilebridge ./internal/service/notification \
      ./internal/storage/sqlite/...
  mkdir -p "${AO_BUILD_ROOT}/bin"
  go build -trimpath -buildvcs=false \
    -ldflags '-X github.com/aoagents/agent-orchestrator/backend/internal/cli.Version=0.11.1 -X github.com/aoagents/agent-orchestrator/backend/internal/cli.Commit=2f6d98f272afa2cd9ea142511fe3a9197d94d2c6 -X github.com/aoagents/agent-orchestrator/backend/internal/cli.Date=2026-07-29T03:21:29Z' \
    -o "${AO_BUILD_ROOT}/bin/ao" ./cmd/ao
)
"${AO_BUILD_ROOT}/bin/ao" version
printf '%s  %s\n' \
  b6249d803dd3c3ad8a315783dd3443f0ed0771f5d73d094267ff2f79b0f08bb0 \
  "${AO_BUILD_ROOT}/bin/ao" |
  sha256sum --check -
```

Install the current binary and exact current-host base unit, then remove the
active Linear override. The managed unit intentionally records this host's Node
path, tmux wrapper path, loopback proxy on port 7897, and `NO_PROXY` networks.
They are reconstruction facts for this host, not portable defaults; change them
only after verifying the replacement paths and network route.

```bash
set -euo pipefail
install -m 0755 "${AO_BUILD_ROOT}/bin/ao" /home/fqzhang/.local/bin/ao
install -d -m 0700 /home/fqzhang/.ao
install -D -m 0600 \
  "${CALIBRATION_ROOT}/docs/runbooks/artifacts/agent-orchestrator-v0.11.1.service" \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service
if test -f \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf
then
  mv \
    /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf \
    "${AO_BACKUP}/linear.conf.disabled"
fi
systemctl --user daemon-reload
systemctl --user enable agent-orchestrator.service
systemctl --user restart agent-orchestrator.service
for attempt in $(seq 1 30)
do
  if ao status --json
  then
    break
  fi
  test "${attempt}" -lt 30
  sleep 1
done
```

Register the project if it is missing, then replace its complete configuration
without tracker provider, project, assignee, or workflow:

```bash
set -euo pipefail
if ! ao project get calibration --json >/dev/null 2>&1
then
  ao project add \
    --id calibration \
    --name calibration \
    --path /home/fqzhang/project/calibration \
    --worker-agent codex
fi
PROJECT_CONFIG='{"defaultBranch":"main","sessionPrefix":"calibration","env":{"CODEX_HOME":"/home/fqzhang/.ao/codex-home"},"agentConfig":{},"worker":{"agent":"codex","agentConfig":{"permissions":"bypass-permissions"}},"orchestrator":{"agentConfig":{}}}'
ao project set-config calibration \
  --config-json "${PROJECT_CONFIG}" --json
ao version
ao status --json
ao doctor --json
ao project get calibration --json
```

Extract and adapt only the renderer from the verified AppImage:

```bash
set -euo pipefail
APPIMAGE_ROOT="${AO_BUILD_ROOT}/appimage"
ASAR_ROOT="${AO_BUILD_ROOT}/asar"
install -d -m 0700 "${APPIMAGE_ROOT}" "${ASAR_ROOT}"
chmod 0755 "${AO_BUILD_ROOT}/agent-orchestrator-v0.11.1.AppImage"
(
  cd "${APPIMAGE_ROOT}"
  "${AO_BUILD_ROOT}/agent-orchestrator-v0.11.1.AppImage" \
    --appimage-extract >/dev/null
)
npx -y asar@3.2.0 extract \
  "${APPIMAGE_ROOT}/squashfs-root/resources/app.asar" "${ASAR_ROOT}"
DASHBOARD_ROOT=/home/fqzhang/.local/share/ao-dashboard
RENDERER_ROOT="${DASHBOARD_ROOT}/v0.11.1"
install -d -m 0700 "${DASHBOARD_ROOT}" "${RENDERER_ROOT}"
cp -a "${ASAR_ROOT}/.vite/renderer/main_window/." "${RENDERER_ROOT}/"
install -m 0600 \
  "${CALIBRATION_ROOT}/docs/runbooks/artifacts/ao-dashboard-readonly-shim.js" \
  "${RENDERER_ROOT}/ao-dashboard-readonly-shim.js"
install -m 0600 \
  "${CALIBRATION_ROOT}/docs/runbooks/artifacts/ao-dashboard-readonly-health.json" \
  "${RENDERER_ROOT}/ao-dashboard-readonly-health.json"
python3 - "${RENDERER_ROOT}" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
index = root / "index.html"
text = index.read_text()
text = text.replace(
    '<script type="module"',
    '<script src="./ao-dashboard-readonly-shim.js"></script>\n'
    '\t\t<script type="module"',
    1,
)
index.write_text(text)
for path in (root / "assets").glob("*.js"):
    text = path.read_text()
    path.write_text(
        text.replace("http://127.0.0.1:", "http://192.168.30.205:")
    )
PY
find "${RENDERER_ROOT}" -type d -exec chmod 0700 {} +
find "${RENDERER_ROOT}" -type f -exec chmod 0600 {} +
```

Install and enable the fixed-port read-only proxy:

```bash
set -euo pipefail
DASHBOARD_ROOT=/home/fqzhang/.local/share/ao-dashboard
install -d -m 0700 \
  "${DASHBOARD_ROOT}/client-body" "${DASHBOARD_ROOT}/proxy" \
  "${DASHBOARD_ROOT}/fastcgi" "${DASHBOARD_ROOT}/uwsgi" \
  "${DASHBOARD_ROOT}/scgi"
install -m 0600 \
  "${CALIBRATION_ROOT}/docs/runbooks/artifacts/ao-dashboard-readonly.nginx.conf" \
  "${DASHBOARD_ROOT}/nginx.conf"
install -D -m 0600 \
  "${CALIBRATION_ROOT}/docs/runbooks/artifacts/ao-dashboard-readonly.service" \
  /home/fqzhang/.config/systemd/user/ao-dashboard-readonly.service
/usr/sbin/nginx -t -c "${DASHBOARD_ROOT}/nginx.conf"
systemctl --user daemon-reload
systemctl --user enable ao-dashboard-readonly.service
systemctl --user restart ao-dashboard-readonly.service
```

Verify the active boundary:

```bash
ao version
sha256sum /home/fqzhang/.local/bin/ao
ao status --json
ao doctor --json
ao project get calibration --json
systemctl --user show agent-orchestrator.service \
  -p ActiveState -p SubState -p DropInPaths -p ExecStart
systemctl --user show ao-dashboard-readonly.service \
  -p ActiveState -p SubState -p ExecStart
ss -ltnp | rg '127.0.0.1:3001|192.168.30.205:31080'
curl --noproxy '*' --interface 192.168.30.205 \
  http://192.168.30.205:31080/dashboard-live
curl --noproxy '*' --interface 192.168.30.205 \
  http://192.168.30.205:31080/dashboard-health
```

`/dashboard-live` proves only that nginx can serve the packaged renderer
surface. `/dashboard-health` proxies AO's `/readyz` and must fail when the AO
dependency is unavailable. Require both. Also require an allowed
`/api/v1/notifications?limit=1` read, an HTTP 403 mutation readback, and HTTP
403 for root, liveness, health, and API reads sourced from an interface outside
`192.168.30.0/24`.

Dashboard notifications are the only accepted attention event surface. Do not
add an external notifier. The historical fork, Linear wrapper, credential
boundary, and canary material below are retained only for rollback and audit.

At `2026-07-29T08:37:48Z`, upstream v0.11.1 refreshed PR #38 as mergeability
blocked while reporting `review: none` and `reviewComments: false`; it did not
automatically continue this worker. That readback does not prove complete
inline-review visibility or automatic review-to-worker continuation. Continue
to use explicit operator or conversation-authorized AO continuation when the
Dashboard does not surface and deliver actionable review. Do not add a watcher
or adapter as an implicit workaround.

## Historical Pinned Inputs

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

## Historical Rebuild Procedures

Everything in this section reconstructs superseded fork or canary states. It
does not reconstruct the current v0.11.1 runtime or Dashboard.

### Historical Phase 3 fork

Start from the calibration checkout, preserve its root for later managed
artifact installation, then clone the AO fork:

```bash
set -euo pipefail
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
set -euo pipefail
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
set -euo pipefail
AO_CUTOVER_BACKUP="/home/fqzhang/.ao/backups/phase3-trimpath-$(date +%Y%m%d%H%M%S)"
install -d -m 0700 "${AO_CUTOVER_BACKUP}"
install -m 0755 /home/fqzhang/.local/bin/ao \
  "${AO_CUTOVER_BACKUP}/ao-pre-reproducible"
install -m 0755 "${AO_BUILD_ROOT}/bin/ao" /home/fqzhang/.local/bin/ao
printf '%s  %s\n' \
  ce2df0db2e6ad7f1eb65906a04b900620941ba716d0ad1b14378db9db1387d91 \
  /home/fqzhang/.local/bin/ao |
  sha256sum --check -
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

### Historical Phase 3 Linear credential override

The superseded Phase 3 host added Linear access without placing a credential in the base
unit or repository. Store the credential only at
`/home/fqzhang/.config/agent-orchestrator/linear-api-key`, mode `0600`, inside
the mode `0700` directory `/home/fqzhang/.config/agent-orchestrator`.

The mode `0755` wrapper
`/home/fqzhang/.local/lib/ao/bin/ao-daemon-with-linear` is managed from
[`artifacts/ao-daemon-with-linear`](artifacts/ao-daemon-with-linear). Install
it together with the managed drop-in only after both repository artifacts pass
their recorded digest checks:

```bash
set -euo pipefail
CALIBRATION_ROOT="$(git rev-parse --show-toplevel)"
WRAPPER_SOURCE="${CALIBRATION_ROOT}/docs/runbooks/artifacts/ao-daemon-with-linear"
DROPIN_SOURCE="${CALIBRATION_ROOT}/docs/runbooks/artifacts/linear.conf"
WRAPPER_TARGET=/home/fqzhang/.local/lib/ao/bin/ao-daemon-with-linear
DROPIN_TARGET=/home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf
printf '%s  %s\n%s  %s\n' \
  bb5421301d09df0c3fa9176dffb1fbb5170cb02d897610b0137a155cb4c08090 \
  "${WRAPPER_SOURCE}" \
  be96ac3b7e948656c7c747e641201d7d989dbc3eec4886d16b548a7bc9c685df \
  "${DROPIN_SOURCE}" |
  sha256sum --check -
install -D -m 0755 \
  "${WRAPPER_SOURCE}" "${WRAPPER_TARGET}"
install -d -m 0700 \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d
install -m 0644 "${DROPIN_SOURCE}" "${DROPIN_TARGET}"
printf '%s  %s\n%s  %s\n' \
  bb5421301d09df0c3fa9176dffb1fbb5170cb02d897610b0137a155cb4c08090 \
  "${WRAPPER_TARGET}" \
  be96ac3b7e948656c7c747e641201d7d989dbc3eec4886d16b548a7bc9c685df \
  "${DROPIN_TARGET}" |
  sha256sum --check -
systemctl --user daemon-reload
systemctl --user restart agent-orchestrator.service
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
inside a mode `0700` directory.

The expected drop-in SHA-256 is
`be96ac3b7e948656c7c747e641201d7d989dbc3eec4886d16b548a7bc9c685df`.
The combined transaction above checks both source and installed hashes before
the reload and restart activate the credential wrapper.

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

## Historical Headless Dashboard Canary

This section records the superseded 0.10.3 experiment. Its conclusion that no
Web Dashboard was retained is historical and must not override the current
v0.11.1 reconstruction, service, and verification procedure above.

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

The historical canary did not use `ao start` on this headless host. At that
time, operators used `ao status --json`, project and session readback, the
loopback AO API, and the owning Codex or GitHub surfaces for current status.
The current v0.11.1 compatibility deployment is the explicitly reviewed
exception. Do not reconstruct the old loopback canary or infer a broader
custom-frontend precedent from it.

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
Every path snapshots the complete worker-session readback before stopping the
daemon. A binary-only rollback retains the current database and uses that
snapshot for post-restart reconciliation. A rollback that restores historical
`ao.db` is stricter: after stopping the daemon, it queries the now-stable
current and retained databases read-only and rejects nonterminated workers in
either one. A rejected check restarts the unchanged current service so AO
remains available for remediation. Preserve each current worker's Git/worktree
and pull-request state, terminate it through AO, and rerun the block. A retained
database with nonterminated ownership requires an explicitly reviewed
reconciliation copy; do not install it as-is.

For the immediate pre-security-fix binary, disable the Linear drop-in, restore
the retained executable, and verify the base service:

```bash
set -euo pipefail
ROLLBACK_AO=/home/fqzhang/.ao/backups/phase3-runtimeenv-68496903/ao-before-runtimeenv
printf '%s  %s\n' \
  2fbd3af959a1135c7d0b3cefeb0c5597b3f68a53c39e5102c418f5db302f9a16 \
  "${ROLLBACK_AO}" |
  sha256sum --check -
SESSION_SNAPSHOT="$(mktemp)"
POST_SESSION_STATE="$(mktemp)"
trap 'rm -f "${SESSION_SNAPSHOT}" "${POST_SESSION_STATE}"' EXIT
ao session ls --include-terminated --json > "${SESSION_SNAPSHOT}"
systemctl --user stop agent-orchestrator.service
if systemctl --user is-active --quiet agent-orchestrator.service; then
  echo "agent-orchestrator.service remained active after stop" >&2
  exit 1
fi
ROLLBACK_SAVE="/home/fqzhang/.ao/backups/rollback-$(date +%Y%m%d%H%M%S)"
install -d -m 0700 "${ROLLBACK_SAVE}"
install -m 0600 "${SESSION_SNAPSHOT}" \
  "${ROLLBACK_SAVE}/session-state.json"
install -m 0600 /home/fqzhang/.ao/data/ao.db "${ROLLBACK_SAVE}/ao.db"
install -m 0755 /home/fqzhang/.local/bin/ao "${ROLLBACK_SAVE}/ao"
install -m 0600 \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service \
  "${ROLLBACK_SAVE}/agent-orchestrator.service"
if [ -e /home/fqzhang/.local/lib/ao/bin/ao-daemon-with-linear ]; then
  install -m 0755 \
    /home/fqzhang/.local/lib/ao/bin/ao-daemon-with-linear \
    "${ROLLBACK_SAVE}/ao-daemon-with-linear"
fi
if [ -e /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf ]; then
  install -m 0644 \
    /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf \
    "${ROLLBACK_SAVE}/linear.conf"
  mv \
    /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf \
    /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf.disabled
fi
install -m 0755 "${ROLLBACK_AO}" /home/fqzhang/.local/bin/ao
printf '%s  %s\n' \
  2fbd3af959a1135c7d0b3cefeb0c5597b3f68a53c39e5102c418f5db302f9a16 \
  /home/fqzhang/.local/bin/ao |
  sha256sum --check -
systemctl --user daemon-reload
systemctl --user start agent-orchestrator.service
ao session ls --include-terminated --json > "${POST_SESSION_STATE}"
python - "${SESSION_SNAPSHOT}" "${POST_SESSION_STATE}" <<'PY'
import json
import sys

keys = (
    "id",
    "projectId",
    "role",
    "harness",
    "isTerminated",
    "status",
    "createdAt",
)

def normalized(path):
    with open(path, encoding="utf-8") as stream:
        payload = json.load(stream)
    return sorted(
        [{key: session.get(key) for key in keys} for session in payload["data"]],
        key=lambda session: session["id"],
    )

if normalized(sys.argv[1]) != normalized(sys.argv[2]):
    raise SystemExit("post-rollback worker-session readback differs from snapshot")
PY
systemctl --user show agent-orchestrator.service \
  -p DropInPaths -p ExecStart -p ActiveState
ao status --json
rm -f "${SESSION_SNAPSHOT}" "${POST_SESSION_STATE}"
trap - EXIT
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
ROLLBACK_ROOT=/home/fqzhang/.ao/backups/phase3-c5ed22df
printf '%s  %s\n%s  %s\n%s  %s\n' \
  4e23bde24054b18a4c443f463542e50fde11ac2e11ff552209b62ba269674981 \
  "${ROLLBACK_ROOT}/ao" \
  57134ffb27f203f7ae8528e8d7a9816374239941d6a075217c5c0a9441d85f0a \
  "${ROLLBACK_ROOT}/ao.db" \
  7946749c60bfb423bcc0863142ed0612ffd4083eb0fb780f242a0a61a3c1fb6b \
  "${ROLLBACK_ROOT}/agent-orchestrator.service" |
  sha256sum --check -
SESSION_SNAPSHOT="$(mktemp)"
trap 'rm -f "${SESSION_SNAPSHOT}"' EXIT
ao session ls --include-terminated --json > "${SESSION_SNAPSHOT}"
systemctl --user stop agent-orchestrator.service
if systemctl --user is-active --quiet agent-orchestrator.service; then
  echo "agent-orchestrator.service remained active after stop" >&2
  exit 1
fi
if ! python - /home/fqzhang/.ao/data/ao.db "${ROLLBACK_ROOT}/ao.db" <<'PY'; then
import sqlite3
import sys

def active_workers(path):
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as database:
        return [
            row[0]
            for row in database.execute(
                "SELECT id FROM sessions "
                "WHERE kind = 'worker' AND is_terminated = 0 ORDER BY id"
            )
        ]

current_active = active_workers(sys.argv[1])
retained_active = active_workers(sys.argv[2])
failures = []
if current_active:
    failures.append(
        "drain current nonterminated workers through AO: "
        + ", ".join(current_active)
    )
if retained_active:
    failures.append(
        "retained database has nonterminated ownership and requires "
        "an explicitly reviewed reconciliation copy: "
        + ", ".join(retained_active)
    )
if failures:
    raise SystemExit("; ".join(failures))
PY
  systemctl --user start agent-orchestrator.service
  echo "rollback rejected; unchanged current AO service restarted" >&2
  exit 1
fi
ROLLBACK_SAVE="/home/fqzhang/.ao/backups/rollback-$(date +%Y%m%d%H%M%S)"
install -d -m 0700 "${ROLLBACK_SAVE}"
install -m 0600 "${SESSION_SNAPSHOT}" \
  "${ROLLBACK_SAVE}/session-state.json"
install -m 0600 /home/fqzhang/.ao/data/ao.db "${ROLLBACK_SAVE}/ao.db"
install -m 0755 /home/fqzhang/.local/bin/ao "${ROLLBACK_SAVE}/ao"
install -m 0600 \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service \
  "${ROLLBACK_SAVE}/agent-orchestrator.service"
if [ -e /home/fqzhang/.local/lib/ao/bin/ao-daemon-with-linear ]; then
  install -m 0755 \
    /home/fqzhang/.local/lib/ao/bin/ao-daemon-with-linear \
    "${ROLLBACK_SAVE}/ao-daemon-with-linear"
fi
if [ -e /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf ]; then
  install -m 0644 \
    /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf \
    "${ROLLBACK_SAVE}/linear.conf"
  mv \
    /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf \
    /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf.disabled
fi
install -m 0755 "${ROLLBACK_ROOT}/ao" /home/fqzhang/.local/bin/ao
install -m 0600 "${ROLLBACK_ROOT}/ao.db" /home/fqzhang/.ao/data/ao.db
install -m 0600 "${ROLLBACK_ROOT}/agent-orchestrator.service" \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service
printf '%s  %s\n%s  %s\n%s  %s\n' \
  4e23bde24054b18a4c443f463542e50fde11ac2e11ff552209b62ba269674981 \
  /home/fqzhang/.local/bin/ao \
  57134ffb27f203f7ae8528e8d7a9816374239941d6a075217c5c0a9441d85f0a \
  /home/fqzhang/.ao/data/ao.db \
  7946749c60bfb423bcc0863142ed0612ffd4083eb0fb780f242a0a61a3c1fb6b \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service |
  sha256sum --check -
systemctl --user daemon-reload
systemctl --user start agent-orchestrator.service
systemctl --user show agent-orchestrator.service \
  -p DropInPaths -p ExecStart -p ActiveState
ao status --json
rm -f "${SESSION_SNAPSHOT}"
trap - EXIT
```

Expected results are binary SHA-256
`4e23bde24054b18a4c443f463542e50fde11ac2e11ff552209b62ba269674981`,
database SHA-256
`57134ffb27f203f7ae8528e8d7a9816374239941d6a075217c5c0a9441d85f0a`,
base-unit SHA-256
`7946749c60bfb423bcc0863142ed0612ffd4083eb0fb780f242a0a61a3c1fb6b`,
empty `DropInPaths`, effective `ExecStart` ending in `ao daemon`, active
service state, and ready AO status.
The retained database currently contains six nonterminated worker rows, so the
unmodified historical set intentionally fails its retained-ownership gate and
must not be installed without an explicitly reviewed reconciliation copy.

For the earlier upstream canary, restore both historical binaries and its
matching unit:

```bash
set -euo pipefail
ROLLBACK_ROOT=/home/fqzhang/.local/lib/ao/backups/20260726-upstream-9f8c085f
printf '%s  %s\n%s  %s\n%s  %s\n%s  %s\n' \
  25fab37d7279e72d0e3c2295630c1eb47ed4ff4f54c08b02e4125ca3b9efcdeb \
  "${ROLLBACK_ROOT}/ao" \
  5bd25fd1647c4c6eb2e22b35aa9f257c0d76d23c5ed0fa42c5bed32745e290e8 \
  "${ROLLBACK_ROOT}/ao-daemon" \
  7beffe130d21409160b226ad543df64876d277511c847b9907e519855a3e15dd \
  "${ROLLBACK_ROOT}/ao.db" \
  f79d3908773ff8ddbe799b2f9e32256caa1ceb33f0910acfa2c7a038c2ac332c \
  "${ROLLBACK_ROOT}/agent-orchestrator.service" |
  sha256sum --check -
SESSION_SNAPSHOT="$(mktemp)"
trap 'rm -f "${SESSION_SNAPSHOT}"' EXIT
ao session ls --include-terminated --json > "${SESSION_SNAPSHOT}"
systemctl --user stop agent-orchestrator.service
if systemctl --user is-active --quiet agent-orchestrator.service; then
  echo "agent-orchestrator.service remained active after stop" >&2
  exit 1
fi
if ! python - /home/fqzhang/.ao/data/ao.db "${ROLLBACK_ROOT}/ao.db" <<'PY'; then
import sqlite3
import sys

def active_workers(path):
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as database:
        return [
            row[0]
            for row in database.execute(
                "SELECT id FROM sessions "
                "WHERE kind = 'worker' AND is_terminated = 0 ORDER BY id"
            )
        ]

current_active = active_workers(sys.argv[1])
retained_active = active_workers(sys.argv[2])
failures = []
if current_active:
    failures.append(
        "drain current nonterminated workers through AO: "
        + ", ".join(current_active)
    )
if retained_active:
    failures.append(
        "retained database has nonterminated ownership and requires "
        "an explicitly reviewed reconciliation copy: "
        + ", ".join(retained_active)
    )
if failures:
    raise SystemExit("; ".join(failures))
PY
  systemctl --user start agent-orchestrator.service
  echo "rollback rejected; unchanged current AO service restarted" >&2
  exit 1
fi
ROLLBACK_SAVE="/home/fqzhang/.ao/backups/rollback-$(date +%Y%m%d%H%M%S)"
install -d -m 0700 "${ROLLBACK_SAVE}"
install -m 0600 "${SESSION_SNAPSHOT}" \
  "${ROLLBACK_SAVE}/session-state.json"
install -m 0600 /home/fqzhang/.ao/data/ao.db "${ROLLBACK_SAVE}/ao.db"
install -m 0755 /home/fqzhang/.local/bin/ao "${ROLLBACK_SAVE}/ao"
if [ -e /home/fqzhang/.local/bin/ao-daemon ]; then
  install -m 0755 /home/fqzhang/.local/bin/ao-daemon \
    "${ROLLBACK_SAVE}/ao-daemon"
fi
install -m 0600 \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service \
  "${ROLLBACK_SAVE}/agent-orchestrator.service"
if [ -e /home/fqzhang/.local/lib/ao/bin/ao-daemon-with-linear ]; then
  install -m 0755 \
    /home/fqzhang/.local/lib/ao/bin/ao-daemon-with-linear \
    "${ROLLBACK_SAVE}/ao-daemon-with-linear"
fi
if [ -e /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf ]; then
  install -m 0644 \
    /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf \
    "${ROLLBACK_SAVE}/linear.conf"
  mv \
    /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf \
    /home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf.disabled
fi
install -m 0755 "${ROLLBACK_ROOT}/ao" /home/fqzhang/.local/bin/ao
install -m 0755 "${ROLLBACK_ROOT}/ao-daemon" \
  /home/fqzhang/.local/bin/ao-daemon
install -m 0600 "${ROLLBACK_ROOT}/ao.db" /home/fqzhang/.ao/data/ao.db
install -m 0600 "${ROLLBACK_ROOT}/agent-orchestrator.service" \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service
printf '%s  %s\n%s  %s\n%s  %s\n%s  %s\n' \
  25fab37d7279e72d0e3c2295630c1eb47ed4ff4f54c08b02e4125ca3b9efcdeb \
  /home/fqzhang/.local/bin/ao \
  5bd25fd1647c4c6eb2e22b35aa9f257c0d76d23c5ed0fa42c5bed32745e290e8 \
  /home/fqzhang/.local/bin/ao-daemon \
  7beffe130d21409160b226ad543df64876d277511c847b9907e519855a3e15dd \
  /home/fqzhang/.ao/data/ao.db \
  f79d3908773ff8ddbe799b2f9e32256caa1ceb33f0910acfa2c7a038c2ac332c \
  /home/fqzhang/.config/systemd/user/agent-orchestrator.service |
  sha256sum --check -
systemctl --user daemon-reload
systemctl --user start agent-orchestrator.service
systemctl --user show agent-orchestrator.service \
  -p DropInPaths -p ExecStart -p ActiveState
ao status --json
rm -f "${SESSION_SNAPSHOT}"
trap - EXIT
```

Expected hashes are
`25fab37d7279e72d0e3c2295630c1eb47ed4ff4f54c08b02e4125ca3b9efcdeb`
for `ao` and
`5bd25fd1647c4c6eb2e22b35aa9f257c0d76d23c5ed0fa42c5bed32745e290e8`
for `ao-daemon`, with database SHA-256
`7beffe130d21409160b226ad543df64876d277511c847b9907e519855a3e15dd`
and base-unit SHA-256
`f79d3908773ff8ddbe799b2f9e32256caa1ceb33f0910acfa2c7a038c2ac332c`.
`DropInPaths` must be empty, effective `ExecStart` must end in `ao-daemon`, the
service must be active, and AO status must be ready.
The retained upstream database currently contains three nonterminated worker
rows, so this unmodified set also intentionally fails before installation.

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
