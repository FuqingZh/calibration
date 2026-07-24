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
  Sessions with Codex. A host worker is not the default for such work.
- Existing AO remains available only for host-coupled repositories and for
  review continuation that has been proven on the accepted host. This decision
  does not expand AO enrollment or its authority.
- GitHub rulesets own required checks and approval requirements. GitHub's
  native auto-merge owns the final merge action after those gates pass.
- The first pilot covers `calibration` and `biofetch` across five real pull
  requests. Every pilot pull request requires one approval from an independent
  human before merge.

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

Before counting the first pilot pull request, obtain fresh readback evidence
for all of the following:

1. `calibration` and `biofetch` are addressable from the intended Linear
   workspace without creating a separate Linear project for each repository.
2. Linear's native GitHub integration links a test or pilot issue to its pull
   request and projects pull-request status into the issue.
3. An explicitly delegated Linear Coding Session starts Codex against the
   intended repository and branch with sufficient repository instructions and
   a reproducible validation path.
4. Each repository's GitHub ruleset requires its declared checks and one
   independent human approval, with no actor or agent path that bypasses those
   requirements.
5. GitHub native auto-merge can be selected for an eligible pilot pull request
   and does not merge until the required checks and independent approval are
   satisfied.
6. AO remains unselected for cloud-reproducible pilot work and no repository
   is newly or bulk enrolled in AO.

For each of the five real pilot pull requests, retain evidence that:

1. a Linear issue recorded intent, human ownership, and explicit agent
   delegation;
2. the coding session and resulting pull request targeted the intended
   repository and branch;
3. repository-owned validation passed;
4. the native integration projected the pull-request state into Linear;
5. an independent human approved the final reviewed head;
6. required GitHub gates passed before native auto-merge merged the pull
   request; and
7. the merge result and final Linear status were read back from their owning
   systems.

A failed gate stops the affected pilot pull request from being counted. Record
the failure and choose either a bounded correction in the owning system or a
new decision; do not fill the gap with an MVP-excluded service.

## Fresh Verification Evidence

Reserved for dated readback and representative pilot evidence.

No fresh Linear or GitHub control-plane evidence has been supplied yet.
Therefore this record does **not** claim that the native GitHub integration,
Coding Sessions, repository rulesets, approval requirements, or native
auto-merge are currently enabled or correctly configured.

When evidence is available, append it here with the observation date, owning
surface, repository and pull-request or issue identifier, observed state, and
readback method. Keep acceptance evidence distinct from configuration plans or
screenshots that do not show the effective state.

## Consequences

- The pilot uses native systems as the source of truth and adds no parallel
  scheduler, database, or merge authority.
- Human responsibility remains explicit: delegation starts agent work, while
  an independent human approval remains a merge gate.
- Native auto-merge is mechanical execution after policy gates, not permission
  for an agent to approve or merge its own work.
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
