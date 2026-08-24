#!/usr/bin/env python3
"""Run one isolated writable calibration evaluation case."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import select
import shlex
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
COMMAND_FAMILIES = frozenset(
    {
        "focused_test",
        "docs_check",
        "runtime_test",
        "repository_check",
        "complete_gate",
        "generator",
        "artifact_readback",
        "docs_only",
        "structural_check",
        "behavior_sample",
        "unrelated_suite",
        "schema_contract",
        "consumer_a",
        "consumer_b",
        "example_check",
        "host_probe",
        "diff_inspection",
        "contract_check",
        "consumer_check",
        "host_check",
    }
)
EXIT_STATES = frozenset({"zero", "nonzero", "any"})
FINAL_STATUSES = frozenset(
    {"verified_ready", "conditionally_ready", "not_yet_verified"}
)
BROKER_PIPE_BUF_BYTES = 4096
BROKER_FRAME_LIMIT_BYTES = 1_048_576
# The broker retains at most this many bytes across stdout and stderr. Child
# output uses bounded kernel pipes; the runner never materializes it on disk.
BROKER_CAPTURE_LIMIT_BYTES = 262_144
BROKER_MAX_REQUESTS = 64
BROKER_MAX_EVENTS = 32
BROKER_MAX_ERRORS = 32
BROKER_PROCESS_POLL_SECONDS = 0.01
BROKER_FRAME_TIMEOUT_SECONDS = 5.0
BROKER_LOCK_TIMEOUT_SECONDS = 5.0
BROKER_CHECK_TIMEOUT_SECONDS = 120.0
BOUNDARY_PREFLIGHT_TIMEOUT_SECONDS = 30.0
MODEL_EXECUTION_TIMEOUT_SECONDS = 900.0
SHELL_WRAPPER_NAME = "executor-shell"
SHELL_MANIFEST_NAME = "executor-shell-manifest.json"
REAL_SHELL_DIRECTORY = "real-shell"
EXECUTOR_PERMISSION_PROFILE = "evaluation_runner"
EXECUTOR_PERMISSION_PROFILE_CONFIG = (
    'permissions={evaluation_runner={extends=":workspace",'
    'filesystem={"/output"="deny"},network={enabled=false}}}'
)
EXECUTOR_DEFAULT_PERMISSIONS_CONFIG = 'default_permissions="evaluation_runner"'


def _valid_request_id(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _encode_broker_reply(reply: Mapping[str, object]) -> bytes:
    """Serialize the exact newline-framed response used for FIFO delivery."""
    return (json.dumps(reply, separators=(",", ":")) + "\n").encode("utf-8")


def _delivery_receipt_line(token: str) -> str:
    """Return the exact shim line that corroborates an accepted delivery."""
    return f"CALIBRATION_BROKER_RECEIPT:{token}"


def _delivery_receipt_lines(output: str) -> list[str]:
    """Extract only structured delivery receipts from untrusted aggregate output."""
    prefix = "CALIBRATION_BROKER_RECEIPT:"
    return [line for line in output.splitlines() if line.startswith(prefix)]


class _PayloadValidator(Protocol):
    def validate(self, instance: object) -> None: ...


@dataclass(frozen=True)
class CaseSpec:
    """One writable evaluation case and its deterministic contract."""

    case_id: str
    title: str
    fixture: str
    prompt: str
    verify: tuple[tuple[str, ...], ...]
    allowed_changes: frozenset[str]
    required_changes: frozenset[str]
    fixture_root: Path = Path(".")
    command_contract: dict[str, object] | None = None
    final_contract: dict[str, object] | None = None


class EvaluationError(RuntimeError):
    """Raised when an evaluation input or environment is invalid."""


@dataclass(frozen=True)
class BrokerEvent:
    """One check actually started by the runner-owned command broker."""

    execution_id: int
    family: str
    argv: tuple[str, ...]
    argv_sha256: str
    cwd: str
    execution_context: str
    exit_code: int
    stdout: str
    stderr: str
    # Kept only in runner memory so the oracle can corroborate shim delivery.
    # It is deliberately absent from result payloads and broker event mappings.
    delivery_receipt: str | None = None


class CommandBroker:
    """Execute exact command aliases received through private runner FIFOs."""

    def __init__(
        self, case: CaseSpec, workspace: Path, runtime: Path, run_id: str
    ) -> None:
        self.case = case
        self.workspace = workspace
        self.runtime = runtime
        self.run_id = run_id
        self.request_path = runtime / "request.fifo"
        self.response_path = runtime / "response.fifo"
        self.lock_path = runtime / "broker.lock"
        self.events: list[BrokerEvent] = []
        self.errors: list[str] = []
        self._lock = threading.Lock()
        self._request_fd: int | None = None
        self._response_fd: int | None = None
        self._request_count = 0
        self._thread: threading.Thread | None = None
        self._stopping = threading.Event()
        self._process_lock = threading.Lock()
        self._active_process: subprocess.Popen[bytes] | None = None

    def start(self) -> None:
        self._stopping.clear()
        self._create_transport()
        try:
            request_fd = os.open(
                self.request_path,
                os.O_RDWR | os.O_NONBLOCK | getattr(os, "O_NOFOLLOW", 0),
            )
            response_fd = os.open(
                self.response_path,
                os.O_RDWR | os.O_NONBLOCK | getattr(os, "O_NOFOLLOW", 0),
            )
            pipe_buf = os.fpathconf(request_fd, "PC_PIPE_BUF")
            if pipe_buf < BROKER_PIPE_BUF_BYTES:
                raise EvaluationError("broker request FIFO PIPE_BUF is too small")
            aliases = cast(
                dict[str, list[list[str]]],
                (self.case.command_contract or {}).get("aliases", {}),
            )
            for commands in aliases.values():
                for argv in commands:
                    request = json.dumps(
                        {"protocol_version": 1, "request_id": "0" * 64, "argv": argv},
                        separators=(",", ":"),
                    ).encode("utf-8")
                    if len(request) + 1 > pipe_buf:
                        raise EvaluationError(
                            "canonical broker request exceeds PIPE_BUF"
                        )
            self._request_fd = request_fd
            self._response_fd = response_fd
            os.chmod(self.request_path, 0o200)
            os.chmod(self.response_path, 0o400)
            os.chmod(self.lock_path, 0o400)
        except (OSError, EvaluationError) as exc:
            for descriptor in (locals().get("request_fd"), locals().get("response_fd")):
                if isinstance(descriptor, int):
                    with suppress(OSError):
                        os.close(descriptor)
            self._request_fd = None
            self._response_fd = None
            self._remove_transport()
            raise EvaluationError(f"cannot open broker FIFO transport: {exc}") from exc
        self._thread = threading.Thread(
            target=self._serve, args=(request_fd,), daemon=True
        )
        self._thread.start()

    def close(self) -> None:
        self._stopping.set()
        failure: EvaluationError | None = None
        try:
            self._terminate_active_process()
        except EvaluationError as exc:
            failure = exc
        finally:
            if self._request_fd is not None:
                with suppress(OSError):
                    os.close(self._request_fd)
                self._request_fd = None
            if self._response_fd is not None:
                with suppress(OSError):
                    os.close(self._response_fd)
                self._response_fd = None
            if self._thread is not None:
                self._thread.join(timeout=BROKER_FRAME_TIMEOUT_SECONDS + 1.0)
                if self._thread.is_alive():
                    self._record_error("broker server did not stop within deadline")
                    failure = failure or EvaluationError(
                        "broker server did not stop within deadline"
                    )
                else:
                    self._thread = None
            self._remove_transport()
        if failure is not None:
            raise failure

    def _terminate_active_process(self) -> None:
        with self._process_lock:
            process = self._active_process
        if process is None or process.poll() is not None:
            return
        self._kill_process_tree(process)
        try:
            process.wait(timeout=BROKER_FRAME_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired as exc:
            self._record_error("broker check did not stop within deadline")
            raise EvaluationError("broker check did not stop within deadline") from exc

    @staticmethod
    def _kill_process_tree(process: subprocess.Popen[bytes]) -> None:
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)

    def _create_transport(self) -> None:
        for path in (self.request_path, self.response_path, self.lock_path):
            if path.exists() or path.is_symlink():
                raise EvaluationError(f"broker transport path already exists: {path}")
        try:
            os.mkfifo(self.request_path, 0o600)
            os.mkfifo(self.response_path, 0o600)
            descriptor = os.open(
                self.lock_path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                0o600,
            )
            os.close(descriptor)
            for path, kind in (
                (self.request_path, stat.S_IFIFO),
                (self.response_path, stat.S_IFIFO),
                (self.lock_path, stat.S_IFREG),
            ):
                if stat.S_IFMT(os.lstat(path).st_mode) != kind:
                    raise EvaluationError("broker transport has unsafe file type")
        except (OSError, EvaluationError) as exc:
            self._remove_transport()
            raise EvaluationError(
                f"cannot create broker FIFO transport: {exc}"
            ) from exc

    def _remove_transport(self) -> None:
        for path in (self.request_path, self.response_path, self.lock_path):
            with suppress(OSError):
                path.unlink()

    def _serve(self, request_fd: int) -> None:
        pending = bytearray()
        deadline: float | None = None
        while not self._stopping.is_set():
            try:
                readable, _, _ = select.select([request_fd], [], [], 0.2)
            except (OSError, ValueError):
                return
            if not readable:
                if deadline is not None and time.monotonic() >= deadline:
                    self._record_error("broker request timed out")
                    pending.clear()
                    deadline = None
                continue
            try:
                chunk = os.read(request_fd, BROKER_PIPE_BUF_BYTES)
            except BlockingIOError:
                continue
            if not chunk:
                continue
            pending.extend(chunk)
            deadline = deadline or time.monotonic() + BROKER_FRAME_TIMEOUT_SECONDS
            if len(pending) > BROKER_PIPE_BUF_BYTES:
                self._record_error("broker request is too large")
                pending.clear()
                deadline = None
                continue
            while b"\n" in pending:
                raw, _, tail = pending.partition(b"\n")
                pending = bytearray(tail)
                deadline = (
                    time.monotonic() + BROKER_FRAME_TIMEOUT_SECONDS if pending else None
                )
                self._handle_request(bytes(raw))

    def _handle_request(self, raw: bytes) -> None:
        request_id: str | None = None
        try:
            self._request_count += 1
            if self._request_count > BROKER_MAX_REQUESTS:
                self._stopping.set()
                raise EvaluationError("broker request budget exceeded")
            request = json.loads(raw.decode("utf-8"))
            if not isinstance(request, dict):
                raise ValueError("invalid broker request")
            request = cast(dict[str, object], request)
            if set(request) != {
                "protocol_version",
                "request_id",
                "argv",
            }:
                raise ValueError("invalid broker request")
            if request["protocol_version"] != 1:
                raise ValueError("unsupported broker protocol")
            if not _valid_request_id(request["request_id"]):
                raise ValueError("invalid broker request id")
            request_id = cast(str, request["request_id"])
            if not isinstance(request["argv"], list):
                raise ValueError("invalid broker argv")
            values = cast(list[object], request["argv"])
            if not values or not all(
                isinstance(value, str) and value for value in values
            ):
                raise ValueError("invalid broker argv")
            event = self.execute(
                tuple(cast(str, value) for value in values), request_id
            )
            reply: dict[str, object] = {
                "protocol_version": 1,
                "request_id": request_id,
                "accepted": event is not None,
                "reason": "accepted" if event is not None else "unrecognized",
            }
            if event is not None:
                reply.update(
                    exit_code=event.exit_code,
                    stdout=event.stdout,
                    stderr=event.stderr,
                    receipt_token=event.delivery_receipt,
                )
        except Exception as exc:
            self._record_error(f"broker request failed: {exc}")
            reply = {
                "protocol_version": 1,
                "request_id": request_id,
                "accepted": False,
                "reason": "broker_error",
            }
        self._write_reply(reply)

    def _write_reply(self, reply: dict[str, object]) -> None:
        raw = _encode_broker_reply(reply)
        if len(raw) > BROKER_FRAME_LIMIT_BYTES:
            self._record_error("broker response is too large")
            return
        if self._response_fd is None:
            self._record_error("broker response FIFO is unavailable")
            return
        try:
            offset = 0
            deadline = time.monotonic() + BROKER_FRAME_TIMEOUT_SECONDS
            while offset < len(raw):
                if time.monotonic() >= deadline:
                    raise TimeoutError("broker response timed out")
                try:
                    offset += os.write(self._response_fd, raw[offset:])
                except BlockingIOError:
                    time.sleep(0.01)
        except TimeoutError as exc:
            self._record_error(str(exc))
        except OSError as exc:
            self._record_error(f"broker reply failed: {exc}")

    def _record_error(self, message: str) -> None:
        if len(self.errors) < BROKER_MAX_ERRORS:
            self.errors.append(message)
        if len(self.errors) >= BROKER_MAX_ERRORS:
            self._stopping.set()

    def _family(self, argv: tuple[str, ...]) -> str | None:
        if self.case.command_contract is None:
            return None
        aliases = cast(
            dict[str, list[list[str]]], self.case.command_contract["aliases"]
        )
        matches = [
            family
            for family, prefixes in aliases.items()
            if any(list(argv) == prefix for prefix in prefixes)
        ]
        return matches[0] if len(matches) == 1 else None

    def execute(
        self, argv: tuple[str, ...], request_id: str = "0" * 64
    ) -> BrokerEvent | None:
        """Run an exact configured alias; unknown requests are deliberately inert."""
        family = self._family(argv)
        if family is None:
            return None
        with self._lock:
            if self._stopping.is_set():
                raise EvaluationError("broker is stopping")
            if len(self.events) >= BROKER_MAX_EVENTS:
                self._stopping.set()
                raise EvaluationError("broker event budget exceeded")
            execution_id = len(self.events) + 1
            try:
                with self._process_lock:
                    if self._stopping.is_set():
                        raise EvaluationError("broker is stopping")
                    process = subprocess.Popen(
                        self._inner_command(argv),
                        cwd=self.workspace,
                        env=_evaluation_env(),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=False,
                        start_new_session=True,
                    )
                    self._active_process = process
                try:
                    captured_stdout, captured_stderr, exit_code = self._read_capture(
                        process
                    )
                except EvaluationError:
                    self._kill_process_tree(process)
                    with suppress(subprocess.TimeoutExpired):
                        process.wait(timeout=BROKER_FRAME_TIMEOUT_SECONDS)
                    for pipe in (process.stdout, process.stderr):
                        if pipe is not None:
                            pipe.close()
                    raise
                finally:
                    with self._process_lock:
                        if self._active_process is process:
                            self._active_process = None
                for pipe in (process.stdout, process.stderr):
                    if pipe is not None:
                        pipe.close()
            except subprocess.TimeoutExpired as exc:
                raise EvaluationError("broker check timed out") from exc
            event = BrokerEvent(
                execution_id=execution_id,
                family=family,
                argv=argv,
                argv_sha256=hashlib.sha256("\0".join(argv).encode()).hexdigest(),
                cwd="/workspace",
                execution_context="executor_sandbox",
                exit_code=exit_code,
                stdout=captured_stdout,
                stderr=captured_stderr,
                delivery_receipt=secrets.token_hex(32),
            )
            if not self._accepted_reply_fits(event, request_id):
                raise EvaluationError("broker response is too large")
            self.events.append(event)
            return event

    @staticmethod
    def _accepted_reply_fits(event: BrokerEvent, request_id: str) -> bool:
        """Check the actual JSON response size before making an event observable."""
        reply = {
            "protocol_version": 1,
            "request_id": request_id,
            "accepted": True,
            "reason": "accepted",
            "exit_code": event.exit_code,
            "stdout": event.stdout,
            "stderr": event.stderr,
            "receipt_token": event.delivery_receipt,
        }
        return len(_encode_broker_reply(reply)) <= BROKER_FRAME_LIMIT_BYTES

    def _read_capture(self, process: subprocess.Popen[bytes]) -> tuple[str, str, int]:
        """Bound the combined executor output while draining both kernel pipes."""
        if process.stdout is None or process.stderr is None:
            raise EvaluationError("broker check capture pipes are unavailable")
        stdout_fd = process.stdout.fileno()
        stderr_fd = process.stderr.fileno()
        for descriptor in (stdout_fd, stderr_fd):
            os.set_blocking(descriptor, False)
        buffers = {stdout_fd: bytearray(), stderr_fd: bytearray()}
        open_descriptors = set(buffers)
        deadline = time.monotonic() + BROKER_CHECK_TIMEOUT_SECONDS
        while open_descriptors:
            if self._stopping.is_set():
                raise EvaluationError("broker check was stopped")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise EvaluationError("broker check timed out")
            readable, _, _ = select.select(
                list(open_descriptors),
                [],
                [],
                min(remaining, BROKER_PROCESS_POLL_SECONDS),
            )
            for descriptor in readable:
                try:
                    captured = sum(len(buffer) for buffer in buffers.values())
                    chunk = os.read(
                        descriptor,
                        min(65536, BROKER_CAPTURE_LIMIT_BYTES - captured + 1),
                    )
                except BlockingIOError:
                    continue
                if not chunk:
                    open_descriptors.remove(descriptor)
                    continue
                if captured + len(chunk) > BROKER_CAPTURE_LIMIT_BYTES:
                    raise EvaluationError("broker check output is too large")
                buffers[descriptor].extend(chunk)
            if process.poll() is not None and not readable:
                continue
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise EvaluationError("broker check timed out")
        try:
            exit_code = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired as exc:
            raise EvaluationError("broker check timed out") from exc
        if self._stopping.is_set():
            raise EvaluationError("broker check was stopped")
        return (
            buffers[stdout_fd].decode("utf-8", "replace"),
            buffers[stderr_fd].decode("utf-8", "replace"),
            exit_code,
        )

    def _inner_command(self, argv: tuple[str, ...]) -> list[str]:
        if shutil.which("bwrap") is None:
            raise EvaluationError("bwrap is required for command broker")
        python_root = Path(sys.executable).resolve().parents[1]
        command = [
            "bwrap",
            "--die-with-parent",
            "--unshare-pid",
            "--unshare-net",
            "--dir",
            "/usr",
            "--ro-bind",
            "/usr",
            "/usr",
            "--dir",
            "/etc",
            "--ro-bind",
            "/etc",
            "/etc",
            "--symlink",
            "usr/bin",
            "/bin",
            "--symlink",
            "usr/sbin",
            "/sbin",
            "--symlink",
            "usr/lib",
            "/lib",
            "--symlink",
            "usr/lib64",
            "/lib64",
            "--dev",
            "/dev",
            "--proc",
            "/proc",
            "--dir",
            "/runtime",
            "--ro-bind",
            str(python_root),
            "/runtime/python",
            "--dir",
            "/workspace",
            "--ro-bind",
            str(self.workspace),
            "/workspace",
            "--tmpfs",
            "/tmp",
            "--tmpfs",
            "/scratch",
        ]
        for relative in sorted(self.case.allowed_changes):
            command.extend(
                ("--bind", str(self.workspace / relative), f"/workspace/{relative}")
            )
        command.extend(("--chdir", "/workspace", "--", "/usr/bin/env", "-i"))
        command.extend(
            (
                "PATH=/runtime/python/bin:/usr/bin:/bin",
                "PYTHONDONTWRITEBYTECODE=1",
                f"CALIBRATION_EVAL_RUN_ID={self.run_id}",
                "HOME=/tmp",
                "TMPDIR=/tmp",
            )
        )
        command.extend(argv)
        return command


def _required_string(data: dict[str, object], key: str, path: Path) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise EvaluationError(f"{path}: {key} must be a non-empty string")
    return value.strip()


def _string_set(
    data: dict[str, object], key: str, path: Path, *, allow_empty: bool = False
) -> frozenset[str]:
    value = data.get(key)
    if not isinstance(value, list) or (not value and not allow_empty):
        raise EvaluationError(f"{path}: {key} must be a non-empty list")
    items = cast(list[object], value)
    if not all(isinstance(item, str) and item.strip() for item in items):
        raise EvaluationError(f"{path}: {key} entries must be non-empty strings")
    normalized = frozenset(cast(str, item).strip() for item in items)
    for item in normalized:
        candidate = Path(item)
        if candidate.is_absolute() or item in {".", ".."} or ".." in candidate.parts:
            raise EvaluationError(f"{path}: {key} entries must be relative paths")
    return normalized


def _commands(
    data: dict[str, object], key: str, path: Path
) -> tuple[tuple[str, ...], ...]:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise EvaluationError(f"{path}: {key} must be a non-empty command list")
    commands: list[tuple[str, ...]] = []
    for raw_command in cast(list[object], value):
        if not isinstance(raw_command, list) or not raw_command:
            raise EvaluationError(f"{path}: {key} entries must be non-empty lists")
        parts = cast(list[object], raw_command)
        if not all(isinstance(part, str) and part for part in parts):
            raise EvaluationError(f"{path}: {key} command parts must be strings")
        commands.append(tuple(cast(str, part) for part in parts))
    return tuple(commands)


def _mapping(data: dict[str, object], key: str, path: Path) -> dict[str, object] | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, dict):
        raise EvaluationError(f"{path}: {key} must be a mapping")
    return cast(dict[str, object], value)


def _validate_command_contract(raw: dict[str, object], path: Path) -> dict[str, object]:
    families = raw.get("families")
    if not isinstance(families, dict) or not families:
        raise EvaluationError(
            f"{path}: command_contract.families must be a non-empty mapping"
        )
    normalized_aliases: dict[str, list[list[str]]] = {}
    wrapper_required: list[str] = []
    covered_seams: dict[str, str] = {}
    execution_contexts: dict[str, str] = {}
    exact_aliases: set[tuple[str, ...]] = set()
    for family, configuration in cast(dict[object, object], families).items():
        if not isinstance(family, str) or family not in COMMAND_FAMILIES:
            raise EvaluationError(f"{path}: unknown command family {family!r}")
        if not isinstance(configuration, dict):
            raise EvaluationError(f"{path}: family {family} must be a mapping")
        configuration = cast(dict[str, object], configuration)
        prefixes = configuration.get("commands")
        if not isinstance(prefixes, list) or not prefixes:
            raise EvaluationError(
                f"{path}: commands for {family} must be a non-empty list"
            )
        parsed: list[list[str]] = []
        for prefix in cast(list[object], prefixes):
            if not isinstance(prefix, list):
                raise EvaluationError(
                    f"{path}: alias prefixes must be non-empty string lists"
                )
            prefix_items = cast(list[object], prefix)
            if not prefix_items or not all(
                isinstance(item, str) and item for item in prefix_items
            ):
                raise EvaluationError(
                    f"{path}: alias prefixes must be non-empty string lists"
                )
            parsed.append(cast(list[str], prefix_items))
            alias = tuple(cast(str, item) for item in prefix_items)
            if alias in exact_aliases:
                raise EvaluationError(f"{path}: command aliases must not overlap")
            exact_aliases.add(alias)
        normalized_aliases[family] = parsed
        wrapper = configuration.get("wrapper_required", False)
        if not isinstance(wrapper, bool):
            raise EvaluationError(
                f"{path}: wrapper_required for {family} must be boolean"
            )
        if wrapper:
            seam = configuration.get("covered_seam")
            if not isinstance(seam, str) or not seam:
                raise EvaluationError(
                    f"{path}: wrapped family {family} needs covered_seam"
                )
            wrapper_required.append(family)
            covered_seams[family] = seam
        execution_context = configuration.get("execution_context", "executor_sandbox")
        if execution_context != "executor_sandbox":
            raise EvaluationError(
                f"{path}: execution_context for {family} must be executor_sandbox"
            )
        execution_contexts[family] = cast(str, execution_context)

    def observations(key: str) -> list[dict[str, object]]:
        value = raw.get(key, [])
        if not isinstance(value, list):
            raise EvaluationError(f"{path}: command_contract.{key} must be a list")
        parsed: list[dict[str, object]] = []
        for item in cast(list[object], value):
            if not isinstance(item, dict):
                raise EvaluationError(f"{path}: {key} observations require family")
            item = cast(dict[str, object], item)
            if not isinstance(item.get("family"), str):
                raise EvaluationError(f"{path}: {key} observations require family")
            family = cast(str, item["family"])
            if family not in normalized_aliases:
                raise EvaluationError(f"{path}: {key} family must have aliases")
            exit_state = item.get("exit", "any")
            if exit_state not in EXIT_STATES:
                raise EvaluationError(
                    f"{path}: {key} exit must be zero, nonzero, or any"
                )
            parsed.append({"family": family, "exit": exit_state})
        return parsed

    forbidden = raw.get("forbidden", [])
    if not isinstance(forbidden, list) or not all(
        isinstance(x, str) and x in normalized_aliases
        for x in cast(list[object], forbidden)
    ):
        raise EvaluationError(
            f"{path}: command_contract.forbidden must name configured families"
        )
    return {
        "aliases": normalized_aliases,
        "required": observations("required"),
        "forbidden": [
            {"family": cast(str, x), "exit": "any"}
            for x in cast(list[object], forbidden)
        ],
        "ordered_required": observations("ordered"),
        "wrapper_required": wrapper_required,
        "covered_seams": covered_seams,
        "execution_contexts": execution_contexts,
    }


def _validate_final_contract(raw: dict[str, object], path: Path) -> dict[str, object]:
    required = raw.get("required_tokens", [])
    forbidden = raw.get("forbidden_statuses", [])
    if not isinstance(required, list) or not all(
        isinstance(x, str) and x for x in cast(list[object], required)
    ):
        raise EvaluationError(
            f"{path}: final_contract.required_tokens must be a string list"
        )
    if not isinstance(forbidden, list) or not all(
        isinstance(x, str) and x in FINAL_STATUSES
        for x in cast(list[object], forbidden)
    ):
        raise EvaluationError(
            f"{path}: final_contract.forbidden_statuses must use known statuses"
        )
    allowed = raw.get("allowed_statuses", list(FINAL_STATUSES))
    if (
        not isinstance(allowed, list)
        or not allowed
        or not all(
            isinstance(x, str) and x in FINAL_STATUSES
            for x in cast(list[object], allowed)
        )
    ):
        raise EvaluationError(
            f"{path}: final_contract.allowed_statuses must use known statuses"
        )
    return {
        "required_tokens": [cast(str, x) for x in cast(list[object], required)],
        "forbidden_statuses": [cast(str, x) for x in cast(list[object], forbidden)],
        "allowed_statuses": [cast(str, x) for x in cast(list[object], allowed)],
    }


def load_case(path: Path) -> CaseSpec:
    """Load and validate one case definition."""
    try:
        raw = cast(object, yaml.safe_load(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise EvaluationError(f"{path}: cannot load case: {exc}") from exc
    if not isinstance(raw, dict):
        raise EvaluationError(f"{path}: case must be a mapping")
    data = cast(dict[str, object], raw)
    command_contract = _mapping(data, "command_contract", path)
    final_contract = _mapping(data, "final_contract", path)
    case = CaseSpec(
        case_id=_required_string(data, "id", path),
        title=_required_string(data, "title", path),
        fixture=_required_string(data, "fixture", path),
        prompt=_required_string(data, "prompt", path),
        verify=_commands(data, "verify", path),
        allowed_changes=_string_set(
            data, "allowed_changes", path, allow_empty=final_contract is not None
        ),
        required_changes=_string_set(
            data, "required_changes", path, allow_empty=final_contract is not None
        ),
        fixture_root=path.parent.parent / "fixtures",
        command_contract=(
            _validate_command_contract(command_contract, path)
            if command_contract is not None
            else None
        ),
        final_contract=(
            _validate_final_contract(final_contract, path)
            if final_contract is not None
            else None
        ),
    )
    if not case.required_changes <= case.allowed_changes:
        raise EvaluationError(f"{path}: required_changes must be allowed")
    fixture = case.fixture_root / case.fixture
    if not fixture.is_dir():
        raise EvaluationError(f"{path}: missing fixture {fixture}")
    return case


def _run(
    command: tuple[str, ...] | list[str],
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


def _evaluation_env() -> dict[str, str]:
    """Return the runner-controlled environment for mutable evaluation phases."""
    env = os.environ.copy()
    # Python imports are not semantic fixture edits; preserve the path oracle by
    # preventing runner-owned commands from materializing bytecode artifacts.
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def prepare_workspace(case: CaseSpec, workspace: Path) -> None:
    """Copy and commit one pristine fixture repository."""
    if workspace.exists():
        raise EvaluationError(f"workspace already exists: {workspace}")
    fixture = case.fixture_root / case.fixture
    shutil.copytree(fixture, workspace)
    # The named :workspace-derived permission profile reserves this directory
    # as read-only. Materialize it before the executor boundary so Codex never
    # tries to create it through the workspace's read-only base mount.
    for protected_directory in (".agents", ".codex"):
        (workspace / protected_directory).mkdir(exist_ok=True)
    commands = (
        ("git", "init", "-q"),
        ("git", "config", "user.name", "Calibration Evaluation"),
        ("git", "config", "user.email", "evaluation@example.invalid"),
        ("git", "add", "."),
        ("git", "commit", "-q", "-m", "fixture baseline"),
    )
    for command in commands:
        result = _run(command, workspace)
        if result.returncode:
            raise EvaluationError(
                f"{' '.join(command)} failed: {result.stderr.strip()}"
            )


def changed_paths(workspace: Path) -> frozenset[str]:
    """Return changed and untracked paths relative to the fixture root."""
    result = _run(("git", "status", "--porcelain"), workspace)
    if result.returncode:
        raise EvaluationError(f"git status failed: {result.stderr.strip()}")
    paths: set[str] = set()
    for line in result.stdout.splitlines():
        value = line[3:]
        paths.add(value.rsplit(" -> ", maxsplit=1)[-1])
    return frozenset(paths)


def verify_workspace(case: CaseSpec, workspace: Path) -> dict[str, object]:
    """Execute deterministic checks and classify the final repository state."""
    checks: list[dict[str, object]] = []
    for command in case.verify:
        result = _run(command, workspace, env=_evaluation_env())
        checks.append(
            {
                "phase": "post_run_verification",
                "command": list(command),
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
    changed = changed_paths(workspace)
    unexpected = sorted(changed - case.allowed_changes)
    missing = sorted(case.required_changes - changed)
    passed = (
        all(cast(int, check["exit_code"]) == 0 for check in checks)
        and not unexpected
        and not missing
    )
    return {
        "case_id": case.case_id,
        "passed": passed,
        "checks": checks,
        "changed_paths": sorted(changed),
        "unexpected_changes": unexpected,
        "missing_required_changes": missing,
    }


def _shell_plan(command: str) -> tuple[list[list[str]], list[str]]:
    """Return command chunks and their preceding shell operators."""
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError as exc:
        raise EvaluationError(f"malformed command shell syntax: {exc}") from exc
    shell_invocations = {
        "/bin/bash",
        "/usr/bin/bash",
        "bash",
        "/bin/sh",
        "/usr/bin/sh",
        "sh",
    }
    if (
        len(tokens) == 3
        and tokens[0] in shell_invocations
        and tokens[1] in {"-c", "-lc", "-cl"}
    ):
        return _shell_plan(tokens[2])
    chunks: list[list[str]] = []
    operators: list[str] = []
    current: list[str] = []
    for token in tokens:
        if token in {"&&", "||", ";"}:
            if not current:
                raise EvaluationError("malformed compound command")
            chunks.append(current)
            operators.append(token)
            current = []
        else:
            current.append(token)
    if not current:
        raise EvaluationError("malformed compound command")
    chunks.append(current)
    return chunks, operators


def _shell_commands(command: str) -> list[list[str]]:
    """Return conservative direct command chunks, including simple compounds."""
    return _shell_plan(command)[0]


def _is_discovery(tokens: list[str]) -> bool:
    if not tokens:
        return False
    if tokens[0] in {"pwd", "ls", "cat", "head", "tail", "which"}:
        return True
    if tokens[0] == "find":
        executing_actions = {
            "-delete",
            "-exec",
            "-execdir",
            "-fls",
            "-fprint",
            "-fprintf",
            "-ok",
            "-okdir",
        }
        return not any(token in executing_actions for token in tokens[1:])
    if tokens[0] == "rg":
        return not any(
            token == "--pre" or token.startswith("--pre=") for token in tokens
        )
    if tokens[0] == "sed":
        return (
            len(tokens) >= 4
            and tokens[1] == "-n"
            and tokens[2].removesuffix("p").replace(",", "").isdigit()
        )
    if tokens[:2] in (["git", "diff"], ["git", "log"]):
        return not any(
            token in {"--ext-diff", "--textconv"} or token.startswith("--ext-diff=")
            for token in tokens[2:]
        )
    return tokens[:2] in (["git", "status"], ["command", "-v"])


def _unknown_validation(tokens: list[str]) -> bool:
    text = " ".join(tokens).lower()
    return any(
        word in text
        for word in (
            "test",
            "check",
            "lint",
            "build",
            "verify",
            "pytest",
            "ruff",
            "pyright",
        )
    )


def _command_events(trajectory: str) -> tuple[list[dict[str, object]], list[str]]:
    events: list[dict[str, object]] = []
    errors: list[str] = []
    for line_number, line in enumerate(trajectory.splitlines(), start=1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: malformed JSON: {exc.msg}")
            continue
        if not isinstance(value, dict):
            continue
        value = cast(dict[str, object], value)
        if value.get("type") != "item.completed":
            continue
        item = value.get("item")
        if not isinstance(item, dict):
            continue
        item = cast(dict[str, object], item)
        if item.get("type") != "command_execution":
            continue
        command = item.get("command")
        if not isinstance(command, str) or not command.strip():
            errors.append(f"line {line_number}: malformed command_execution event")
            continue
        output = item.get("aggregated_output", item.get("output", ""))
        if not isinstance(output, str):
            errors.append(f"line {line_number}: malformed command output")
            continue
        exit_code = item.get("exit_code")
        if exit_code is not None and (
            not isinstance(exit_code, int) or isinstance(exit_code, bool)
        ):
            errors.append(f"line {line_number}: malformed exit_code")
            continue
        events.append(
            {
                "line": line_number,
                "sequence": len(events),
                "raw_command": command,
                "aggregate_output": output,
                "exit_code": exit_code,
            }
        )
    return events, errors


def _exit_matches(exit_code: object, expected: object) -> bool:
    if expected == "any":
        return isinstance(exit_code, int)
    if not isinstance(exit_code, int):
        return False
    return (exit_code == 0) if expected == "zero" else (exit_code != 0)


def _broker_mapping(event: BrokerEvent | dict[str, object]) -> dict[str, object]:
    if isinstance(event, BrokerEvent):
        return {
            "execution_id": event.execution_id,
            "family": event.family,
            "argv": list(event.argv),
            "argv_sha256": event.argv_sha256,
            "cwd": event.cwd,
            "execution_context": event.execution_context,
            "exit_code": event.exit_code,
        }
    return event


def _bypass(tokens: list[str]) -> bool:
    return (
        bool(tokens)
        and tokens[:2] != ["command", "-v"]
        and (
            tokens[0].startswith("/")
            or tokens[0] in {"env", "exec", "command", "function"}
            or "=" in tokens[0]
            or any(token.startswith("PATH=") for token in tokens)
        )
    )


def command_oracle(
    case: CaseSpec,
    trajectory: str,
    run_id: str,
    broker_events: Sequence[BrokerEvent | dict[str, object]] | None = None,
) -> dict[str, object]:
    """Corroborate raw chronology with runner-owned broker execution evidence."""
    if case.command_contract is None:
        return {"enabled": False, "valid": True, "observations": [], "errors": []}
    del run_id
    contract = case.command_contract
    events, errors = _command_events(trajectory)
    broker_sources = list(broker_events or [])
    broker = [_broker_mapping(event) for event in broker_sources]
    delivery_receipts = [
        event.delivery_receipt if isinstance(event, BrokerEvent) else None
        for event in broker_sources
    ]
    if broker_events is None:
        errors.append("missing runner-owned broker evidence")
    observations: list[dict[str, object]] = []
    aliases = cast(dict[str, list[list[str]]], contract["aliases"])
    for expected_id, authoritative in enumerate(broker, start=1):
        argv = authoritative.get("argv")
        if authoritative.get("execution_id") != expected_id:
            errors.append("broker execution_id must be continuous and unique")
        if not isinstance(argv, list):
            errors.append("broker argv is invalid")
            continue
        raw_argv = cast(list[object], argv)
        if not all(isinstance(item, str) for item in raw_argv):
            errors.append("broker argv is invalid")
            continue
        canonical_argv = cast(list[str], raw_argv)
        digest = hashlib.sha256("\0".join(canonical_argv).encode()).hexdigest()
        if authoritative.get("argv_sha256") != digest:
            errors.append("broker argv sha256 mismatch")
        if authoritative.get("cwd") != "/workspace":
            errors.append("broker cwd is invalid")
        if authoritative.get("execution_context") != "executor_sandbox":
            errors.append("broker execution context is invalid")
        exit_code = authoritative.get("exit_code")
        if not isinstance(exit_code, int) or isinstance(exit_code, bool):
            errors.append("broker exit code is invalid")
        receipt_token = delivery_receipts[expected_id - 1]
        if isinstance(
            broker_sources[expected_id - 1], BrokerEvent
        ) and not _valid_request_id(receipt_token):
            errors.append("broker delivery receipt is invalid")
    broker_position = 0
    for event in events:
        try:
            raw_command = cast(str, event["raw_command"])
            chunks = _shell_commands(raw_command)
            _, operators = _shell_plan(raw_command)
        except EvaluationError as exc:
            errors.append(f"line {event['line']}: {exc}")
            continue
        previous_exit: object | None = None
        previous_kind: str | None = None
        receipt_lines = _delivery_receipt_lines(cast(str, event["aggregate_output"]))
        receipt_position = 0
        for index, tokens in enumerate(chunks):
            bypass_reported = False
            if index:
                operator = operators[index - 1]
                if operator == ";":
                    executed = True
                elif isinstance(previous_exit, int):
                    executed = (
                        previous_exit == 0 if operator == "&&" else previous_exit != 0
                    )
                elif previous_kind == "neutral":
                    # Discovery commands do not have runner-owned exits.  They
                    # cannot establish a branch. Keep pure discovery chronology
                    # observable, but treat a later exact check as executed only
                    # when its next runner-owned broker event proves it.
                    executed = _is_discovery(tokens) or (
                        broker_position < len(broker)
                        and broker[broker_position].get("argv") == tokens
                    )
                    if _bypass(tokens):
                        errors.append(
                            f"line {event['line']}: command bypass is invalid"
                        )
                        bypass_reported = True
                else:
                    executed = False
                    errors.append(
                        f"cannot determine compound branch at line {event['line']}"
                    )
                if not executed:
                    # Raw parent-shell status is never truth.  A matching next
                    # broker event proves execution and exposes the inconsistency.
                    if (
                        broker_position < len(broker)
                        and broker[broker_position].get("argv") == tokens
                    ):
                        errors.append(
                            f"compound chronology inconsistent at line {event['line']}"
                        )
                        executed = True
                    else:
                        continue
            family = next(
                (
                    name
                    for name, prefixes in aliases.items()
                    if any(tokens == prefix for prefix in prefixes)
                ),
                None,
            )
            if _bypass(tokens) and not bypass_reported:
                errors.append(f"line {event['line']}: command bypass is invalid")
            kind = family or (
                "neutral"
                if _is_discovery(tokens)
                else "unknown_validation"
                if _unknown_validation(tokens)
                else "unrecognized"
            )
            exit_code: object | None = None
            if family is not None:
                if broker_position >= len(broker):
                    errors.append(
                        f"missing broker event for {family} at line {event['line']}"
                    )
                else:
                    receipt_token = delivery_receipts[broker_position]
                    authoritative = broker[broker_position]
                    broker_position += 1
                    if (
                        authoritative.get("family") != family
                        or authoritative.get("argv") != tokens
                        or authoritative.get("execution_context") != "executor_sandbox"
                    ):
                        errors.append(
                            f"raw/broker mismatch for {family} at line {event['line']}"
                        )
                    else:
                        exit_code = authoritative.get("exit_code")
                        if not isinstance(exit_code, int) or isinstance(
                            exit_code, bool
                        ):
                            errors.append(f"invalid broker exit for {family}")
                        else:
                            if receipt_token is not None:
                                expected_receipt = _delivery_receipt_line(receipt_token)
                                actual_receipt = (
                                    receipt_lines[receipt_position]
                                    if receipt_position < len(receipt_lines)
                                    else None
                                )
                                receipt_position += 1
                                if actual_receipt != expected_receipt:
                                    errors.append(
                                        "transport/delivery receipt mismatch for "
                                        f"{family} at line {event['line']}"
                                    )
                            if len(chunks) == 1:
                                # A direct shim invocation has exactly one
                                # canonical command and no shell aggregation to
                                # explain a different raw result. The broker
                                # remains the child execution authority, while
                                # the raw exit corroborates that the shim
                                # delivered its reply.
                                raw_exit = event["exit_code"]
                                if raw_exit != exit_code:
                                    errors.append(
                                        "transport/delivery exit mismatch for "
                                        f"{family} at line {event['line']}"
                                    )
            previous_exit = exit_code
            observations.append(
                {
                    "line": event["line"],
                    "sequence": event["sequence"],
                    "raw_command": event["raw_command"],
                    "argv": tokens,
                    "family": kind,
                    "exit_code": exit_code,
                }
            )
            if kind == "unknown_validation":
                errors.append(f"line {event['line']}: unknown validation command")
            elif kind == "unrecognized":
                errors.append(f"line {event['line']}: unrecognized command")
            previous_kind = kind
        if receipt_position != len(receipt_lines):
            errors.append(f"line {event['line']}: unexpected delivery receipt")
    if broker_position != len(broker):
        errors.append("broker event has no raw command counterpart")
    for requirement in cast(list[dict[str, object]], contract["required"]):
        if not any(
            obs["family"] == requirement["family"]
            and _exit_matches(obs["exit_code"], requirement["exit"])
            for obs in observations
        ):
            errors.append(
                f"missing required {requirement['family']} ({requirement['exit']})"
            )
    for forbidden in cast(list[dict[str, object]], contract["forbidden"]):
        if any(obs["family"] == forbidden["family"] for obs in observations):
            errors.append(f"forbidden family observed: {forbidden['family']}")
    ordered = cast(list[dict[str, object]], contract["ordered_required"])
    position = 0
    for requirement in ordered:
        found = next(
            (
                index
                for index in range(position, len(observations))
                if observations[index]["family"] == requirement["family"]
                and _exit_matches(observations[index]["exit_code"], requirement["exit"])
            ),
            None,
        )
        if found is None:
            missing = requirement["family"]
            exit_state = requirement["exit"]
            errors.append(
                f"ordered required observation missing: {missing} ({exit_state})"
            )
            break
        position = found + 1
    return {
        "enabled": True,
        "valid": not errors,
        "observations": observations,
        "broker_events": broker,
        "errors": errors,
    }


def final_oracle(case: CaseSpec, final_message: Path) -> dict[str, object]:
    if case.final_contract is None:
        return {"enabled": False, "valid": True, "errors": []}
    errors: list[str] = []
    text = final_message.read_text(encoding="utf-8") if final_message.is_file() else ""
    lines = [
        line for line in text.splitlines() if line.startswith("VERIFICATION_STATUS:")
    ]
    if len(lines) != 1:
        errors.append("expected exactly one VERIFICATION_STATUS line")
        status = None
    else:
        status = lines[0].removeprefix("VERIFICATION_STATUS:").strip()
        if status not in FINAL_STATUSES:
            errors.append("invalid verification status")
    contract = case.final_contract
    if status is not None and status not in cast(
        list[str], contract["allowed_statuses"]
    ):
        errors.append("verification status is not allowed")
    if status in cast(list[str], contract["forbidden_statuses"]):
        errors.append("verification status is forbidden")
    for token in cast(list[str], contract["required_tokens"]):
        if token not in text:
            errors.append(f"missing required final-answer token: {token}")
    return {"enabled": True, "valid": not errors, "status": status, "errors": errors}


def validate_result_payload(case: CaseSpec, payload: dict[str, object]) -> None:
    """Validate results when an evaluation supplies its frozen JSON schema."""
    schema_path = case.fixture_root.parent / "result.schema.json"
    if not schema_path.is_file():
        return
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvaluationError(
            f"cannot load result schema {schema_path}: {exc}"
        ) from exc
    if not isinstance(schema, dict):
        raise EvaluationError(f"result schema must be an object: {schema_path}")
    schema = cast(dict[str, Any], schema)
    try:
        Draft202012Validator.check_schema(schema)
        validator = cast(_PayloadValidator, Draft202012Validator(schema))
        validator.validate(payload)
    except (SchemaError, ValidationError) as exc:
        raise EvaluationError(
            f"result schema validation failed: {exc.message}"
        ) from exc


def _write_private_file(path: Path, text: str) -> None:
    """Write a runner control artifact without following executor-created links."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError as exc:
        raise EvaluationError(
            f"runner control artifact already exists: {path}"
        ) from exc
    except OSError as exc:
        raise EvaluationError(
            f"cannot create runner control artifact {path}: {exc}"
        ) from exc
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            os.fchmod(handle.fileno(), 0o600)
            handle.write(text)
    except (OSError, UnicodeError) as exc:
        raise EvaluationError(
            f"cannot write runner control artifact {path}: {exc}"
        ) from exc


