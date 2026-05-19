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
| `has_` | factual presence, containment, possession, or attached-resource existence predicate | returns `bool`; not for general state adjectives such as available, ready, or valid |
| `should_` | policy predicate | returns `bool` |
| `validate_` | strong validation | invalid input raises |
| `ensure_` | ensure a required object, node, property, or state exists and return it if useful | may create or repair before returning |

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

### Editing and Mutation

| Prefix | Use | Notes |
| --- | --- | --- |
| `clear_` | clear the contents or state of an existing object while retaining the object itself | whole-content clearing, not targeted removal |
| `remove_` | remove a member, entry, field, node, or child object from an existing parent or container | targeted removal, not whole-content clearing |
| `insert_` | insert content, nodes, or elements into an existing ordered or anchored target at a defined position | structural insertion only; use when insertion position is essential |

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
| `has_` / `is_` / `should_` | `has_` for presence, containment, possession, or attached-resource existence; `is_` for factual state or property; `should_` for policy | using `has_` for adjective-like states such as available, ready, or valid; using `infer_` for boolean checks; using `should_` for factual state |
| `ensure_` / `validate_` | `ensure_` may create, repair, or initialize so a required state or object exists; `validate_` only checks and raises on invalid input | using `validate_` for repair or `ensure_` as a pure validation gate |
| `calculate_` / `derive_` | `calculate_` for numeric values; `derive_` only for non-scalar artifacts when no more precise prefix fits | mixing numeric outputs into `derive_`, or using `derive_` for in-place assignment, classification, formatting, filtering, selection, or plain aggregation |
| `classify_` / `format_` | `classify_` assigns rule-based categories; `format_` produces human-facing text | using `format_` for structural reshaping or `classify_` for aggregation |
| `create_` / `generate_` | `create_` for one object; `generate_` for batch or sequence output | using `generate_` for one-off construction |
| `read_` / `scan_` | `read_` for materialized parsing; `scan_` for lazy or metadata-first access | materializing the primary payload by default in `scan_` |
| `write_` / `sink_` | `write_` for ordinary persistence; `sink_` for true streaming | using `sink_` for non-streaming writes |
| `select_` / `filter_` | `select_` for projection; `filter_` for predicates | mixing projection into `filter_` or predicates into `select_` |
| `clear_` / `remove_` | `clear_` empties retained object contents or state; `remove_` deletes specific members, entries, fields, or nodes | using `clear_` for targeted deletion or `remove_` for whole-object clearing |
| `insert_` / `apply_` | `insert_` for position-aware structural insertion into an existing target; `apply_` for applying a plan, rule, or spec to a target | using `apply_` when insertion position is the essential behavior, or `insert_` for generic rule application |
| `sanitize_` | minimally repair invalid input while preserving semantics where possible | business filtering, row dropping, or destructive rewriting hidden behind `sanitize_` |
| `validate_` | strong validation | full payload parsing that belongs in `read_` or `scan_` |
| `summarize_` / `report_` | `summarize_` reduces source data; `report_` assembles a human-facing artifact | using `report_` as a catch-all for low-level serialization |

## Type Naming

- Prefer domain-first type names.
- Add a suffix only when it communicates lifecycle, role, or contract semantics that the domain noun alone would not make clear.
- Do not use `Spec` as the default catch-all suffix for every structured object.
- Prefer domain words such as `Kind`, `Mode`, `State`, `Level`, or `Format` over mechanical `Enum` naming when they naturally express the closed set.
- Avoid prefix forms such as `SpecThing` or `ReportThing` unless tooling constraints force them.

### Decision Rule

1. Start with the domain noun or domain phrase.
2. Ask whether users need help distinguishing declaration vs config vs plan vs result vs helper.
3. Add the narrowest suffix that resolves that ambiguity.
4. If the suffix does not change how a reader should use the type, remove it.

### Type Taxonomy

| Form | Use | Avoid | Example |
| --- | --- | --- | --- |
| bare domain noun | default choice when the role is already obvious from context | adding suffixes just to mirror implementation structure | `WorkspacePaths` |
| `Spec` | user-supplied or registry-held declaration that is validated or materialized later | plain config bags, immutable result facts, or fully-applied runtime objects | `ContrastSpec`, `CommandSpec` |
| `Options` | one cohesive package of call-level or component-level configuration | single local knobs, policies, or facts/results | `XlsxWriteOptions` |
| `Policy` | a local behavioral stance or decision policy within a larger options surface | top-level config packages, executable plans, or enums | `ScientificPolicy`, `XlsxValuePolicy` |
| `Patch` | partial overlay meant to be merged into another object | complete configurations or final materialized state | `CellFormatPatch` |
| `Plan` | a derived, executable, or validated plan ready to be applied | raw user declarations or final human-facing reports | `ContrastPlan`, `WorkspacePlan` |
| `Layout` | a structural arrangement or topology concept; may appear bare or combined with another suffix when both matter | using `Layout` as a vague synonym for all config objects | `WorkspaceLayoutSpec` |
| `Report` | human-oriented, aggregated, or post-run result artifact | low-level serialization payloads or one-row entities | `CopyReport`, `XlsxReport` |
| `Record` | one row/item/event/entity-shaped fact | aggregated reports, config bags, or mutable staging objects | `FastaHeaderRecord` |
| `Buffer` | mutable accumulation or staging object that exists to be filled and drained | immutable results or pure declarations | `*Buffer` |
| `Builder` | staged construction helper with an explicit build/finalize step | plain configs or one-shot creation helpers | `ParserBuilder` |
| `Adapter` | boundary-layer object that translates one stable contract, protocol, or model shape into another | plain data holders, result facts, or thin wrappers that only rename or forward | `LegacyConfigAdapter` |

