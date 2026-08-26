# Type Naming

Use these rules for classes, dataclasses, enums, config objects, plans,
reports, records, builders, buffers, and adapters.

- Prefer domain-first type names.
- Add a suffix only when it communicates lifecycle, role, or contract semantics that the domain noun alone would not make clear.
- Do not use `Spec` as the default catch-all suffix for every structured object.
- Prefer domain words such as `Kind`, `Mode`, `State`, `Level`, or `Format` over mechanical `Enum` naming when they naturally express the closed set.
- Avoid prefix forms such as `SpecThing` or `ReportThing` unless tooling constraints force them.

## Decision Rule

1. Start with the domain noun or domain phrase.
2. Ask whether users need help distinguishing declaration vs config vs plan vs result vs helper.
3. Add the narrowest suffix that resolves that ambiguity.
4. If the suffix does not change how a reader should use the type, remove it.

## Type Taxonomy

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

## Naming Boundaries for Structured Types

- Use `Spec` when the object is primarily a declaration authored by a caller and later turned into another artifact.
- Use `Options` when the object is the main bundle of settings accepted by one public operation or component.
- Use `Policy` when the object governs one localized behavioral concern inside a larger operation.
- Use `Patch` when unset fields mean "leave existing value unchanged" and merge semantics are central.
- Use `Plan` when the object is already normalized or derived for execution.
- Use `Report` when the object is mainly for communicating results back to humans or orchestration layers.
- Use `Record` when the object represents a single factual entry rather than a whole report.
- Use `Adapter` when the object's primary job is to translate between two stable contracts, protocols, or model shapes at a boundary.
- Keep `Layout` only when spatial or directory arrangement is the semantic center; combine with `Spec` or `Plan` only if both layout and lifecycle semantics matter.

## Examples and Judgement Calls

- `ContrastSpec` is appropriate when callers declare one contrast and the system later derives a `ContrastPlan`.
- `WorkspaceLayoutSpec` is acceptable when layout semantics and declaration semantics both matter before `WorkspacePlan` materialization.
- `XlsxWriteOptions` is preferable to `XlsxWriteSpec` because the object is the main options bag for one writer/component.
- `AutofitPolicy` is preferable to `AutofitOptions` when the object governs one localized decision inside a larger write operation.
- `CellFormatPatch` is preferable to `CellFormatSpec` when merge/overlay semantics are the defining behavior.
- `LegacyConfigAdapter` is appropriate when a boundary object exists to translate old user-facing configuration into a newer internal contract.
