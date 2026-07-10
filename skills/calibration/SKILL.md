---
name: calibration
description: Use for cross-project engineering decisions about coding, refactoring, architecture, interfaces, naming, APIs, CLIs, schemas, testing, validation, and durable documentation.
---

# Calibration

Calibrate each engineering decision against the most specific applicable source
of truth.

Apply direct user instructions first, then the most specific repository-local
rules, then shared defaults; note any conflict that changes the outcome.

## Route

Read `../../references/engineering/principles.md` as the shared baseline.

Load only the routers required by the decisions at hand:

- naming decisions:
  `../../references/engineering/naming/README.md`
- refactoring, debugging, and verification:
  `../../references/engineering/discipline/README.md`
- architecture, module boundaries, interfaces, and abstraction:
  `../../references/engineering/design/README.md`
- long-form engineering specifications and document routing:
  `../../references/engineering/docs_index.md`

If a routed reference is unavailable, continue only from the shared baseline,
name the missing source, and do not invent its rules.

Suggest `$retrospect` when completed work reveals a failed assumption,
consequential rework, validation surprise, repeated pattern, or delivery risk
worth carrying forward.

Complete only when the selected rules have been applied and every affected
public or cross-boundary contract has an explicit compatibility, verification,
and documentation decision.
