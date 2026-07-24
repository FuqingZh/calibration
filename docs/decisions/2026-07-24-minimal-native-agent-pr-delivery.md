# Minimal Native Agent Pull-Request Delivery

Date: 2026-07-24

Status: Accepted for a bounded pilot; GitHub gates verified, Linear gates pending

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
  AO only after fresh evidence passes every activation gate below.
- Existing AO remains required for host-coupled repositories, for review
  continuation proven on the accepted host, and as the fallback while any
  native activation gate is pending or failed. This decision does not expand
  AO enrollment or its authority.
- GitHub rulesets own required checks and approval requirements. GitHub's
  native auto-merge owns the final merge action after those gates pass. This
  record captures the user's 2026-07-24 acceptance as the bounded risk
  authorization to select native auto-merge only for pull requests explicitly
  enrolled in this five-pull-request pilot and only after fresh effective
  ruleset readback proves the gates below. Outside the pilot, merge and risk
  decisions remain with the user.
- The first active pilot repository is `seqevi`; `calibration` and `biofetch`
  remain later candidates across the same five-real-pull-request sample. Every
  pilot pull request requires one approval from an independent human before
  merge.
- Pull request #24 configures this policy. It used AO under the prior
  repository rule, is not enrolled in the pilot, must not have native
  auto-merge selected or be merged, and does not count toward the five pilot
  pull requests.

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
   `2026 Q3 Agent PR 闭环试点`; the active `seqevi` pilot and later repository
   candidates are addressable there without creating a separate Linear
   project for each repository.
2. Linear's native GitHub integration links a test or pilot issue to its pull
   request and projects pull-request status into the issue.
3. The target repository's effective GitHub ruleset requires its declared
   checks on a branch updated against the current base, resolution of all
   review threads, dismissal or invalidation of approvals when the approved
   head becomes stale, and one independent human approval, with no actor or
   agent path that bypasses those requirements.
4. GitHub native auto-merge is available to the enrolled pull request and
   cannot merge it until the required checks, unresolved-thread enforcement,
   current-base validation, stale-approval behavior, no-bypass policy, and
   independent approval requirements are satisfied.
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
| Required checks on the current base | Fail | The rulesets name `validate-skills` and `validate-biofetch`, but both report `strict_required_status_checks_policy: false`; without the MVP-excluded merge queue, neither requires an enrolled branch to be current before merge. |
| Unresolved-thread enforcement | Pass | Both applicable rulesets report `required_review_thread_resolution: true`. |
| One independent human approval | Fail | Both applicable rulesets report `required_approving_review_count: 0`. |
| Stale-approval behavior | Fail | Both report `dismiss_stale_reviews_on_push: false` and `require_last_push_approval: false`. |
| No bypass | Pass | Both applicable rulesets report `bypass_actors: []`. |
| Native auto-merge availability | Fail | Both repositories report `allow_auto_merge: false`. |
| Explicit five-PR enrollment before auto-merge | Pending | No pilot pull request was enrolled; pull request #24 is explicitly excluded. |

Because the current-base check, approval, stale-approval, and auto-merge gates
failed, the pilot is not ready to enroll its first pull request. No Linear or
GitHub control is claimed verified beyond the exact readbacks above. Future
evidence must record the observation date, owning surface, repository and
pull-request or issue identifier, observed state, and readback method. Keep
acceptance evidence distinct from configuration plans or screenshots that do
not show effective state.

### 2026-07-24 FUQ-8 Post-change Readback

At `2026-07-24T10:43:10+08:00`, reversible GitHub settings changes authorized
by FUQ-8 were complete and read back through repository, ruleset-detail, and
effective `main` branch-rule endpoints. The captured pre-change payloads were
retained before the sequential writes; no rollback was needed.

Successful check run ID `89173737622`, context `validate-skills`, check suite
ID `81271001424`, and successful check run ID `89373776787`, context
`validate-biofetch`, check suite ID `81449099637`, both identified their
producing GitHub App as ID `15368`, slug `github-actions`, name
`GitHub Actions`. That observed App ID, rather than a guessed value, was used
as each required check's `integration_id`.

`FuqingZh/calibration` read back default branch `main` and
`allow_auto_merge: true`. Active ruleset ID `19191911`, name
`default-branch-pr-gate`, retained target `branch`, condition
`include: ["~DEFAULT_BRANCH"]`, `exclude: []`, `bypass_actors: []`,
`deletion`, `non_fast_forward`, and allowed merge methods `merge`, `squash`,
and `rebase`. Its detail and effective `main` rules both reported:

- required context `validate-skills`, `integration_id: 15368`,
  `strict_required_status_checks_policy: true`, and
  `do_not_enforce_on_create: false`;
- `required_approving_review_count: 1`,
  `dismiss_stale_reviews_on_push: true`,
  `require_last_push_approval: false`,
  `required_review_thread_resolution: true`,
  `require_code_owner_review: false`, and `required_reviewers: []`.

