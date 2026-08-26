from __future__ import annotations

import json
import os
import stat
import subprocess
import threading
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

from scripts import run_writable_agent_eval as evaluation
from scripts.run_writable_agent_eval import BrokerEvent, CaseSpec, EvaluationError


def _case() -> CaseSpec:
    return CaseSpec(
        case_id="F01",
        title="FIFO broker coverage",
        fixture="sample",
        prompt="Exercise the broker.",
        verify=(("true",),),
        allowed_changes=frozenset({"value.txt"}),
        required_changes=frozenset({"value.txt"}),
        command_contract={"aliases": {"focused_test": [["check"]]}},
    )


def _broker(tmp_path: Path) -> evaluation.CommandBroker:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    return evaluation.CommandBroker(_case(), workspace, runtime, "run")


def _event() -> BrokerEvent:
    return BrokerEvent(
        execution_id=1,
        family="focused_test",
        argv=("check",),
        argv_sha256="hash",
        cwd="/workspace",
        execution_context="executor_sandbox",
        exit_code=0,
        stdout="ok\n",
        stderr="",
    )


def test_fifo_broker_rejects_invalid_protocol_shapes_without_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only an exact frame can produce a correlated accepted reply."""
    broker = _broker(tmp_path)
    replies: list[dict[str, object]] = []
    monkeypatch.setattr(broker, "_write_reply", replies.append)

    invalid = (
        {"protocol_version": 1, "request_id": "0" * 64, "argv": ["check"], "x": 1},
        {"protocol_version": 2, "request_id": "0" * 64, "argv": ["check"]},
        {"protocol_version": 1, "request_id": "0" * 64, "argv": "check"},
        {"protocol_version": 1, "request_id": "0" * 64, "argv": [""]},
    )
    for payload in invalid:
        broker._handle_request(json.dumps(payload).encode("utf-8"))

    assert broker.events == []
    assert all(reply["accepted"] is False for reply in replies)
    assert all(reply["reason"] == "broker_error" for reply in replies)

    def exact_alias(argv: tuple[str, ...], request_id: str) -> BrokerEvent:
        assert argv == ("check",)
        assert request_id == "a" * 64
        return _event()

    monkeypatch.setattr(broker, "execute", exact_alias)
    broker._handle_request(
        json.dumps(
            {"protocol_version": 1, "request_id": "a" * 64, "argv": ["check"]}
        ).encode("utf-8")
    )
    assert replies[-1]["accepted"] is True
    assert replies[-1]["request_id"] == "a" * 64


def test_fifo_broker_fails_closed_when_transport_cannot_deliver(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Transport faults are recorded rather than converted into broker evidence."""
    broker = _broker(tmp_path)
    reply: dict[str, object] = {
        "protocol_version": 1,
        "request_id": "a" * 64,
        "accepted": False,
    }

    monkeypatch.setattr(evaluation, "BROKER_FRAME_LIMIT_BYTES", 1)
    broker._write_reply(reply)
    assert broker.errors == ["broker response is too large"]

    monkeypatch.setattr(evaluation, "BROKER_FRAME_LIMIT_BYTES", 1024)
    broker._write_reply(reply)
    assert broker.errors[-1] == "broker response FIFO is unavailable"

    broker._response_fd = 9
    writes: list[bytes] = []

    def blocked_once(_descriptor: int, payload: bytes) -> int:
        writes.append(payload)
        if len(writes) == 1:
            raise BlockingIOError
        return len(payload)

    monkeypatch.setattr(evaluation.os, "write", blocked_once)

    def no_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(evaluation.time, "sleep", no_sleep)
    broker._write_reply(reply)
    assert len(writes) == 2

    def broken_writer(_descriptor: int, _payload: bytes) -> int:
        raise OSError("closed")

    monkeypatch.setattr(evaluation.os, "write", broken_writer)
    broker._write_reply(reply)
    assert "broker reply failed: closed" in broker.errors

    monkeypatch.setattr(evaluation, "BROKER_FRAME_TIMEOUT_SECONDS", 0.0)
    broker._write_reply(reply)
    assert "broker response timed out" in broker.errors

    monkeypatch.setattr(evaluation, "BROKER_MAX_ERRORS", len(broker.errors))
    broker._record_error("one error too many")
    assert broker._stopping.is_set()
    assert "one error too many" not in broker.errors


