---
name: writing-code-docs
description: Use for writing, revising, or auditing docstrings and language-native documentation comments. Also use at public APIs and durable workflow or product boundaries when code documentation must explain usage, contracts, maintenance rationale, or compatibility-sensitive behavior.
---

# Writing Code Docs

Document the contract, not the code.

## Route

Identify the language, its documentation carrier, and the repository-local
convention before writing.

Follow the repository's documentation convention when one is present.

For Python without a local convention, use Google-style docstrings; read
`references/python-google.md` for non-trivial sections, examples, or
maintenance notes.

For another language without a local convention or bundled reference, consult
its official documentation convention; if that is unavailable, state the gap
before choosing a format. Do not transfer Python sections by analogy.

## Decide

Determine whether the code is library-facing, maintenance-facing, both, or
neither.

Write only contract information that is not readily recoverable from the name,
signature, types, schema, or nearby code.

## Library-Facing

For library-facing code, document correct use and the behavior callers may rely
on.

Add the smallest stable example for each distinct usage mode that is not
obvious from the signature; do not add multiple examples that prove the same
contract.

## Maintenance-Facing

For maintenance-facing code, document the boundary a maintainer must preserve,
why it exists, and which apparently safe changes would violate it.

When both apply, serve both readers without repeating the same fact.

Do not translate domain terms when translation would change their technical or
product meaning.

## Boundaries

Do not use code documentation to compensate for a bad name, unclear boundary,
or mechanical wrapper; improve the code instead.

Do not use code documentation to replace tests, runtime or schema validation,
user guides, or architecture records.

Do not invent documentation sections that the language or repository convention
does not support.

Complete only when every in-scope symbol has been classified and each retained
code document follows the selected convention, serves its identified reader,
and adds contract information not readily recoverable from code.
