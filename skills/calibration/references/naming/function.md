# Function Naming

Use these rules for public API functions and module-level function prefixes.

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
