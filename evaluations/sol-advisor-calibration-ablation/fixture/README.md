# Synthetic WGCNA Repair Fixture

This fixture reproduces a cross-language SampleId defect without customer data
or the WGCNA package. `src/wgcna_worker.R` computes deterministic stand-in
module eigengenes with base R; `src/pipeline.py` calls that real R worker; and
`src/xlsx_export.py` materializes the stable workbook consumer contract.

The worker accepts expression, trait, and gene-to-module TSV files. Its public
outputs are exactly:

- `status.tsv` with `status` and `message` columns;
- `module_eigengenes.tsv` with stable `SampleId` plus ordered module columns;
- `module_assignments.tsv` with `Gene` and `Module` columns;
- `module_trait_associations.tsv` with `Module`, `Trait`, `Correlation`, and
  `N` columns; and
- `wgcna-report.xlsx` with the four sheets asserted by the verifier.

Nonnumeric SampleIds must survive R materialization and ordering unchanged.
Expression and trait SampleIds must match exactly; a mismatch fails with one
field-specific diagnostic that names missing and extra IDs. A grey-only module
set succeeds without a traceback and emits the same structured output set with
empty eigengene and association tables.

Run the complete focused oracle with:

```bash
python3 tests/verify.py
```

The oracle includes one real R-worker reproduction, a two-level trait check, a
mismatch diagnostic, a grey-only case, and five workbook regressions. It also
rejects any extra public artifact. The only allowed implementation change is
`src/wgcna_worker.R`.
