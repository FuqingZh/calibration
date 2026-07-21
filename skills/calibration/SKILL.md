---
name: calibration
description: Use for cross-project engineering decisions about coding, refactoring, architecture, interfaces, naming, APIs, CLIs, schemas, testing, validation, repository harnesses, agent or workflow evaluation, and durable documentation.
---

# Calibration

Calibrate each engineering decision against the most specific applicable source
of truth.

Apply direct user instructions first, then the most specific repository-local
rules, then shared defaults. Name any conflict that changes the outcome.

## Baseline

Read `../../references/engineering/principles.md`.

## Route

Load only the routers required by the decisions at hand:

- naming: `../../references/engineering/naming/README.md`
- refactoring, debugging, verification, repository harnesses, and agent or
  workflow evaluation:
  `../../references/engineering/discipline/README.md`
- repository capability assessment, minimal adoption, and delivery feedback,
  including setup discovery, pull-request validation, CI, agent review, cloud
  execution gaps, and repeated delivery failures:
  `../../references/engineering/discipline/harness.md`
- architecture, module boundaries, interfaces, and abstraction:
  `../../references/engineering/design/README.md`
- long-form engineering specifications and document routing:
  `../../references/engineering/docs_index.md`

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
