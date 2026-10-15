"""Socket doubles for unit tests of executor preflight cleanup and rejection.

Tests choose connection delivery and probe outcomes explicitly. These helpers
replace only the listener and command construction; they never bypass preflight.
"""

from pathlib import Path

import pytest

from scripts import run_writable_agent_eval as evaluation
from scripts.run_writable_agent_eval import CaseSpec


class PreflightClient:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class PreflightListener:
    def __init__(
        self,
        client: PreflightClient | None = None,
        *,
        port: int = 43123,
        peer_port: int = 43124,
    ) -> None:
        self.client = client
        self.port = port
        self.peer_port = peer_port
        self.closed = False
        self.timeouts: list[float] = []

    def bind(self, address: tuple[str, int]) -> None:
        assert address == ("127.0.0.1", 0)

    def listen(self, backlog: int) -> None:
        assert backlog == 1

    def settimeout(self, timeout: float) -> None:
        self.timeouts.append(timeout)

    def getsockname(self) -> tuple[str, int]:
        return ("127.0.0.1", self.port)

    def accept(self) -> tuple[PreflightClient, tuple[str, int]]:
        if self.client is None:
            raise TimeoutError
        return self.client, ("127.0.0.1", self.peer_port)

    def close(self) -> None:
        self.closed = True


def patch_preflight_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    listener: PreflightListener,
    *,
    command: str = "synthetic-preflight",
) -> None:
    def fake_socket(_family: int, _kind: int) -> PreflightListener:
        return listener

    def synthetic_command(
        _case: CaseSpec,
        _workspace: Path,
        _output_dir: Path,
        _runtime: Path,
        _listener_port: int,
    ) -> list[str]:
        return [command]

    monkeypatch.setattr(evaluation.socket, "socket", fake_socket)
    monkeypatch.setattr(
        evaluation,
        "build_executor_boundary_preflight_command",
        synthetic_command,
    )
