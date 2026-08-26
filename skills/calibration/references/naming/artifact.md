# Workflow Artifact Filename Naming

Use filename prefixes to distinguish the lifecycle role of exported workflow
artifacts. The prefix is part of the public contract when downstream tasks,
reports, or users discover files by name.

| Prefix | Meaning | Primary Data? | Typical Uses |
| --- | --- | ---: | --- |
| `data-*` | Core data produced by a stage or consumed by downstream computation | yes | parquet tables, VCF/PLINK prefixes, foreground/background sets, QTL/GWAS main results |
| `info-*` | Identity, mapping, configuration, or input-contract context needed to interpret data | partial | sample tables, contrast tables, protein ID maps, mapping-conflict notes |
| `stats-*` | Run statistics, QC counts, or summaries for reporting and debugging | no | filter counts, hit counts, QQ-point summaries, ORA input sizes, LD statistics |

## Decision Rule

1. If a downstream step continues scientific or statistical computation from
   the artifact, use `data-*`.
2. If the artifact explains identity, mapping, grouping, or analysis scope for
   another artifact, use `info-*`.
3. If the artifact is used only for QC, reporting, provenance, or debugging and
   is not a computational input contract, use `stats-*`.

## Boundaries

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