@pytest.mark.parametrize(
    "mode", ["empty", "blocked", "oversized", "unavailable", "read-unavailable"]
)
def test_fifo_broker_drops_incomplete_or_oversized_request_frames(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    """A non-frame request never reaches command execution."""
    broker = _broker(tmp_path)
    calls = 0

    def select_once(*_args: object) -> tuple[list[int], list[int], list[int]]:
        nonlocal calls
        calls += 1
        if mode == "unavailable":
            raise OSError("request FIFO disappeared")
        if calls == 1:
            return ([7], [], [])
        broker._stopping.set()
        return ([], [], [])

    def read_frame(_descriptor: int, _size: int) -> bytes:
        if mode == "read-unavailable":
            broker._stopping.set()
            raise OSError("request FIFO closed")
        if mode == "blocked":
            raise BlockingIOError
        if mode == "oversized":
            return b"x" * (evaluation.BROKER_PIPE_BUF_BYTES + 1)
        return b""

    monkeypatch.setattr(evaluation.select, "select", select_once)
    monkeypatch.setattr(evaluation.os, "read", read_frame)
    broker._serve(7)

    assert broker.events == []
    if mode == "oversized":
        assert broker.errors == ["broker request is too large"]
    else:
        assert broker.errors == []


def test_fifo_broker_surfaces_unexpected_request_read_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker(tmp_path)

    def readable(*_args: object) -> tuple[list[int], list[int], list[int]]:
        return ([7], [], [])

    def broken_read(_descriptor: int, _size: int) -> bytes:
        raise OSError("unexpected FIFO failure")

    monkeypatch.setattr(evaluation.select, "select", readable)
    monkeypatch.setattr(evaluation.os, "read", broken_read)

    with pytest.raises(OSError, match="unexpected FIFO failure"):
        broker._serve(7)


def test_fifo_broker_detects_unsafe_transport_and_shutdown_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unsafe files and a stuck service leave no reusable transport behind."""
    broker = _broker(tmp_path)

    def regular_file_stat(_path: Path) -> os.stat_result:
        return os.stat_result((stat.S_IFREG | 0o600, 0, 0, 0, 0, 0, 0, 0, 0, 0))

    monkeypatch.setattr(evaluation.os, "lstat", regular_file_stat)
    with pytest.raises(EvaluationError, match="unsafe file type"):
        broker.start()
    assert not any(broker.runtime.iterdir())

    class StuckServer:
        def join(self, timeout: float) -> None:
            assert timeout > 0

        def is_alive(self) -> bool:
            return True

    broker._thread = cast(threading.Thread, StuckServer())
    with pytest.raises(EvaluationError, match="server did not stop"):
        broker.close()
    assert not any(broker.runtime.iterdir())
    assert "broker server did not stop within deadline" in broker.errors


def test_fifo_broker_stops_processes_on_deadline_or_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A stopped broker cannot start or preserve another canonical check."""
    broker = _broker(tmp_path)
    monkeypatch.setattr(evaluation, "BROKER_MAX_EVENTS", 0)
    with pytest.raises(EvaluationError, match="event budget exceeded"):
        broker.execute(("check",))
    assert broker.events == []
    assert broker._stopping.is_set()

    timeout_root = tmp_path / "timeout"
    timeout_root.mkdir()
    timeout_broker = _broker(timeout_root)

    class NeverStops:
        pid = 1

        @staticmethod
        def poll() -> None:
            return None

        @staticmethod
        def wait(*, timeout: float) -> int:
            del timeout
            raise subprocess.TimeoutExpired("check", 0)

    timeout_broker._active_process = cast(subprocess.Popen[bytes], NeverStops())

    def no_kill(_process: subprocess.Popen[bytes]) -> None:
        return None

    monkeypatch.setattr(timeout_broker, "_kill_process_tree", no_kill)
    with pytest.raises(EvaluationError, match="did not stop"):
        timeout_broker.close()
    assert "broker check did not stop within deadline" in timeout_broker.errors


def test_fifo_broker_refuses_checks_after_shutdown_crosses_lock_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Shutdown between alias matching and launch must not run a check."""
    broker = _broker(tmp_path)

    class StopBeforeLaunch:
        def __enter__(self) -> StopBeforeLaunch:
            broker._stopping.set()
            return self

        def __exit__(
            self,
            _exc_type: object,
            _exc_value: object,
            _traceback: object,
        ) -> bool:
            return False

    broker._process_lock = cast(threading.Lock, StopBeforeLaunch())
    with pytest.raises(EvaluationError, match="broker is stopping"):
        broker.execute(("check",))
    assert broker.events == []


def test_fifo_broker_refuses_checks_when_already_stopping(tmp_path: Path) -> None:
    broker = _broker(tmp_path)
    broker._stopping.set()

    with pytest.raises(EvaluationError, match="broker is stopping"):
        broker.execute(("check",))


def test_fifo_broker_executes_with_mocked_process_runtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Process lifecycle logic is covered without requiring host bubblewrap."""
    broker = _broker(tmp_path)

    class Pipe:
        closed = False

        def close(self) -> None:
            self.closed = True

    class Process:
        stdout = Pipe()
        stderr = Pipe()

    process = Process()

    def command(_argv: tuple[str, ...]) -> list[str]:
        return ["synthetic-check"]

    def popen(*_args: object, **_kwargs: object) -> Process:
        return process

    def capture(_process: subprocess.Popen[bytes]) -> tuple[str, str, int]:
        return ("stdout", "stderr", 7)

    monkeypatch.setattr(broker, "_inner_command", command)
    monkeypatch.setattr(evaluation.subprocess, "Popen", popen)
    monkeypatch.setattr(broker, "_read_capture", capture)

    event = broker.execute(("check",), "a" * 64)

    assert event is not None
    assert event.exit_code == 7
    assert event.stdout == "stdout"
    assert event.stderr == "stderr"
    assert process.stdout.closed is True
    assert process.stderr.closed is True

    oversized_root = tmp_path / "oversized"
    oversized_root.mkdir()
    oversized = _broker(oversized_root)
    oversized_process = Process()

    def oversized_popen(*_args: object, **_kwargs: object) -> Process:
        return oversized_process

    def reply_does_not_fit(_event: BrokerEvent, _request_id: str) -> bool:
        return False

    monkeypatch.setattr(oversized, "_inner_command", command)
    monkeypatch.setattr(evaluation.subprocess, "Popen", oversized_popen)
    monkeypatch.setattr(oversized, "_read_capture", capture)
    monkeypatch.setattr(oversized, "_accepted_reply_fits", reply_does_not_fit)
    with pytest.raises(EvaluationError, match="broker response is too large"):
        oversized.execute(("check",))


def test_fifo_broker_closes_mocked_pipes_after_capture_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker(tmp_path)

    class Pipe:
        closed = False

        def close(self) -> None:
            self.closed = True

    class Process:
        pid = 99_999_999
        stdout = Pipe()
        stderr = Pipe()

        def wait(self, timeout: float | None = None) -> int:
            del timeout
            return 1

    process = Process()

    def command(_argv: tuple[str, ...]) -> list[str]:
        return ["synthetic-check"]

    def popen(*_args: object, **_kwargs: object) -> Process:
        return process

    def capture(_process: subprocess.Popen[bytes]) -> tuple[str, str, int]:
        raise EvaluationError("capture failed")

    def no_kill(_process: subprocess.Popen[bytes]) -> None:
        return None

    monkeypatch.setattr(broker, "_inner_command", command)
    monkeypatch.setattr(evaluation.subprocess, "Popen", popen)
    monkeypatch.setattr(broker, "_read_capture", capture)
    monkeypatch.setattr(broker, "_kill_process_tree", no_kill)

    with pytest.raises(EvaluationError, match="capture failed"):
        broker.execute(("check",))
    assert process.stdout.closed is True
    assert process.stderr.closed is True


def test_fifo_broker_builds_inner_boundary_without_host_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker(tmp_path)

    def bwrap_path(name: str) -> str | None:
        return "/usr/bin/bwrap" if name == "bwrap" else None

    monkeypatch.setattr(evaluation.shutil, "which", bwrap_path)
    command = broker._inner_command(("check",))

    assert command[:3] == ["bwrap", "--die-with-parent", "--unshare-pid"]
    assert "--unshare-net" in command
    assert command[-1] == "check"

    def unavailable(_name: str) -> None:
        return None

    monkeypatch.setattr(evaluation.shutil, "which", unavailable)
    with pytest.raises(EvaluationError, match="bwrap is required"):
        broker._inner_command(("check",))


def test_fifo_broker_converts_process_wait_timeout_to_failed_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A launch-time timeout never creates observable command evidence."""
    broker = _broker(tmp_path)

    class Process:
        stdout = None
        stderr = None

    def expired_capture(_process: subprocess.Popen[bytes]) -> tuple[str, str, int]:
        raise subprocess.TimeoutExpired("check", 0)

    def inner_command(_argv: tuple[str, ...]) -> list[str]:
        return ["check"]

    def process(*_args: object, **_kwargs: object) -> Process:
        return Process()

    monkeypatch.setattr(broker, "_inner_command", inner_command)
    monkeypatch.setattr(evaluation.subprocess, "Popen", process)
    monkeypatch.setattr(broker, "_read_capture", expired_capture)
    with pytest.raises(EvaluationError, match="broker check timed out"):
        broker.execute(("check",))
    assert broker.events == []


def test_fifo_broker_capture_drains_both_streams_before_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A completed check records both streams only after both pipes close."""
    broker = _broker(tmp_path)

    class Pipe:
        def __init__(self, descriptor: int) -> None:
            self.descriptor = descriptor

        def fileno(self) -> int:
            return self.descriptor

    class Process:
        stdout = Pipe(31)
        stderr = Pipe(32)

        @staticmethod
        def poll() -> None:
            return None

        @staticmethod
        def wait(*, timeout: float) -> int:
            assert timeout > 0
            return 7

    reads = {31: [b"stdout", b""], 32: [b"stderr", b""]}

    def readable(
        descriptors: list[int],
        _write: list[object],
        _error: list[object],
        _timeout: float,
    ) -> tuple[list[int], list[int], list[int]]:
        return ([next(fd for fd in descriptors if reads[fd])], [], [])

    def read(descriptor: int, _size: int) -> bytes:
        return reads[descriptor].pop(0)

    def no_set_blocking(_fd: int, _enabled: bool) -> None:
        return None

    monkeypatch.setattr(evaluation.os, "set_blocking", no_set_blocking)
    monkeypatch.setattr(evaluation.select, "select", readable)
    monkeypatch.setattr(evaluation.os, "read", read)
    assert broker._read_capture(cast(subprocess.Popen[bytes], Process())) == (
        "stdout",
        "stderr",
        7,
    )


def test_fifo_broker_capture_rejects_missing_pipes_and_expired_deadlines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The broker cannot turn an unreadable or late capture into an event."""
    broker = _broker(tmp_path)

    class MissingPipes:
        stdout = None
        stderr = None

    missing_pipes = cast(subprocess.Popen[bytes], MissingPipes())
    with pytest.raises(EvaluationError, match="pipes are unavailable"):
        broker._read_capture(missing_pipes)

    class Pipe:
        def __init__(self, descriptor: int) -> None:
            self.descriptor = descriptor

        def fileno(self) -> int:
            return self.descriptor

    class Process:
        stdout = Pipe(51)
        stderr = Pipe(52)

    def no_set_blocking(_fd: int, _enabled: bool) -> None:
        return None

    monkeypatch.setattr(evaluation.os, "set_blocking", no_set_blocking)
    monkeypatch.setattr(evaluation, "BROKER_CHECK_TIMEOUT_SECONDS", 0.0)
    with pytest.raises(EvaluationError, match="broker check timed out"):
        broker._read_capture(cast(subprocess.Popen[bytes], Process()))


def test_fifo_broker_capture_ignores_spurious_readability_before_shutdown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A nonblocking read race must not emit a partial command result."""
    broker = _broker(tmp_path)

    class Pipe:
        def __init__(self, descriptor: int) -> None:
            self.descriptor = descriptor

        def fileno(self) -> int:
            return self.descriptor

    class Process:
        stdout = Pipe(61)
        stderr = Pipe(62)

        @staticmethod
        def poll() -> None:
            return None

    calls = 0

    def readable(
        _descriptors: list[int],
        _write: list[object],
        _error: list[object],
        _timeout: float,
    ) -> tuple[list[int], list[int], list[int]]:
        nonlocal calls
        calls += 1
        if calls == 1:
            return ([61], [], [])
        broker._stopping.set()
        return ([], [], [])

    def blocked_read(_descriptor: int, _size: int) -> bytes:
        raise BlockingIOError

    def no_set_blocking(_fd: int, _enabled: bool) -> None:
        return None

    monkeypatch.setattr(evaluation.os, "set_blocking", no_set_blocking)
    monkeypatch.setattr(evaluation.select, "select", readable)
    monkeypatch.setattr(evaluation.os, "read", blocked_read)
    with pytest.raises(EvaluationError, match="was stopped"):
        broker._read_capture(cast(subprocess.Popen[bytes], Process()))


def test_fifo_broker_capture_rejects_combined_overflow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker(tmp_path)

    class Pipe:
        def __init__(self, descriptor: int) -> None:
            self.descriptor = descriptor

        def fileno(self) -> int:
            return self.descriptor

    class Process:
        stdout = Pipe(81)
        stderr = Pipe(82)

        @staticmethod
        def poll() -> None:
            return None

    def readable(
        _descriptors: list[int],
        _write: list[object],
        _error: list[object],
        _timeout: float,
    ) -> tuple[list[int], list[int], list[int]]:
        return ([81], [], [])

    def oversized(_descriptor: int, _size: int) -> bytes:
        return b"xx"

    def no_set_blocking(_fd: int, _enabled: bool) -> None:
        return None

    monkeypatch.setattr(evaluation, "BROKER_CAPTURE_LIMIT_BYTES", 1)
    monkeypatch.setattr(evaluation.os, "set_blocking", no_set_blocking)
    monkeypatch.setattr(evaluation.select, "select", readable)
    monkeypatch.setattr(evaluation.os, "read", oversized)

    with pytest.raises(EvaluationError, match="output is too large"):
        broker._read_capture(cast(subprocess.Popen[bytes], Process()))


def test_fifo_broker_capture_waits_for_eof_after_process_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker(tmp_path)

    class Pipe:
        def __init__(self, descriptor: int) -> None:
            self.descriptor = descriptor

        def fileno(self) -> int:
            return self.descriptor

    class Process:
        stdout = Pipe(91)
        stderr = Pipe(92)

        @staticmethod
        def poll() -> int:
            return 0

        @staticmethod
        def wait(*, timeout: float) -> int:
            assert timeout > 0
            return 0

    calls = 0

    def readable(
        descriptors: list[int],
        _write: list[object],
        _error: list[object],
        _timeout: float,
    ) -> tuple[list[int], list[int], list[int]]:
        nonlocal calls
        calls += 1
        if calls == 1:
            return ([], [], [])
        return ([descriptors[0]], [], [])

    def eof(_descriptor: int, _size: int) -> bytes:
        return b""

    def no_set_blocking(_fd: int, _enabled: bool) -> None:
        return None

    monkeypatch.setattr(evaluation.os, "set_blocking", no_set_blocking)
    monkeypatch.setattr(evaluation.select, "select", readable)
    monkeypatch.setattr(evaluation.os, "read", eof)

    assert broker._read_capture(cast(subprocess.Popen[bytes], Process())) == (
        "",
        "",
        0,
    )


def test_fifo_broker_capture_rechecks_deadline_after_both_pipes_close(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """EOF does not permit an expired process wait deadline."""
    broker = _broker(tmp_path)

    class Pipe:
        def __init__(self, descriptor: int) -> None:
            self.descriptor = descriptor

        def fileno(self) -> int:
            return self.descriptor

    class Process:
        stdout = Pipe(71)
        stderr = Pipe(72)

        @staticmethod
        def poll() -> None:
            return None

    reads = {71: [b""], 72: [b""]}
    clock = iter((0.0, 0.0, 0.0, 2.0))

    def readable(
        descriptors: list[int],
        _write: list[object],
        _error: list[object],
        _timeout: float,
    ) -> tuple[list[int], list[int], list[int]]:
        return ([next(fd for fd in descriptors if reads[fd])], [], [])

    def read(descriptor: int, _size: int) -> bytes:
        return reads[descriptor].pop(0)

    def no_set_blocking(_fd: int, _enabled: bool) -> None:
        return None

    monkeypatch.setattr(evaluation, "BROKER_CHECK_TIMEOUT_SECONDS", 1.0)
    monkeypatch.setattr(evaluation.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(evaluation.os, "set_blocking", no_set_blocking)
    monkeypatch.setattr(evaluation.select, "select", readable)
    monkeypatch.setattr(evaluation.os, "read", read)
    with pytest.raises(EvaluationError, match="broker check timed out"):
        broker._read_capture(cast(subprocess.Popen[bytes], Process()))


@pytest.mark.parametrize("stop_after_wait", [False, True])
def test_fifo_broker_capture_rejects_late_wait_or_shutdown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stop_after_wait: bool
) -> None:
    """Pipes reaching EOF is insufficient without a timely, live process result."""
    broker = _broker(tmp_path)

    class Pipe:
        def __init__(self, descriptor: int) -> None:
            self.descriptor = descriptor

        def fileno(self) -> int:
            return self.descriptor

    class Process:
        stdout = Pipe(41)
        stderr = Pipe(42)

        @staticmethod
        def poll() -> None:
            return None

        def wait(self, *, timeout: float) -> int:
            assert timeout > 0
            if stop_after_wait:
                broker._stopping.set()
                return 0
            raise subprocess.TimeoutExpired("check", timeout)

    reads = {41: [b""], 42: [b""]}

    def readable(
        descriptors: list[int],
        _write: list[object],
        _error: list[object],
        _timeout: float,
    ) -> tuple[list[int], list[int], list[int]]:
        return ([next(fd for fd in descriptors if reads[fd])], [], [])

    def read(descriptor: int, _size: int) -> bytes:
        return reads[descriptor].pop(0)

    def no_set_blocking(_fd: int, _enabled: bool) -> None:
        return None

    monkeypatch.setattr(evaluation.os, "set_blocking", no_set_blocking)
    monkeypatch.setattr(evaluation.select, "select", readable)
    monkeypatch.setattr(evaluation.os, "read", read)
    message = "was stopped" if stop_after_wait else "timed out"
    with pytest.raises(EvaluationError, match=message):
        broker._read_capture(cast(subprocess.Popen[bytes], Process()))


def test_command_oracle_flags_bypass_after_neutral_discovery() -> None:
    """A discovery command cannot authorize a shell-level validation bypass."""
    case = replace(
        _case(),
        command_contract={
            "aliases": {"focused_test": [["check"]]},
            "required": [],
            "forbidden": [],
            "ordered_required": [],
            "wrapper_required": [],
            "covered_seams": {},
            "execution_contexts": {"focused_test": "executor_sandbox"},
        },
    )
    trajectory = json.dumps(
        {
            "type": "item.completed",
            "item": {
                "type": "command_execution",
                "command": "pwd && env CHECK=1",
                "exit_code": 0,
                "aggregated_output": "",
            },
        }
    )
    oracle = evaluation.command_oracle(case, trajectory, "run", [])
    assert any(
        "command bypass is invalid" in error
        for error in cast(list[str], oracle["errors"])
    )


def test_executor_boundary_preflight_rejects_command_tail_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The probe must preserve the exact executor command tail."""
    workspace = tmp_path / "workspace"
    output = tmp_path / "output"
    runtime = tmp_path / "runtime"
    workspace.mkdir()
    output.mkdir()
    runtime.mkdir()

    def malformed_command(*_args: object) -> list[str]:
        return ["not-codex"]

    monkeypatch.setattr(evaluation, "build_bwrap_command", malformed_command)
    with pytest.raises(EvaluationError, match="command is malformed"):
        evaluation.build_executor_boundary_preflight_command(
            _case(), workspace, output, runtime, 1234
        )


def test_executor_boundary_preflight_builds_exact_sandbox_probe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Probe construction is portable and does not execute a host sandbox."""

    def codex_command(*_args: object) -> list[str]:
        return ["codex-tail"]

    def outer_command(*_args: object) -> list[str]:
        return ["outer", "codex-tail"]

    monkeypatch.setattr(evaluation, "build_codex_command", codex_command)
    monkeypatch.setattr(evaluation, "build_bwrap_command", outer_command)

    command = evaluation.build_executor_boundary_preflight_command(
        _case(), tmp_path / "workspace", tmp_path / "output", tmp_path / "runtime", 7
    )

    assert command[0] == "outer"
    probe = command[-1]
    assert "executor-boundary-preflight-ok" in probe
    assert "127.0.0.1" in probe


@pytest.mark.parametrize(
    ("kind", "message"),
    [
        ("timeout", "preflight timed out"),
        ("nonzero", "preflight failed: rejected"),
        ("marker", "did not prove shell start"),
        ("loopback", "permitted loopback network"),
    ],
)
def test_executor_boundary_preflight_fails_closed_on_probe_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str, message: str
) -> None:
    """Every failed probe outcome prevents the executor route from being trusted."""
    workspace = tmp_path / "workspace"
    output = tmp_path / "output"
    runtime = tmp_path / "runtime"
    workspace.mkdir()
    output.mkdir()
    runtime.mkdir()

    class Client:
        closed = False

        def close(self) -> None:
            self.closed = True

    client = Client()

    class Listener:
        def bind(self, _address: tuple[str, int]) -> None:
            return None

        def listen(self, _backlog: int) -> None:
            return None

        def settimeout(self, _timeout: float) -> None:
            return None

        def getsockname(self) -> tuple[str, int]:
            return ("127.0.0.1", 2345)

        def accept(self) -> tuple[Client, tuple[str, int]]:
            if kind == "loopback":
                return (client, ("127.0.0.1", 3456))
            raise TimeoutError

        def close(self) -> None:
            return None

    def command(*_args: object) -> list[str]:
        return ["probe"]

    def run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if kind == "timeout":
            raise subprocess.TimeoutExpired("probe", 0)
        if kind == "nonzero":
            return subprocess.CompletedProcess(["probe"], 1, "", "rejected")
        stdout = "wrong" if kind == "marker" else "executor-boundary-preflight-ok"
        return subprocess.CompletedProcess(["probe"], 0, stdout, "")

    def listener_socket(*_args: object) -> Listener:
        return Listener()

    monkeypatch.setattr(evaluation.socket, "socket", listener_socket)
    monkeypatch.setattr(
        evaluation, "build_executor_boundary_preflight_command", command
    )
    monkeypatch.setattr(evaluation.subprocess, "run", run)
    with pytest.raises(EvaluationError, match=message):
        evaluation.run_executor_boundary_preflight(_case(), workspace, output, runtime)
    assert not (output / ".executor-boundary-preflight-private").exists()
    if kind == "loopback":
        assert client.closed


def test_executor_boundary_preflight_accepts_denied_loopback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    output = tmp_path / "output"
    runtime = tmp_path / "runtime"
    workspace.mkdir()
    output.mkdir()
    runtime.mkdir()

    class Listener:
        def bind(self, _address: tuple[str, int]) -> None:
            return None

        def listen(self, _backlog: int) -> None:
            return None

        def settimeout(self, _timeout: float) -> None:
            return None

        def getsockname(self) -> tuple[str, int]:
            return ("127.0.0.1", 2345)

        def accept(self) -> tuple[object, tuple[str, int]]:
            raise TimeoutError

        def close(self) -> None:
            return None

    def listener_socket(*_args: object) -> Listener:
        return Listener()

    def command(*_args: object) -> list[str]:
        return ["probe"]

    def run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            ["probe"], 0, "executor-boundary-preflight-ok\n", ""
        )

    monkeypatch.setattr(evaluation.socket, "socket", listener_socket)
    monkeypatch.setattr(
        evaluation, "build_executor_boundary_preflight_command", command
    )
    monkeypatch.setattr(evaluation.subprocess, "run", run)

    evaluation.run_executor_boundary_preflight(_case(), workspace, output, runtime)

    assert not (output / ".executor-boundary-preflight-private").exists()


