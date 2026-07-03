---
name: writing-docstrings
description: Write, revise, audit, or standardize Python docstrings. Use for explicit docstring requests, public or exported Python API documentation, reusable package APIs, and durable workflow or product contract boundaries where a docstring should explain usage, contract, maintenance rationale, or compatibility-sensitive behavior.
---

# Writing Docstrings

Use this skill to improve Python docstrings without turning docstrings into
ceremony for every function.

## First Pass

1. Check repository-local style first. If the repository already uses numpydoc,
   Sphinx, Google style, or another convention, follow it.
2. If no local rule exists, use Google-style docstrings compatible with the
   VS Code autoDocstring default.
3. Decide whether the target is library-facing, maintenance-facing, or neither.
4. Write only docstrings that add contract information a reader cannot recover
   cheaply from the name, signature, type hints, schema, or nearby code.

Read `references/python-google.md` when writing or reviewing non-trivial
docstrings, examples, or maintenance-facing notes.

## Library-Facing Mode

Use this mode for reusable package APIs and user-facing library surfaces.

Target reader: a user learning how to call the API correctly.

Write docstrings for public or exported functions, classes, and methods that
are part of the package promise. Prefer these Google-style sections when they
carry information: summary, `Args:`, `Returns:`, `Yields:`, `Raises:`, and
`Examples:`.

`Examples:` is expected for library-facing public APIs. Cover every distinct
user-facing usage mode with the smallest stable example that proves that mode.
Prefer several short examples over one long omnibus example. Do not include
multiple examples that teach the same point.

## Maintenance-Facing Mode

Use this mode for workflow and product repositories where the function carries a
durable business or technical boundary but is not primarily an importable
library API.

Target reader: a maintainer trying not to break the product workflow.

Write docstrings for functions or classes that define or protect stage
boundaries, artifact or schema contracts, report/package handoffs, product
routing, cross-language or cross-module joins, compatibility-sensitive behavior,
or technical choices that are easy to simplify incorrectly.

Do not require `Examples:` in this mode. Use `Notes:` for business path,
ownership, contract, technical rationale, compatibility constraints, and
easy-to-misread maintenance warnings. Default to English, but keep domain terms
in another language when translation would lose product or report meaning.

## Do Not Write

Do not add docstrings that:

- repeat the function name, signature, or type hints without adding semantics
- compensate for bad names, unclear boundaries, or thin wrappers
- explain local implementation mechanics that are already readable
- replace tests, schema validation, README/API documentation, or architecture
  docs
- invent custom sections such as `Rationale:` unless the repository already
  uses them

For thin wrappers and mechanical forwarding layers, prefer improving the
boundary, name, or implementation instead of adding explanatory docstrings.

## Self-Review

Before finishing, check:

- The docstring has the correct reader: API user or future maintainer.
- Every section earns its place.
- Type hints are not repeated unless extra semantics such as shape, units,
  ordering, mutability, valid ranges, or stability guarantees matter.
- Examples cover distinct usage modes without becoming long tutorials.
- Maintenance-facing notes explain business path, contract, or technical
  rationale rather than restating code.
