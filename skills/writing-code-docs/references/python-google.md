# Python Google-Style Docstrings

Use this reference when writing or reviewing non-trivial Python docstrings.

## Section Policy

- Summary: say what contract the callable offers, not how the implementation
  works.
- `Args:`: document parameters only when semantics, units, shape, mutation,
  default behavior, or valid values are not obvious from the signature.
- `Returns:` / `Yields:`: document structure, stability, ordering, units, and
  ownership, not just the type name.
- `Raises:`: document expected caller-visible failures. Do not list defensive
  implementation errors that callers cannot act on.
- `Examples:`: use for library-facing APIs. Cover each distinct usage mode with
  the smallest stable example that proves that mode.
- `Notes:`: use for maintenance-facing workflow boundaries, business path,
  ownership, contract, compatibility, and technical rationale.

## Example Coverage

Short examples are a shape rule, not a count limit.

Good examples:

- are realistic and stable
- teach one usage mode each
- use real API names and plausible data
- show the result when it clarifies the contract
- avoid repeating the same point in multiple forms

Do not omit a real usage mode only to keep the section short. Prefer several
short examples over one long example that mixes unrelated modes.

## Library-Facing Function

Too thin:

```python
def parse_range(value: str) -> tuple[int, int]:
    """Parse a range string."""
```

Useful:

```python
def parse_range(value: str) -> tuple[int, int]:
    """Parse an inclusive integer range.

    Args:
        value: Range text in ``START-END`` form. Whitespace around the bounds is
            ignored.

    Returns:
        The inclusive lower and upper bounds.

    Raises:
        ValueError: If either bound is missing, non-integer, or the lower bound
            is greater than the upper bound.

    Examples:
        >>> parse_range("1-3")
        (1, 3)
    """
```

Why it works: the docstring defines the accepted syntax, inclusivity, whitespace
handling, and caller-visible failure behavior.

## Multi-Mode Public API

Several short examples are better than one overloaded example when the API has
distinct usage modes.

```python
def read_table(path: str, *, columns: list[str] | None = None) -> Table:
    """Read a tabular file.

    Args:
        path: Path to a CSV or TSV file. The delimiter is inferred from the file
            extension.
        columns: Optional subset of columns to load. Column order is preserved.

    Returns:
        A table with rows in file order.

    Examples:
        Read a complete table:

        >>> read_table("samples.tsv")
        Table(columns=["sample", "group"])

        Load only selected columns:

        >>> read_table("samples.tsv", columns=["sample"])
        Table(columns=["sample"])
    """
```

Why it works: each example proves a different user-facing mode. It does not add
a third example for another ordinary TSV file, because that would teach the same
point.

## Maintenance-Facing Boundary

Do not force `Examples:` when the callable is a workflow boundary whose real
inputs are product manifests, stage artifacts, or environment-specific paths.

```python
def build_report_package(manifest: DeliveryManifest, output_dir: Path) -> None:
    """Build the customer-facing report package from validated artifacts.

    This is the boundary between analysis execution and delivery packaging.
    Keep package layout decisions here so upstream stages do not need to know
    report delivery rules.

    Args:
        manifest: Validated delivery manifest. The manifest is the package
            completeness contract.
        output_dir: Destination directory for the generated package.

    Notes:
        Do not scan stage directories here to discover missing files. Package
        completeness is a product contract owned by the manifest, not a
        filesystem discovery rule.
    """
```

Why it works: the reader learns where the function sits in the business path,
what contract it protects, and which tempting simplification would break the
product boundary.
