# Naming

This document is the cross-project source of truth for naming and interface
conventions.

## Scope

- Public API naming
- Module-level function prefixes
- Public method boundaries
- Public CLI option naming
- Public-facing schema and export header naming
- Workflow expectations tied to naming clarity

Internal variable naming is guidance, not a merge gate.

## Public API Prefixes

### Compute and Infer

| Prefix | Use | Notes |
| --- | --- | --- |
| `calculate_` | deterministic numeric calculation | numeric result |
| `derive_` | derive a non-scalar artifact when no more precise prefix fits | structural fallback only; not for in-place assignment, classification, formatting, filtering, selection, or plain aggregation |
| `estimate_` | approximate numeric value | approximation allowed |
| `infer_` | infer latent property, classification, schema guess, or structured interpretation from incomplete evidence | not for plain boolean checks or direct numeric computation |

### Construction

| Prefix | Use | Notes |
| --- | --- | --- |
| `create_` | create or instantiate a single object | single-object construction |
| `generate_` | generate a sequence or batch of outputs | batch or sequence output |
| `sample_` | random sampling | stochastic selection |

### Parse and Encode

| Prefix | Use | Notes |
| --- | --- | --- |
| `parse_` | textual or syntactic representation to structured form | parsing to structure |
| `decode_` | encoded representation to raw value | encoded to raw |
| `encode_` | raw value to encoded representation | raw to encoded |

### Validation

| Prefix | Use | Notes |
| --- | --- | --- |
| `is_` | factual predicate | returns `bool` |
| `should_` | policy predicate | returns `bool` |
| `validate_` | strong validation | invalid input raises |

### Transform

| Prefix | Use | Notes |
| --- | --- | --- |
| `classify_` | assign a category, state, bucket, or label by rule | use for rule-based classification, not aggregation or free-form formatting |
| `format_` | produce a human-facing display string or label | presentation text only; not structural reshaping or parsing |
| `convert_` | equivalent type or format conversion | prefer reversibility |
| `sanitize_` | repair invalid text, field names, or unsupported characters | not business filtering |
| `center_` | location shift only | additive shift only |
| `scale_` | scale change only | multiplicative change only |
| `standardize_` | explicitly defined statistical standardization | for named statistical transforms |
| `normalize_` | broader distribution or scale normalization | use when a more precise transform prefix does not fit |

### Selection and Extraction

| Prefix | Use | Notes |
| --- | --- | --- |
| `filter_` | predicate-based filtering | not projection |
| `select_` | projection or reordering of fields or columns | not predicate filtering |
| `extract_` | extract substructure from nested or composite input | for nested or composite inputs |

### Planning and Application

| Prefix | Use | Notes |
| --- | --- | --- |
| `plan_` | produce a plan or specification | planning step |
| `apply_` | apply a plan to a target | application step |

### I/O

| Prefix | Use | Notes |
| --- | --- | --- |
| `copy_` | copy or migrate objects or filesystem resources | object or filesystem copying |
| `read_` | read and parse into an object | materialized read |
| `scan_` | lazy, deferred, or metadata-first access | avoid full materialization by default |
| `sink_` | truly streaming write without full materialization | streaming output only |
| `write_` | serialize and write an object | non-streaming persistence |

### Workflow and Presentation

| Prefix | Use |
| --- | --- |
| `prepare_` | preparation step |
| `run_` | main workflow step |
| `finalize_` | finalization step |
| `summarize_` | concise overview, aggregate description, or summary table |
| `plot_` | construct a plot or plotting object from data or specification |
| `render_` | render an already-defined presentation object or spec for display without implicit persistence |
| `report_` | assemble a human-oriented report artifact without implicit persistence |

## Naming Boundaries

