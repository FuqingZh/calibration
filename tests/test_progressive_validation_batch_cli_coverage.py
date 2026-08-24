from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import run_progressive_validation_selection_eval as batch


@pytest.mark.parametrize(
    ("command", "arguments", "target"),
    [
        (
            "freeze",
            [
                "--baseline-commit",
                "a",
                "--candidate-commit",
                "b",
                "--model",
                "m",
                "--reasoning-effort",
                "low",
            ],
            "freeze_batch",
        ),
        ("verify", [], "verify_freeze"),
        ("run-smoke", ["--auth-file", "auth"], "run_smoke"),
        ("run-one", ["--auth-file", "auth", "--slot-id", "slot"], "run_manifest_slot"),
        ("smoke-status", [], "smoke_status"),
        (
            "project",
            ["--private-result", "private", "--public-path", "public"],
            "project_public",
        ),
        (
            "summarize",
            ["--projection", "one", "--projection", "two"],
            "summarize_public",
        ),
    ],
)
def test_main_routes_each_declared_cli_command(
    command: str,
    arguments: list[str],
    target: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    received: dict[str, object] = {}

    def fake(*args: object, **kwargs: object) -> dict[str, object]:
        received["args"] = args
        received["kwargs"] = kwargs
        return {"route": target}

    monkeypatch.setattr(batch, target, fake)
    argv = [command]
    if command in {"freeze", "verify", "run-smoke", "run-one", "smoke-status"}:
        argv.extend(("--private-root", "/private"))
    argv.extend(arguments)
    assert batch.main(argv) == 0
    payload = json.loads(capsys.readouterr().out)
    if command == "run-smoke":
        assert payload["completed"]["route"] == target
    else:
        assert payload["route"] == target
    assert received


def test_main_reports_batch_errors_as_machine_readable_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def rejected(_root: Path) -> dict[str, object]:
        raise batch.BatchError("freeze mismatch")

    monkeypatch.setattr(batch, "verify_freeze", rejected)
    assert batch.main(["verify", "--private-root", "/private"]) == 1
    assert json.loads(capsys.readouterr().out) == {
        "error": "freeze mismatch",
        "state": "failed",
    }
