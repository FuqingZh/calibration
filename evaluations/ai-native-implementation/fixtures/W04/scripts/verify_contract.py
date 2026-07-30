"""Verify the public slug helper contract."""

from src.slug import normalize_slug


expected_doc = "Normalize a value into a URL slug."
if normalize_slug.__doc__ != expected_doc:
    raise SystemExit(f"normalize_slug doc contract mismatch: {normalize_slug.__doc__!r}")
