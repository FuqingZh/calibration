"""Record validation."""


def validate_record(record: dict[str, str]) -> None:
    """Validate required record fields."""
    missing = {"name", "note"} - record.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
