"""Focused recovery coverage for the no-model executor boundary preflight."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Never, cast

import pytest

from scripts import run_writable_agent_eval as evaluation
from scripts.run_writable_agent_eval import CaseSpec, EvaluationError


def _case(command_contract: dict[str, object] | None = None) -> CaseSpec:
    return CaseSpec(
        case_id="boundary",
        title="boundary coverage",
        fixture="fixture",
        prompt="unused",
        verify=(("true",),),
        allowed_changes=frozenset({"value.txt"}),
        required_changes=frozenset({"value.txt"}),
        command_contract=command_contract,
    )


class _FakeClient:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class _FakeListener:
    def __init__(self, client: _FakeClient | None = None) -> None:
        self.client = client
        self.closed = False
        self.timeouts: list[float] = []

    def bind(self, address: tuple[str, int]) -> None:
        assert address == ("127.0.0.1", 0)

    def listen(self, backlog: int) -> None:
        assert backlog == 1

    def settimeout(self, timeout: float) -> None:
        self.timeouts.append(timeout)

    def getsockname(self) -> tuple[str, int]:
        return ("127.0.0.1", 43123)

    def accept(self) -> tuple[_FakeClient, tuple[str, int]]:
        if self.client is None:
            raise TimeoutError
        return self.client, ("127.0.0.1", 43124)

    def close(self) -> None:
        self.closed = True


def _patch_preflight_dependencies(
    monkeypatch: pytest.MonkeyPatch, listener: _FakeListener
) -> None:
    def fake_socket(_family: int, _kind: int) -> _FakeListener:
        return listener

    def synthetic_command(
        _case: CaseSpec,
        _workspace: Path,
        _output_dir: Path,
        _runtime: Path,
        _listener_port: int,
    ) -> list[str]:
        return ["synthetic-preflight"]

    monkeypatch.setattr(evaluation.socket, "socket", fake_socket)
    monkeypatch.setattr(
        evaluation,
        "build_executor_boundary_preflight_command",
        synthetic_command,
    )


def test_neutral_prefix_still_rejects_bypass_without_broker_proof() -> None:
    case = _case(
        {
            "aliases": {"focused_test": [["pytest"]]},
            "required": [],
            "forbidden": [],
            "ordered_required": [],
            "wrapper_required": [],
            "covered_seams": {},
            "execution_contexts": {},
        }
    )
    trajectory = (
        '{"type":"item.completed","item":{"type":"command_execution",'
        '"command":"command -v pytest && /usr/bin/pytest","exit_code":0}}'
    )

    result = evaluation.command_oracle(case, trajectory, "run", [])

    assert result["valid"] is False
    errors = cast(list[str], result["errors"])
    assert any("command bypass is invalid" in error for error in errors)


def test_preflight_rejects_a_command_without_the_expected_codex_tail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def outer_command(
        _case: CaseSpec,
        _workspace: Path,
        _output_dir: Path,
        _model: str,
        _reasoning_effort: str,
        _broker_runtime: Path | None = None,
    ) -> list[str]:
        return ["outer-command"]

    monkeypatch.setattr(evaluation, "build_bwrap_command", outer_command)

    with pytest.raises(EvaluationError, match="preflight command is malformed"):
        evaluation.build_executor_boundary_preflight_command(
            _case(),
            tmp_path / "workspace",
            tmp_path / "output",
            tmp_path / "runtime",
            1,
        )


def test_preflight_timeout_is_reported_and_private_marker_is_removed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    output = tmp_path / "output"
    output.mkdir()
    listener = _FakeListener()
    _patch_preflight_dependencies(monkeypatch, listener)

    def timed_out(*_args: object, **_kwargs: object) -> Never:
        raise subprocess.TimeoutExpired("synthetic-preflight", 1)

    monkeypatch.setattr(evaluation.subprocess, "run", timed_out)

    with pytest.raises(EvaluationError, match="preflight timed out"):
        evaluation.run_executor_boundary_preflight(
            _case(), tmp_path, output, tmp_path / "runtime"
        )

    assert listener.closed is True
    assert not (output / ".executor-boundary-preflight-private").exists()


@pytest.mark.parametrize(
    ("stdout", "stderr", "expected"),
    [
        ("ignored stdout", "stderr detail", "stderr detail"),
        ("stdout fallback", "", "stdout fallback"),
        ("", "", "executor boundary preflight failed"),
    ],
)
def test_preflight_nonzero_reports_stderr_then_stdout_or_no_detail(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    stdout: str,
    stderr: str,
    expected: str,
) -> None:
    output = tmp_path / "output"
    output.mkdir()
    listener = _FakeListener()
    _patch_preflight_dependencies(monkeypatch, listener)

    def nonzero_result(
        *_args: object, **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["synthetic-preflight"], returncode=1, stdout=stdout, stderr=stderr
        )

    monkeypatch.setattr(
        evaluation.subprocess,
        "run",
        nonzero_result,
    )

    with pytest.raises(EvaluationError, match=expected):
        evaluation.run_executor_boundary_preflight(
            _case(), tmp_path, output, tmp_path / "runtime"
        )


def test_preflight_rejects_an_unexpected_success_marker(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    output = tmp_path / "output"
    output.mkdir()
    _patch_preflight_dependencies(monkeypatch, _FakeListener())

    def wrong_marker(
        *_args: object, **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["synthetic-preflight"], returncode=0, stdout="wrong marker", stderr=""
        )

    monkeypatch.setattr(
        evaluation.subprocess,
        "run",
        wrong_marker,
    )

    with pytest.raises(EvaluationError, match="did not prove shell start"):
        evaluation.run_executor_boundary_preflight(
            _case(), tmp_path, output, tmp_path / "runtime"
        )


def test_preflight_rejects_a_loopback_connection(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    output = tmp_path / "output"
    output.mkdir()
    client = _FakeClient()
    listener = _FakeListener(client)
    _patch_preflight_dependencies(monkeypatch, listener)

    def successful_result(
        *_args: object, **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["synthetic-preflight"],
            returncode=0,
            stdout="executor-boundary-preflight-ok\n",
            stderr="",
        )

    monkeypatch.setattr(
        evaluation.subprocess,
        "run",
        successful_result,
    )

    with pytest.raises(EvaluationError, match="permitted loopback network"):
        evaluation.run_executor_boundary_preflight(
            _case(), tmp_path, output, tmp_path / "runtime"
        )

    assert client.closed is True
    assert listener.closed is True
