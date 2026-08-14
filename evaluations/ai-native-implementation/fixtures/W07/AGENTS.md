# Repository Instructions

- Preserve the public `publish(path, key)` behavior and runtime tests.
- Keep publish orchestration in `src/resource_publication.py`; reusable helpers
  remain owned by `src/publication_core.py`.
- Treat `vendor/` as a read-only external dependency snapshot.
- This is ordinary local implementation with clear executable feedback; work
  directly without invoking Calibration or another workflow skill.
- Run `python scripts/check.py` before claiming completion.
