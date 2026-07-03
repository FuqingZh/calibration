# Writing Docstrings Skill Design

Date: 2026-07-03

## Purpose

This document records the design direction for a future `writing-docstrings`
skill.

The skill should improve docstring quality for Python APIs and durable workflow
boundaries without turning docstrings into ceremony for every function.

## Context

Docstrings serve different roles in different repository types.

In small reusable packages such as `cliguards` or `bioextract`, the important
question is usually straightforward: which functions, classes, and methods are
part of the public promise a user may import or learn from API documentation.
Those surfaces need user-facing docstrings.

In workflow and product repositories such as `proteomics` or
`trait_association`, many important functions are not library APIs. They are
maintenance boundaries: stage handoffs, product routing, artifact schemas,
report/package contracts, cross-language joins, or compatibility-sensitive
workflow decisions. These functions need docstrings when they explain business
path, ownership, contract, and technical rationale that future maintainers
would otherwise rediscover.

The skill therefore must not use only Python visibility rules such as leading
underscores or `__all__`. It should decide from contract role and reader need.

## Decision

Create a narrow model-invoked `writing-docstrings` skill in a later
implementation pass.

The v1 skill should:

- support Python only
- use Google-style docstrings by default, matching the VS Code autoDocstring
  default style
- trigger narrowly for explicit docstring tasks, public or exported Python API
  documentation, and durable workflow/product contract boundaries
- avoid special FastAPI/OpenAPI rules in v1
- leave Rust and R as future branches, not partially specified behavior

The skill should define two docstring modes.

## Library-Facing Docstrings

Use this mode for reusable package APIs and user-facing library surfaces.

Target reader: a user learning how to call the API correctly.

Write docstrings for public or exported functions, classes, and methods that
are part of the package promise. Follow repository-local style first; otherwise
use Google-style sections such as summary, `Args:`, `Returns:`, `Raises:`, and
`Examples:`.

`Examples:` is expected for library-facing public APIs. The examples must be
short, realistic, stable, and useful. Shortness is not a reason to omit real
usage modes. Cover every distinct user-facing usage mode with the smallest
stable example that proves that mode. Prefer several short examples over one
long omnibus example. Do not include multiple examples that teach the same
point.

## Maintenance-Facing Docstrings

Use this mode for workflow and product repositories where a function carries a
durable business or technical boundary but is not primarily an importable
library API.

Target reader: a maintainer trying not to break the product workflow.

Write docstrings for functions or classes that define or protect:

- stage or product-flow boundaries
- artifact or schema contracts
- report or package handoffs
- product routing behavior
- cross-language or cross-module handoffs
- compatibility-sensitive behavior
- technical choices that are easy to simplify incorrectly

Do not require `Examples:` for this mode. Examples in business workflows often
need real paths, real tables, or real configs; fake examples create more noise
than value. Use `Notes:` for business path, ownership, contract, technical
rationale, compatibility constraints, and easy-to-misread maintenance warnings.

Default to English. Keep Chinese business terms when they are part of the
product/report vocabulary or when translation would lose meaning.

## Non-Goals

The skill should not:

- add docstrings to every function
- compensate for bad names, bad boundaries, or thin wrappers
- repeat type hints in prose unless there is extra semantic information such as
  shape, units, ordering, mutability, valid ranges, or stability guarantees
- replace tests, schema validation, README/API documentation, or architecture
  docs
- invent custom sections such as `Rationale:` unless a repository already uses
  them

For thin wrappers and mechanical forwarding layers, prefer improving the
boundary, name, or implementation instead of adding explanatory docstrings.

## Skill Shape

Keep `SKILL.md` short and operational:

- trigger description
- public or maintenance boundary gate
- Google-style section policy
- example coverage rule
- self-review checklist

Place detailed examples in a disclosed reference such as
`references/python-google.md`. Include only a few calibration examples:

- a library-facing function with too-thin versus useful docstrings
- a multi-mode public API with several short examples
- a maintenance-facing workflow boundary that uses `Notes:` and no `Examples:`

The reference examples should teach degree and judgment. They should not become
a long style guide.

## Consequences

This design preserves the value of docstrings while avoiding documentation
ceremony:

- reusable packages get high-quality user-facing API docs
- workflow repositories get maintainability notes at real contract boundaries
- local helpers and obvious implementation details stay uncluttered
- example density follows user-facing usage modes rather than fixed counts

The cost is that the skill must make a contextual judgment before writing:
library-facing and maintenance-facing docstrings optimize for different
readers.

## Reopen Conditions

Revisit this decision if:

- FastAPI or another web framework becomes a primary target for generated API
  documentation
- Rust or R docstrings become active work instead of future branches
- repository-local style rules conflict with Google-style defaults often enough
  that a router is needed
- forward-testing shows the skill still writes ceremonial docstrings or misses
  maintenance-critical workflow boundaries
