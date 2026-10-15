"""Synthetic cases and command evidence shared by writable runner tests.

Each builder retains the existing payload and serialization. The function-scoped
fixture creates files only; tests apply runtime and preflight patches locally.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml


def write_fixture(root: Path, name: str = "sample") -> Path:
    fixture = root / "fixtures" / name
    fixture.mkdir(parents=True)
    (fixture / "value.txt").write_text("before\n", encoding="utf-8")
    return fixture


def case_data(**updates: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": "T01",
        "title": "Test case",
        "fixture": "sample",
        "prompt": "Fix the fixture.",
        "verify": [["python", "-c", "print('ok')"]],
        "allowed_changes": ["value.txt"],
        "required_changes": ["value.txt"],
    }
    data.update(updates)
    return data


def write_case(path: Path, **updates: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(case_data(**updates), sort_keys=False),
        encoding="utf-8",
    )
    return path


def command_event(command: str, exit_code: int, output: str = "") -> str:
    """Build one minimal captured Codex command_execution event."""
    return json.dumps(
        {
            "type": "item.completed",
            "item": {
                "type": "command_execution",
                "command": command,
                "exit_code": exit_code,
                "aggregated_output": output,
            },
        }
    )


def broker_event(family: str, argv: list[str], exit_code: int) -> dict[str, object]:
    return {
        "execution_id": 1,
        "family": family,
        "argv": argv,
        "argv_sha256": hashlib.sha256("\0".join(argv).encode()).hexdigest(),
        "cwd": "/workspace",
        "execution_context": "executor_sandbox",
        "exit_code": exit_code,
    }


@pytest.fixture
def evaluation_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "evaluation"
    write_fixture(root)
    return root