| Boundary | Use | Avoid |
| --- | --- | --- |
| `infer_` | evidence-based interpretation, classification, schema guess, or structured inference result | plain boolean predicates, direct numeric computation, or pure reshaping without uncertainty |
| `is_` / `should_` | `is_` for factual `bool`; `should_` for policy | using `infer_` for boolean checks |
| `calculate_` / `derive_` | `calculate_` for numeric values; `derive_` only for non-scalar artifacts when no more precise prefix fits | mixing numeric outputs into `derive_`, or using `derive_` for in-place assignment, classification, formatting, filtering, selection, or plain aggregation |
| `classify_` / `format_` | `classify_` assigns rule-based categories; `format_` produces human-facing text | using `format_` for structural reshaping or `classify_` for aggregation |
| `create_` / `generate_` | `create_` for one object; `generate_` for batch or sequence output | using `generate_` for one-off construction |
| `read_` / `scan_` | `read_` for materialized parsing; `scan_` for lazy or metadata-first access | materializing the primary payload by default in `scan_` |
| `write_` / `sink_` | `write_` for ordinary persistence; `sink_` for true streaming | using `sink_` for non-streaming writes |
| `select_` / `filter_` | `select_` for projection; `filter_` for predicates | mixing projection into `filter_` or predicates into `select_` |
| `sanitize_` | minimally repair invalid input while preserving semantics where possible | business filtering, row dropping, or destructive rewriting hidden behind `sanitize_` |
| `validate_` | strong validation | full payload parsing that belongs in `read_` or `scan_` |
| `summarize_` / `report_` | `summarize_` reduces source data; `report_` assembles a human-facing artifact | using `report_` as a catch-all for low-level serialization |

## Type Naming

- Prefer domain-first type names.
- Use suffixes such as `Spec`, `Report`, `Builder`, `Buffer`, and `Record`
  only when the suffix adds real semantic value.
- Prefer domain words such as `Kind`, `Mode`, `State`, `Level`, or `Format`
  over mechanical `Enum` naming when they naturally express the closed set.
- Avoid prefix forms such as `SpecThing` or `ReportThing` unless tooling
  constraints force them.

## Public Method Boundaries

Public methods should mainly express protocol, lifecycle, or object-local
configuration. Domain behavior should remain module-level functions that follow
the prefix rules above.

Allowed common public methods:

- `close()`
- `run()`
- `render()`
- `report()`
- `build()` on `*Builder`
- `from_*()` or `make()` as classmethod factories
- `add_*`, `select_*`, `group()`, `command()`, `done()`, `end()`, `with_*`
  on builders or fluent configuration helpers

Prefer module-level functions over vague public methods such as:

- `save`, `load`, `export`, `dump`
- `execute`, `start`, `stop`, `finish`, `shutdown`, `dispose`
- `process`, `do`, `get`, `show`

## CLI Option Naming

- Boolean options:
  - `is_...` for factual or state toggles
  - `should_...` for policy or strategy toggles
- Non-boolean options:
  - prefer explicit semantic names over abbreviations
  - use `file_...` and `dir_...` for known file and directory paths
  - use `rule_...` for strategy or mode selectors
  - use `thr_...` for thresholds and cutoffs

## Internal Naming Guidance

- Prefer semantic names over type-only names.
- For parameters, use role-oriented names such as `file_...`, `dir_...`,
  `path_...`, `rule_...`, `thr_...`, `df_...`, `dt_...`, `map_...`, `set_...`,
  and `fn_...` when they improve clarity.
- For locals, prefer clear domain names over generic placeholders.
- Avoid `obj`, `tmp`, `x`, or `value` when a concrete role name exists.
- In Python and Rust loop binders, use an underscore-prefixed binder such as
  `_sheet` or `_name`.
- In Python `lambda` parameters and Rust closure parameters, use the same
  underscore-prefixed binder style as loops, such as `_sheet` or `_name`.
- In R loop binders, use a dot-prefixed binder such as `.sheet` or `.name`.
- In R anonymous function parameters, including `\(.x)` style binders, use the
  same dot-prefixed binder style as loops, such as `.sheet` or `.name`.

## Public-facing Schema and Header Naming

| Context | Rule | Example |
| --- | --- | --- |
| Exported headers | use PascalCase | `SampleId`, `PtmFdr` |
| Standalone abbreviation token | use ALLCAPS | `ID`, `PTM`, `FDR` |
| Abbreviation inside a multi-token header | use PascalCase abbreviation segment | `SampleId`, `PtmFdr` |
| Internal storage | snake_case is acceptable internally; expose PascalCase through views, aliases, or export adapters | `sample_id` -> `SampleId` |

## Workflow Expectations

- Keep the business-critical path shallow, direct, and linearly readable.
- Do not introduce wrapper layers whose only effect is renaming or forwarding
  without semantic narrowing, contract stabilization, or real duplication
  reduction.
- Keep API changes minimal and explicit.
- Add or update tests with each behavior change.
- Keep docs and examples in sync with public API.
