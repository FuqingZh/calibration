# Linear projection and explicit Agent dispatch

Date: 2026-07-29

Status: Accepted for staged implementation

## Decision

Linear is the human-facing workbench, intent surface, and progress projection.
It is not an AO scheduler.

AO remains the only execution controller for worker sessions, retries,
pull-request observation, review continuation, and termination. Models execute
inside an AO-authorized run; they do not authorize new runs.

The only accepted Linear-originated dispatch signal is a new Linear
AgentSession created by an explicit delegation or an explicitly supported
agent mention. Issue state, labels, assignee changes, attachments, pull-request
links, and GitHub merge events never authorize AO session creation.

A thin bridge may translate the signed AgentSession event into one existing AO
session-spawn request and project AO results back into Linear. The bridge owns
authentication, authorization, delivery deduplication, and the durable mapping
between a Linear AgentSession and an AO session. It does not own scheduling,
worker retry, pull-request lifecycle, or model behavior.

## Evidence that changed the design

The three-scenario state-driven acceptance plan failed at its central boundary.
The relevant FUQ-23 sequence was:

| UTC timestamp | Evidence |
| --- | --- |
| `2026-07-29 02:08:26` | `calibration-23` was terminated after FUQ-23 became Canceled. |
| `2026-07-29 02:17:03` | Pull request 34 merged. |
| `2026-07-29 02:17:05.883` | Linear history recorded FUQ-23 moving from Canceled to In Progress under the FuQing Zhang actor; `autoClosed` was absent. |
| `2026-07-29 02:17:18.346` | AO created `calibration-24` for the same canonical Linear issue. |
| `2026-07-29 02:18:02.556` | Linear history recorded FUQ-23 moving back to Canceled. |
| `2026-07-29 02:18:21` | `calibration-24` terminated. |

The deployed intake implementation treated every nonterminal Linear state as
eligible and deduplicated only against nonterminated sessions. Once
`calibration-23` terminated, a later active state was indistinguishable from a
newly authorized run.

This was not only an integration-rule defect. The architecture overloaded one
presentation field with two meanings:

- current work status; and
- permission to allocate an execution worker.

No Linear/GitHub closing-link configuration can make that overloaded contract
safe. A non-closing reference avoids one automatic completion transition, but
it cannot prove that every future active state is a deliberate AO dispatch.

## Ownership

| Owner | Responsibility |
| --- | --- |
| Linear | Human issue record, explicit Agent delegation/mention, AgentSession UI, and projected progress. |
| Linear Agent bridge | Verify signed events, enforce allowlists, deduplicate deliveries, map one AgentSession to one AO session, and project AO facts. |
| AO | Create and supervise sessions, execute repository work, observe PR/CI/review state, continue the owning worker, and terminate runs. |
| Model | Plan and execute inside the authority and permissions of one AO run. |
| User | Product intent, dispatch, cancellation, merge, and risk authority. |

## Command and projection contracts

### Inbound commands

Version 1 accepts only:

- a new AgentSession created by delegation to the installed private AO Agent;
  and
- an AgentSession created by the exact supported dispatch mention contract
  after that payload has been verified against a real Developer Preview event.

Ordinary `Issue`, label, attachment, state, assignee, and GitHub integration
webhooks are not dispatch inputs. Cancellation and retry remain AO commands in
version 1. Adding Linear-side control commands requires a separate accepted
contract and cannot be inferred from issue state.

### Outbound projection

The bridge may project these verified AO facts:

| AO fact | Linear projection |
| --- | --- |
| Session created | AgentSession acknowledgement, AO session identity, and configured In Progress state |
| Pull request ready | PR external URL and configured In Review state |
| Recoverable worker retry | AgentSession activity; no new Linear dispatch generation |
| Pull request merged and AO completion accepted | configured Done state |
| Explicit AO cancellation | configured Canceled state |
| Unrecoverable run failure | AgentSession failure activity and configured blocked state when available |

Linear workflow states are configured by UUID. Display names are not protocol
identifiers.

## Idempotency and generations

- Linear delivery UUID is the transport deduplication key.
- Linear AgentSession ID is the dispatch idempotency key.
- One AgentSession maps to at most one AO session creation result.
- A repeated or retried webhook returns the existing mapping.
- A second AgentSession for an issue with an active AO run returns the active
  mapping instead of creating another worker.
- After a terminal run, only a new AgentSession may create a new generation.
- Issue state changes never increment a generation.

The bridge stores mappings and applied projection effects. This is an
integration ledger, not a scheduler. AO remains authoritative for live session
state and retry behavior.

## Security boundary

- The public endpoint exposes only the Linear Agent webhook route.
- Every request verifies Linear's HMAC signature and timestamp before parsing
  an action.
- Team, app actor, and AO project mappings are allowlisted.
- AO remains loopback-only and is never reverse-proxied directly.
- Linear OAuth and webhook secrets belong only to the bridge service and must
  not enter the AO daemon or worker environment.
- The bridge acknowledges a valid AgentSession promptly and performs AO work
  asynchronously.
- The bridge uses the existing AO HTTP contract; it does not read or write
  AO's SQLite database.

Linear's Agent APIs are a Developer Preview. Payload fixtures, compatibility
tests, and a kill switch are required before live dispatch.

## Compatibility and retirement

The current `trackerIntake` configuration remains disabled throughout the
migration. The fork-only Linear tracker adapter and its daemon credential are
retained until the new bridge passes a real canary, then removed in a separate
reviewable change. GitHub review continuation and upstream AO session behavior
remain unchanged.

The old Symphony workflow-run scheduler has already been removed by the
upstream-first v0.11 convergence. It is not restored by this design.

## Consequences

- A transient or manual Linear status change cannot create a worker.
- An explicit re-delegation can intentionally create a new run generation.
- Linear stays useful as the visible workbench without becoming the execution
  control plane.
- The only new maintained code is the protocol boundary that no third party can
  define for this deployment: authorization, idempotency, AO mapping, and
  projection policy.
- Live rollout depends on a user-configured private Linear Agent application
  and a controlled public HTTPS endpoint.

## References

- [Linear Agents developer preview](https://linear.app/developers/agents)
- [Linear Agent interaction](https://linear.app/developers/agent-interaction)
- [Linear webhook security](https://linear.app/developers/webhooks)
- [Linear agents user documentation](https://linear.app/docs/agents-in-linear)
- [Explicit Agent command bridge implementation plan](../implementation-plan/20260729-v2.1-linear-agent-command-bridge-implementation-plan.md)
