# Minimal Native Agent Pull-Request Delivery

Date: 2026-07-24

Status: Accepted for a bounded pilot; external settings not yet verified

## Context

The repository delivery loop and the later AO continuation canary proved that
an agent can implement, validate, review, and deliver a pull request without a
new general-purpose orchestration system. They did not establish that AO
should become the default intake or delivery layer for repositories whose work
is reproducible in a cloud coding environment.

The smallest next step is to use the native ownership boundaries already
present in Linear, Linear Coding Sessions, Codex, and GitHub. The pilot must
separate the accepted design from external control-plane state: this record
does not prove that any required Linear or GitHub setting is enabled.

## Decision

- Linear owns work intent, the human assignee, and explicit delegation to an
  agent.
- Linear's native GitHub integration owns projection of issue-to-pull-request
  status back into Linear.
- Work that is reproducible in a cloud environment should prefer Linear Coding
  Sessions with Codex. Work explicitly enrolled in the Linear project
  `2026 Q3 Agent PR 闭环试点` uses that native path without starting or claiming
  AO. A host worker is not the default for such work.
- Existing AO remains available only for host-coupled repositories and for
  review continuation that has been proven on the accepted host. This decision
  does not expand AO enrollment or its authority.
- GitHub rulesets own required checks and approval requirements. GitHub's
  native auto-merge owns the final merge action after those gates pass. This
  record captures the user's 2026-07-24 acceptance as the bounded risk
  authorization to select native auto-merge only for pull requests explicitly
  enrolled in this five-pull-request pilot and only after fresh effective
  ruleset readback proves the gates below. Outside the pilot, merge and risk
  decisions remain with the user.
- The first pilot covers `calibration` and `biofetch` across five real pull
  requests. Every pilot pull request requires one approval from an independent
  human before merge.
- Pull request #24 configures this policy. It used AO under the prior
  repository rule, is not enrolled in the pilot, must not have native
  auto-merge enabled or selected during this smoke, and does not count toward
  the five pilot pull requests.

## MVP Boundaries

The MVP includes no:

- custom pull-request babysitter;
- webhook service or state database;
- Symphony or Loops deployment;
- merge queue;
- zero-human merge;
- per-repository Linear project; or
- bulk AO enrollment.

These exclusions are part of the accepted minimum, not deferred
implementation tasks. A later proposal needs evidence from the pilot before it
can add one of these surfaces.

## Ownership

| Capability | Owner |
| --- | --- |
| Intent, human assignment, and agent delegation | Linear |
| Coding session for cloud-reproducible work | Linear Coding Sessions and Codex |
| Issue-to-pull-request status projection | Linear native GitHub integration |
| Repository validation and required merge gates | repository and GitHub rulesets |
| Independent approval | human reviewer |
| Gate-satisfied merge action | GitHub native auto-merge |
| Proven host-coupled execution or review continuation | existing AO service |

## Smoke Gates

Before enrolling each pilot pull request, obtain fresh effective readback
evidence for all of the following:

1. The intended work is explicitly enrolled in the shared Linear project
   `2026 Q3 Agent PR 闭环试点`; `calibration` and `biofetch` are addressable
   there without creating a separate Linear project for each repository.
2. Linear's native GitHub integration links a test or pilot issue to its pull
   request and projects pull-request status into the issue.
3. The target repository's effective GitHub ruleset requires its declared
   checks, resolution of all review threads, dismissal or invalidation of
   approvals when the approved head becomes stale, and one independent human
   approval, with no actor or agent path that bypasses those requirements.
4. GitHub native auto-merge is available to the enrolled pull request and
   cannot merge it until the required checks, unresolved-thread enforcement,
   stale-approval behavior, no-bypass policy, and independent approval
   requirements are satisfied.
5. The pull request is explicitly identified as one of the five pilot pull
   requests before auto-merge is selected.

For each of the five real pilot pull requests, retain evidence that:

1. a Linear issue recorded intent, human ownership, and explicit agent
   delegation;
2. an explicitly delegated Linear Coding Session started Codex against the
   intended repository and isolated task branch without starting or claiming
   an AO worker;
3. the resulting pull request targeted the intended repository and branch;
4. repository-owned validation passed;
5. the native integration projected the pull-request state into Linear;
6. all review threads were resolved, any approval on a stale head was
   dismissed or invalidated, no bypass was used, and an independent human
   approved the final reviewed head;
7. required GitHub gates passed before native auto-merge merged the pull
   request; and
8. the merge result and final Linear status were read back from their owning
   systems.

A failed gate stops the affected pilot pull request from being counted. Record
the failure and choose either a bounded correction in the owning system or a
new decision; do not fill the gap with an MVP-excluded service.

## Fresh Verification Evidence

### 2026-07-24 Setup Smoke

GitHub was read through read-only `gh api` repository, ruleset, effective
branch-rule, pull-request, check-run, and GraphQL review-thread queries at
`2026-07-24T09:39:58+08:00`.

#### Linear Readback

- The one shared project `2026 Q3 Agent PR 闭环试点`, ID
  `f3dcf706-6df3-479c-8dd2-0592300370a5`, was confirmed `In Progress`, `High`,
  on team `FuqingZh`, spanning `calibration` and `biofetch`.
- `FUQ-6` was `In Review`, assigned to the user, and had pull request #24
  attached. The pull-request body contained `Refs FUQ-6`. `FUQ-7` and `FUQ-8`
  were `Todo` and assigned to the user.
