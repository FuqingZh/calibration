---
name: writing-code-docs
description: Use for writing, revising, or auditing docstrings and language-native documentation comments. Also use at public APIs and durable workflow or product boundaries when code documentation must explain usage, contracts, maintenance rationale, or compatibility-sensitive behavior.
---

# Writing Code Docs

For repository work, trace in-scope symbols through relevant code, call sites,
tests, schemas, or outputs until their contracts are clear to their readers.

For a self-contained code snippet, work from the supplied implementation and
requirements. Do not search the workspace for callers or conventions unless
the user connects the snippet to a repository. State material gaps rather than
inventing behavior.

A contract is clear to callers when they know what they may rely on, and to
maintainers when they know what they must preserve.

## Convention

For repository work, find and follow its language-native documentation
convention. For standalone snippets, use the supplied format or the language
fallback below; do not search an unrelated workspace.

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

Classify in-scope symbols as caller-facing, maintainer-facing, both, or neither.
Do not document symbols with no reader.

In prose, do not restate what names, signatures, types, schemas, or nearby code
already show.

For callers, show how to use the symbol and what they may rely on.

Give every caller-facing class, function, method, and property its own example,
even when its contract is simple.

Use short examples that exercise the symbol and show each distinct public
consequence once.

If coverage remains unclear, consult
[Polars: Writing doc examples](https://docs.pola.rs/development/contributing/test/#writing-doc-examples)
for default use, meaningful parameter effects, and interactions. Inspect one
analogous API page only if still needed. Keep the selected language format;
do not import Polars' numpydoc format. If unavailable, use the rules above.

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

Complete when all in-scope documentation meets the reader, convention, and
example requirements above, and maintenance notes identify boundaries that
an apparently safe change could break.
