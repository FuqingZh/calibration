"""Verify shared Ruff fallback adoption and local-contract precedence."""

import tomllib
from pathlib import Path


def load_configuration(path: str) -> dict[str, object]:
    return tomllib.loads(Path(path).read_text(encoding="utf-8"))


fallback = load_configuration("fallback-project/pyproject.toml")
local = load_configuration("local-project/pyproject.toml")

expected_fallback = ["E", "F", "I", "UP", "B", "SIM", "RUF"]
fallback_ruff = fallback["tool"]["ruff"]
fallback_lint = fallback_ruff["lint"]
actual_fallback = fallback_lint["select"]
if actual_fallback != expected_fallback:
    raise SystemExit(f"fallback Ruff selection mismatch: {actual_fallback!r}")

if fallback_ruff.get("preview") is True or fallback_lint.get("preview") is True:
    raise SystemExit("fallback project must not enable Ruff preview")

expected_local = ["E", "F", "S"]
actual_local = local["tool"]["ruff"]["lint"]["select"]
if actual_local != expected_local:
    raise SystemExit(f"local Ruff selection changed: {actual_local!r}")
