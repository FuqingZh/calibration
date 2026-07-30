# Final Operational Closeout

Date: 2026-07-30

Status: Accepted; stable maintenance mode

## Decision

Calibration has no active implementation phase. The repository is in stable
maintenance mode: accept conversation-authorized, task-specific work when a
concrete need arises, preserve the current authority map, and do not keep a
standing implementation program open.

For implementation intended to cross a pull-request boundary in this accepted
AO repository, the conversation authorizes a task-specific AO worker. A
separate AO orchestrator is optional when coordination benefits from one; it is
not required for ordinary single-task delivery. AO remains the continuation and
worker-isolation adapter, while GitHub pull requests remain the delivery, CI,
review, and merge fact source.

Linear intake remains deferred and outside the execution critical path.
Symphony is closed at its recorded `NO-GO`; neither system is an active
implementation phase or prerequisite. Reopening either requires its existing
decision's reopen conditions and a new conversation-authorized task.

The AO project-level `autoMerge` setting remains disabled. The real accepted
merge mechanism is GitHub native per-pull-request auto-merge, requested only
after the exact-current-head CI, review, and unresolved-thread gates are freshly
read back. AO does not supply an always-on merge policy or a proven
negative-cancellation monitor.

## Closeout Readback

At the start of this closeout, local `HEAD`, local `main`, `origin/main`, and
GitHub `main` all resolved to clean merge commit
`2c228e9e65465e568551e4d36df67702cb7a85fe`, with no worktree changes.

AO's authoritative readback reported:

- daemon state `ready`, health `ok`, and `/readyz` readback `ready` on loopback
  port 3001;
- `ao doctor --json` with zero failures;
- the `calibration` project on default branch `main`, empty
  `trackerIntake`, and no project `autoMerge` setting;
- task-specific worker `calibration-30`, display name
  `operational-closeout`, active for this decision; and
- merged worker status for `calibration-1`, `calibration-3`,
  `calibration-8`, `calibration-9`, `calibration-14`, `calibration-18`,
  `calibration-27`, `calibration-28`, and `calibration-29`.

The recent delivery sequence is:

| PR | Merged result | AO ownership readback |
| --- | --- | --- |
| [#38](https://github.com/FuqingZh/calibration/pull/38) | AO-native delivery convergence, merge commit `bcf259b03f12b4096d635d60312e3f2cae5cfe59` | `calibration-27`, merged |
| [#39](https://github.com/FuqingZh/calibration/pull/39) | Default repository quality gate, merge commit `7f57e59a6c6718ec7c84001819056a8cc726bcf5` | No PR-to-session row remained in the AO readback; do not infer one |
| [#40](https://github.com/FuqingZh/calibration/pull/40) | AO host-context and Codex-home compatibility, merge commit `5d8f2b435f16822adf85348d1e5f2287831b4613` | `calibration-28`, merged |
| [#41](https://github.com/FuqingZh/calibration/pull/41) | High-signal Ruff baseline and low-risk native auto-merge policy, merge commit `2c228e9e65465e568551e4d36df67702cb7a85fe` | `calibration-29`, merged |

PR #37 remains the bounded GitHub native auto-merge happy-path evidence. GitHub
read the exact head `5e1627f063dc5238aeb6758b02cebf5282eb1892`,
successful required check, mergeability, draft state, and zero unresolved
threads before `gh pr merge 37 --auto --squash` was requested. It proves only
the already-green per-PR native path, not cancellation after later head, check,
or review changes.

PR #41 is an ordering deviation, not additional exact-head proof. The user's
instruction included the intended merge command inside Markdown backticks.
Command substitution executed that command before the rendered instruction
reached `calibration-29`: GitHub recorded the merge at
`2026-07-30T05:30:23Z`, and the worker received the instruction at
`2026-07-30T05:30:25Z`. The required check had passed and the existing five
threads were resolved, but the worker's fresh gate reads began only after the
merge, and the fresh review of head
`4c7add2c061bb513c248633b5b0525b6f5e3a590` arrived at
`2026-07-30T05:32:57Z`. Therefore PR #41 establishes the merged result and the
need to avoid executable command substitution in operational instructions; it
does not establish that every exact-current-head gate was read before merge.

## Maintenance Boundary

Maintenance work should remain proportional to a concrete repository need.
Documentation may record new current decisions without rewriting historical
evidence. Code, skills, evaluation behavior, installer behavior, AO services,
host configuration, credentials, and local Codex installation change only
under a separately authorized task with their owning validation.

This closeout does not retire the repository. It closes the implementation
program and leaves the accepted repository contracts, quality gate, evaluation
fixtures, skills, and AO delivery adapter available for ordinary maintenance.

## Reopen Conditions

Open a new implementation phase only when representative evidence or a concrete
maintenance task shows that the current stable surface is insufficient.
Reconsider this closeout if:

- repeated work needs coordination beyond task-specific workers;
- GitHub native per-PR auto-merge or the exact-head gate changes materially;
- AO project configuration, host compatibility, or continuation behavior
  changes;
- Linear or Symphony independently satisfies its recorded reopen conditions;
  or
- a code, skill, evaluation, installer, security, release, permission, secret,
  or compatibility change requires a new scoped decision.
