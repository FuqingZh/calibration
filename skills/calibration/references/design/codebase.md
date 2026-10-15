# Codebase Design

Use this when deciding module boundaries, interface shape, abstraction depth,
adapters, shared helpers, wrapper layers, and where logic belongs.

## Vocabulary

- Deep module: a module whose interface is simpler than the functionality it
  hides.
- Interface: everything a caller must know to use the module correctly, including
  names, inputs, outputs, errors, side effects, configuration, call ordering,
  lifecycle, and any performance guarantees the caller relies on.
- Locality: the ability to understand or change behavior by reading one small
  region instead of chasing scattered helpers.
- Leverage: the amount of real complexity removed or real reuse gained by an
  abstraction.
- Deletion test: mentally inline the abstraction into its callers. Remove it
  when this eliminates indirection without duplicating policy, exposing hidden
  complexity, or losing a contract. Keep it when callers would otherwise each
  need to manage that complexity.

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
- callers can use the boundary without managing the complexity it owns
- the deletion test identifies what complexity or contract justifies keeping
  the abstraction; otherwise remove it
- the main path is easier to audit, not merely more factored
- compatibility, tests, and documentation impacts are known