def build_codex_command(
    case: CaseSpec,
    workspace: Path,
    final_message: Path,
    model: str,
    reasoning_effort: str,
    executable: str = "codex",
) -> list[str]:
    """Build the frozen non-interactive Codex command."""
    return [
        executable,
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--strict-config",
        "--disable",
        "apps",
        "--disable",
        "plugins",
        "--disable",
        "multi_agent",
        "--disable",
        "browser_use",
        "--disable",
        "browser_use_external",
        "--json",
        "--color",
        "never",
        "--model",
        model,
        "--config",
        f'model_reasoning_effort="{reasoning_effort}"',
        "--config",
        EXECUTOR_PERMISSION_PROFILE_CONFIG,
        "--config",
        EXECUTOR_DEFAULT_PERMISSIONS_CONFIG,
        "--cd",
        str(workspace),
        "--output-last-message",
        str(final_message),
        case.prompt,
    ]


def build_permission_profile_sandbox_command(
    executable: str, workspace: Path, argv: Sequence[str]
) -> list[str]:
    """Build a no-model probe through the same named permission profile.

    ``codex exec`` selects the profile through ``default_permissions`` on this
    frozen CLI version, while ``codex sandbox`` exposes explicit ``-P``.  Keep
    the two configuration overrides byte-for-byte identical so the integration
    probe exercises the policy used by executor command tools.
    """
    return [
        executable,
        "sandbox",
        "--config",
        EXECUTOR_PERMISSION_PROFILE_CONFIG,
        "--config",
        EXECUTOR_DEFAULT_PERMISSIONS_CONFIG,
        "--permission-profile",
        EXECUTOR_PERMISSION_PROFILE,
        "--cd",
        str(workspace),
        "--",
        *argv,
    ]


