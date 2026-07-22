# Variable Naming

Follow the language-native convention; for Python, follow
[PEP 8](https://peps.python.org/pep-0008/#function-and-variable-names).

Internal variable naming is guidance, not a merge gate unless a
repository-local rule makes it one.

- Use plural names for collections instead of concrete container types.
- In dense tabular or analytical code, use compact `structure_role` names such
  as `df_evidence`, `cols_required`, and `ids_unmapped` when they improve
  scanability.
- Name dictionary-like lookups `value_by_key` when both roles are known, such
  as `evidence_by_sequence_id` or `sample_ids_by_group`.
- Use `is_` for state, `has_` for presence, `should_` for policy, and `can_`
  for capability.

Read `loop.md` when naming loop, lambda, closure, or anonymous-function
binders.
