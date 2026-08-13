# Acme Parser 4.2 empty-tag behavior

## Verified behavior

Acme Parser 4.2 distinguishes between self-closing and explicitly closed empty
tags:

| Input | Parsed result |
| --- | --- |
| `<tag/>` | Missing field |
| `<tag></tag>` | Empty string |

This behavior was reproduced with fixtures A, B, and C on 2026-08-12.

## Compatibility guidance

When an empty string must be preserved, emit an explicitly closed tag:
`<tag></tag>`.

This note is scoped to Acme Parser 4.2. Reverify the behavior before relying on
it with another parser version.