def build_executor_boundary_preflight_command(
    case: CaseSpec,
    workspace: Path,
    output_dir: Path,
    runtime: Path,
    listener_port: int,
) -> list[str]:
    """Build the no-model command that proves the executor command boundary.

    This deliberately uses the same outer root, named Codex permission profile,
    and ``/bin/bash -c`` route that Codex command tools use later.  The listener
    is runner-owned: a successful connection is evidence that the profile did
    not preserve its network denial.
    """
    command = build_bwrap_command(
        case,
        workspace,
        output_dir,
        "boundary-preflight",
        "low",
        runtime,
    )
    codex_tail = build_codex_command(
        case,
        Path("/workspace"),
        Path("/output/final-message.txt"),
        "boundary-preflight",
        "low",
        "/runtime/codex/bin/codex",
    )
    if command[-len(codex_tail) :] != codex_tail:
        raise EvaluationError("executor boundary preflight command is malformed")
    probe = "\n".join(
        (
            "from pathlib import Path",
            "import fcntl, json, os, secrets, select, socket, time",
            "try:",
            "    Path('/output/.executor-boundary-preflight-private').read_text()",
            "except OSError:",
            "    pass",
            "else:",
            "    raise SystemExit('preflight can read /output')",
            "try:",
            f"    socket.create_connection(('127.0.0.1', {listener_port}), 0.2)",
            "except OSError:",
            "    pass",
            "else:",
            "    raise SystemExit('preflight network is enabled')",
            "request_id = secrets.token_hex(32)",
            "payload = {'protocol_version': 1, 'request_id': request_id,",
            "           'argv': ['__preflight_unrecognized__']}",
            "request = (json.dumps(payload, separators=(',', ':')) + '\\n').encode()",
            f"if len(request) > {BROKER_PIPE_BUF_BYTES}:",
            "    raise SystemExit('preflight request too large')",
            "nofollow = getattr(os, 'O_NOFOLLOW', 0)",
            "lock = os.open('/broker/broker.lock', os.O_RDONLY | nofollow)",
            "response_fd = None",
            "try:",
            f"    lock_deadline = time.monotonic() + {BROKER_LOCK_TIMEOUT_SECONDS!r}",
            "    while True:",
            "        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)",
            "        except BlockingIOError:",
            "            if time.monotonic() >= lock_deadline:",
            "                raise SystemExit('preflight broker lock timeout')",
            "            time.sleep(0.01)",
            "        else: break",
            "    response_flags = os.O_RDONLY | os.O_NONBLOCK | nofollow",
            "    response_fd = os.open('/broker/response.fifo', response_flags)",
            "    request_fd = os.open('/broker/request.fifo', os.O_WRONLY | nofollow)",
            "    try:",
            "        if os.write(request_fd, request) != len(request):",
            "            raise SystemExit('preflight request not atomic')",
            "    finally:",
            "        os.close(request_fd)",
            "    deadline = time.monotonic() + 5.0",
            "    raw = bytearray()",
            "    while b'\\n' not in raw:",
            "        remaining = deadline - time.monotonic()",
            "        if remaining <= 0:",
            "            raise SystemExit('preflight broker timeout')",
            "        if not select.select([response_fd], [], [], remaining)[0]:",
            "            continue",
            "        raw.extend(os.read(response_fd, 65536))",
            "        if len(raw) > 1048576:",
            "            raise SystemExit('preflight broker response too large')",
            "finally:",
            "    if response_fd is not None: os.close(response_fd)",
            "    fcntl.flock(lock, fcntl.LOCK_UN)",
            "    os.close(lock)",
            "line, separator, tail = raw.partition(b'\\n')",
            "if not separator or tail:",
            "    raise SystemExit('preflight broker framing invalid')",
            "reply = json.loads(line.decode())",
            "expected = {'protocol_version': 1, 'request_id': request_id,",
            "            'accepted': False, 'reason': 'unrecognized'}",
            "if reply != expected:",
            "    raise SystemExit('preflight broker reply invalid')",
            "def denied(action, label):",
            "    try: action()",
            "    except OSError: return",
            "    raise SystemExit('preflight broker allowed ' + label)",
            "denied(lambda: os.open('/broker/request.fifo', os.O_RDONLY),",
            "       'request read')",
            "denied(lambda: os.open('/broker/request.fifo', os.O_RDWR),",
            "       'request read-write')",
            "denied(lambda: os.open('/broker/response.fifo', os.O_WRONLY),",
            "       'response write')",
            "denied(lambda: os.open('/broker/response.fifo', os.O_RDWR),",
            "       'response read-write')",
            "request_mode_fd = os.open('/broker/request.fifo', os.O_WRONLY)",
            "try:",
            "    denied(lambda: os.fchmod(request_mode_fd, 0o600), 'fchmod')",
            "finally:",
            "    os.close(request_mode_fd)",
            "denied(lambda: os.chmod('/broker/request.fifo', 0o600), 'chmod')",
            "denied(lambda: os.unlink('/broker/response.fifo'), 'unlink')",
            "denied(lambda: os.rename('/broker/broker.lock', '/broker/moved'),",
            "       'rename')",
            "print('executor-boundary-preflight-ok')",
        )
    )
    command[-len(codex_tail) :] = build_permission_profile_sandbox_command(
        "/runtime/codex/bin/codex",
        Path("/workspace"),
        ("/bin/bash", "-c", f"/runtime/python/bin/python3 -c {shlex.quote(probe)}"),
    )
    return command


