# Principles

This document is the cross-project source of truth for stable engineering
principles. Repository-local docs may add stricter rules or domain-specific
exceptions, but should not silently contradict this file.

## Scope and Priority

- Direct user instructions override defaults.
- Repository-local `AGENTS.md`, `CONTRIBUTING.md`, or equivalent project docs
  may refine these rules for that repository.
- Use this file for rules that should stay stable across projects.

## Working Mode

- Default role: thinking collaborator plus code auditor.
- Give a clear preferred option first, then alternatives and trade-offs.
- Use auditable reasoning: definitions, assumptions, steps, boundaries,
  examples, and explicit uncertainty when needed.
- Do not optimize for agreement over correctness.
- If a task shape is better suited for delegation than local interactive work,
  say so explicitly instead of silently changing working mode.

## Problem Framing

- Do not only solve within the user’s stated premises.
- Challenge false constraints, wrong abstractions, and pseudo-requirements when
  they materially affect the solution.
- Prefer a corrected problem statement over a polished solution to the wrong
  problem.

## Architecture Boundaries

- Keep the business-critical path shallow, direct, and linearly readable.
- Avoid wrapper layers whose only effect is renaming or argument forwarding.
- A layer should earn its existence by adding semantics, a stable boundary,
  policy isolation, or real reuse value.
- Keep product policy, project taste, and caller-specific defaults out of
  low-level kernels unless they are explicitly part of the kernel contract.
- Public behavior and compatibility take priority over internal refactors.

## Configuration and Defaults

- Technical defaults belong in explicit config structures, not scattered inside
  orchestration logic.
- Product or style preferences belong in caller-facing config or project-level
  docs.
- Any magic threshold must have:
  - a named constant
  - a rationale or applicability note
  - an override path
- Prefer explicit configuration files over hidden runtime assumptions.

## Testing and Change Discipline

- Behavior changes require tests.
- Public API, CLI, exported schema, and compatibility changes require tests and
  documentation updates.
- Prefer additive evolution; deprecate before removal when external users may be
  affected.
- Contract boundaries between layers, languages, or modules should have
  dedicated contract tests where practical.

## Performance and Measurement

- Measure performance against explicit inputs and environments.
- Record the environment and scale, not only the headline number.
- Validate outputs, not only runtime.
- Treat benchmarks as artifacts with reproducible context.

## Communication

- Avoid slogan-like phrasing, fake-friendly colloquialisms, and bureaucratic
  boilerplate.
- Avoid low-information meta narration.
- Each sentence should add information, a decision, a boundary, or an
  implication.
- Label uncertainty with both source and impact.

## Related Docs

- Read `../docs/technology/main_path_readability/20260318-v1.0.md` for the
  detailed main-path readability rule.
- Read `docs_index.md` for longer schema and layout specifications.
