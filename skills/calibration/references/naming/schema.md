# Schema and Header Naming

Use these rules for public-facing schema fields and exported headers.

| Context | Rule | Example |
| --- | --- | --- |
| Exported headers | use PascalCase | `SampleId`, `PtmFdr` |
| Standalone abbreviation token | use ALLCAPS | `ID`, `PTM`, `FDR` |
| Abbreviation inside a multi-token header | use PascalCase abbreviation segment | `SampleId`, `PtmFdr` |
| Internal storage | snake_case is acceptable internally; expose PascalCase through views, aliases, or export adapters | `sample_id` -> `SampleId` |
