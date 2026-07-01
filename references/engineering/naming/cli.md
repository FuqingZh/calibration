# CLI Option Naming

Use these rules for command-line option names.

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
