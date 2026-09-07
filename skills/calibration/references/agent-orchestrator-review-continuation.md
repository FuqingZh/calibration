# Portable Agent Orchestrator Integration Guide

This is the single calibration authority for AO adoption, owner routing, and
release boundaries. AO is an optional environment adapter. Calibration does
not install, upgrade, fork, or patch AO; upstream Desktop owns distribution.
Private host paths and service configuration remain in rendered local authority,
which the global instructions discover only for explicit host-operation tasks.

## Version And Native Mechanics

The command and capability corrections below were checked against upstream
[v0.12.12](https://github.com/Untrivial-ai/agent-orchestrator/releases/tag/v0.12.12),
commit `84fb37ce5aa947ceb9b19b0c2435b242ac92ce26`. This is source evidence, not
proof of the installed daemon version or a passing local continuation loop.

Use the installed AO's native `using-ao` skill for command mechanics and
`ao <command> --help` for authoritative flags. AO installs its embedded catalog
at daemon boot; if unavailable, use CLI help without installing another copy.
Do not mirror that catalog, retry implementation, or feedback scheduler here.
On older versions, check actual capabilities before acting; do not invent flags
or replace an unavailable operation with cross-worktree writes.

In v0.12.12, an open draft PR can be claimed without marking it ready, and
`ao session resume-agent` resumes an exited agent in a non-terminated session.
The typed project configuration has no `autoMerge` field. Do not apply obsolete
project settings. These capabilities grant no ownership or merge authority.

## Adoption And State Evidence

Classify observations by owner: **sandbox state**, **worker state**, **daemon
state**, or **host state**. A sandbox mismatch does not establish a host failure.
Use `indeterminate` when evidence is sandbox-only; `daemon ready` requires
an authoritative active host service, ready/running AO readback, and a passing
health probe. Repeated failure in the owning host context establishes
`unavailable`. Use `delivery degraded` only for an external integration or
authentication failure while the core daemon remains ready.

Distinguish **registered**, **configured**, **runtime-ready**, and
**continuation-proven** adoption. The last requires a real PR's actionable CI
or review feedback to return to its owning worker, which can push a correction.
Registration, matching settings, and static health alone do not prove that loop.
Record accepted adoption in the owning repository. Conversation-authorized
implementation is sufficient intake; neither an issue tracker nor a separate
orchestrator session is required.

The optional `scripts/adopt_ao_repository.py` helper supports an already
installed, CLI-capable AO and a Linux user-service profile with `systemd --user`
and compatible tmux prerequisites. It is not a universal Desktop adapter; do
not impose those platform prerequisites on other AO deployments.

## Authority And Single Writer

Before any mutation, preserve any already AO-owned repository, worktree, or
branch: the controller remains read-only, even without a PR. Review, analysis,
and discussion alone authorize no implementation.

Lifecycle routing requires installed AO, an adopted repository, supplied local
host authority, and an accepted continuation-proven orchestrator or an
explicitly bounded canary for this task. Verify authoritative `daemon ready`
before owner lookup and handoff. Without these gates, do not send, restore,
claim, or spawn: use isolated-worktree fallback only for new or unowned
pull-request-bound work; preserve an existing AO-owned PR's branch, worktree,
and feedback for AO or owner restoration.

For truly unowned new implementation, start a task-specific owning worker,
perform fresh authoritative session readback, and hand off through the state
routing below; only that owner creates the implementation branch or PR. For an
existing owned PR, including a draft, route to its owner. Before claiming any
unclaimed PR or spawning its new owner, prove every controller, human, or non-AO
writer is quiesced and cannot write. AO-owner absence alone is not proof.
Otherwise preserve state, do not claim or spawn, and escalate. Claim without
takeover; claim requires an existing PR, but it does not require ready status.

Compare the assigned writable workspace and Git root with the owning AO
worker's target. A workspace capability mismatch does not mean AO unavailable.
Do not patch, stage, commit, or push in an owner's sibling worktree. A successful
claim does not prove branch checkout: inspect the actual branch and workspace.
Do not repeat rejected filesystem escalation.

Explicit transfer requires the former owner to be quiesced: authoritative
readback proves the owner cannot write, ownership is released, and runtime
release is complete with an empty containment boundary. An idle or live owner,
or a terminated owner with cleanup pending, is not quiesced. Without a real
enforceable containment or write-authority revocation mechanism and its verified
release, preserve state and do not transfer. Process, tmux, session, or writer
absence is not equivalent proof, including when AO itself is unavailable.

## Route The Current Owner

Inspect `session.isTerminated` before `session.activity.state`; derived
`session.status` is board/SCM state, not the activity authority.

| Authoritative state | Action within existing authority |
| --- | --- |
| Terminated | Restore only after runtime release and an empty OS-owned containment boundary are proved; otherwise preserve state and monitor |
| Non-terminated, `active` or `idle` | Send the already-authorized task to the owner |
| Non-terminated, `waiting_input` | Hold for provenance; send only when authoritative evidence proves an already-authorized ordinary idle prompt; escalate permission or user-decision prompts |
| Non-terminated, `exited` | Use the installed native resume-agent command; inspect help for older-version compatibility |
| Non-terminated, `blocked` | Return to human authority |

After spawn, claim, restore, or resume, perform fresh authoritative readback and
apply this table before sending. Native message guards do not authorize replying
to a permission prompt. The controller then performs readback; the owner handles
same-scope mechanical feedback through AO's native CI/review loop. Verify the
configured loop instead of creating a second controller polling or nudge loop.

## Delivery And Release

GitHub native per-PR auto-merge may use already-granted low-risk implementation
authority only after required CI passes on the exact current head, current-head
review is clean, and no actionable review threads remain. Read back those gates
immediately before requesting it. An explicit user stop, stricter repository
policy, security, secrets, permissions, release, compatibility, or irreversible
risk withholds that authority. Deploy needs separate explicit authority unless
a distinct deployment contract grants it. Native AO merge checks do not extend
these permissions or cover a bypass through another tool.

Once PR attribution is verified and before merge, enable the supported native
per-session terminate-on-PR-merge policy and read it back. It grants no merge
authority. Let AO evaluate multi-PR completion and clean resources; retain the
terminated session record as audit history. For cancelled, no-PR, or
closed-unmerged work, explicitly terminate only after state and dirty-worktree
checks. Preserve dirty worktrees; report `preserved_dirty`, `failed`, and any
unproved release rather than force-deleting them.

Treat termination as complete or runtime as released only after the worker's
OS-owned containment boundary is empty. A terminated session can retain pending
cleanup; terminal, tmux, shell, or session disappearance is not proof that
children exited. Keep partial release observable and retryable. In the checked
v0.12.12 source, tmux reaping is best-effort; per-worker systemd scopes remain a
proposed mechanism, not verified current AO behavior. When emptiness cannot be
proved, report the narrower evidence and do not claim full process release.

Owner retries are limited to idempotent transient operations and polling, with
an explicit attempt or deadline budget, backoff, and `Retry-After`. Stop on head
or scope change, cancellation, non-transient authentication or permission
failure, or budget exhaustion. For an external write with unknown outcome, use
authoritative readback and deduplication first; retry only if the intended state
is absent. Preserve observable state and report the actual stop reason. A
cross-contract review request or exhausted review-convergence budget routes back
to calibration; transport exhaustion is a preserve-and-report condition.

## Discovery And Dashboard Boundaries

Keep discovery and mutations within the assigned workspace. Do not recursively
scan a parent aggregation root containing sibling worktrees. For a remote mount,
network filesystem, or large shared filesystem, select concrete subdirectories
and a traversal-aware bound such as maximum depth; bound file type, file size,
result count, and concurrency. Consult rendered local authority for explicit
host operations; portable skills do not discover private profiles directly.

Dashboard Terminal is off by default under calibration's exposure policy.
Private-LAN opt-in requires an exact client IP allowlist, an exact WebSocket
Origin, an exact `/mux` route, and a loopback upstream together. Origin checking
is not authentication. Multi-user, dynamic-address, public, or untrusted
networks require authentication. An existing-session terminal grants no REST
mutation or standalone-shell authority. Deployment values and configurations
remain private host authority.