def run_executor_boundary_preflight(
    case: CaseSpec, workspace: Path, output_dir: Path, runtime: Path
) -> None:
    """Fail closed unless the exact no-model executor command path is usable."""
    private_marker = output_dir / ".executor-boundary-preflight-private"
    _write_private_file(private_marker, "runner-owned preflight sentinel\n")
    listener: socket.socket | None = None
    try:
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(BOUNDARY_PREFLIGHT_TIMEOUT_SECONDS)
        assert listener is not None
        port = cast(int, listener.getsockname()[1])
        command = build_executor_boundary_preflight_command(
            case, workspace, output_dir, runtime, port
        )
        try:
            result = subprocess.run(
                command,
                cwd=workspace,
                env=_evaluation_env(),
                check=False,
                capture_output=True,
                text=True,
                timeout=BOUNDARY_PREFLIGHT_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise EvaluationError("executor boundary preflight timed out") from exc
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise EvaluationError(
                "executor boundary preflight failed" + (f": {detail}" if detail else "")
            )
        if result.stdout.strip() != "executor-boundary-preflight-ok":
            raise EvaluationError(
                "executor boundary preflight did not prove shell start"
            )
        listener.settimeout(0.2)
        try:
            client, _ = listener.accept()
        except TimeoutError:
            return
        else:
            client.close()
            raise EvaluationError(
                "executor boundary preflight permitted loopback network"
            )
    finally:
        if listener is not None:
            listener.close()
        with suppress(FileNotFoundError):
            private_marker.unlink()


def _run_model(
    command: tuple[str, ...] | list[str], cwd: Path, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    """Run the outer Codex process with a bounded, fail-closed deadline."""
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=MODEL_EXECUTION_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise EvaluationError("model execution timed out") from exc


def build_bwrap_command(
    case: CaseSpec,
    workspace: Path,
    output_dir: Path,
    model: str,
    reasoning_effort: str,
    broker_runtime: Path | None = None,
) -> list[str]:
    """Build the isolated executor root from resolved runtime paths."""
    if shutil.which("bwrap") is None:
        raise EvaluationError("bwrap is required for writable evaluation boundary")
    python_root = Path(sys.executable).resolve().parents[1]
    codex = shutil.which("codex")
    if codex is None:
        raise EvaluationError("Codex executable is required for writable evaluation")
    codex_root = Path(codex).resolve().parents[1]
    if (
        not (python_root / "bin/python3.13").is_file()
        or not (codex_root / "bin/codex").is_file()
    ):
        raise EvaluationError("resolved runtime layout is invalid")
    command = [
        "bwrap",
        "--die-with-parent",
        "--unshare-pid",
        "--dir",
        "/usr",
        "--ro-bind",
        "/usr",
        "/usr",
        "--dir",
        "/etc",
        "--ro-bind",
        "/etc",
        "/etc",
        "--symlink",
        "usr/bin",
        "/bin",
        "--symlink",
        "usr/sbin",
        "/sbin",
        "--symlink",
        "usr/lib",
        "/lib",
        "--symlink",
        "usr/lib64",
        "/lib64",
        "--dev",
        "/dev",
        "--proc",
        "/proc",
        "--tmpfs",
        "/tmp",
        "--dir",
        "/runtime",
        "--ro-bind",
        str(python_root),
        "/runtime/python",
        "--ro-bind",
        str(codex_root),
        "/runtime/codex",
        "--dir",
        "/workspace",
        "--ro-bind",
        str(workspace),
        "/workspace",
        "--dir",
        "/output",
        "--bind",
        str(output_dir),
        "/output",
    ]
    if broker_runtime is not None:
        _validate_shell_runtime(broker_runtime, case)
        command.extend(
            ("--dir", "/broker", "--ro-bind", str(broker_runtime), "/broker")
        )
        # Codex command tools commonly invoke an absolute /bin/bash or
        # /usr/bin/bash. Override the real paths in this outer root so PATH
        # precedence cannot be bypassed. The named Codex permission profile,
        # verified by the runner-owned preflight, owns command-tool networking.
        command.extend(
            (
                "--ro-bind",
                str(broker_runtime / SHELL_WRAPPER_NAME),
                "/usr/bin/bash",
                "--ro-bind",
                str(broker_runtime / SHELL_WRAPPER_NAME),
                "/usr/bin/sh",
            )
        )
    for relative in sorted(case.allowed_changes):
        target = workspace / relative
        command.extend(("--bind", str(target), f"/workspace/{relative}"))
    command.extend(("--chdir", "/workspace", "--", "/usr/bin/env", "-i"))
    path = "/broker/bin:/runtime/python/bin:/runtime/codex/codex-path:/usr/bin:/bin"
    if broker_runtime is None:
        path = "/runtime/python/bin:/runtime/codex/codex-path:/usr/bin:/bin"
    command.extend(
        (
            f"PATH={path}",
            "HOME=/output/home",
            "TMPDIR=/output/tmp",
            "TMP=/output/tmp",
            "TEMP=/output/tmp",
            "CODEX_HOME=/output/codex-home",
            "GIT_OPTIONAL_LOCKS=0",
            "PYTHONDONTWRITEBYTECODE=1",
        )
    )
    for key in (
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "NO_PROXY",
    ):
        value = os.environ.get(key)
        if value:
            command.append(f"{key}={value}")
    command.extend(
        build_codex_command(
            case,
            Path("/workspace"),
            Path("/output/final-message.txt"),
            model,
            reasoning_effort,
            "/runtime/codex/bin/codex",
        )
    )
    return command


def _validate_boundary_paths(case: CaseSpec, workspace: Path, output_dir: Path) -> None:
    workspace_root = workspace.resolve()
    if changed_paths(workspace):
        raise EvaluationError("workspace must be pristine before executor boundary")
    if output_dir.resolve().is_relative_to(workspace_root):
        raise EvaluationError("output directory must be outside workspace")
    for relative in case.allowed_changes:
        target = workspace / relative
        if (
            target.is_symlink()
            or not target.is_file()
            or not target.resolve().is_relative_to(workspace_root)
        ):
            raise EvaluationError(
                "allowed change must be an existing in-workspace regular file: "
                f"{relative}"
            )


def install_arm_home(source_root: Path, auth_file: Path, codex_home: Path) -> None:
    """Install one arm into an isolated Codex home."""
    if not (source_root / "install.sh").is_file():
        raise EvaluationError(f"missing arm installer: {source_root / 'install.sh'}")
    if not auth_file.is_file():
        raise EvaluationError(f"missing Codex auth file: {auth_file}")
    codex_home.mkdir(mode=0o700, parents=True)
    install_home = codex_home / "home"
    install_home.mkdir(mode=0o700)
    shutil.copyfile(auth_file, codex_home / "auth.json")
    (codex_home / "auth.json").chmod(0o600)
    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)
    env["HOME"] = str(install_home)
    result = _run(("bash", "install.sh"), source_root, env=env)
    if result.returncode:
        raise EvaluationError(f"arm install failed: {result.stderr.strip()}")
    skills_dir = codex_home / "skills"
    if skills_dir.is_dir():
        for link in sorted(skills_dir.iterdir()):
            if not link.is_symlink():
                continue
            target = link.resolve()
            if not target.exists():
                raise EvaluationError(f"installed skill link is broken: {link}")
            link.unlink()
            if target.is_dir():
                shutil.copytree(target, link)
            else:
                shutil.copy2(target, link)
    runtime_closure = (
        (source_root / "references", codex_home / "references"),
        (
            source_root / "docs/runbooks/agent-orchestrator-review-continuation.md",
            codex_home / "docs/runbooks/agent-orchestrator-review-continuation.md",
        ),
        (source_root / "thirdparty/licenses", codex_home / "licenses"),
    )
    for source, destination in runtime_closure:
        if not source.exists():
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)
    agents_file = codex_home / "AGENTS.md"
    if agents_file.is_file():
        rendered = agents_file.read_text(encoding="utf-8")
        rendered = rendered.replace(str(source_root.resolve()), "/output/codex-home")
        rendered = rendered.replace(str(codex_home.resolve()), "/output/codex-home")
        agents_file.write_text(rendered, encoding="utf-8")
    for candidate in codex_home.rglob("*"):
        if candidate.is_symlink() and not candidate.resolve().is_relative_to(
            codex_home
        ):
            raise EvaluationError(f"installed home retains external link: {candidate}")


