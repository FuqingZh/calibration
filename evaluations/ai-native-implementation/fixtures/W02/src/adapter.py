"""Stable adapter boundary."""

from src.schema import validate_record


def accept_record(record: dict[str, str]) -> dict[str, str]:
    """Validate and return one record without rewriting caller data."""
    validate_record(record)
    return record
