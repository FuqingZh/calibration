---
name: writing-code-docs
description: Use for writing, revising, or auditing docstrings and language-native documentation comments. Also use at public APIs and durable workflow or product boundaries when code documentation must explain usage, contracts, maintenance rationale, or compatibility-sensitive behavior.
---

# Writing Code Docs

Trace each in-scope symbol through real use until its contract is clear to its
intended readers.

Ground that contract in relevant code, call sites, tests, schemas, or outputs,
not the signature alone.

A contract is clear to callers when they know what they may rely on, and to
maintainers when they know what they must preserve.

## Convention

Before writing, find and follow any repository-local, language-native
documentation convention.

For Python without a local convention, follow the docstring convention in the
[Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings).

Under that fallback, use
[doctest-style](https://docs.python.org/3/library/doctest.html) `Examples:` for
caller-facing examples and `Notes:` for maintenance boundaries.

For other languages without a local convention, follow the official
documentation convention; if none exists, state the gap before choosing a
format.

Do not transfer Python sections by analogy.

## Readers

Classify each in-scope symbol by its readers: callers, maintainers, both, or
none.

Do not document symbols with no reader.

In prose, do not restate what names, signatures, types, schemas, or nearby code
already show.

For callers, show how to use the symbol and what they may rely on.

Give every caller-facing class, function, method, and property its own example,
even when its contract is simple.

Exercise the symbol and show the smallest public consequence that explains why
a caller would use it.

Cover each distinct public consequence once.

When example coverage or granularity remains unclear, read
[Polars: Writing doc examples](https://docs.pola.rs/development/contributing/test/#writing-doc-examples).
Borrow its coverage judgment: start with default use, show meaningful parameter
effects and special interactions, and keep each example short without repeating
the same consequence. Inspect one analogous Polars API page only when that
still leaves the degree unclear.

Keep the repository's selected format, or the Google-style fallback for Python.
Polars' numpydoc section format is not part of this skill. If the link is
unavailable, continue from the rules above.

For maintainers, name the boundary, why it exists, and the tempting change that
would break it.

When both apply, serve each reader without duplication.

## Boundaries

Keep domain terms unchanged unless the repository defines their translation.

Treat bad names, unclear boundaries, and mechanical wrappers as code problems,
not documentation problems; fix them when in scope and report them otherwise.

Do not substitute documentation for tests, validation, user guides, or
architecture records.

## Completion

Complete only when every in-scope symbol has been classified, every retained
code document follows the selected language convention and serves its readers,
each caller-facing symbol has its own example, the examples collectively cover
every distinct public consequence once, and maintenance notes state any
boundary that is easy to break by an apparently safe change.
