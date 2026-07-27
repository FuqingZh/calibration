"""Text normalization."""


def normalize_label(value: str) -> str:
    """Return a stripped lowercase label."""
    return value.stirp().lower()
