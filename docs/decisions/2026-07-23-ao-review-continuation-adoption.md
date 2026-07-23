# AO Review Continuation Adoption

Date: 2026-07-23

Status: Accepted as a user-level canary service

## Context

The repository delivery loop already assigns pull-request validation and
platform-native agent review to GitHub and Codex. The remaining operational
gap was continuation: Automatic Codex Review could publish an actionable
inline finding, but it did not resume the server-side worker that owned the
pull request. A foreground Codex task therefore still had to poll, interpret,
and relay mechanical feedback, consuming the human attention the loop was
intended to preserve.

Three candidate paths were tested:

- ChatGPT Scheduled Tasks could provide time-based polling, but the available
  Windows and SSH surfaces did not provide a dependable server-side task
  creation or continuation bridge. Polling was also a weaker fit than the
  GitHub event that already represented the state change.
- OpenAI Symphony remained a useful orchestration reference, but the pinned
  implementation failed the predeclared dependency and full-suite readiness
  gates recorded in the 2026-07-22 closeout. Its `NO-GO` remains in force.
- Agent Orchestrator (AO) already owned pull-request observation, worker
  identity, Worktrees, and worker continuation. Community issue
  [#2827](https://github.com/AgentWrapper/agent-orchestrator/issues/2827)
  identified that bot-authored review findings were filtered out, and pull
  request [#2872](https://github.com/AgentWrapper/agent-orchestrator/pull/2872)
  supplied the narrow lifecycle fix.

The AO candidate still required two observed corrections on this host:

1. COMMENTED reviews can advance GitHub's provider timestamp without changing
   the aggregate review decision, so AO must refresh review threads on that
   provider update.
2. A long multiline finding can remain in Codex's collapsed-paste editor, so
   the tmux runtime must leave that state and submit one carriage return after
   a bounded settle interval.

The installed-service canary then exposed three environment requirements:

1. an AO worker must use a minimal isolated `CODEX_HOME` so Desktop Apps and
   Plugins do not add unrelated MCP startup failures;
2. the user service must carry the host's proxy environment so Codex model
   requests can reach the network; and
3. tmux's micromamba libraries must be scoped to a tmux wrapper. A service-wide
   `LD_LIBRARY_PATH` polluted Git/curl certificate discovery and broke an
   otherwise valid push.

## Decision

- Retain GitHub Actions and Automatic Codex Review as the native validation and
  review surfaces.
- Use a pinned AO build for the missing event-to-original-worker continuation
  layer and, on this accepted single-user host, for task-specific worker start
  or claim after a conversation explicitly authorizes implementation and
  pull-request delivery. This does not authorize unattended issue intake,
  automatic work discovery, a separate scheduler, or a PR babysitter.
- Run AO as the `fqzhang` user through `systemd --user`; keep its state under
  `/home/fqzhang/.ao` and install its two binaries under
  `/home/fqzhang/.local/bin`.
- Register repositories individually when recurring continuation is materially
  useful. The persistent host service is reusable across repositories, but its
  presence does not require every repository to adopt AO.
- For `calibration`, use a Codex worker, allow actionable review findings only
  from `chatgpt-codex-connector`, use the isolated AO Codex home, and keep
  auto-merge disabled.
- Accept the current single-user host risk of AO's `bypass-permissions` mode.
  For Codex this is the permissionless
  `--dangerously-bypass-approvals-and-sandbox` launch mode. The user explicitly
  accepted this risk on 2026-07-23; it is not a cross-project default and must
  not be silently applied on another host or for another owner.
- Reuse the existing user Codex and GitHub authentication. Do not create or
  copy a second broad token merely for AO.

The operational source of truth is
[`../runbooks/agent-orchestrator-review-continuation.md`](../runbooks/agent-orchestrator-review-continuation.md).

## Evidence

- Tested AO base:
  [`04841344c82f213b8fc0e34b713e2442f8793d2b`](https://github.com/AgentWrapper/agent-orchestrator/commit/04841344c82f213b8fc0e34b713e2442f8793d2b),
  the then-current head of AO pull request #2872.
- Local observer correction:
  `12559c9245a41b10c7798e9281253032791fafd9`.
- Local tmux correction:
  `e88f0d89c1b5da5efe808a0f2a144f5e1603b5a7`.
- Focused Go tests passed for tmux, SCM observation, lifecycle, domain, and the
  GitHub SCM adapter.
- A 1.2 KB message reached the restored Codex worker without a manual
  keystroke, and the worker replied `FINAL_AUTOMATED_PASS`.
- A real GitHub review update was delivered to the original worker. It
  implemented, tested, and committed the requested symlink fix as `1bba0e6` on
  [canary pull request #2](https://github.com/FuqingZh/codex-continuation-canary/pull/2).
  `Canary CI / validate` passed and all review threads were resolved.
- A second installed-service canary exercised the complete native loop on
  [canary pull request #3](https://github.com/FuqingZh/codex-continuation-canary/pull/3).
  Automatic Codex Review published an anchored P1 path-traversal finding at
  `2026-07-23T02:19:26Z`. AO delivered it to the original
  `codex-continuation-canary-4` worker, which added traversal, absolute-path,
  and symlink-escape tests, committed `6a2b1a35cfdabd1c5e28d768190d71613fced3f6`,
  and pushed without a human comment or relay. `Canary CI / validate` passed,
  the thread became resolved and outdated, and Automatic Review returned `+1`
  at `2026-07-23T02:22:15Z`. Auto-merge remained disabled and the canary pull
  request remained open.
- After user-level installation, `ao doctor --json` reported 13 passing checks
  and zero failures. Restart readback reported the service `enabled`, `active`,
  and `ready`, with the persisted `calibration` project configuration.
- Replaying the retained patches from the pinned base exposed that the host's
  default tmux 2.7 fails AO's runtime integration at the unsupported
  `window-size` option. The same focused suite passed with the already
  available tmux 3.5 runtime, so the service and runbook now select that
  version explicitly.
- Installed binary SHA-256 values are recorded in the runbook.
- After replacing the service-wide library path with a tmux-only wrapper,
  private-repository `git ls-remote` succeeded without a certificate override
  and `ao doctor --json` again reported zero failures.
- The first bounded real-repository intake used
  [`FuqingZh/biofetch`](https://github.com/FuqingZh/biofetch). After pull
  request [#5](https://github.com/FuqingZh/biofetch/pull/5) removed an obsolete
  tracked `.codex` placeholder that blocked hook provisioning, the
  conversation-authorized `biofetch-1` worker updated three direct patch
  dependencies and opened pull request
  [#6](https://github.com/FuqingZh/biofetch/pull/6). Repository validation,
  `validate-biofetch`, and Automatic Review passed; after explicit human merge
  authorization, main advanced to
  `1248e3473c86192aa17c48062bf001ea97482d4f` and AO terminated the worker as
  `merged`.

The retained patches were replayed from the pinned base in a new Worktree. The
focused suite passed with tmux 3.5, and both binaries were rebuilt with VCS
stamping disabled so equivalent patch replay does not depend on new committer
metadata. Those rebuilt hashes are the installed and documented values.

These observations prove the bounded review-to-worker continuation and current
host installation. They do not establish AO upstream stability, cross-host
portability, autonomous merge safety, or effectiveness for every repository.

## Consequences

- A review finding can return to the worker that already owns context and the
  isolated Worktree, reducing foreground polling and human relay work.
- In an individually registered repository on this host, an authorized
  pull-request implementation task can start or claim its worker without the
  user repeating the AO tool name. Analysis and planning remain read-only, and
  AO does not discover or claim new work without a conversation-authorized
  task.
- The service is deliberately a pinned canary because AO pull request #2872 is
  still open and its head has advanced beyond the tested commit. Updating to a
  later upstream revision requires rebuilding and rerunning the focused and
  real-event checks; a moving pull-request head is not an approved update.
- The two local patches are stored with the runbook so a new host does not
  depend on `/tmp`, the original task, or local Git objects.
- Repository authority, acceptance commands, CI, review policy, credentials,
  and merge decisions remain with their existing owners. AO owns continuation,
  not correctness or product intent.
- The earlier Symphony closeouts remain valid for Symphony. AO is a narrower
  successor implementation, not evidence that those gates passed.

## Reopen Conditions

Revisit this decision when any of the following occurs:

- AO #2872 merges or changes enough to replace the pinned base;
- upstream incorporates either local patch;
- a Codex or AO upgrade changes permission flags, hook delivery, tmux behavior,
  project configuration, or service startup;
- a second user, shared host, secret boundary, or higher-impact repository
  makes the accepted single-user permissionless risk inappropriate;
- repeated tasks show that issue claiming, broader orchestration, or another
  engine is needed; or
- a repository proposes auto-merge under an explicit independent risk policy.