def test_run_case_uses_runner_issued_identity_not_workspace_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The executor environment receives the output-directory identity only."""
    fixture_root = tmp_path / "fixtures" / "sample"
    fixture_root.mkdir(parents=True)
    (fixture_root / "value.txt").write_text("before\n", encoding="utf-8")
    case = replace(_case(), fixture_root=fixture_root.parent, command_contract=None)
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    observed: dict[str, str] = {}

    class QuietBroker:
        def __init__(self, *_args: object) -> None:
            self.events: list[BrokerEvent] = []
            self.errors: list[str] = []

        def start(self) -> None:
            return None

        def close(self) -> None:
            return None

    def model(
        command: list[str], cwd: Path, env: dict[str, str]
    ) -> subprocess.CompletedProcess[str]:
        del cwd
        observed["run_id"] = env["CALIBRATION_EVAL_RUN_ID"]
        (workspace / "value.txt").write_text("after\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    def no_install(*_args: object) -> None:
        return None

    def no_create_shims(*_args: object) -> None:
        return None

    def no_preflight(*_args: object) -> None:
        return None

    def bwrap_command(*_args: object) -> list[str]:
        return ["codex"]

    monkeypatch.setattr(evaluation, "CommandBroker", cast(Any, QuietBroker))
    monkeypatch.setattr(evaluation, "install_arm_home", no_install)
    monkeypatch.setattr(evaluation, "create_broker_shims", no_create_shims)
    monkeypatch.setattr(evaluation, "run_executor_boundary_preflight", no_preflight)
    monkeypatch.setattr(evaluation, "build_bwrap_command", bwrap_command)
    monkeypatch.setattr(evaluation, "_run_model", model)
    output = tmp_path / "untrusted-workspace-name"
    evaluation.run_case(
        case, workspace, tmp_path, tmp_path / "auth", output, "m", "low"
    )
    assert observed["run_id"] == output.name


def test_run_case_rejects_preflight_broker_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Preflight transport activity is invalid evidence, even if the probe returns."""
    fixture_root = tmp_path / "fixtures" / "sample"
    fixture_root.mkdir(parents=True)
    (fixture_root / "value.txt").write_text("before\n", encoding="utf-8")
    case = replace(_case(), fixture_root=fixture_root.parent, command_contract=None)
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)

    class BrokerWithPreflightEvent:
        def __init__(self, *_args: object) -> None:
            self.events = [_event()]
            self.errors: list[str] = []

        def start(self) -> None:
            return None

        def close(self) -> None:
            return None

    def no_op(*_args: object) -> None:
        return None

    monkeypatch.setattr(
        evaluation, "CommandBroker", cast(Any, BrokerWithPreflightEvent)
    )
    monkeypatch.setattr(evaluation, "install_arm_home", no_op)
    monkeypatch.setattr(evaluation, "create_broker_shims", no_op)
    monkeypatch.setattr(evaluation, "run_executor_boundary_preflight", no_op)
    with pytest.raises(EvaluationError, match="broker evidence is invalid"):
        evaluation.run_case(
            case,
            workspace,
            tmp_path,
            tmp_path / "auth",
            tmp_path / "output",
            "m",
            "low",
        )
