---
name: calibration
description: Use for substantive cross-project engineering judgment, non-local architecture or refactoring, public or compatibility-sensitive contracts, unclear validation, repository harnesses, or agent or workflow evaluation. Ordinary local implementation and repository prose with clear repository rules and executable feedback do not require this skill; cross-boundary contract documentation does.
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

Read `references/principles.md`.

## Route

Load only the routers required by the decisions at hand:

- naming: `references/naming/README.md`
- refactoring, debugging, verification, repository harnesses, and agent or
  workflow evaluation:
  `references/discipline/README.md`
- repository capability assessment, minimal adoption, repeated delivery
  failures, missing CI or review capability, cross-contract review feedback,
  review-convergence exhaustion, and delivery topology decisions:
  `references/discipline/harness.md`
- explicit AO onboarding, AO diagnosis, or AO-mediated pull-request delivery
  for an opted-in repository using an already installed Agent Orchestrator:
  `references/agent-orchestrator-review-continuation.md`
- architecture, module boundaries, interfaces, and abstraction:
  `references/design/README.md`
- cross-boundary contract documentation or long-form engineering specifications:
  `references/docs_index.md`
- task-level retrospectives and retrospective persistence: `$retrospect`

Do not load the AO guide merely because a repository is opted in. Ordinary
calibration engineering tasks remain on the engineering references above.

For ordinary GitHub mechanics, use focused installed skills when their triggers
apply: `github:gh-address-comments` for actionable pull-request feedback and
`github:gh-fix-ci` for failing GitHub Actions checks. If unavailable, use
repository- or platform-native tooling. These optional skills provide mechanics;
they do not grant write or scope authority, transfer AO ownership, or trigger
calibration merely by being present or absent.

For a completion claim involving a public or cross-boundary contract, always
load `references/discipline/verification.md`.

If a routed reference is unavailable, continue from the baseline, name the
missing source, and do not invent its rules.

Suggest `$retrospect` when completed work reveals a failed assumption,
consequential rework, validation surprise, repeated pattern, or delivery risk
worth carrying forward.

## Completion

Complete only when the selected rules have been applied and every affected
public or cross-boundary contract has an explicit compatibility, verification,
and documentation decision supported by fresh evidence.
