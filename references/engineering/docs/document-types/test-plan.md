# Test Plan

## Use When

Use this type for a durable validation strategy or acceptance contract that
must be reused across changes, releases, or environments.

## Method Reference

Use the repository's configured test and verification entrypoints. Keep test
plans complementary to executable tests and CI rather than duplicating their
implementation details.

## Local Requirements

- Place it in project `docs/testing/` when the project maintains durable testing
  guidance there.
- State the scope, risks, affected contracts, and test levels.
- Identify fixtures, data boundaries, environment assumptions, and required
  setup.
- Give commands or CI checks, expected evidence, and failure interpretation.
- Define acceptance criteria and any manual artifact or runtime inspection.
- Record compatibility, cleanup, and rollback implications when applicable.

## Complete When

Another contributor can run the stated checks and determine whether the
documented change satisfies its acceptance contract.
