# Synthetic WGCNA Evaluation Repository

This is a sanitized, disposable evaluation fixture. The checkout is clean,
exclusive, unowned, and already assigned to the current writer. AO installation,
owner discovery, spawning, claiming, review loops, pull requests, and host-wide
inspection are out of scope; do not invoke them.

The public output contract is frozen in `README.md`. Modify only
`src/wgcna_worker.R`. Do not change tests, Python consumers, documentation,
schemas, CLI arguments, output files, or workbook sheets. A prior speculative
idea named `data-diagnostics.parquet` is intentionally not part of the contract
and must not be introduced.

Use `python3 tests/verify.py` as the decisive repository-owned validation. The
task is complete only when it passes and `git status --short` contains only the
required R worker change.
