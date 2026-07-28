# AO Phase 3 Deployment Reproducibility Closeout

Date: 2026-07-27

Status: Deployed and host-verified

## Context

The accepted AO user service was upgraded from the earlier patched canary to
the Phase 3 fork deployment that adds read-only Linear tracker support. This
closeout records only the calibration-repository operational evidence needed
to reconstruct, verify, or roll back that deployment. It does not copy the
credential into Git, change the AO implementation, or expand the accepted
automation boundary.

## Deployed State

- Fork: `https://github.com/FuqingZh/agent-orchestrator.git`
- Deployed fork `main` commit:
  `68496903141232718c23b8f13f4efede2d6f7b58`
- Merged security-fix head:
  `4c241b1447b4c5c303593ac0a94386cc3dfd3261`
- Current executable: `/home/fqzhang/.local/bin/ao`
- Current installed SHA-256:
  `ce2df0db2e6ad7f1eb65906a04b900620941ba716d0ad1b14378db9db1387d91`
- Pre-reproducible Phase 3 installed SHA-256, retained as rollback evidence:
  `ec19ff3a87a15a04eb3d9d647397c2cc32a820da19448cc93b6fe4f423cc4016`
- Pre-security-fix rollback:
  `/home/fqzhang/.ao/backups/phase3-runtimeenv-68496903/ao-before-runtimeenv`,
  SHA-256
  `2fbd3af959a1135c7d0b3cefeb0c5597b3f68a53c39e5102c418f5db302f9a16`
- Linear credential:
  `/home/fqzhang/.config/agent-orchestrator/linear-api-key`, mode `0600`,
  inside mode `0700` directory
  `/home/fqzhang/.config/agent-orchestrator`
- Credential wrapper:
  `/home/fqzhang/.local/lib/ao/bin/ao-daemon-with-linear`, mode `0755`
- Credential wrapper SHA-256:
  `0531d973a0cd690b03b52530388cf138e5a4b54899167a341ca0d1a5ff88d2d7`
- Active service drop-in:
  `/home/fqzhang/.config/systemd/user/agent-orchestrator.service.d/linear.conf`,
  mode `0644`, inside a mode `0700` drop-in directory

The wrapper reads the credential at process start, rejects a missing, unreadable,
or empty file, exports it only to the daemon process as `AO_LINEAR_API_KEY`,
and executes `/home/fqzhang/.local/bin/ao daemon`. The active drop-in clears the
base unit's `ExecStart` and replaces it with the wrapper. The credential value
is not present in the unit, drop-in, wrapper, repository, or this decision. The
complete managed wrapper source is
[`../runbooks/artifacts/ao-daemon-with-linear`](../runbooks/artifacts/ao-daemon-with-linear).

