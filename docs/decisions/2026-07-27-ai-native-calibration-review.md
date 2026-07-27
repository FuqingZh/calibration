# AI-Native Calibration Review

Version: v1.1
Date: 2026-07-27
Status: accepted direction; candidate regression-accepted by
`2026-07-27-ai-native-calibration-evaluation-closeout.md`

## Decision

Keep calibration's evidence, compatibility, and verification discipline, but
reduce its intervention in ordinary repository-local implementation.

The next baseline should:

1. prefer outcome constraints and executable feedback over prescribed
   implementation steps;
2. let agents choose and revise execution paths within reversible
   repository-local boundaries;
3. reserve calibration's default trigger for substantive cross-project
   judgment, non-local design, public or compatibility-sensitive contracts,
   unclear validation, harness and evaluation work, and durable engineering
   documentation; and
4. evaluate lightweight autonomous work explicitly rather than measuring only
   whether agents reject excessive process.

This is a bounded behavior change. It does not weaken repository-local
instructions, compatibility requirements, verification, permission boundaries,
or human authority over product intent and risk.

## Evidence Reviewed

The review inspected the current:

- global `AGENTS.md` template and `$calibration` trigger;
- calibration principles and routed engineering references;
- repository harness, verification, and evaluation disciplines;
- implementation-plan document contract;
- calibration behavioral prompt set;
- repository quality gate and current documentation entrypoint; and
- accepted and rejected harness evaluation closeouts summarized by
  `docs/README.md`.

The current guidance already contains strong proportionality:

- do not default to more prompt text;
- add the smallest capability that addresses an observed gap;
- stop when the feedback loop is adequate;
- escalate only decisions requiring human authority;
- persist implementation plans only when explicitly requested or required by a
  repository workflow; and
- require representative evidence before claiming a workflow improvement.

The issue is therefore not primarily incorrect engineering guidance. It is the
frequency and shape of its intervention.

## Findings

### F1: The default trigger is broader than the judgment surface

The global template currently invokes calibration before nearly every
substantive coding, refactoring, interface, testing, validation, or
documentation change. A small reversible edit with clear repository rules and
an executable test loop therefore pays the same routing entry cost as a
cross-project architecture or compatibility decision.

The skill itself is compact and routes references selectively, but the broad
trigger still makes calibration an obligatory process layer. The trigger
should instead follow the presence of substantive engineering judgment or a
feedback gap.

### F2: Outcome autonomy is implied but not stated as a baseline

Harness guidance says not to ask users for discoverable facts and to escalate
only material decisions. It also prefers tests, tools, and observable artifacts
over instructions. These rules imply local autonomy, but no baseline principle
explicitly authorizes an agent to choose and revise its implementation path
from current evidence.

Without that positive rule, an agent can correctly avoid asking questions yet
still overproduce plans, preserve a disproven approach, or wait for unnecessary
step-level approval.

### F3: Evaluation covers restraint better than autonomous execution

The behavioral cases cover local authority, proportional harness adoption,
placement of repeated operations, human escalation, evaluation integrity, and
orchestrator gates. They are strong tests of whether an agent refuses excess
process.

They do not directly test whether an agent:

- starts a clear, reversible local task without a specification or plan;
- abandons an early plan when runtime evidence disproves it; or
- completes a bounded repair without unnecessary human confirmation.

The evaluation surface should include those behaviors before claiming that
lighter calibration improves engineering outcomes.

### F4: Some process-heavy surfaces remain intentionally unchanged

The implementation-plan contract is deliberately decision-complete, and the
documentation entrypoint carries substantial historical state. The AO runbook
also remains reachable from the calibration route on the accepted host.

These may warrant later simplification, but changing them now would mix
independent concerns into the trigger and autonomy correction. This review
therefore records them as follow-up candidates rather than modifying them.

## Accepted Changes

### C1: Add outcome autonomy to shared principles

The baseline should prefer outcomes, invariants, boundaries, and executable
acceptance feedback over prescribed steps. Plans are working hypotheses;
repository and runtime evidence can revise them.

Durable process artifacts remain justified by coordination, risk,
interruption, or repeated failure, not by the mere presence of code changes.

### C2: Narrow the default calibration entry

The global template and skill metadata should distinguish ordinary local
implementation from substantive engineering judgment.

Ordinary local implementation proceeds directly from repository authority and
executable feedback. Calibration remains available explicitly and may still be
invoked implicitly for its narrower judgment surface.

### C3: Add a lightweight autonomy evaluation slice

Behavioral prompts should cover:

- a reversible local edit with clear repository tests;
- runtime evidence invalidating an existing plan; and
- a bounded repair that does not need step-level human approval.

Adding parseable cases defines the evaluation surface. Static validation alone
does not prove an improvement; a later representative model-backed comparison
is required for that claim.

The comparison is now complete. It supports regression acceptance but not
comparative improvement; see
`2026-07-27-ai-native-calibration-evaluation-closeout.md`.

## Compatibility And Risks

- Existing repository-local `AGENTS.md` requirements continue to override the
  shared default.
- Public and cross-boundary changes still require compatibility and final
  contract verification.
- Explicit user requests for plans or staged approval still apply when they
  express a real desired artifact or risk boundary.
- A narrower trigger may cause calibration not to load when a seemingly local
  task hides a public boundary. The retained public-contract, unclear-
  validation, and non-local-change triggers limit this risk.
- The new behavioral cases are specifications, not measured evidence. No claim
  of improved model behavior is made by this change alone.

## Reopen Conditions

Revisit this decision when representative evaluation shows that the narrower
trigger:

- misses compatibility-sensitive decisions;
- causes material regressions in repository-rule compliance or verification;
- does not reduce unnecessary planning, context, or human confirmation; or
- requires a different division between calibration and repository-local
  authority.

Separately consider a successor only when evidence supports simplifying the
implementation-plan contract, current documentation route, or host-specific AO
integration.