def _validate_shell_runtime(runtime: Path, case: CaseSpec) -> None:
    """Reject a missing or mismatched runner-owned nested-shell closure."""
    wrapper = runtime / SHELL_WRAPPER_NAME
    manifest_path = runtime / SHELL_MANIFEST_NAME
    real_shells = runtime / REAL_SHELL_DIRECTORY
    if not wrapper.is_file() or not os.access(wrapper, os.X_OK):
        raise EvaluationError("runner-owned executor shell wrapper is missing")
    if not manifest_path.is_file():
        raise EvaluationError("runner-owned executor shell manifest is missing")
    for name in ("bash", "sh"):
        shell = real_shells / name
        if not shell.is_file() or not os.access(shell, os.X_OK):
            raise EvaluationError(f"runner-owned real shell is missing: {name}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvaluationError(
            "runner-owned executor shell manifest is invalid"
        ) from exc
    if not isinstance(manifest, dict):
        raise EvaluationError("runner-owned executor shell manifest is invalid")
    manifest_data = cast(dict[str, object], manifest)
    if manifest_data.get("allowed_changes") != sorted(case.allowed_changes):
        raise EvaluationError(
            "runner-owned executor shell manifest does not match case"
        )


def create_broker_shims(runtime: Path, case: CaseSpec | None = None) -> None:
    """Create immutable-in-executor PATH shims for command evidence tools."""
    bin_dir = runtime / "bin"
    bin_dir.mkdir()
    template = """#!/runtime/python/bin/python3
import fcntl, json, os, secrets, select, sys, time
tool = {tool!r}
request_id = secrets.token_hex(32)
payload = {{"protocol_version": 1, "request_id": request_id,
           "argv": [tool, *sys.argv[1:]]}}
request = (json.dumps(payload, separators=(",", ":")) + "\\n").encode("utf-8")
if len(request) > {pipe_buf}:
    raise SystemExit("runner-owned check broker request is too large")
nofollow = getattr(os, "O_NOFOLLOW", 0)
lock = os.open("/broker/broker.lock", os.O_RDONLY | nofollow)
response_fd = None
try:
    lock_deadline = time.monotonic() + {lock_timeout!r}
    while True:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            if time.monotonic() >= lock_deadline:
                raise RuntimeError("broker lock timed out")
            time.sleep(0.01)
        else:
            break
    response_flags = os.O_RDONLY | os.O_NONBLOCK | nofollow
    response_fd = os.open("/broker/response.fifo", response_flags)
    request_fd = os.open("/broker/request.fifo", os.O_WRONLY | nofollow)
    try:
        if os.write(request_fd, request) != len(request):
            raise RuntimeError("broker request was not written atomically")
    finally:
        os.close(request_fd)
    response_bytes = bytearray()
    deadline = time.monotonic() + {frame_timeout!r}
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError("broker response timed out")
        readable, _, _ = select.select([response_fd], [], [], remaining)
        if not readable:
            continue
        chunk = os.read(response_fd, 65536)
        if not chunk:
            continue
        response_bytes.extend(chunk)
        if len(response_bytes) > {frame_limit}:
            raise RuntimeError("broker response is too large")
        if b"\\n" in response_bytes:
            line, separator, tail = response_bytes.partition(b"\\n")
            if tail or not separator:
                raise RuntimeError("broker response framing is invalid")
            response = json.loads(line.decode("utf-8"))
            break
finally:
    if response_fd is not None:
        os.close(response_fd)
    fcntl.flock(lock, fcntl.LOCK_UN)
    os.close(lock)
if not isinstance(response, dict):
    raise SystemExit("runner-owned check broker response mismatch")
if response.get("protocol_version") != 1 or response.get("request_id") != request_id:
    raise SystemExit("runner-owned check broker response mismatch")
if response.get("accepted"):
    receipt_token = response.get("receipt_token")
    if (not isinstance(receipt_token, str) or len(receipt_token) != 64
            or any(character not in "0123456789abcdef" for character in receipt_token)):
        raise SystemExit("runner-owned check broker response mismatch")
    sys.stderr.write("CALIBRATION_BROKER_RECEIPT:" + receipt_token + "\\n")
    sys.stderr.flush()
    sys.stdout.write(response.get("stdout", ""))
    sys.stderr.write(response.get("stderr", ""))
    raise SystemExit(response["exit_code"])
if response.get("reason") == "unrecognized":
    os.execv({real!r}, [tool, *sys.argv[1:]])
sys.stderr.write("runner-owned check broker failed\\n")
raise SystemExit(125)
"""
    for tool in ("bash", "sh", "python", "python3", "make"):
        path = bin_dir / tool
        real = (
            "/runtime/python/bin/" + tool
            if tool.startswith("python")
            else "/usr/bin/" + tool
        )
        path.write_text(
            template.format(
                tool=tool,
                real=real,
                frame_limit=BROKER_FRAME_LIMIT_BYTES,
                frame_timeout=BROKER_FRAME_TIMEOUT_SECONDS,
                lock_timeout=BROKER_LOCK_TIMEOUT_SECONDS,
                pipe_buf=BROKER_PIPE_BUF_BYTES,
            ),
            encoding="utf-8",
        )
        path.chmod(0o555)
    if case is not None:
        _create_executor_shell_runtime(runtime, case)


