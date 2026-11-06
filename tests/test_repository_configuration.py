from __future__ import annotations

import tomllib

from tests.support import REPOSITORY_ROOT


def test_repository_ruff_baseline_is_explicit_and_stable() -> None:
    configuration = tomllib.loads(
        (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    ruff = configuration["tool"]["ruff"]
    assert ruff["lint"]["select"] == ["E", "F", "I", "UP", "B", "SIM", "RUF"]
    assert not ruff.get("preview", False)
    assert not ruff["lint"].get("preview", False)
