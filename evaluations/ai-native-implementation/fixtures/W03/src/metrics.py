"""Observed-value metrics."""


def mean_observed(values: list[float | None]) -> float:
    """Return the mean of observed values, or zero when none are observed."""
    return sum(values) / len(values)
