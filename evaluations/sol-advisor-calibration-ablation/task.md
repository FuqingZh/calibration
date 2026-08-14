Repair the synthetic WGCNA workflow in this repository.

Start by running `python3 tests/verify.py` and use its first failing evidence to
diagnose the defect. The real R worker currently loses stable nonnumeric
`SampleId` values while materializing and ordering module eigengenes. Implement
the smallest complete repair in `src/wgcna_worker.R` so that:

- nonnumeric SampleIds survive the R worker unchanged and align to traits even
  when trait rows use a different order;
- two-level traits produce finite module/trait associations;
- a SampleId set mismatch produces the existing field-specific error naming
  missing and extra IDs;
- grey-only input succeeds with the existing structured empty outputs; and
- all five existing workbook regressions pass.

The output schema, CLI, Python pipeline, workbook sheets, tests, and docs are
frozen. Modify only `src/wgcna_worker.R`. Do not add
`data-diagnostics.parquet`, a manifest field, a new sheet, or another consumer.
This checkout is clean, exclusive, unowned, and already assigned to you; AO and
PR delivery are out of scope.

After the patch, rerun `python3 tests/verify.py`, inspect the complete diff, and
confirm `git status --short` lists only `src/wgcna_worker.R`. Finish only with
the actual validation result and concise residual risk.
