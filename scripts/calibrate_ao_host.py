#!/usr/bin/env python3
"""Inspect and render private AO host authority without applying host changes."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tomllib
import urllib.parse
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import NoReturn, cast

Runner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]
JSON_SCHEMA_VERSION = 1
PROFILE_VERSION = 2
DEFAULT_BASE_URL = "http://127.0.0.1:3001"
EXIT_OK = 0
EXIT_INVALID = 1
EXIT_USAGE = 2
EXIT_PROBE = 3
PROBE_TIMEOUT_SECONDS = 10
V1_KEYS = {
    "ao": {
        "cli",
        "data_dir",
        "codex_home",
        "daemon_service",
        "loopback_base_url",
        "health_path",
        "ready_path",
    },
    "dashboard": {
        "listen_host",
        "listen_port",
        "trusted_readonly_cidrs",
        "document_root",
        "active_config",
        "desired_service",
        "rollback_service",
    },
    "terminal": {
        "desired_enabled",
        "trust_model",
        "allowed_client_ips",
        "allowed_origin",
        "path",
        "upstream",
        "upstream_origin",
        "require_authentication_if",
    },
    "paths": {
        "private_authority",
        "desired_nginx_artifact",
        "desired_service_artifact",
        "state_root",
    },
}
V2_ADDITIONS = {
    "ao": {"runtime_owner", "process_containment"},
    "dashboard": {"mode", "nginx_executable", "pid_file"},
    "terminal": {"origin_mode"},
}
DOCTOR_CORE_CHECKS = {
    "config",
    "data-dir",
    "data-dir-write",
    "sqlite",
    "hooks-log",
    "daemon",
    "git",
    "tmux",
    "ao-binary",
    "claude-code",
    "codex",
    "codex-launch-flags",
}


class CalibrationError(RuntimeError):
    """Report a profile, candidate, or probe contract failure."""


class JsonArgumentParser(argparse.ArgumentParser):
    """Emit the CLI's fixed JSON error envelope for usage failures."""

    def error(self, message: str) -> NoReturn:
        _emit("usage", False, error={"kind": "usage", "message": message})
        raise SystemExit(EXIT_USAGE)


@dataclass(frozen=True)
class Evidence:
    """One observation with its owning state and normalized result."""

    id: str
    owner: str
    status: str
    detail: str


def _emit(
    command: str,
    ok: bool,
    *,
    result: Mapping[str, object] | None = None,
    error: Mapping[str, object] | None = None,
) -> None:
    supplied = dict(result or {})
    payload: dict[str, object] = {
        "schema_version": JSON_SCHEMA_VERSION,
        "command": command,
        "context": supplied.pop("context", "auto"),
        "states": supplied.pop(
            "states",
            {
                "daemon": "indeterminate",
                "delivery": "not_applicable",
                "operation": "ready" if ok else "unavailable",
            },
        ),
        "capabilities": supplied.pop("capabilities", supplied),
        "probes": supplied.pop("probes", []),
        "known_issues": supplied.pop("known_issues", []),
        "next_actions": supplied.pop("next_actions", []),
    }
    if error is not None:
        cast(dict[str, object], payload["capabilities"])["error"] = dict(error)
    print(json.dumps(payload, indent=2, sort_keys=True))


def _run(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        check=False,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
        timeout=PROBE_TIMEOUT_SECONDS,
    )


def _probe(runner: Runner, owner: str, name: str, command: Sequence[str]) -> Evidence:
    try:
        result = runner(command)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return Evidence(name, owner, "fail", f"{type(exc).__name__}: {exc}")
    detail = result.stdout.strip() or result.stderr.strip() or "no output"
    return Evidence(name, owner, "pass" if result.returncode == 0 else "fail", detail)


def _probe_mux(runner: Runner, owner: str, command: Sequence[str]) -> Evidence:
    try:
        result = runner(command)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return Evidence("mux", owner, "fail", f"{type(exc).__name__}: {exc}")
    detail = result.stdout.strip() or result.stderr.strip() or "no output"
    handshake = re.search(r"^HTTP/\S+\s+101(?:\s|$)", detail, re.MULTILINE)
    return Evidence("mux", owner, "pass" if handshake else "fail", detail)


def _json_object(text: str) -> dict[str, object]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return cast(dict[str, object], value) if isinstance(value, dict) else {}


def _required_subset(
    value: Mapping[str, object], required: Mapping[str, type[object]]
) -> bool:
    return all(
        key in value and isinstance(value[key], expected)
        for key, expected in required.items()
    )


def _profile_base_url(profile: Path | None) -> str:
    if profile is None or not profile.exists():
        return DEFAULT_BASE_URL
    try:
        parsed = _load_profile(profile)
    except CalibrationError:
        return DEFAULT_BASE_URL
    ao = cast(dict[str, object], parsed["ao"])
    return cast(str, ao["loopback_base_url"])


def _validate_loopback_url(value: object, label: str, *, mux_path: bool = False) -> str:
    if not isinstance(value, str):
        raise CalibrationError(f"{label} must be a string")
    if any(character.isspace() or ord(character) < 0x20 for character in value):
        raise CalibrationError(f"{label} must not contain whitespace or controls")
    try:
        parsed = urllib.parse.urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise CalibrationError(f"{label} must be a valid loopback URL") from exc
    expected_path = "/mux" if mux_path else ""
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "::1", "localhost"}
        or port is None
        or not 1 <= port <= 65535
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path != expected_path
        or parsed.query
        or parsed.fragment
    ):
        raise CalibrationError(f"{label} must be an HTTP loopback URL")
    return value


def _validate_interpolated_scalar(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or re.fullmatch(r"[A-Za-z0-9_./:@+-]+", value) is None
    ):
        raise CalibrationError(f"{label} contains unsafe configuration syntax")
    return value


def _validate_service_unit(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.@-]*\.service", value) is None
    ):
        raise CalibrationError(f"{label} must be a safe systemd service unit")
    return value


def _dashboard_url(host: str, port: int) -> str:
    address = f"[{host}]" if ipaddress.ip_address(host).version == 6 else host
    return f"http://{address}:{port}"


def _mux_probe_command(base_url: str, origin: object) -> tuple[str, ...]:
    return (
        "curl",
        "--http1.1",
        "--max-time",
        "2",
        "-sS",
        "-D",
        "-",
        "-o",
        "/dev/null",
        "-H",
        f"Origin: {origin}",
        "-H",
        "Connection: Upgrade",
        "-H",
        "Upgrade: websocket",
        "-H",
        "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==",
        "-H",
        "Sec-WebSocket-Version: 13",
        base_url + "/mux",
    )


def _validate_origin(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise CalibrationError(f"{label} must be an exact Origin")
    try:
        parsed = urllib.parse.urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise CalibrationError(f"{label} must be an exact Origin") from exc
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.hostname is None
        or (port is not None and not 1 <= port <= 65535)
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
        or re.fullmatch(
            r"(?:[A-Za-z0-9.-]+|\[[0-9A-Fa-f:]+\])(?::[0-9]+)?",
            parsed.netloc,
        )
        is None
        or any(character.isspace() for character in value)
        or any(ord(character) < 0x20 for character in value)
        or any(character in value for character in "\"';#")
    ):
        raise CalibrationError(f"{label} must be an exact Origin")
    return value


def evaluate_daemon_state(
    probes: Mapping[str, Evidence],
    *,
    context: str,
    status: Mapping[str, object],
    health: Mapping[str, object],
    ready: Mapping[str, object],
    core_doctor_failure: bool = False,
) -> str:
    """Classify daemon state from authoritative probe values only."""
    if context != "host":
        return "indeterminate"
    service = probes["systemd-active"]
    health_probe = probes["healthz"]
    ready_probe = probes["readyz"]
    main_pid_text = probes["main-pid"].detail
    main_pid = int(main_pid_text) if main_pid_text.isdecimal() else None
    endpoint_identity = {
        "pid": int,
        "executablePath": str,
        "workingDirectory": str,
        "startupWorkingDirectory": str,
    }
    identity_matches = (
        main_pid is not None
        and isinstance(status.get("pid"), int)
        and status.get("pid") == main_pid
        and isinstance(status.get("port"), int)
        and status.get("health") == "ok"
        and status.get("ready") == "ready"
        and _required_subset(health, endpoint_identity)
        and _required_subset(ready, endpoint_identity)
        and health.get("pid") == main_pid
        and ready.get("pid") == main_pid
        and health.get("status") == "ok"
        and ready.get("status") == "ready"
        and health.get("service") == "agent-orchestrator-daemon"
        and ready.get("service") == "agent-orchestrator-daemon"
        and all(
            health.get(field) == ready.get(field)
            for field in (
                "executablePath",
                "workingDirectory",
                "startupWorkingDirectory",
            )
        )
    )
    if (
        service.status == "pass"
        and service.detail == "active"
        and probes["status"].status == "pass"
        and status.get("state") in {"ready", "running"}
        and health_probe.status == "pass"
        and ready_probe.status == "pass"
        and identity_matches
        and not core_doctor_failure
    ):
        return "ready"
    if probes["ao-version"].status == "fail" and context == "host":
        return "not_installed"
    if (
        context == "host"
        and service.detail in {"inactive", "failed"}
        and health_probe.status == "fail"
        and ready_probe.status == "fail"
    ):
        return "unavailable"
    return "indeterminate"