The wrapper-to-daemon credential handoff is not sufficient to protect worker
environments by itself. The deployed AO build must filter both
`AO_LINEAR_API_KEY` and `AO_LINEAR_OAUTH_TOKEN` before creating tmux panes.
The AO-side filtering fix head was
[`4c241b1447b4c5c303593ac0a94386cc3dfd3261`](https://github.com/FuqingZh/agent-orchestrator/commit/4c241b1447b4c5c303593ac0a94386cc3dfd3261)
in agent-orchestrator
[pull request #10](https://github.com/FuqingZh/agent-orchestrator/pull/10).
Its focused, race, full lint, vet, Linux build, and Windows build validation
passed; fresh Automatic Review reported no major issues and its two P1 threads
were resolved. PR #10 merged as
`68496903141232718c23b8f13f4efede2d6f7b58`, which is also fork
`origin/main`.

Two independent builds from the merge commit with
`-trimpath -buildvcs=false` produced the same SHA-256,
`ce2df0db2e6ad7f1eb65906a04b900620941ba716d0ad1b14378db9db1387d91`.
This canonical hash is qualified to Go 1.26.4 on `linux/amd64`; another
supported toolchain or target requires its own recorded hash. That binary is
installed. The Linear drop-in is restored and effective
`ExecStart` is `/home/fqzhang/.local/lib/ao/bin/ao-daemon-with-linear`.
After restart, AO reported ready and healthy, doctor reported zero failures,
and all nine pre-existing tmux pane PIDs were unchanged.

A fresh AO worker pane performed a boolean presence check that never printed
credential values and reported exactly `LINEAR_ENV_CLEAN`; the disposable
worker was then terminated. This closes the ambient-environment acceptance gate
for removing `AO_LINEAR_API_KEY` and `AO_LINEAR_OAUTH_TOKEN` from new panes.

It does not establish worker-secret isolation. The daemon and workers share the
`fqzhang` account and workers use `bypass-permissions`, so a worker with that
authority may read the mode `0600` credential file or inspect same-user process
state through host interfaces permitted by the operating system. Preventing a
worker from obtaining the credential requires privilege separation, such as a
distinct daemon account or security boundary inaccessible to workers. The
accepted evidence is limited to ambient-environment hygiene.

## Reproducible Build And Source Sync

Building source tree `e9505779` from two different worktrees with only
`-buildvcs=false` produced different hashes. Building both with:

```bash
go build -trimpath -buildvcs=false -o "${AO_BUILD_ROOT}/bin/ao" ./cmd/ao
```

produced the canonical SHA-256
`2fbd3af959a1135c7d0b3cefeb0c5597b3f68a53c39e5102c418f5db302f9a16`.
The deployment build therefore requires both flags; `-buildvcs=false` alone is
not reproducible across worktree paths.

On this checkout, `git fetch origin main` updated only `FETCH_HEAD`; it did not
durably update `refs/remotes/origin/main`. Durable source synchronization used:

```bash
git fetch origin refs/heads/main:refs/remotes/origin/main
git rev-parse refs/remotes/origin/main
git ls-remote origin refs/heads/main
```

Both readbacks must report
`68496903141232718c23b8f13f4efede2d6f7b58` before building the cutover
artifact.

## Verification Boundary

Verification must run in the same user and service context as the deployment:
the `fqzhang` user, its `systemd --user` manager, the deployed wrapper and
drop-in, and the service's actual environment. A shell-only invocation,
different user, or differently constructed environment does not verify the
installed service. Read back the effective unit with `systemctl --user cat`
and `systemctl --user show`, then verify the active daemon and installed hash
using the commands in the AO runbook. The installed security-fix binary
`sha256sum /home/fqzhang/.local/bin/ao` must report
`ce2df0db2e6ad7f1eb65906a04b900620941ba716d0ad1b14378db9db1387d91`.
The earlier `2fbd3af9...` and `ec19ff3a...` results identify retained rollback
artifacts.

The Phase 3 smoke validates the credential and read-only Linear API identity
path; it does not exercise AO's tracker adapter and is not a real Linear intake
loop. The installed binary hash, service wiring, AO health, focused AO tests,
and fresh-worker ambient-environment check are separate evidence. They do not
prove privilege-separated secret isolation, sustained polling, durable claim
coordination, issue-to-worker creation, restart recovery, or end-to-end
processing of a real Linear issue. Do not describe the deployment as a proven
production Linear intake service until a separately authorized real-project
canary exercises those behaviors.

The bounded smoke must also remain read-only: authenticate a `viewer` GraphQL
query using the credential file, require a non-empty viewer id and no GraphQL
errors, and make no project, issue, comment, or workflow mutation. The runbook
owns the executable command and full success criteria.

## Rollback

The immediate pre-security-fix binary is retained at
`/home/fqzhang/.ao/backups/phase3-runtimeenv-68496903/ao-before-runtimeenv`,
with SHA-256
`2fbd3af959a1135c7d0b3cefeb0c5597b3f68a53c39e5102c418f5db302f9a16`.
Rollback to it requires disabling the Linear drop-in so the credential is not
activated with a binary that lacks the accepted worker-environment filter.

The immediate pre-Phase-3 artifacts are retained under
`/home/fqzhang/.ao/backups/phase3-c5ed22df/`:

- `ao`
- `ao-phase3-before-typed-nil-fix`
- `ao.db`
- `agent-orchestrator.service`

The pre-reproducible Phase 3 binary with SHA-256
`ec19ff3a87a15a04eb3d9d647397c2cc32a820da19448cc93b6fe4f423cc4016`
must also remain recoverable in the cutover backup. It is rollback evidence,
not the canonical reproducible deployment artifact.

This immediate set is internally consistent because its retained base unit
starts `ao daemon`; it does not require the separate `ao-daemon` executable.
The older base unit that starts `ao-daemon` must be restored only with the
matching retained executable under the earlier upstream-canary backup.

The earlier upstream-canary artifacts are retained under
`/home/fqzhang/.local/lib/ao/backups/20260726-upstream-9f8c085f/`:

- `ao`
- `ao-daemon`
- `ao.db`
- `agent-orchestrator.service`

Rollback requires stopping the user service, preserving the current database
and binaries as a new dated backup, restoring one internally consistent
binary/database/unit set, removing or disabling the Linear drop-in when
returning to a non-Linear build, reloading the user manager, and rerunning
host-context verification. Do not delete the credential as part of ordinary
rollback; credential revocation or removal is a separate explicit security
operation.

## Consequences

- The deployment can be identified by source commit and a worktree-independent
  installed artifact hash.
- Secret material remains outside Git with a read-only owner boundary.
- Service reconstruction includes the wrapper and effective systemd override,
  rather than assuming the base unit alone starts the daemon.
- Static health and the Phase 3 smoke remain narrower evidence than a real
  Linear intake loop.

The operational command source of truth remains
[`../runbooks/agent-orchestrator-review-continuation.md`](../runbooks/agent-orchestrator-review-continuation.md).