- The `FUQ-6` status and pull-request attachment were written explicitly
  during setup. They do not prove automatic status or attachment projection by
  Linear's native GitHub integration.
- No Linear Coding Session was delegated during this smoke.
- The old observation project, ID
  `b2043b72-183a-4896-a01a-93802ce63a27`, was confirmed `Canceled` with
  `canceledAt` `2026-07-24T01:38:07.935Z`; `FUQ-1` through `FUQ-5` were each
  confirmed `Canceled`.

#### GitHub Effective Readback

`FuqingZh/calibration` reported default branch `main` and
`allow_auto_merge: false`. Its only repository ruleset applicable to `main`
was active branch ruleset ID `19191911`, name `default-branch-pr-gate`, with
condition `include: ["~DEFAULT_BRANCH"]`, `exclude: []`, and
`bypass_actors: []`. Its effective rules were:

- `required_status_checks`: context `validate-skills`,
  `strict_required_status_checks_policy: false`, and
  `do_not_enforce_on_create: false`;
- `pull_request`: `required_approving_review_count: 0`,
  `dismiss_stale_reviews_on_push: false`,
  `require_last_push_approval: false`,
  `required_review_thread_resolution: true`,
  `require_code_owner_review: false`, `required_reviewers: []`, and merge
  methods `merge`, `squash`, and `rebase`;
- `deletion` and `non_fast_forward`.

`FuqingZh/biofetch` reported default branch `main` and
`allow_auto_merge: false`. Its only repository ruleset applicable to `main`
was active branch ruleset ID `19191969`, name `default-branch-pr-gate`, with
condition `include: ["~DEFAULT_BRANCH"]`, `exclude: []`, and
`bypass_actors: []`. Its effective rules matched `calibration` except that the
required status-check context was `validate-biofetch`.

The ruleset responses exposed conversation resolution and stale-review
settings as the values above. They did not expose a separate stale-approval
field beyond `dismiss_stale_reviews_on_push` and
`require_last_push_approval`, or an app/integration binding for either required
status-check context; those additional properties were unobservable in this
readback.

Pull request #24 was open and ready for review, targeting `main` at base
`a4a9a711fbfc50ee093242091af85074341480e9` from head
`01a2938574381e594159e1553be70a6f125d60ed` on
`codex/docs/calibration-native-agent-pr-pilot`. GitHub reported it
`MERGEABLE` with merge state `CLEAN`. Check run ID `89378145562`,
`validate-skills`, completed `success`. All four review threads were resolved
and outdated. `auto_merge` and `autoMergeRequest` were both `null`.

Pull request #24 remains excluded from the pilot because it was created under
the previous AO rule. It was not enrolled, auto-merge was not enabled or
selected, and it was not merged during this smoke.

#### Gate Result

| Gate | Result | Evidence |
| --- | --- | --- |
| Shared Linear project and repository scope | Pass | The named project, ID, state, priority, team, and both-repository scope were read back. |
| Native issue-to-pull-request status projection | Pending | `FUQ-6` status and attachment were explicit setup writes, not an observed automatic projection. |
| Linear Coding Session delegation and native routing | Pending | No Coding Session was delegated; no pilot pull request was enrolled. |
| Required repository status checks | Pass | The applicable active rulesets require `validate-skills` and `validate-biofetch`, respectively. |
| Unresolved-thread enforcement | Pass | Both applicable rulesets report `required_review_thread_resolution: true`. |
| One independent human approval | Fail | Both applicable rulesets report `required_approving_review_count: 0`. |
| Stale-approval behavior | Fail | Both report `dismiss_stale_reviews_on_push: false` and `require_last_push_approval: false`. |
| No bypass | Pass | Both applicable rulesets report `bypass_actors: []`. |
| Native auto-merge availability | Fail | Both repositories report `allow_auto_merge: false`. |
| Explicit five-PR enrollment before auto-merge | Pending | No pilot pull request was enrolled; pull request #24 is explicitly excluded. |

Because the approval, stale-approval, and auto-merge gates failed, the pilot is
not ready to enroll its first pull request. No Linear or GitHub control is
claimed verified beyond the exact readbacks above. Future evidence must record
the observation date, owning surface, repository and pull-request or issue
identifier, observed state, and readback method. Keep acceptance evidence
distinct from configuration plans or screenshots that do not show effective
state.

## Consequences

- The pilot uses native systems as the source of truth and adds no parallel
  scheduler, database, or merge authority.
- Human responsibility remains explicit: delegation starts agent work, while
  an independent human approval remains a merge gate.
- Native auto-merge is mechanical execution after policy gates, not permission
  for an agent to approve or merge its own work.
- Outside an explicitly enrolled pilot pull request, merge remains a user
  decision.
- AO remains a narrow exception for topology already shown to need it, rather
  than the standard route for new repositories.
- The five-pull-request sample is evidence for deciding whether this boundary
  is sufficient; it is not evidence for unattended or organization-wide
  rollout.

## Reopen Conditions

Revisit this decision after the five-pull-request pilot, or earlier if fresh
evidence shows that a native owner cannot satisfy a smoke gate, a repository
cannot be reproduced in the cloud, review continuation repeatedly requires a
host-coupled worker, or the independent human approval policy needs to change.
Any proposal for an excluded MVP component requires a concrete observed gap
and a separate risk decision.