def _create_executor_shell_runtime(runtime: Path, case: CaseSpec) -> None:
    """Materialize immutable inputs for generic executor command shells."""
    manifest = runtime / SHELL_MANIFEST_NAME
    manifest.write_text(
        json.dumps({"allowed_changes": sorted(case.allowed_changes)}) + "\n",
        encoding="utf-8",
    )
    manifest.chmod(0o444)
    real_shells = runtime / REAL_SHELL_DIRECTORY
    real_shells.mkdir()
    for name in ("bash", "sh"):
        source = Path("/usr/bin") / name
        if not source.is_file():
            raise EvaluationError(f"required real shell is missing: {source}")
        destination = real_shells / name
        shutil.copyfile(source, destination)
        destination.chmod(0o555)
    wrapper = runtime / SHELL_WRAPPER_NAME
    wrapper.write_text(_EXECUTOR_SHELL_WRAPPER, encoding="utf-8")
    wrapper.chmod(0o555)


_EXECUTOR_SHELL_WRAPPER = r"""#!/runtime/python/bin/python3
import json
import os
import sys

MANIFEST = "/broker/executor-shell-manifest.json"
try:
    with open(MANIFEST, encoding="utf-8") as handle:
        allowed = json.load(handle)["allowed_changes"]
except (OSError, ValueError, KeyError, TypeError) as exc:
    raise SystemExit(f"runner-owned executor shell manifest is unusable: {exc}")
if not isinstance(allowed, list) or not all(
    isinstance(item, str)
    and item
    and not item.startswith("/")
    and ".." not in item.split("/")
    for item in allowed
):
    raise SystemExit("runner-owned executor shell manifest is invalid")
shell = os.path.basename(sys.argv[0])
if shell not in {"bash", "sh"}:
    raise SystemExit("runner-owned executor shell was invoked unexpectedly")
command = [
    "/usr/bin/bwrap", "--die-with-parent", "--unshare-pid",
    "--dir", "/usr", "--ro-bind", "/usr", "/usr",
    "--dir", "/etc", "--ro-bind", "/etc", "/etc",
    "--symlink", "usr/bin", "/bin", "--symlink", "usr/sbin", "/sbin",
    "--symlink", "usr/lib", "/lib", "--symlink", "usr/lib64", "/lib64",
    "--dev", "/dev", "--proc", "/proc",
    "--dir", "/runtime", "--ro-bind", "/runtime/python", "/runtime/python",
    "--dir", "/broker", "--ro-bind", "/broker", "/broker",
    "--dir", "/workspace", "--ro-bind", "/workspace", "/workspace",
    "--dir", "/tmp", "--bind", "/tmp", "/tmp",
]
for relative in sorted(allowed):
    command.extend(("--bind", f"/workspace/{relative}", f"/workspace/{relative}"))
command.extend((
    "--ro-bind", f"/broker/real-shell/{shell}", f"/usr/bin/{shell}",
    "--chdir", "/workspace", "--", "/usr/bin/env", "-i",
    "PATH=/broker/bin:/runtime/python/bin:/usr/bin:/bin",
    "PYTHONDONTWRITEBYTECODE=1", "HOME=/tmp", "TMPDIR=/tmp",
    f"/usr/bin/{shell}", *sys.argv[1:],
))
os.execv(command[0], command)
"""