def evaluate_delivery_state(
    probes: Mapping[str, Evidence],
    *,
    daemon_state: str,
    dashboard_enabled: bool | None,
    terminal_enabled: bool | None,
    external_failure: bool = False,
) -> str:
    """Classify Dashboard delivery independently from daemon readiness."""
    if daemon_state == "ready" and external_failure:
        return "degraded"
    if dashboard_enabled is False:
        return "not_applicable"
    if dashboard_enabled is None or daemon_state != "ready":
        return "indeterminate"
    if probes["dashboard"].status != "pass":
        return "degraded"
    if terminal_enabled is True and probes["mux"].status != "pass":
        return "degraded"
    return "ready"


def _doctor_failure_classes(doctor: Mapping[str, object]) -> tuple[bool, bool]:
    checks = doctor.get("checks")
    items = cast(list[object], checks) if isinstance(checks, list) else []
    external_failure = False
    core_failure = False
    for raw_item in items:
        if isinstance(raw_item, dict):
            item = cast(dict[str, object], raw_item)
            name = item.get("name")
            level = item.get("level")
            if isinstance(name, str) and level in {"FAIL", "ERROR"}:
                if any(
                    token in name.casefold()
                    for token in ("auth", "github", "token", "integration")
                ):
                    external_failure = True
                elif name in DOCTOR_CORE_CHECKS or name:
                    core_failure = True
    return external_failure, core_failure


def _version_before(value: object, minimum: tuple[int, int]) -> bool:
    if not isinstance(value, str):
        return False
    match = re.fullmatch(r"(\d+)\.(\d+)(?:\..*)?", value)
    return match is not None and tuple(map(int, match.groups())) < minimum


def evaluate_known_issues(
    *,
    probes: Mapping[str, Evidence],
    status: Mapping[str, object],
    doctor: Mapping[str, object],
    capabilities: Mapping[str, object],
    terminal: Mapping[str, object] | None,
    context: str = "host",
    external_doctor_failure: bool = False,
) -> list[str]:
    """Return stable issue IDs from already collected, mutation-free evidence."""
    issues: list[str] = []
    if (
        context == "auto"
        or status.get("state") not in {"ready", "running"}
        or (
            context == "sandbox"
            and doctor.get("ok") is not True
            and not external_doctor_failure
        )
    ):
        issues.append("AO-HOST-CONTEXT-MISMATCH")
    if _version_before(capabilities.get("glibc_version"), (2, 38)):
        issues.append("AO-GLIBC-INCOMPATIBLE")
    if _version_before(capabilities.get("tmux_version"), (3, 5)):
        issues.append("AO-TMUX-TOO-OLD")
    if capabilities.get("codex_home_compatible") is False:
        issues.append("AO-CODEX-HOME-CONFLICT")
    if (
        terminal is not None
        and terminal.get("desired_enabled") is True
        and probes["mux"].status == "fail"
    ):
        issues.append("AO-DASHBOARD-MUX-NOT-PROXIED")
    if terminal is not None and terminal.get("origin_mode", "preserve") != "preserve":
        issues.append("AO-DASHBOARD-UPSTREAM-ORIGIN-REWRITE")
    if capabilities.get("effective_process_containment") != "systemd-scope-verified":
        issues.append("AO-PROCESS-CONTAINMENT-UNVERIFIED")
    return issues


def inspect_host(
    runner: Runner = _run,
    *,
    profile: Path | None = None,
    context: str = "auto",
) -> dict[str, object]:
    """Collect state-owner evidence without requiring a host profile.

    Examples:
        A caller may inject a fake runner and assert the returned
        ``classification`` without reading or changing active host state.

    Notes:
        Daemon readiness requires authoritative service, AO status, process
        identity, and endpoint evidence. Sandbox-owned observations cannot
        establish host readiness.
    """
    if context not in {"auto", "host", "sandbox"}:
        raise CalibrationError("context must be auto, host, or sandbox")
    if profile is not None and not profile.exists():
        raise CalibrationError(f"{profile} does not exist")
    base = _profile_base_url(profile)
    health = "/healthz"
    ready = "/readyz"
    service = "agent-orchestrator.service"
    ao_cli = "ao"
    dashboard_base: str | None = None
    terminal_profile: dict[str, object] | None = None
    if profile is not None and profile.exists():
        parsed = _load_profile(profile)
        ao = cast(dict[str, object], parsed["ao"])
        dashboard = _section(parsed, "dashboard")
        terminal_profile = _section(dashboard, "terminal")
        health = cast(str, ao["health_path"])
        ready = cast(str, ao["ready_path"])
        service = cast(str, ao["daemon_service"])
        ao_cli = cast(str, ao["cli"])
        if dashboard.get("mode", "read-only") == "read-only":
            dashboard_base = _dashboard_url(
                cast(str, dashboard["listen_host"]),
                cast(int, dashboard["listen_port"]),
            )
    authoritative_owner = "host" if context == "host" else "sandbox"
    endpoint_owner = "daemon" if context == "host" else "sandbox"
    evidence = [
        _probe(runner, authoritative_owner, "ao-version", (ao_cli, "version")),
        _probe(runner, "sandbox", "glibc", ("ldd", "--version")),
        _probe(runner, "worker", "tmux", ("tmux", "-V")),
        _probe(runner, "worker", "cgroup", ("stat", "-fc", "%T", "/sys/fs/cgroup")),
        _probe(
            runner,
            authoritative_owner,
            "systemd-active",
            ("systemctl", "--user", "is-active", service),
        ),
        _probe(
            runner,
            authoritative_owner,
            "main-pid",
            ("systemctl", "--user", "show", service, "-p", "MainPID", "--value"),
        ),
        _probe(runner, authoritative_owner, "status", (ao_cli, "status", "--json")),
        _probe(runner, authoritative_owner, "doctor", (ao_cli, "doctor", "--json")),
        _probe(runner, endpoint_owner, "healthz", ("curl", "-fsS", base + health)),
        _probe(runner, endpoint_owner, "readyz", ("curl", "-fsS", base + ready)),
    ]
    evidence.append(
        _probe(
            runner,
            endpoint_owner,
            "dashboard",
            ("curl", "-fsS", dashboard_base + "/dashboard-health"),
        )
        if dashboard_base is not None
        else Evidence(
            "dashboard", endpoint_owner, "unknown", "Dashboard not configured"
        )
    )
    evidence.append(
        _probe_mux(
            runner,
            endpoint_owner,
            _mux_probe_command(dashboard_base, terminal_profile["allowed_origin"]),
        )
        if dashboard_base is not None
        and terminal_profile is not None
        and terminal_profile.get("desired_enabled") is True
        else Evidence("mux", endpoint_owner, "unknown", "Terminal not configured")
    )
    by_name = {item.id: item for item in evidence}
    status = _json_object(by_name["status"].detail)
    doctor = _json_object(by_name["doctor"].detail)
    external_doctor_failure, core_doctor_failure = _doctor_failure_classes(doctor)
    doctor_valid = _required_subset(doctor, {"ok": bool, "checks": list})
    if (
        doctor_valid
        and doctor["ok"] is False
        and not external_doctor_failure
        and not core_doctor_failure
    ):
        core_doctor_failure = True
    core_doctor_failure = core_doctor_failure or not doctor_valid
    health_payload = _json_object(by_name["healthz"].detail)
    ready_payload = _json_object(by_name["readyz"].detail)
    daemon_state = evaluate_daemon_state(
        by_name,
        context=context,
        status=status,
        health=health_payload,
        ready=ready_payload,
        core_doctor_failure=core_doctor_failure,
    )
    tmux_match = re.search(r"\btmux\s+(\d+(?:\.\d+)+)", by_name["tmux"].detail)
    glibc_match = re.search(r"(\d+(?:\.\d+)+)", by_name["glibc"].detail)
    cgroup_text = by_name["cgroup"].detail
    cgroup_version = (
        "v2"
        if "cgroup2" in cgroup_text
        else "v1"
        if cgroup_text in {"tmpfs", "cgroup"}
        else "unknown"
    )
    terminal: dict[str, object] | None = None
    desired_process_containment: object = None
    codex_home_compatible: bool | None = None
    if profile is not None and profile.exists():
        parsed = _load_profile(profile)
        terminal = _section(_section(parsed, "dashboard"), "terminal")
        desired_process_containment = _section(parsed, "ao").get(
            "process_containment", "legacy"
        )
        try:
            _validate_codex_home(Path(cast(str, _section(parsed, "ao")["codex_home"])))
            codex_home_compatible = True
        except CalibrationError:
            codex_home_compatible = False
    capabilities: dict[str, object] = {
        "loopback_base_url": base,
        "ao_version_text": by_name["ao-version"].detail,
        "glibc_version": glibc_match.group(1) if glibc_match else None,
        "tmux_version": tmux_match.group(1) if tmux_match else None,
        "cgroup_version": cgroup_version,
        "codex_home_compatible": codex_home_compatible,
        "desired_process_containment": desired_process_containment,
        "effective_process_containment": "unverified",
        "ao_status": status,
        "ao_doctor": doctor,
        "healthz": health_payload,
        "readyz": ready_payload,
        "status_required_subset_valid": _required_subset(status, {"state": str}),
        "doctor_required_subset_valid": _required_subset(
            doctor, {"ok": bool, "checks": list}
        ),
    }
    delivery_state = evaluate_delivery_state(
        by_name,
        daemon_state=daemon_state,
        dashboard_enabled=dashboard_base is not None,
        terminal_enabled=(
            cast(bool, terminal["desired_enabled"]) if terminal is not None else None
        ),
        external_failure=external_doctor_failure,
    )
    issues = evaluate_known_issues(
        probes=by_name,
        status=status,
        doctor=doctor,
        capabilities=capabilities,
        terminal=terminal,
        context=context,
        external_doctor_failure=external_doctor_failure,
    )
    return {
        "schema_version": JSON_SCHEMA_VERSION,
        "command": "inspect",
        "context": context,
        "states": {
            "daemon": daemon_state,
            "delivery": delivery_state,
        },
        "capabilities": capabilities,
        "probes": [
            {
                **asdict(item),
                "detail": item.detail[:1000],
            }
            for item in evidence
        ],
        "known_issues": issues,
        "next_actions": [f"investigate {issue}" for issue in issues],
    }


