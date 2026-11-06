# Naming Sources

Use existing contracts and mature ecosystem guidance for naming decisions.
Read only the source needed for the current language, framework, or interface.

## Authority

- Preserve published compatibility and names required by protocols, overrides,
  serialization, or framework integration. A style preference does not authorize
  renaming an existing interface.
- Follow repository conventions and the API being extended. For new surfaces
  without an established convention, use the relevant language or framework
  guidance below.
- Let configured formatters and linters check mechanical conventions. Keep any
  additional domain vocabulary or naming policy in the owning repository.

## Language And Framework Sources

- Python: [PEP 8 naming conventions](https://peps.python.org/pep-0008/#naming-conventions).
- Rust: [Rust API Guidelines: Naming](https://rust-lang.github.io/api-guidelines/naming.html).
- R projects adopting tidyverse conventions:
  [Tidyverse style guide](https://style.tidyverse.org/syntax.html#object-names).
  Follow existing base R or other ecosystem conventions where they apply.
- For other languages or framework-specific interfaces, consult their official
  guidance when needed. If no applicable source is available, state the gap and
  follow the nearest existing repository convention.

## Other Contracts

- CLI options: [CLI sources](cli.md).
- Versions and release compatibility: [version guidance](version.md).
- Schema fields and exported headers: [schema guidance](schema.md).
- Workflow artifact filenames: [artifact guidance](artifact.md).
- Git branches: [collaboration sources](../docs/workflow/branch_and_pr_collaboration/20260602-v1.0.md).

The former function, method, type, variable, loop, and branch paths remain as
compatibility pointers. They add no separate naming taxonomy.