def run_case(
    case: CaseSpec,
    workspace: Path,
    source_root: Path,
    auth_file: Path,
    output_dir: Path,
    model: str,
    reasoning_effort: str,
) -> dict[str, object]:
    """Run one model turn and return its deterministic result."""
    if output_dir.exists():
        raise EvaluationError(f"output directory already exists: {output_dir}")
    if not (workspace / ".git").is_dir():
        raise EvaluationError(f"workspace is not prepared: {workspace}")
    _validate_boundary_paths(case, workspace, output_dir)
    output_dir.mkdir(mode=0o700, parents=True)
    executor_dir = output_dir / "executor"
    executor_dir.mkdir(mode=0o700)
    (executor_dir / "tmp").mkdir()
    (executor_dir / "home").mkdir()
    final_message = executor_dir / "final-message.txt"
    trajectory = output_dir / "trajectory.jsonl"
    stderr_path = output_dir / "codex.stderr"
    codex_home = executor_dir / "codex-home"
    install_arm_home(source_root, auth_file, codex_home)
    env = _evaluation_env()
    env["CODEX_HOME"] = str(codex_home)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["TMPDIR"] = str(executor_dir / "tmp")
    env["TMP"] = env["TMPDIR"]
    env["TEMP"] = env["TMPDIR"]
    # Repository-owned wrappers use this runner-issued identity; workspace data
    # never chooses the identity that the oracle accepts.
    env["CALIBRATION_EVAL_RUN_ID"] = output_dir.name
    with tempfile.TemporaryDirectory(prefix="calibration-eval-broker-") as raw_runtime:
        runtime = Path(raw_runtime)
        create_broker_shims(runtime, case)
        preflight_broker = CommandBroker(case, workspace, runtime, output_dir.name)
        preflight_broker.start()
        try:
            run_executor_boundary_preflight(case, workspace, executor_dir, runtime)
        finally:
            preflight_broker.close()
        if preflight_broker.events or preflight_broker.errors:
            raise EvaluationError(
                "executor boundary preflight broker evidence is invalid"
            )
        broker = CommandBroker(case, workspace, runtime, output_dir.name)
        broker.start()
        try:
            command = build_bwrap_command(
                case, workspace, executor_dir, model, reasoning_effort, runtime
            )
            started = time.monotonic()
            result = _run_model(command, workspace, env)
        finally:
            broker.close()
    elapsed = time.monotonic() - started
    _write_private_file(trajectory, result.stdout)
    _write_private_file(stderr_path, result.stderr)
    verification = verify_workspace(case, workspace)
    run_id = output_dir.name
    executor_oracle = command_oracle(case, result.stdout, run_id, broker.events)
    if broker.errors:
        executor_oracle["errors"] = (
            cast(list[str], executor_oracle["errors"]) + broker.errors
        )
        executor_oracle["valid"] = False
    final_answer_oracle = final_oracle(case, final_message)
    verification["passed"] = (
        result.returncode == 0
        and bool(verification["passed"])
        and bool(executor_oracle["valid"])
        and bool(final_answer_oracle["valid"])
    )
    payload: dict[str, object] = {
        "case_id": case.case_id,
        "model": model,
        "reasoning_effort": reasoning_effort,
        "codex_exit_code": result.returncode,
        "elapsed_seconds": elapsed,
        "verification": verification,
        "command_oracle": executor_oracle,
        "final_oracle": final_answer_oracle,
    }
    validate_result_payload(case, payload)
    _write_private_file(
        output_dir / "result.json", json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "verify", "run"):
        child = subparsers.add_parser(name)
        child.add_argument("--case", type=Path, required=True)
        child.add_argument("--workspace", type=Path, required=True)
        if name == "run":
            child.add_argument("--source-root", type=Path, required=True)
            child.add_argument("--auth-file", type=Path, required=True)
            child.add_argument("--output-dir", type=Path, required=True)
            child.add_argument("--model", required=True)
            child.add_argument("--reasoning-effort", default="medium")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the requested evaluation operation."""
    args = _parser().parse_args(argv)
    try:
        case = load_case(cast(Path, args.case))
        workspace = cast(Path, args.workspace)
        if args.command == "prepare":
            prepare_workspace(case, workspace)
            payload: dict[str, object] = {
                "case_id": case.case_id,
                "workspace": str(workspace),
                "state": "prepared",
            }
        elif args.command == "verify":
            payload = verify_workspace(case, workspace)
        else:
            payload = run_case(
                case,
                workspace,
                cast(Path, args.source_root),
                cast(Path, args.auth_file),
                cast(Path, args.output_dir),
                cast(str, args.model),
                cast(str, args.reasoning_effort),
            )
    except EvaluationError as exc:
        print(json.dumps({"error": str(exc), "state": "failed"}, sort_keys=True))
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through main()
    raise SystemExit(main())