### Naming Boundaries for Structured Types

- Use `Spec` when the object is primarily a declaration authored by a caller and later turned into another artifact.
- Use `Options` when the object is the main bundle of settings accepted by one public operation or component.
- Use `Policy` when the object governs one localized behavioral concern inside a larger operation.
- Use `Patch` when unset fields mean “leave existing value unchanged” and merge semantics are central.
- Use `Plan` when the object is already normalized or derived for execution.
- Use `Report` when the object is mainly for communicating results back to humans or orchestration layers.
- Use `Record` when the object represents a single factual entry rather than a whole report.
- Use `Adapter` when the object's primary job is to translate between two stable contracts, protocols, or model shapes at a boundary.
- Keep `Layout` only when spatial or directory arrangement is the semantic center; combine with `Spec` or `Plan` only if both layout and lifecycle semantics matter.

### Examples and Judgement Calls

- `ContrastSpec` is appropriate when callers declare one contrast and the system later derives a `ContrastPlan`.
- `WorkspaceLayoutSpec` is acceptable when layout semantics and declaration semantics both matter before `WorkspacePlan` materialization.
- `XlsxWriteOptions` is preferable to `XlsxWriteSpec` because the object is the main options bag for one writer/component.
- `AutofitPolicy` is preferable to `AutofitOptions` when the object governs one localized decision inside a larger write operation.
- `CellFormatPatch` is preferable to `CellFormatSpec` when merge/overlay semantics are the defining behavior.
- `LegacyConfigAdapter` is appropriate when a boundary object exists to translate old user-facing configuration into a newer internal contract.

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

- Long option spelling should preserve `snake_case` after the leading `--`.
  Do not convert role prefixes or multi-token names to kebab-case unless a
  repository-local compatibility rule explicitly requires it.
- Boolean options:
  - `has_...` for factual presence, containment, or possession toggles
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
  `path_...`, `rule_...`, `thr_...`, `df_...`, `dt_...`, `set_...`,
  and `fn_...` when they improve clarity.
- For dictionaries and dictionary-like mappings, prefer `value_by_key` names
  over generic `map_...` names when both key and value roles are known, such as
  `sample_ids_by_group`, `sample_idx_by_id`, or `row_by_term`.
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

## Workflow Artifact Filename Prefixes

Use filename prefixes to distinguish the lifecycle role of exported workflow
artifacts. The prefix is part of the public contract when downstream tasks,
reports, or users discover files by name.

| Prefix | Meaning | Primary Data? | Typical Uses |
| --- | --- | ---: | --- |
| `data-*` | Core data produced by a stage or consumed by downstream computation | yes | parquet tables, VCF/PLINK prefixes, foreground/background sets, QTL/GWAS main results |
| `info-*` | Identity, mapping, configuration, or input-contract context needed to interpret data | partial | sample tables, contrast tables, protein ID maps, mapping-conflict notes |
| `stats-*` | Run statistics, QC counts, or summaries for reporting and debugging | no | filter counts, hit counts, QQ-point summaries, ORA input sizes, LD statistics |

### Decision Rule

1. If a downstream step continues scientific or statistical computation from
   the artifact, use `data-*`.
2. If the artifact explains identity, mapping, grouping, or analysis scope for
   another artifact, use `info-*`.
3. If the artifact is used only for QC, reporting, provenance, or debugging and
   is not a computational input contract, use `stats-*`.

### Boundaries

- Do not name count or QC summaries as `data-*` merely because they are stored as
  tables. Use `stats-*` unless downstream computation depends on them as primary
  data.
- Do not hide identity maps inside `data-*` when their purpose is explaining
  what IDs mean. Prefer `info-*` for maps such as `info-samples.tsv`,
  `info-contrasts.tsv`, or `info-protein_id_map_conflicts.tsv`.
- Use `data-*` for mapping-like tables only when the table itself is the main
  computational input, such as `data-foregrounds.tsv` or a model-ready design
  matrix.
- Keep compatibility filenames only at explicit legacy boundaries. New contract
  files should follow the prefix decision rule.

## Workflow Expectations

- Keep the business-critical path shallow, direct, and linearly readable.
- Do not introduce wrapper layers whose only effect is renaming or forwarding
  without semantic narrowing, contract stabilization, or real duplication
  reduction.
- Keep API changes minimal and explicit.
- Add or update tests with each behavior change.
- Keep docs and examples in sync with public API.
