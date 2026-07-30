---
name: calibration
description: Use for substantive cross-project engineering judgment, non-local architecture or refactoring, public or compatibility-sensitive contracts, unclear validation, repository harnesses, agent or workflow evaluation, and durable engineering documentation. Ordinary local implementation with clear repository rules and executable feedback does not require this skill.
---

# Calibration

Calibrate each engineering decision against the most specific applicable source
of truth.

Apply direct user instructions first, then the most specific repository-local
rules, then shared defaults. Name any conflict that changes the outcome.

Prefer outcome constraints and executable feedback over prescribed
implementation steps. Within reversible repository-local boundaries, let the
agent choose and revise its path from current evidence. Do not require a plan,
specification, or approval stage merely because a task changes code.

## Baseline

Read `../../references/engineering/principles.md`.

## Route

Load only the routers required by the decisions at hand:

- naming: `../../references/engineering/naming/README.md`
- refactoring, debugging, verification, repository harnesses, and agent or
  workflow evaluation:
  `../../references/engineering/discipline/README.md`
- repository capability assessment, minimal adoption, and delivery feedback,
  including implementation-task intake for an already adopted orchestrator,
  setup discovery, pull-request validation, CI, agent review, cloud execution
  gaps, and repeated delivery failures:
  `../../references/engineering/discipline/harness.md`
- explicit AO onboarding, AO diagnosis, or AO-mediated pull-request delivery
  for an opted-in repository using an already installed Agent Orchestrator:
  `../../docs/runbooks/agent-orchestrator-review-continuation.md`
- architecture, module boundaries, interfaces, and abstraction:
  `../../references/engineering/design/README.md`
- long-form engineering specifications and document routing:
  `../../references/engineering/docs_index.md`

Do not load the AO guide merely because a repository is opted in. Ordinary
calibration engineering tasks remain on the engineering references above.

For a completion claim involving a public or cross-boundary contract, always
load `../../references/engineering/discipline/verification.md`.

If a routed reference is unavailable, continue from the baseline, name the
missing source, and do not invent its rules.

Suggest `$retrospect` when completed work reveals a failed assumption,
consequential rework, validation surprise, repeated pattern, or delivery risk
worth carrying forward.

## Completion

Complete only when the selected rules have been applied and every affected
public or cross-boundary contract has an explicit compatibility, verification,
and documentation decision supported by fresh evidence.
