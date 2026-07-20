# Principles

These are the cross-project defaults that remain useful across engineering
topics.

## Problem Framing

- Challenge a false constraint, wrong abstraction, or pseudo-requirement when
  it materially changes the solution.
- Prefer a corrected problem statement over a polished solution to the wrong
  problem.

## Native Abstractions and Data Flow

- Prefer the installed domain library's native bulk abstractions over
  handwritten loops or ad hoc intermediate state.
- For tabular data, prefer DataFrame or query-expression APIs for projection,
  grouping, window calculation, joining, reshaping, and column-wise transforms.
- For arrays and numerical work, prefer vectorized or batched APIs from the
  numerical or statistical library that owns the operation.
- For graph, text, sequence, Excel, Parquet, JSON, and similar structured
  domains, use stable parser, writer, graph, or domain-model APIs instead of
  manual string splitting or reimplementing core algorithms.
- Keep information on one appropriate structure when it naturally belongs
  there. Split, pivot, rejoin, or materialize parallel state only when a
  boundary or algorithm requires it.
- Convert to lower-level forms such as lists, dictionaries, NumPy arrays,
  pandas frames, or temporary files at explicit boundaries, close to the caller
  that requires the conversion.
- For fast-moving libraries, inspect the installed version, available API,
  source, or a small executable example before relying on remembered idioms.

## Configuration and Defaults

- Put technical defaults in explicit configuration structures rather than
  scattering them through orchestration logic.
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

- Keep long-lived architecture, contracts, plans, test plans, and benchmark
  records in project `docs/`.
- Keep task-level execution retrospectives, judgment errors, and short-lived
  observations in project `.traces/`.
- Use reconstructable git history, session logs, test artifacts, and product
  logs as raw process evidence. Use `.traces/evidence/` only when the evidence
  cannot be reconstructed, and keep it out of git by default.
- Promote repeatedly validated trace observations into project documentation,
  repository instructions, or calibration.

## Performance and Measurement

- Measure against explicit inputs, environments, and scale.
- Validate outputs as well as runtime.
- Keep benchmarks as reproducible artifacts rather than isolated headline
  numbers.

## Communication

- Lead with the conclusion or preferred option.
- Include the evidence checked and enough rationale to audit the decision.
- State material assumptions, uncertainty, and residual risk with their impact.
- Give the next action when one remains.
- Remove repeated background, low-information process narration, slogans, and
  boilerplate before removing decision evidence.
- Provide concise decision rationale rather than private chain-of-thought.