def _safe_path(path: Path, *, may_create: bool, directory: bool | None = None) -> Path:
    expanded = path.expanduser()
    if not expanded.is_absolute():
        raise CalibrationError(f"{path} must be absolute")
    current = Path(expanded.anchor)
    for part in expanded.parts[1:]:
        current /= part
        if current.is_symlink():
            raise CalibrationError(f"{path} must not traverse a symlink")
    if expanded.exists():
        if stat.S_IMODE(expanded.stat().st_mode) & 0o077:
            raise CalibrationError(f"{path} must not be accessible by group or other")
        if directory is True and not expanded.is_dir():
            raise CalibrationError(f"{path} must be a directory")
        if directory is False and not expanded.is_file():
            raise CalibrationError(f"{path} must be a regular file")
    elif not may_create:
        raise CalibrationError(f"{path} does not exist")
    return expanded.resolve()


def _validate_codex_home(path: Path) -> Path:
    home = _safe_path(path, may_create=False, directory=True)
    config = home / "config.toml"
    if config.is_symlink() or not config.is_file():
        raise CalibrationError(f"{config} must be a regular file")
    if stat.S_IMODE(config.stat().st_mode) & 0o077:
        raise CalibrationError(f"{config} must not be accessible by group or other")
    try:
        parsed = tomllib.loads(config.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise CalibrationError(f"{config} must contain valid TOML: {exc}") from exc
    features = parsed.get("features")
    if not isinstance(features, dict):
        raise CalibrationError(f"{config} must define [features]")
    feature_map = cast(dict[str, object], features)
    if feature_map.get("apps") is not False or feature_map.get("plugins") is not False:
        raise CalibrationError(f"{config} requires apps=false and plugins=false")
    if "mcp_servers" in parsed:
        raise CalibrationError(f"{config} must not define top-level mcp_servers")
    auth = home / "auth.json"
    if not auth.is_file():
        raise CalibrationError(f"{auth} must resolve to an authentication file")
    if stat.S_IMODE(auth.stat().st_mode) & 0o077:
        raise CalibrationError(f"{auth} must not be accessible by group or other")
    try:
        auth_payload = json.loads(auth.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CalibrationError(f"{auth} must contain valid JSON: {exc}") from exc
    if not isinstance(auth_payload, dict):
        raise CalibrationError(f"{auth} must contain a JSON object")
    return home


def _section(profile: Mapping[str, object], name: str) -> dict[str, object]:
    value = profile.get(name)
    if not isinstance(value, dict):
        raise CalibrationError(f"profile must define [{name}]")
    return cast(dict[str, object], value)


def _validate_keys(
    section: Mapping[str, object],
    required: set[str],
    label: str,
    additions: set[str] | None = None,
) -> None:
    additions = additions or set()
    missing = required - set(section)
    unknown = set(section) - required - additions
    if missing:
        raise CalibrationError(f"{label} missing keys: {', '.join(sorted(missing))}")
    if unknown:
        raise CalibrationError(f"{label} unknown keys: {', '.join(sorted(unknown))}")


def _validate_storage_boundaries(boundaries: object) -> list[dict[str, object]]:
    values = cast(list[object], boundaries) if isinstance(boundaries, list) else []
    if not values:
        raise CalibrationError("storage.boundaries must not be empty")
    validated: list[dict[str, object]] = []
    for raw_boundary in values:
        if not isinstance(raw_boundary, dict):
            raise CalibrationError("storage.boundaries entries must be objects")
        boundary = cast(dict[str, object], raw_boundary)
        if set(boundary) != {"path", "kind", "recursive_search"}:
            raise CalibrationError(
                "storage boundary requires path, kind, and recursive_search"
            )
        if (
            not isinstance(boundary["path"], str)
            or not Path(boundary["path"]).is_absolute()
            or not isinstance(boundary["kind"], str)
            or not isinstance(boundary["recursive_search"], bool)
        ):
            raise CalibrationError("storage boundary fields have invalid types")
        _validate_interpolated_scalar(boundary["path"], "storage boundary path")
        if re.fullmatch(r"[a-z0-9-]+", boundary["kind"]) is None:
            raise CalibrationError("storage boundary kind is invalid")
        if boundary["recursive_search"] is not False:
            raise CalibrationError(
                "storage boundary recursive_search must be false in the host profile"
            )
        validated.append(boundary)
    return validated


def _load_profile(path: Path) -> dict[str, object]:
    safe = _safe_path(path, may_create=False, directory=False)
    try:
        profile = tomllib.loads(safe.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise CalibrationError(f"{safe} must contain valid TOML: {exc}") from exc
    version = profile.get("schema_version", 1)
    if type(version) is not int or version not in {1, 2}:
        raise CalibrationError(f"unsupported schema_version: {version!r}")
    allowed_top = {"schema_version", "ao", "dashboard", "paths"}
    if version == 2:
        allowed_top.add("storage")
    unknown_top = set(profile) - allowed_top
    if unknown_top:
        raise CalibrationError(
            "unknown top-level keys: " + ", ".join(sorted(unknown_top))
        )
    ao = _section(profile, "ao")
    dashboard = _section(profile, "dashboard")
    terminal = _section(dashboard, "terminal")
    paths = _section(profile, "paths")
    additions: dict[str, set[str]] = (
        V2_ADDITIONS
        if version == 2
        else {"ao": set(), "dashboard": set(), "terminal": set()}
    )
    _validate_keys(ao, V1_KEYS["ao"], "ao", additions["ao"])
    _validate_keys(
        dashboard,
        V1_KEYS["dashboard"] | {"terminal"},
        "dashboard",
        additions["dashboard"],
    )
    _validate_keys(
        terminal, V1_KEYS["terminal"], "dashboard.terminal", additions["terminal"]
    )
    _validate_keys(paths, V1_KEYS["paths"], "paths")
    if version == 2:
        storage = _section(profile, "storage")
        _validate_keys(storage, {"boundaries"}, "storage")
    for key in (
        "cli",
        "data_dir",
        "codex_home",
        "daemon_service",
        "loopback_base_url",
        "health_path",
        "ready_path",
    ):
        if not isinstance(ao[key], str):
            raise CalibrationError(f"ao.{key} must be a string")
    cli = cast(str, ao["cli"])
    if "/" in cli and not Path(cli).is_absolute():
        raise CalibrationError("ao.cli path must be absolute")
    if "/" not in cli and re.fullmatch(r"[A-Za-z0-9._-]+", cli) is None:
        raise CalibrationError("ao.cli must be an executable name or absolute path")
    _validate_service_unit(ao["daemon_service"], "ao.daemon_service")
    _validate_loopback_url(ao["loopback_base_url"], "ao.loopback_base_url")
    for key in ("health_path", "ready_path"):
        value = cast(str, ao[key])
        if (
            not value.startswith("/")
            or value.startswith("//")
            or re.fullmatch(r"/[A-Za-z0-9/_-]*", value) is None
        ):
            raise CalibrationError(f"ao.{key} must be an absolute URL path")
    listen_host = dashboard.get("listen_host")
    listen_port = dashboard.get("listen_port")
    readonly_cidrs = dashboard.get("trusted_readonly_cidrs")
    if not isinstance(listen_host, str):
        raise CalibrationError("dashboard.listen_host must be an IP address")
    try:
        ipaddress.ip_address(listen_host)
    except ValueError as exc:
        raise CalibrationError("dashboard.listen_host must be an IP address") from exc
    if type(listen_port) is not int or listen_port < 0 or listen_port > 65535:
        raise CalibrationError("dashboard.listen_port must be an integer port")
    if dashboard.get("mode", "read-only") == "read-only" and listen_port == 0:
        raise CalibrationError("enabled dashboard listen_port must be 1 through 65535")
    cidr_values = (
        cast(list[object], readonly_cidrs) if isinstance(readonly_cidrs, list) else []
    )
    if not isinstance(readonly_cidrs, list) or not all(
        isinstance(value, str) for value in cidr_values
    ):
        raise CalibrationError("dashboard.trusted_readonly_cidrs must be CIDR strings")
    if dashboard.get("mode", "read-only") == "read-only" and not cidr_values:
        raise CalibrationError("read-only dashboard requires trusted_readonly_cidrs")
    try:
        for value in cidr_values:
            ipaddress.ip_network(cast(str, value), strict=False)
    except ValueError as exc:
        raise CalibrationError(
            "dashboard.trusted_readonly_cidrs must be valid CIDRs"
        ) from exc
    absolute_fields = [
        ("ao.data_dir", ao["data_dir"]),
        ("ao.codex_home", ao["codex_home"]),
        ("dashboard.document_root", dashboard["document_root"]),
        ("dashboard.active_config", dashboard["active_config"]),
        *[(f"paths.{key}", paths[key]) for key in V1_KEYS["paths"]],
    ]
    if version == 2:
        absolute_fields.extend(
            [
                ("dashboard.nginx_executable", dashboard["nginx_executable"]),
                ("dashboard.pid_file", dashboard["pid_file"]),
            ]
        )
    for label, value in absolute_fields:
        if not isinstance(value, str) or not Path(value).is_absolute():
            raise CalibrationError(f"{label} must be an absolute path")
        _validate_interpolated_scalar(value, label)
    _validate_service_unit(
        dashboard.get("desired_service"), "dashboard.desired_service"
    )
    _validate_service_unit(
        dashboard.get("rollback_service"), "dashboard.rollback_service"
    )
    if version == 1:
        _validate_terminal_v1(terminal)
    else:
        if ao.get("runtime_owner") != "systemd-user":
            raise CalibrationError("ao.runtime_owner must be systemd-user")
        if ao.get("process_containment") != "legacy":
            raise CalibrationError("ao.process_containment must be legacy")
        if dashboard.get("mode") not in {"disabled", "read-only"}:
            raise CalibrationError(
                "dashboard.mode must be read-only when enabled, or disabled"
            )
        _validate_storage_boundaries(_section(profile, "storage").get("boundaries"))
        if (
            terminal.get("desired_enabled") is True
            and dashboard.get("mode") != "read-only"
        ):
            raise CalibrationError(
                "dashboard.mode must be read-only when terminal is enabled"
            )
        _validate_terminal(terminal)
    return cast(dict[str, object], profile)


def _validate_terminal_v1(terminal: Mapping[str, object]) -> None:
    """Validate the deployed legacy terminal contract without v2 reinterpretation."""
    _validate_terminal_shapes(terminal)
    enabled = terminal.get("desired_enabled")
    if not enabled:
        return
    clients = terminal.get("allowed_client_ips")
    client_values = cast(list[object], clients) if isinstance(clients, list) else []
    if not client_values or not all(isinstance(value, str) for value in client_values):
        raise CalibrationError("legacy terminal requires exact client IPs")
    for value in client_values:
        ipaddress.ip_address(cast(str, value))
    _validate_origin(terminal.get("allowed_origin"), "legacy terminal Origin")
    if terminal.get("path") != "/mux":
        raise CalibrationError("legacy terminal path must be exactly /mux")
    _validate_loopback_url(
        terminal.get("upstream"), "legacy terminal upstream", mux_path=True
    )
    _validate_loopback_url(
        terminal.get("upstream_origin"), "legacy terminal upstream Origin"
    )
    if terminal.get("trust_model") != "single-user-trusted-lan":
        raise CalibrationError("legacy terminal requires single-user-trusted-lan")


def _validate_terminal(terminal: Mapping[str, object]) -> None:
    _validate_terminal_shapes(terminal)
    enabled = terminal.get("desired_enabled")
    if enabled:
        clients = terminal.get("allowed_client_ips")
        client_values = cast(list[object], clients) if isinstance(clients, list) else []
        origin_mode = terminal.get("origin_mode")
        if (
            not client_values
            or not all(isinstance(value, str) for value in client_values)
            or (origin_mode == "preserve" and len(client_values) != 1)
        ):
            raise CalibrationError(
                "terminal requires exact client IPs compatible with origin mode"
            )
        for value in client_values:
            ipaddress.ip_address(cast(str, value))
        _validate_origin(terminal.get("allowed_origin"), "terminal Origin")
        if terminal.get("path") != "/mux":
            raise CalibrationError("terminal path must be exactly /mux")
        _validate_loopback_url(
            terminal.get("upstream"),
            "terminal upstream",
            mux_path=origin_mode == "edge-validated-rewrite",
        )
        if terminal.get("trust_model") != "trusted-single-user":
            raise CalibrationError("terminal requires trusted-single-user")
        if origin_mode not in {"preserve", "edge-validated-rewrite"}:
            raise CalibrationError("terminal requires an explicit Origin mode")
        if origin_mode == "edge-validated-rewrite":
            _validate_loopback_url(
                terminal.get("upstream_origin"), "terminal upstream Origin"
            )


def _validate_terminal_shapes(terminal: Mapping[str, object]) -> None:
    if not isinstance(terminal.get("desired_enabled"), bool):
        raise CalibrationError("dashboard.terminal.desired_enabled must be boolean")
    for key in (
        "trust_model",
        "allowed_origin",
        "path",
        "upstream",
        "upstream_origin",
    ):
        if not isinstance(terminal.get(key), str):
            raise CalibrationError(f"dashboard.terminal.{key} must be a string")
    clients = terminal.get("allowed_client_ips")
    client_values = cast(list[object], clients) if isinstance(clients, list) else []
    if not isinstance(clients, list) or not all(
        isinstance(value, str) for value in client_values
    ):
        raise CalibrationError(
            "dashboard.terminal.allowed_client_ips must be IP strings"
        )
    try:
        for value in cast(list[str], client_values):
            ipaddress.ip_address(value)
    except ValueError as exc:
        raise CalibrationError(
            "dashboard.terminal.allowed_client_ips must be valid IPs"
        ) from exc
    authentication = terminal.get("require_authentication_if")
    authentication_values = (
        cast(list[object], authentication) if isinstance(authentication, list) else []
    )
    if not isinstance(authentication, list) or not all(
        isinstance(value, str) for value in authentication_values
    ):
        raise CalibrationError(
            "dashboard.terminal.require_authentication_if must be strings"
        )
    if "origin_mode" in terminal and not isinstance(terminal["origin_mode"], str):
        raise CalibrationError("dashboard.terminal.origin_mode must be a string")


def _quote(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        return "[" + ", ".join(_quote(item) for item in cast(list[object], value)) + "]"
    if isinstance(value, dict):
        mapping = cast(dict[str, object], value)
        return (
            "{ "
            + ", ".join(f"{key} = {_quote(item)}" for key, item in mapping.items())
            + " }"
        )
    raise CalibrationError(f"unsupported TOML value: {value!r}")


def _canonical_v2(profile: Mapping[str, object]) -> dict[str, object]:
    ao = dict(_section(profile, "ao"))
    dashboard = dict(_section(profile, "dashboard"))
    terminal = dict(_section(dashboard, "terminal"))
    paths = dict(_section(profile, "paths"))
    ao.setdefault("runtime_owner", "systemd-user")
    ao.setdefault("process_containment", "legacy")
    dashboard.setdefault("mode", "read-only")
    dashboard.setdefault("nginx_executable", "/usr/sbin/nginx")
    dashboard.setdefault(
        "pid_file", str(Path(cast(str, paths["state_root"])) / "nginx.pid")
    )
    if profile.get("schema_version", 1) == 1:
        if terminal.get("trust_model") == "single-user-trusted-lan":
            terminal["trust_model"] = "trusted-single-user"
        terminal["origin_mode"] = "edge-validated-rewrite"
    else:
        terminal.setdefault("origin_mode", "preserve")
    dashboard["terminal"] = terminal
    storage = (
        dict(_section(profile, "storage"))
        if profile.get("schema_version") == 2
        else {
            "boundaries": [
                {
                    "path": paths["state_root"],
                    "kind": "host-state",
                    "recursive_search": False,
                },
                {
                    "path": ao["data_dir"],
                    "kind": "ao-data",
                    "recursive_search": False,
                },
            ]
        }
    )
    return {
        "schema_version": 2,
        "ao": ao,
        "dashboard": dashboard,
        "paths": paths,
        "storage": storage,
    }


def _toml(profile: Mapping[str, object]) -> str:
    lines = ["schema_version = 2"]
    for name in ("ao", "dashboard"):
        section = _section(profile, name)
        lines.append(f"\n[{name}]")
        for key, value in section.items():
            if key != "terminal":
                lines.append(f"{key} = {_quote(value)}")
        if name == "dashboard":
            terminal = _section(section, "terminal")
            lines.append("\n[dashboard.terminal]")
            lines.extend(f"{key} = {_quote(value)}" for key, value in terminal.items())
    for name in ("paths", "storage"):
        section = _section(profile, name)
        lines.append(f"\n[{name}]")
        lines.extend(f"{key} = {_quote(value)}" for key, value in section.items())
    return "\n".join(lines) + "\n"


def init_profile(
    path: Path,
    *,
    trust_model: str,
    codex_home: Path,
    data_dir: Path,
    private_authority: Path,
    state_root: Path,
    storage_boundaries: Sequence[Mapping[str, object]] = (),
    dashboard_enabled: bool = False,
    dashboard_listen_host: str | None = None,
    dashboard_listen_port: int | None = None,
    readonly_cidrs: Sequence[str] = (),
    document_root: Path | None = None,
    nginx_executable: Path | None = None,
    nginx_pid_file: Path | None = None,
    active_config: Path | None = None,
    desired_service: str | None = None,
    rollback_service: str | None = None,
    desired_nginx_artifact: Path | None = None,
    desired_service_artifact: Path | None = None,
    terminal: bool = False,
    client_ips: Sequence[str] = (),
    origin: str | None = None,
    upstream: str | None = None,
    upstream_origin: str | None = None,
    origin_mode: str | None = None,
) -> dict[str, object]:
    """Create a canonical schema v2 profile with terminal disabled by default."""
    target = _safe_path(path, may_create=True)
    if target.exists():
        raise CalibrationError(f"{target} already exists")
    if target.parent.exists() and stat.S_IMODE(target.parent.stat().st_mode) & 0o077:
        raise CalibrationError(
            f"{target.parent} must not be accessible by group or other"
        )
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    home = _validate_codex_home(codex_home)
    for private in (data_dir, private_authority.parent, state_root):
        _safe_path(private, may_create=True)
    dashboard_values = (
        dashboard_listen_host,
        dashboard_listen_port,
        document_root,
        nginx_executable,
        nginx_pid_file,
        active_config,
        desired_service,
        rollback_service,
        desired_nginx_artifact,
        desired_service_artifact,
    )
    if dashboard_enabled and (
        any(value is None for value in dashboard_values) or not readonly_cidrs
    ):
        raise CalibrationError(
            "enabled dashboard requires explicit listen, CIDR, path, "
            "nginx, and service values"
        )
    if dashboard_enabled:
        if dashboard_listen_port is None or not 1 <= dashboard_listen_port <= 65535:
            raise CalibrationError(
                "enabled dashboard requires a listen port from 1 through 65535"
            )
        try:
            ipaddress.ip_address(cast(str, dashboard_listen_host))
        except ValueError as exc:
            raise CalibrationError(
                "enabled dashboard requires an exact listen IP"
            ) from exc
    if terminal and (
        not dashboard_enabled
        or not client_ips
        or origin is None
        or upstream is None
        or origin_mode is None
        or (origin_mode == "edge-validated-rewrite" and upstream_origin is None)
    ):
        raise CalibrationError(
            "enabled terminal requires explicit dashboard, IP, Origin, "
            "and upstream values"
        )
    try:
        for cidr in readonly_cidrs:
            ipaddress.ip_network(cidr, strict=False)
    except ValueError as exc:
        raise CalibrationError("readonly CIDRs must be valid networks") from exc
    base = DEFAULT_BASE_URL
    dashboard_host = dashboard_listen_host or "127.0.0.1"
    dashboard_port = dashboard_listen_port or 0
    document = document_root or state_root / "dashboard-disabled"
    nginx = nginx_executable or Path("/usr/sbin/nginx")
    pid_file = nginx_pid_file or state_root / "nginx.pid"
    active = active_config or state_root / "active.conf"
    service = desired_service or "ao-dashboard.service"
    rollback = rollback_service or "ao-dashboard-rollback.service"
    _validate_service_unit(service, "dashboard desired service")
    _validate_service_unit(rollback, "dashboard rollback service")
    nginx_artifact = desired_nginx_artifact or state_root / "nginx.conf"
    service_artifact = desired_service_artifact or state_root / "nginx.service"
    reconstruction_paths = (
        data_dir,
        home,
        private_authority,
        state_root,
        document,
        nginx,
        pid_file,
        active,
        nginx_artifact,
        service_artifact,
    )
    for reconstruction_path in reconstruction_paths:
        if not reconstruction_path.is_absolute():
            raise CalibrationError("reconstruction paths must be absolute")
        _validate_interpolated_scalar(str(reconstruction_path), "reconstruction path")
    boundary_values = list(storage_boundaries) or [
        {
            "path": str(state_root),
            "kind": "host-state",
            "recursive_search": False,
        },
        {
            "path": str(data_dir),
            "kind": "ao-data",
            "recursive_search": False,
        },
    ]
    _validate_storage_boundaries(boundary_values)
    profile: dict[str, object] = {
        "schema_version": PROFILE_VERSION,
        "ao": {
            "cli": "ao",
            "data_dir": str(data_dir),
            "codex_home": str(home),
            "daemon_service": "agent-orchestrator.service",
            "loopback_base_url": base,
            "health_path": "/healthz",
            "ready_path": "/readyz",
        },
        "dashboard": {
            "listen_host": dashboard_host,
            "listen_port": dashboard_port,
            "trusted_readonly_cidrs": list(readonly_cidrs),
            "document_root": str(document),
            "active_config": str(active),
            "desired_service": str(service),
            "rollback_service": str(rollback),
            "nginx_executable": str(nginx),
            "pid_file": str(pid_file),
            "mode": "read-only" if dashboard_enabled else "disabled",
            "terminal": {
                "desired_enabled": terminal,
                "trust_model": trust_model,
                "allowed_client_ips": list(client_ips),
                "allowed_origin": origin or "",
                "path": "/mux",
                "upstream": upstream or base,
                "upstream_origin": upstream_origin or "",
                "origin_mode": origin_mode or "preserve",
                "require_authentication_if": [
                    "multi-user",
                    "dynamic-address",
                    "public-network",
                ],
            },
        },
        "paths": {
            "private_authority": str(private_authority),
            "desired_nginx_artifact": str(nginx_artifact),
            "desired_service_artifact": str(service_artifact),
            "state_root": str(state_root),
        },
        "storage": {"boundaries": boundary_values},
    }
    canonical = _canonical_v2(profile)
    _validate_terminal(_section(_section(canonical, "dashboard"), "terminal"))
    target.write_text(_toml(canonical), encoding="utf-8")
    target.chmod(0o600)
    return canonical


def plan_profile(path: Path) -> dict[str, object]:
    """Describe the canonical candidate without writing it."""
    profile = _load_profile(path)
    version = cast(int, profile.get("schema_version", 1))
    candidate = _canonical_v2(profile)
    dashboard = _section(candidate, "dashboard")
    artifacts = ["AGENTS.md", "host.toml", "runbooks/ao.md", "MANIFEST.json"]
    if dashboard["mode"] == "read-only":
        artifacts.extend(["nginx/ao-terminal.conf", "service/ao-dashboard.service"])
    return {
        "mode": "plan",
        "schema_read": version,
        "schema_render": 2,
        "migration_required": version == 1,
        "candidate_required": True,
        "artifacts": artifacts,
    }


def _candidate_files(profile: Mapping[str, object]) -> dict[str, bytes]:
    canonical = _canonical_v2(profile)
    ao = _section(canonical, "ao")
    dashboard = _section(canonical, "dashboard")
    terminal = _section(_section(canonical, "dashboard"), "terminal")
    paths = _section(canonical, "paths")
    storage = _section(canonical, "storage")
    boundary_lines = "\n".join(
        f"- `{boundary['path']}`: `{boundary['kind']}`, "
        f"recursive search `{str(boundary['recursive_search']).lower()}`"
        for boundary in cast(list[dict[str, object]], storage["boundaries"])
    )
    files: dict[str, bytes] = {
        "AGENTS.md": (
            "# AO Host Authority\n\n"
            f"Profile authority: `{paths['private_authority']}`. Candidate nginx "
            f"and service destinations: `{paths['desired_nginx_artifact']}` and "
            f"`{paths['desired_service_artifact']}`. Rollback service source: "
            f"`{dashboard['rollback_service']}`.\n\n"
            "Classify evidence by sandbox, worker, daemon, and host owner. Only "
            "explicit host context may establish readiness. Sandbox-only stale "
            "status or read-only doctor evidence cannot negate a separate "
            "authoritative host check. Require active host systemd state, AO "
            "ready/running status, matching MainPID plus executable/work/startup "
            "identity across status, healthz, and readyz, valid healthz and readyz "
            "state/service payloads, and no host core doctor failure. "
            "External integration failures degrade delivery. Process "
            "containment remains unverified until OS-owned evidence proves it.\n\n"
            "## Storage routing\n\n"
            f"{boundary_lines}\n\n"
            "Recursive search is off by default; a separate task-specific reason "
            "is required outside this profile to broaden discovery.\n\n"
            "This tree is review material and does not mutate active host state. "
            "Keep Dashboard APIs read-only and preserve the stable known-issue IDs.\n"
        ).encode(),
        "host.toml": _toml(canonical).encode(),
        "runbooks/ao.md": (
            "# AO Host Reconstruction Runbook\n\n"
            f"Canonical candidate profile: `host.toml`; private authority: "
            f"`{paths['private_authority']}`; AO data: "
            f"`{ao['data_dir']}`; Codex home: `{ao['codex_home']}`; state root: "
            f"`{paths['state_root']}`.\n\n"
            "Read live state from the user service manager, AO status and doctor, "
            f"`{ao['loopback_base_url']}{ao['health_path']}`, "
            f"`{ao['loopback_base_url']}{ao['ready_path']}`, and the configured "
            "Dashboard listener. Ready requires active host systemd state, AO "
            "ready/running status, matching MainPID and executable/work/start "
            "identity, valid healthz/readyz status and service fields, and no host "
            "core doctor failure. Sandbox-only stale status or read-only doctor "
            "evidence stays indeterminate and cannot negate a separate authoritative "
            "host check. Without a profile, the Dashboard probe is unknown/not "
            "configured and delivery is `not_applicable`. An unreadable doctor "
            "result is not clean evidence.\n\n"
            "Use `calibrate_ao_host.py inspect --context host --profile <profile>` "
            "for attested observation, `plan --profile <profile>` for migration "
            "readback, `render --profile <profile> --output <new-private-root>` "
            "for a deterministic candidate, and `verify --profile <profile> "
            "--candidate <root>` for read-only comparison. A second render must "
            "be byte-identical.\n\n"
            f"Review candidate destinations `{paths['desired_nginx_artifact']}` "
            f"and `{paths['desired_service_artifact']}` against active config "
            f"`{dashboard['active_config']}`. Rollback authority remains "
            f"`{dashboard['rollback_service']}`. These commands do not change "
            "the active proxy, service manager, or rollback material.\n\n"
            "## Storage routing\n\n"
            f"{boundary_lines}\n\n"
            "Treat recursive search as disabled by default. Any broader search "
            "requires separate task-specific authority outside this profile.\n"
        ).encode(),
    }
    if dashboard["mode"] == "read-only":
        terminal_maps = ""
        mux_location = ""
        if terminal["desired_enabled"]:
            clients = cast(list[str], terminal["allowed_client_ips"])
            origin = cast(str, terminal["allowed_origin"])
            upstream = cast(str, terminal["upstream"])
            upstream_origin = cast(str, terminal["upstream_origin"])
            origin_header = (
                "$http_origin"
                if terminal["origin_mode"] == "preserve"
                else f'"{upstream_origin}"'
            )
            allow_lines = "".join(f"      allow {client};\n" for client in clients)
            terminal_maps = (
                "  map $http_origin $ao_origin_allowed {\n"
                "    default 0;\n"
                f'    "{origin}" 1;\n'
                "  }\n"
                "  map $http_upgrade $ao_upgrade_allowed {\n"
                "    default 0;\n"
                "    websocket 1;\n"
                "  }\n"
            )
            mux_location = (
                "    location = /mux {\n"
                f"{allow_lines}"
                "      deny all;\n"
                "      if ($request_method != GET) { return 405; }\n"
                "      if ($ao_origin_allowed = 0) { return 403; }\n"
                "      if ($ao_upgrade_allowed = 0) { return 400; }\n"
                "      proxy_http_version 1.1;\n"
                "      proxy_set_header Upgrade $http_upgrade;\n"
                '      proxy_set_header Connection "upgrade";\n'
                "      proxy_set_header Host $proxy_host;\n"
                f"      proxy_set_header Origin {origin_header};\n"
                "      proxy_buffering off;\n"
                "      proxy_cache off;\n"
                "      proxy_connect_timeout 2s;\n"
                "      proxy_read_timeout 1h;\n"
                "      proxy_send_timeout 1h;\n"
                f"      proxy_pass {upstream};\n"
                "    }\n"
            )
        readonly_allow_lines = "".join(
            f"      allow {cidr};\n"
            for cidr in cast(list[str], dashboard["trusted_readonly_cidrs"])
        )
        files["nginx/ao-terminal.conf"] = (
            "worker_processes 1;\n"
            "error_log stderr;\n"
            f"pid {dashboard['pid_file']};\n"
            "events { worker_connections 64; }\n"
            "http {\n"
            "  access_log off;\n"
            f"  client_body_temp_path {paths['state_root']}/nginx-client-body;\n"
            f"  proxy_temp_path {paths['state_root']}/nginx-proxy;\n"
            f"  fastcgi_temp_path {paths['state_root']}/nginx-fastcgi;\n"
            f"  uwsgi_temp_path {paths['state_root']}/nginx-uwsgi;\n"
            f"  scgi_temp_path {paths['state_root']}/nginx-scgi;\n"
            f"{terminal_maps}"
            "  server {\n"
            f"    listen {_dashboard_url(cast(str, dashboard['listen_host']), cast(int, dashboard['listen_port'])).removeprefix('http://')};\n"
            f"    root {dashboard['document_root']};\n"
            '    add_header X-Content-Type-Options "nosniff" always;\n'
            '    add_header X-Frame-Options "DENY" always;\n'
            '    add_header Referrer-Policy "no-referrer" always;\n'
            "    location = /dashboard-health {\n"
            "      if ($request_method != GET) { return 405; }\n"
            f"{readonly_allow_lines}"
            "      deny all;\n"
            f"      proxy_pass {ao['loopback_base_url']}{ao['health_path']};\n"
            "    }\n"
            "    location /api/ {\n"
            "      if ($request_method != GET) { return 405; }\n"
            f"{readonly_allow_lines}"
            "      deny all;\n"
            f"      proxy_pass {ao['loopback_base_url']};\n"
            "    }\n"
            "    location / {\n"
            "      if ($request_method != GET) { return 405; }\n"
            f"{readonly_allow_lines}"
            "      deny all;\n"
            "      try_files $uri $uri/ =404;\n"
            "    }\n"
            f"{mux_location}"
            "  }\n"
            "}\n"
        ).encode()
        files["service/ao-dashboard.service"] = (
            "[Unit]\n"
            "Description=AO read-only dashboard candidate\n"
            "After=network.target\n\n"
            "[Service]\n"
            "Type=forking\n"
            f"PIDFile={dashboard['pid_file']}\n"
            f"ExecStart={dashboard['nginx_executable']} "
            f"-p {paths['state_root']} -c {dashboard['active_config']}\n"
            f"ExecReload={dashboard['nginx_executable']} "
            f"-p {paths['state_root']} -c {dashboard['active_config']} -s reload\n"
            f"ExecStop={dashboard['nginx_executable']} "
            f"-p {paths['state_root']} -c {dashboard['active_config']} -s quit\n"
            "UMask=0077\n"
            "NoNewPrivileges=true\n"
            "PrivateTmp=true\n"
            "ProtectSystem=strict\n"
            f"ReadWritePaths={paths['state_root']}\n"
            "Restart=on-failure\n\n"
            "[Install]\n"
            "WantedBy=default.target\n"
        ).encode()
    expected_modes = {name: "0600" for name in files}
    expected_modes["MANIFEST.json"] = "0600"
    expected_modes.update(
        {
            str(Path(name).parent): "0700"
            for name in files
            if Path(name).parent != Path(".")
        }
    )
    expected_modes["."] = "0700"
    manifest = {
        "manifest_schema": 1,
        "generator": "calibrate_ao_host.py",
        "profile_schema": 2,
        "profile_sha256": hashlib.sha256(files["host.toml"]).hexdigest(),
        "expected_modes": expected_modes,
        "files": {
            name: hashlib.sha256(content).hexdigest()
            for name, content in sorted(files.items())
        },
    }
    files["MANIFEST.json"] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    return files


def _tree_bytes(root: Path) -> dict[str, bytes]:
    if any(item.is_symlink() for item in root.rglob("*")):
        raise CalibrationError("candidate tree must not contain symlinks")
    return {
        str(item.relative_to(root)): item.read_bytes()
        for item in root.rglob("*")
        if item.is_file()
    }


def _validate_tree_shape(root: Path, files: Mapping[str, bytes]) -> None:
    expected_files = set(files)
    expected_directories: set[str] = set()
    for name in expected_files:
        parent = Path(name).parent
        while parent != Path("."):
            expected_directories.add(str(parent))
            parent = parent.parent
    actual = {str(item.relative_to(root)): item for item in root.rglob("*")}
    if set(actual) != expected_files | expected_directories:
        raise CalibrationError("candidate tree shape is not canonical")
    for name, item in actual.items():
        if name in expected_files and not item.is_file():
            raise CalibrationError(f"{item} must be a regular file")


def _validate_tree_modes(root: Path) -> None:
    if stat.S_IMODE(root.stat().st_mode) != 0o700:
        raise CalibrationError("candidate root mode must be 0700")
    for item in root.rglob("*"):
        expected = 0o700 if item.is_dir() else 0o600
        if stat.S_IMODE(item.stat().st_mode) != expected:
            raise CalibrationError(f"{item} mode must be {expected:04o}")


def _validate_publish_parent(parent: Path) -> None:
    if not parent.is_dir():
        raise CalibrationError("render output parent must exist")
    mode = stat.S_IMODE(parent.stat().st_mode)
    if mode & 0o022 and not mode & stat.S_ISVTX:
        raise CalibrationError(
            "render output parent must not be group/other-writable without sticky bit"
        )


def render_profile(path: Path, output: Path) -> dict[str, object]:
    """Publish a deterministic private candidate through sibling staging."""
    profile = _load_profile(path)
    files = _candidate_files(profile)
    target = _safe_path(output, may_create=True)
    _validate_publish_parent(target.parent)
    if target.exists():
        if not target.is_dir() or _tree_bytes(target) != files:
            raise CalibrationError("existing output has nonempty drift")
        _validate_tree_shape(target, files)
        _validate_tree_modes(target)
        return {"mode": "render", "output": str(target), "unchanged": True}
    staging = target.with_name(f".{target.name}.staging")
    if staging.exists() or staging.is_symlink():
        raise CalibrationError("sibling staging path must be absent")
    staging.mkdir(mode=0o700, parents=False)
    try:
        for name, content in files.items():
            destination = staging / name
            destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            destination.write_bytes(content)
            destination.chmod(0o600)
        os.replace(staging, target)
    except BaseException:
        if staging.exists():
            for item in sorted(staging.rglob("*"), reverse=True):
                item.unlink() if item.is_file() else item.rmdir()
            staging.rmdir()
        raise
    return {"mode": "render", "output": str(target), "unchanged": False}


def verify_profile(path: Path, *, candidate: Path | None = None) -> dict[str, object]:
    """Verify a v1/v2 profile and optional canonical v2 candidate read-only."""
    profile = _load_profile(path)
    version = cast(int, profile.get("schema_version", 1))
    if candidate is not None:
        root = _safe_path(candidate, may_create=False, directory=True)
        files = _candidate_files(profile)
        if _tree_bytes(root) != files:
            raise CalibrationError("candidate does not match canonical rendering")
        _validate_tree_shape(root, files)
        _validate_tree_modes(root)
    return {
        "mode": "verify",
        "valid": True,
        "schema_read": version,
        "migration_required": version == 1,
        "candidate": candidate is not None,
    }


def _invoke_subprocess_cli(
    argv: Sequence[str], env: Mapping[str, str]
) -> tuple[int, dict[str, object]]:
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), *argv],
        check=False,
        capture_output=True,
        text=True,
        env=dict(env),
        timeout=PROBE_TIMEOUT_SECONDS,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise CalibrationError("canary CLI did not emit JSON") from exc
    if not isinstance(payload, dict):
        raise CalibrationError("canary CLI JSON must be an object")
    return result.returncode, cast(dict[str, object], payload)


def _require_canary_stage(
    stage: str,
    result: tuple[int, dict[str, object]],
    *,
    expected_exit: int = EXIT_OK,
) -> dict[str, object]:
    code, payload = result
    if code != expected_exit:
        raise CalibrationError(
            f"canary {stage} failed with exit {code}: "
            + json.dumps(payload, sort_keys=True)
        )
    if payload.get("command") != stage:
        raise CalibrationError(f"canary {stage} returned an invalid command payload")
    if not isinstance(payload.get("capabilities"), dict):
        raise CalibrationError(f"canary {stage} returned invalid capabilities")
    return payload


def _write_canary_probe_tools(root: Path) -> Path:
    fake_bin = root / "fake-bin"
    fake_bin.mkdir(mode=0o700)
    script = (
        "#!"
        + sys.executable
        + "\n"
        + """import json
import pathlib
import sys

name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
if name == "ao":
    if args == ["version"]:
        print("ao version 1.2.3")
    elif args[:1] == ["status"]:
        status = {"state":"stale","pid":42,"port":3001}
        status.update({"health":"ok","ready":"ready"})
        print(json.dumps(status))
    else:
        check = {"name":"data-dir-write","level":"FAIL"}
        check["detail"] = "read-only sandbox"
        print(json.dumps({"ok":False,"checks":[check]}))
elif name == "systemctl":
    print("42" if "show" in args else "active")
elif name == "ldd":
    print("ldd (GNU libc) 2.39")
elif name == "tmux":
    print("tmux 3.5")
elif name == "stat":
    print("cgroup2fs")
elif name == "curl":
    url = args[-1]
    identity = {"service":"agent-orchestrator-daemon","pid":42}
    identity["executablePath"] = "/opt/example/ao"
    identity["workingDirectory"] = "/opt/example/work"
    identity["startupWorkingDirectory"] = "/opt/example/start"
    if url.endswith("/healthz"):
        print(json.dumps({"status":"ok",**identity}))
    elif url.endswith("/readyz"):
        print(json.dumps({"status":"ready",**identity}))
    elif url.endswith("/mux"):
        print("HTTP/1.1 101 Switching Protocols")
    else:
        print("ok")
"""
    )
    for name in ("ao", "systemctl", "ldd", "tmux", "stat", "curl"):
        tool = fake_bin / name
        tool.write_text(script, encoding="utf-8")
        tool.chmod(0o700)
    return fake_bin


def reconstruction_canary(root: Path, runner: Runner = _run) -> dict[str, object]:
    """Run the real JSON CLI boundary under isolated XDG roots and fake probes."""
    discovered_nginx = shutil.which("nginx")
    nginx_executable = (
        str(Path(discovered_nginx).resolve())
        if discovered_nginx is not None
        else "/usr/sbin/nginx"
    )
    if root.exists():
        if root.is_symlink() or not root.is_dir():
            raise CalibrationError("canary root must be a real directory")
    else:
        root.mkdir(mode=0o700)
    if stat.S_IMODE(root.stat().st_mode) != 0o700:
        raise CalibrationError("canary root mode must be 0700")
    home = root / "home"
    config_home = root / "config"
    state_home = root / "state"
    codex_home = root / "codex"
    for directory in (home, config_home, state_home, codex_home):
        directory.mkdir(mode=0o700, parents=True)
    config = codex_home / "config.toml"
    config.write_text("[features]\napps = false\nplugins = false\n", encoding="utf-8")
    config.chmod(0o600)
    auth = codex_home / "auth.json"
    auth.write_text("{}\n", encoding="utf-8")
    auth.chmod(0o600)
    fake_bin = _write_canary_probe_tools(root)
    canary_env = os.environ.copy()
    canary_env.update(
        {
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(config_home),
            "XDG_STATE_HOME": str(state_home),
            "CODEX_HOME": str(codex_home),
            "PATH": str(fake_bin),
        }
    )
    initialized = config_home / "calibration" / "initialized.toml"
    state_root = state_home / "calibration"
    dashboard_root = state_root / "dashboard"
    init_code = EXIT_OK
    _require_canary_stage(
        "init",
        _invoke_subprocess_cli(
            (
                "init",
                "--profile",
                str(initialized),
                "--trust-model",
                "trusted-single-user",
                "--codex-home",
                str(codex_home),
                "--data-dir",
                str(state_home / "ao"),
                "--private-authority",
                str(config_home / "calibration/AGENTS.md"),
                "--state-root",
                str(state_root),
                "--enable-dashboard",
                "--dashboard-listen-host",
                "127.0.0.1",
                "--dashboard-listen-port",
                "18443",
                "--readonly-cidr",
                "203.0.113.0/24",
                "--document-root",
                str(dashboard_root),
                "--nginx-executable",
                nginx_executable,
                "--nginx-pid-file",
                str(state_root / "nginx.pid"),
                "--active-config",
                str(state_root / "active.conf"),
                "--desired-service",
                "ao-dashboard.service",
                "--rollback-service",
                "ao-dashboard-rollback.service",
                "--desired-nginx-artifact",
                str(state_root / "nginx.conf"),
                "--desired-service-artifact",
                str(state_root / "nginx.service"),
                "--terminal",
                "--client-ip",
                "203.0.113.7",
                "--origin",
                "https://console.example.test",
                "--upstream",
                "http://127.0.0.1:3001/mux",
                "--upstream-origin",
                "http://127.0.0.1:3001",
                "--origin-mode",
                "edge-validated-rewrite",
                "--storage-boundary",
                json.dumps(
                    {
                        "path": str(state_home / "aggregation"),
                        "kind": "aggregation-root",
                        "recursive_search": False,
                    }
                ),
            ),
            canary_env,
        ),
    )
    profile = initialized
    inspect_code = EXIT_PROBE
    _require_canary_stage(
        "inspect",
        _invoke_subprocess_cli(
            ("inspect", "--profile", str(profile), "--context", "sandbox"),
            canary_env,
        ),
        expected_exit=EXIT_PROBE,
    )
    plan_code = EXIT_OK
    _require_canary_stage(
        "plan",
        _invoke_subprocess_cli(("plan", "--profile", str(profile)), canary_env),
    )
    candidate = root / "candidate"
    first_code = EXIT_OK
    first = _require_canary_stage(
        "render",
        _invoke_subprocess_cli(
            ("render", "--profile", str(profile), "--output", str(candidate)),
            canary_env,
        ),
    )
    second_code = EXIT_OK
    second = _require_canary_stage(
        "render",
        _invoke_subprocess_cli(
            ("render", "--profile", str(profile), "--output", str(candidate)),
            canary_env,
        ),
    )
    verify_code = EXIT_OK
    _require_canary_stage(
        "verify",
        _invoke_subprocess_cli(
            (
                "verify",
                "--profile",
                str(profile),
                "--candidate",
                str(candidate),
            ),
            canary_env,
        ),
    )
    dashboard = _section(_canonical_v2(_load_profile(profile)), "dashboard")
    nginx = cast(str, dashboard["nginx_executable"])
    nginx_checked = False
    if runner((nginx, "-v")).returncode == 0:
        state_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        dashboard_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        prefix = root / "nginx-prefix"
        prefix.mkdir(mode=0o700)
        (prefix / "logs").mkdir(mode=0o700)
        nginx_result = runner(
            (
                nginx,
                "-t",
                "-p",
                str(prefix) + "/",
                "-c",
                str(candidate / "nginx/ao-terminal.conf"),
            )
        )
        if nginx_result.returncode != 0:
            raise CalibrationError(
                "nginx candidate validation failed: "
                + (nginx_result.stderr.strip() or nginx_result.stdout.strip())
            )
        nginx_checked = True
    return {
        "init_exit": init_code,
        "inspect_exit": inspect_code,
        "plan_exit": plan_code,
        "first_exit": first_code,
        "second_exit": second_code,
        "verify_exit": verify_code,
        "first_unchanged": cast(dict[str, object], first["capabilities"])["unchanged"],
        "second_unchanged": cast(dict[str, object], second["capabilities"])[
            "unchanged"
        ],
        "nginx_checked": nginx_checked,
    }


def _storage_boundary_argument(value: str) -> dict[str, object]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError("storage boundary must be JSON") from exc
    try:
        return _validate_storage_boundaries([parsed])[0]
    except CalibrationError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description="Calibrate a private AO host profile.")
    commands = parser.add_subparsers(dest="command", required=True)
    inspect_parser = commands.add_parser("inspect")
    inspect_parser.add_argument("--profile", type=Path)
    inspect_parser.add_argument(
        "--context", choices=("auto", "host", "sandbox"), default="auto"
    )
    init_parser = commands.add_parser("init")
    init_parser.add_argument("--profile", type=Path, required=True)
    init_parser.add_argument(
        "--trust-model", choices=("trusted-single-user", "untrusted"), required=True
    )
    init_parser.add_argument("--codex-home", type=Path, required=True)
    init_parser.add_argument("--data-dir", type=Path, required=True)
    init_parser.add_argument("--private-authority", type=Path, required=True)
    init_parser.add_argument("--state-root", type=Path, required=True)
    init_parser.add_argument(
        "--storage-boundary",
        action="append",
        type=_storage_boundary_argument,
        default=[],
    )
    init_parser.add_argument("--enable-dashboard", action="store_true")
    init_parser.add_argument("--dashboard-listen-host")
    init_parser.add_argument("--dashboard-listen-port", type=int)
    init_parser.add_argument("--readonly-cidr", action="append", default=[])
    init_parser.add_argument("--document-root", type=Path)
    init_parser.add_argument("--nginx-executable", type=Path)
    init_parser.add_argument("--nginx-pid-file", type=Path)
    init_parser.add_argument("--active-config", type=Path)
    init_parser.add_argument("--desired-service")
    init_parser.add_argument("--rollback-service")
    init_parser.add_argument("--desired-nginx-artifact", type=Path)
    init_parser.add_argument("--desired-service-artifact", type=Path)
    init_parser.add_argument("--terminal", action="store_true")
    init_parser.add_argument("--client-ip", action="append", default=[])
    init_parser.add_argument("--origin")
    init_parser.add_argument("--upstream")
    init_parser.add_argument("--upstream-origin")
    init_parser.add_argument(
        "--origin-mode",
        choices=("preserve", "edge-validated-rewrite"),
    )
    for name in ("plan", "render", "verify"):
        child = commands.add_parser(name)
        child.add_argument("--profile", type=Path, required=True)
        if name == "render":
            child.add_argument("--output", type=Path, required=True)
        if name == "verify":
            child.add_argument("--candidate", type=Path)
    return parser


def main(argv: Sequence[str] | None = None, *, runner: Runner = _run) -> int:
    """Run the fixed-schema JSON CLI with stable exit categories."""
    args = _parser().parse_args(argv)
    try:
        if args.command == "inspect":
            result = inspect_host(runner, profile=args.profile, context=args.context)
            code = (
                EXIT_OK
                if cast(dict[str, object], result["states"])["daemon"] == "ready"
                else EXIT_PROBE
            )
        elif args.command == "init":
            result = init_profile(
                args.profile,
                trust_model=args.trust_model,
                codex_home=args.codex_home,
                data_dir=args.data_dir,
                private_authority=args.private_authority,
                state_root=args.state_root,
                storage_boundaries=args.storage_boundary,
                dashboard_enabled=args.enable_dashboard,
                dashboard_listen_host=args.dashboard_listen_host,
                dashboard_listen_port=args.dashboard_listen_port,
                readonly_cidrs=args.readonly_cidr,
                document_root=args.document_root,
                nginx_executable=args.nginx_executable,
                nginx_pid_file=args.nginx_pid_file,
                active_config=args.active_config,
                desired_service=args.desired_service,
                rollback_service=args.rollback_service,
                desired_nginx_artifact=args.desired_nginx_artifact,
                desired_service_artifact=args.desired_service_artifact,
                terminal=args.terminal,
                client_ips=args.client_ip,
                origin=args.origin,
                upstream=args.upstream,
                upstream_origin=args.upstream_origin,
                origin_mode=args.origin_mode,
            )
            code = EXIT_OK
        elif args.command == "plan":
            result, code = plan_profile(args.profile), EXIT_OK
        elif args.command == "render":
            result, code = render_profile(args.profile, args.output), EXIT_OK
        else:
            result, code = (
                verify_profile(args.profile, candidate=args.candidate),
                EXIT_OK,
            )
    except (CalibrationError, OSError, ValueError) as exc:
        error_result = {"context": args.context} if args.command == "inspect" else None
        _emit(
            args.command,
            False,
            result=error_result,
            error={"kind": "invalid", "message": str(exc)},
        )
        return EXIT_INVALID
    _emit(args.command, code == EXIT_OK, result=result)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