`FuqingZh/biofetch` read back default branch `main` and
`allow_auto_merge: true`. Active ruleset ID `19191969`, also named
`default-branch-pr-gate`, retained the same enforcement, target, conditions,
bypass list, deletion and non-fast-forward rules, pull-request parameters, and
merge methods. Its detail and effective `main` rules reported required context
`validate-biofetch` bound to `integration_id: 15368`, with strict checks and
the same approval, stale-review, and conversation-resolution parameters.

Pull request #24 was separately read back at head
`bc6dec80cc9caa0d45876f2fdc46cfb3921ae174`, base
`a4a9a711fbfc50ee093242091af85074341480e9`, open and ready for review.
GitHub reported it `MERGEABLE` and `BLOCKED`; `validate-skills` check run ID
`89380197932` was `success`. Three then-current review threads remained open.
`autoMergeRequest` was `null`. Pull request #24 remained excluded, was not
enrolled, did not have auto-merge selected, and was not merged.

#### Post-change Gate Result

| Gate | Result | Evidence |
| --- | --- | --- |
| Shared Linear project and repository scope | Pass | The prior dated readback remains the current evidence. |
| Native issue-to-pull-request status projection | Pending | No automatic projection has been observed; the FUQ-6 setup writes are not proof. |
| Linear Coding Session delegation and native routing | Pending | No Coding Session has been delegated, so AO remains the active fallback and no pilot pull request is enrolled. |
| Required checks on the current base | Pass | Both effective rulesets require strict checks bound to observed GitHub Actions App ID `15368`. |
| Unresolved-thread enforcement | Pass | Both effective rulesets report `required_review_thread_resolution: true`. |
| One independent human approval | Pass | Both effective rulesets report `required_approving_review_count: 1`. |
| Stale-approval behavior | Pass | Both effective rulesets report `dismiss_stale_reviews_on_push: true`. |
| No bypass | Pass | Both effective rulesets report `bypass_actors: []`. |
| Native auto-merge availability | Pass | Both repositories report `allow_auto_merge: true`. |
| Explicit five-PR enrollment before auto-merge | Pending | No counted pilot pull request is enrolled; pull request #24 remains excluded. |

GitHub configuration gates now pass exactly as read back above. Native Linear
projection and Coding Session delegation remain pending, so native routing is
not active, no pull request is enrolled or counted, and AO remains the proven
fallback. This evidence does not claim those pending Linear gates.

### 2026-07-24 `seqevi` First-Pilot Preflight

The user selected the actively developed private repository
[`FuqingZh/seqevi`](https://github.com/FuqingZh/seqevi) as the first pilot
repository. Linear project `2026 Q3 Agent PR 闭环试点` was updated to make
`seqevi` the active repository while retaining `calibration` and `biofetch` as
later candidates. Linear issue
[`FUQ-9`](https://linear.app/fuqingzhang/issue/FUQ-9/以-seqevi-完成第-1-个原生-agent-pr-闭环样本)
records the first-sample intent, human owner, repository links, candidate
task, admission gates, and explicit `0/5` count.

Fresh local inspection found that `seqevi`'s `main` was twelve commits ahead
of `origin/main` and contained an uncommitted execution-profile contract,
implementation, documentation, and tests. The repository-owned
`pdm run check` completed successfully across formatting, Ruff, Pyright, and
123 collected tests. That evidence establishes a healthy local baseline, but
the dirty local tree is not visible to a Linear Coding Session. Existing pull
request
[`seqevi#1`](https://github.com/FuqingZh/seqevi/pull/1) ends before the local
InterPro parity and execution-profile work, so neither that pull request nor
the local baseline is retroactively counted as a native pilot sample.

The first candidate sample is therefore a separate repository-local Stage 2
profile authoring or inspection increment after the current execution-profile
baseline reaches a GitHub branch that a cloud session can clone. It must not
depend on the accepted host's external annotation databases, 217-node runtime,
or uncommitted files.

GitHub repository and ruleset detail were read back after configuration:

- `allow_auto_merge: true`; no pull request has an `autoMergeRequest`;
- active ruleset ID `19322798`, `default-branch-pr-gate`, applies to
  `~DEFAULT_BRANCH` with `bypass_actors: []`;
- required contexts `test (3.12)` and `test (3.13)` are bound to the observed
  GitHub Actions App `integration_id: 15368`;
- `strict_required_status_checks_policy: true`;
- `required_approving_review_count: 1`;
- `dismiss_stale_reviews_on_push: true`; and
- `required_review_thread_resolution: true`.

Existing `seqevi` pull request #1 remained open, ready for review, mergeable,
and `BLOCKED`, with successful existing check runs, no approval, and no
auto-merge request. It was not modified, enrolled, or merged. Linear Coding
Session delegation and native pull-request status projection remain pending
until the GitHub-visible baseline admission gate passes, so the pilot count
remains `0/5`.

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
