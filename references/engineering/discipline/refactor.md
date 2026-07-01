# Refactor Discipline

Use this when changing structure while intending to preserve behavior: refactor,
migration, extraction, file split, wrapper removal, import cleanup, compatibility
cleanup, or staged convergence work.

## Gates

- State the preserved public behavior before editing when the boundary is not
  obvious.
- Keep compatibility first: public API, CLI, schema, file layout, and generated
  output changes must be intentional and documented.
- Prefer semantic movement over mechanical wrappers. A new layer must add a
  real boundary, policy, lifecycle, reuse point, or readability gain.
- After moving code, clean the transition debt in the same batch when practical:
  broad imports, unused exports, duplicate helpers, compatibility aliases,
  suppression comments, temporary names, and dead routes.
- Do not leave lint suppressions such as unused-import ignores as a substitute
  for resolving the actual import surface.
- Search for old paths, names, call sites, docs, tests, fixtures, and generated
  references before claiming convergence.
- Keep tests aligned with the intended preserved behavior. Add or update tests
  when the refactor changes public behavior, compatibility, or cross-module
  contracts.

## Completion Criteria

A refactor is complete only when:

- the main path is at least as readable as before
- old and new boundaries are not both active without a documented reason
- temporary compatibility code is either removed or tracked with an explicit
  retirement condition
- imports, exports, and suppressions reflect real current usage
- relevant tests or smoke checks pass, or the unrun checks are explicitly named
  with the reason they were not run
