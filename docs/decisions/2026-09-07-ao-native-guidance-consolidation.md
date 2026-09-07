# AO Native Guidance Consolidation

Status: implemented locally; static contract validation, no behavioral
improvement or deployed-AO equivalence claim.

## Decision

Use one calibration AO guide for adoption, single-writer ownership, activity
routing, release, and exceptional delivery decisions. Global instructions,
repository instructions, and the harness reference retain an early owned-work
protection and route to that guide before lifecycle actions. Missing guidance
or authority preserves owned state. Native `using-ao` and installed CLI help
own command mechanics; calibration does not duplicate the native catalog or
build a second feedback scheduler.

The checked upstream stable release is
[v0.12.12](https://github.com/Untrivial-ai/agent-orchestrator/releases/tag/v0.12.12),
commit `84fb37ce5aa947ceb9b19b0c2435b242ac92ce26`. At the audit, main was
`8845575a0c2171b1d30d26ad5d00ccbc293bae75`; its two additional commits changed
ACP diff statistics and frontend composition, not the audited AO boundaries.
The installed daemon version and real continuation loop were not checked or
changed by this cleanup. Older versions require capability discovery.

## Corrected Rules And Evidence

- Replace the REST-only exited-agent route with the supported native
  [`ao session resume-agent`](https://github.com/Untrivial-ai/agent-orchestrator/blob/84fb37ce5aa947ceb9b19b0c2435b242ac92ce26/backend/internal/cli/session.go#L268).
- Remove ready-for-review as a claim prerequisite. Upstream
  [claim logic](https://github.com/Untrivial-ai/agent-orchestrator/blob/84fb37ce5aa947ceb9b19b0c2435b242ac92ce26/backend/internal/service/session/claim_pr.go#L129)
  accepts open drafts and preserves their draft state. Quiescence, no-takeover,
  actual workspace/branch inspection, and fresh owner readback still apply.
- Retire instructions to keep the old project `autoMerge` setting disabled.
  The current typed
  [project configuration](https://github.com/Untrivial-ai/agent-orchestrator/blob/84fb37ce5aa947ceb9b19b0c2435b242ac92ce26/backend/internal/domain/projectconfig.go)
  has no such field. Exact-head and human authority gates remain applicable to
  actual merge operations, including native GitHub auto-merge.
- Route command help to the
  [embedded native skill](https://github.com/Untrivial-ai/agent-orchestrator/blob/84fb37ce5aa947ceb9b19b0c2435b242ac92ce26/backend/internal/skillassets/skillassets.go),
  which AO refreshes at daemon boot. Its availability is not merge authority.
- Delegate supported feedback and merge-completion mechanics to native
  [lifecycle reactions](https://github.com/Untrivial-ai/agent-orchestrator/blob/84fb37ce5aa947ceb9b19b0c2435b242ac92ce26/backend/internal/lifecycle/reactions.go).
  Keep configuration readback, incomplete delivery, dirty-worktree protection,
  bounded retry, and escalation rules in calibration.

Do not retire the remaining safety conditions. Native message guards distinguish
human delivery from unsolicited nudges. Claims do not prove other writers have
stopped or that a worktree changed branches. The current tmux teardown remains
[best-effort process reaping](https://github.com/Untrivial-ai/agent-orchestrator/blob/84fb37ce5aa947ceb9b19b0c2435b242ac92ce26/backend/internal/adapters/runtime/tmux/tmux.go#L499),
not proof of an empty OS-owned containment boundary.

## Archive And Active Surface

The exact pre-cleanup instructions are retained as historical plain-text
snapshots outside skill discovery and active reference routing:

- [Global template](../archive/ao-guidance-before-v0.12.12/global-agents.txt)
- [Repository instructions](../archive/ao-guidance-before-v0.12.12/repository-agents.txt)
- [Harness reference](../archive/ao-guidance-before-v0.12.12/harness.txt)
- [AO guide](../archive/ao-guidance-before-v0.12.12/ao-guide.txt)

These four active files shrink from 1,054 to 629 lines (40.3%). This measures
instruction volume, not model tokens, speed, or task success. No source in the
upstream AO repository, private host profile, adoption helper, or live worker
is modified. The managed personal global entry was refreshed after an exact match against
the rendered pre-cleanup template. Its original file and before/after hashes
were saved in the user-selected private temporary area, and the new rendering
was read back. No other skill entry was refreshed.

## Validation And Limits

Contract tests now check that entrypoints reach one canonical guide and that
its individual adoption, permission, ownership, release, merge, and retry
obligations remain present. They no longer require copies of the same long
state machine at every entrypoint. Historical canary and provenance tests remain.
A new behavioral prompt covers draft claim and native resume; it is evaluation
input, not executed behavior evidence.

Use installer tests and isolated dry-runs to verify rendering and preserved
installation contracts. Markdown links, skill portability, lint, and type checks
cover the changed static surfaces. No model A/B or live AO mutation is part of
this cleanup. The previously observed six sandbox integration failures in the
unmodified writable-agent evaluation runner remain a separate validation gap.

Final validation: 137 focused contract, installer, and skill-validator tests
passed. Both isolated installer dry-runs, lock consistency, lint, formatting,
type checks, Markdown links, skill validation, and diff checks passed. The full
repository run reported 546 passed and six failed, with 100% script coverage.
The six failures are the previously observed writable-agent sandbox integration
cases reporting a missing synthetic mount temporary directory `/output/tmp`;
the owning runner and those tests are unchanged. Full-gate success and live AO
behavior are not claimed.
