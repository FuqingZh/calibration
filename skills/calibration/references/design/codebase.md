# Codebase Design

Use this when deciding module boundaries, interface shape, abstraction depth,
adapters, shared helpers, wrapper layers, and where logic belongs.

## Vocabulary

- Deep module: a module whose interface is simpler than the functionality it
  hides.
- Interface: the contract a caller depends on, including names, inputs, outputs,
  errors, side effects, and lifecycle expectations.
- Locality: the ability to understand or change behavior by reading one small
  region instead of chasing scattered helpers.
- Leverage: the amount of real complexity removed or real reuse gained by an
  abstraction.
- Deletion test: if removing a layer makes the main path clearer without losing
  a contract, the layer probably did not earn its place.

## Judgment Checks

- Keep the business-critical path shallow, direct, and linearly readable.
- Add an abstraction only when it creates semantic leverage, lifecycle clarity,
  ownership separation, policy isolation, compatibility protection, or real
  reuse.
- Do not introduce wrappers that only rename, forward arguments, or hide a small
  direct call behind a larger search surface.
- Keep domain behavior in the layer that owns the domain concept. Keep caller
  taste, product defaults, and presentation policy out of low-level kernels
  unless they are part of the explicit contract.
- Prefer one stable interface over parallel compatibility paths. When parallel
  paths are necessary, document their retirement condition.
- Choose names and boundaries that make the main path read as the user's mental
  model, not as the implementation accident.

## Completion Criteria

A design change is ready when:

- the new or changed boundary has a clear caller and responsibility
- the interface is smaller or more stable than the implementation it hides
- the abstraction passes the deletion test or has a documented reason to stay
- the main path is easier to audit, not merely more factored
- compatibility, tests, and documentation impacts are known
