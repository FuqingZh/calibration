# Variable Naming

Use these rules for internal local variables, parameters, dictionary-like
mappings, and structural role names.

Internal variable naming is guidance, not a merge gate unless a
repository-local rule makes it one.

- Prefer semantic names over type-only names.
- For common structures, use `structure_role`: `df_`, `dt_`, `cols_`,
  `col_`, `rows_`, `row_`, `ids_`, `set_`, `file_`, `dir_`, `path_`,
  `rule_`, `thr_`, `fn_`. Prefer `cols_optional`, `col_protein`,
  `ids_sample`, and `rows_output`; avoid `optional_columns`,
  `protein_column`, `sample_ids`, and `output_rows`.
- Use these prefixes for parameters and locals when the structure is part of
  the reader-visible contract or materially improves scanability.
- For dictionaries and dictionary-like mappings, prefer `value_by_key` names
  over generic `map_...` names when both key and value roles are known, such as
  `sample_ids_by_group`, `sample_idx_by_id`, or `row_by_term`.
- For locals, prefer clear domain names over generic placeholders.
- Avoid `obj`, `tmp`, `x`, or `value` when a concrete role name exists.

Read `loop.md` when naming loop, lambda, closure, or anonymous-function
binders.
