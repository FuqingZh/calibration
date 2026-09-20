# Principles

## Problem Framing

Correct a false constraint, abstraction, or requirement when it materially
changes the solution.

## Outcome Autonomy And Feedback

- Work from outcomes, invariants, and acceptance evidence. Within authorized,
  reversible local work, choose and revise the path when current evidence
  disproves an assumption or plan.
- State the completion claim and affected seam, then select the smallest
  repository-owned check that can falsify it. Broaden for a repository mandate
  or an uncovered obligation; report unchecked boundaries and residual risk.
- Add plans, specifications, or approval stages only when coordination, risk,
  interruption, or repeated failure warrants them. A code change alone does
  not require these stages or renewed approval for already-authorized work.

## Native Abstractions and Data Flow

- Prefer established domain parsers, writers, and bulk or vectorized APIs over
  reimplementing their operations.
- Keep related information together. Split, convert, or materialize data only
  at an algorithm or consumer boundary that requires it.
- For fast-moving libraries, verify the installed version and applicable API
  through source, documentation, or a small executable example.

## Configuration and Defaults

- Put technical defaults in explicit configuration structures rather than
  scattering them through orchestration logic.
- Validate extensible configuration by the invariants a consumer requires,
  not by exact equality with the smallest known document. Preserve tolerated
  metadata and extension keys unless the owning contract requires a rewrite.
- Put product and style preferences in caller-facing configuration or
  project-level documentation.
- Give every magic threshold a named constant, an applicability rationale, and
  an override path.
- When no local rule, caller value, compatibility contract, or domain
  requirement specifies a random seed, use `42` as the fallback.
- Treat `42` as a reproducibility default, not a rewrite target. Expose a seed
  when it materially affects reproducibility or public behavior.
- Prefer explicit configuration files over hidden runtime assumptions.

## Project Knowledge

- Treat memory and conversation as leads rather than current authority. Resolve
  discoverable facts from the repository, environment, documentation, and
  tools; escalate product intent, tradeoffs, and risk decisions that require
  human authority.
- Keep long-lived architecture, contracts, plans, test plans, and benchmark
  records in project `docs/`.
- Keep task-level execution retrospectives, judgment errors, and short-lived
  observations in project `.traces/`.
- Use reconstructable git history, session logs, test artifacts, and product
  logs as raw process evidence. Use `.traces/evidence/` only when the evidence
  cannot be reconstructed, and keep it out of git by default.
- Promote repeatedly validated trace observations into project documentation,
  repository instructions, or calibration.
- Turn repeated project operations into repository-owned scripts or tools.
  Turn mechanically decidable invariants into tests, lint, schema checks, or
  CI instead of accumulating reminders.

## Performance and Measurement

Keep reproducible benchmarks with explicit inputs, environment, and scale;
validate outputs as well as runtime.

## Communication

Lead with the conclusion and give the rationale and evidence needed to assess
it, material uncertainty and risk with their impact, and any next action.
Remove repeated background and boilerplate; keep decision rationale concise.
