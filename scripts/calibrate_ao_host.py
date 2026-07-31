#!/usr/bin/env python3
"""Inspect and render private AO host authority without applying host changes."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import re
import stat
import subprocess
import tomllib
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
    "dashboard": {"mode"},
    "terminal": {"origin_mode"},
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
    )


def _probe(runner: Runner, owner: str, name: str, command: Sequence[str]) -> Evidence:
    result = runner(command)
    detail = (result.stdout.strip() or result.stderr.strip() or "no output")[:1000]
    return Evidence(name, owner, "pass" if result.returncode == 0 else "fail", detail)


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


def evaluate_daemon_state(probes: Mapping[str, Evidence], *, context: str) -> str:
    """Classify daemon state from authoritative probe values only."""
    service = probes["systemd-active"]
    health = probes["healthz"]
    ready = probes["readyz"]
    if (
        service.status == "pass"
        and service.detail == "active"
        and health.status == "pass"
        and ready.status == "pass"
    ):
        return "ready"
    if probes["ao-version"].status == "fail" and context == "host":
        return "not_installed"
    if (
        context == "host"
        and service.status == "pass"
        and service.detail != "active"
        and health.status == "fail"
        and ready.status == "fail"
    ):
        return "unavailable"
    return "indeterminate"


def evaluate_delivery_state(
    probes: Mapping[str, Evidence],
    *,
    daemon_state: str,
    terminal_enabled: bool | None,
) -> str:
    """Classify Dashboard delivery independently from daemon readiness."""
    if terminal_enabled is False:
        return "not_applicable"
    if terminal_enabled is None or daemon_state != "ready":
        return "indeterminate"
    return "ready" if probes["mux"].status == "pass" else "degraded"


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
) -> list[str]:
    """Return stable issue IDs from already collected, mutation-free evidence."""
    issues: list[str] = []
    if status.get("state") not in {"ready", "running"} or doctor.get("ok") is not True:
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
    if capabilities.get("process_containment") != "systemd-scope-verified":
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
        Daemon readiness depends on authoritative service and endpoint probes,
        not sandbox-visible AO status or a data-dir write check.
    """
    if context not in {"auto", "host", "sandbox"}:
        raise CalibrationError("context must be auto, host, or sandbox")
    base = _profile_base_url(profile)
    health = "/healthz"
    ready = "/readyz"
    service = "agent-orchestrator.service"
    if profile is not None and profile.exists():
        parsed = _load_profile(profile)
        ao = cast(dict[str, object], parsed["ao"])
        health = cast(str, ao["health_path"])
        ready = cast(str, ao["ready_path"])
        service = cast(str, ao["daemon_service"])
    evidence = [
        _probe(runner, "sandbox", "ao-version", ("ao", "version")),
        _probe(runner, "sandbox", "glibc", ("ldd", "--version")),
        _probe(runner, "worker", "tmux", ("tmux", "-V")),
        _probe(runner, "worker", "cgroup", ("stat", "-fc", "%T", "/sys/fs/cgroup")),
        _probe(
            runner,
            "host",
            "systemd-active",
            ("systemctl", "--user", "is-active", service),
        ),
        _probe(runner, "sandbox", "status", ("ao", "status", "--json")),
        _probe(runner, "host", "doctor", ("ao", "doctor", "--json")),
        _probe(runner, "daemon", "healthz", ("curl", "-fsS", base + health)),
        _probe(runner, "daemon", "readyz", ("curl", "-fsS", base + ready)),
        _probe(runner, "daemon", "dashboard", ("curl", "-fsSI", base + "/")),
        _probe(
            runner,
            "daemon",
            "mux",
            ("curl", "-fsS", "-o", "/dev/null", "-w", "%{http_code}", base + "/mux"),
        ),
    ]
    by_name = {item.id: item for item in evidence}
    daemon_state = evaluate_daemon_state(by_name, context=context)
    status = _json_object(by_name["status"].detail)
    doctor = _json_object(by_name["doctor"].detail)
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
    process_containment: object = None
    codex_home_compatible: bool | None = None
    if profile is not None and profile.exists():
        parsed = _load_profile(profile)
        terminal = _section(_section(parsed, "dashboard"), "terminal")
        process_containment = _section(parsed, "ao").get("process_containment")
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
        "process_containment": process_containment,
        "ao_status": status,
        "ao_doctor": doctor,
        "status_required_subset_valid": _required_subset(status, {"state": str}),
        "doctor_required_subset_valid": _required_subset(
            doctor, {"ok": bool, "checks": list}
        ),
    }
    delivery_state = evaluate_delivery_state(
        by_name,
        daemon_state=daemon_state,
        terminal_enabled=(
            cast(bool, terminal["desired_enabled"]) if terminal is not None else None
        ),
    )
    issues = evaluate_known_issues(
        probes=by_name,
        status=status,
        doctor=doctor,
        capabilities=capabilities,
        terminal=terminal,
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
        "probes": [asdict(item) for item in evidence],
        "known_issues": issues,
        "next_actions": [f"investigate {issue}" for issue in issues],
    }


def _safe_path(path: Path, *, may_create: bool, directory: bool | None = None) -> Path:
    expanded = path.expanduser()
    if not expanded.is_absolute():
        raise CalibrationError(f"{path} must be absolute")
    if expanded.is_symlink() or (
        expanded.parent.exists() and expanded.parent.is_symlink()
    ):
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


def _load_profile(path: Path) -> dict[str, object]:
    safe = _safe_path(path, may_create=False, directory=False)
    try:
        profile = tomllib.loads(safe.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise CalibrationError(f"{safe} must contain valid TOML: {exc}") from exc
    version = profile.get("schema_version", 1)
    if version not in {1, 2}:
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
    if not isinstance(ao["codex_home"], str):
        raise CalibrationError("ao.codex_home must be a string")
    if not Path(ao["codex_home"]).is_absolute():
        raise CalibrationError("ao.codex_home must be absolute")
    if version == 1:
        _validate_terminal_v1(terminal)
    else:
        _validate_terminal(terminal)
    return cast(dict[str, object], profile)


def _validate_terminal_v1(terminal: Mapping[str, object]) -> None:
    """Validate the deployed legacy terminal contract without v2 reinterpretation."""
    enabled = terminal.get("desired_enabled")
    if not isinstance(enabled, bool):
        raise CalibrationError("dashboard.terminal.desired_enabled must be boolean")
    if not enabled:
        return
    clients = terminal.get("allowed_client_ips")
    client_values = cast(list[object], clients) if isinstance(clients, list) else []
    if not client_values or not all(isinstance(value, str) for value in client_values):
        raise CalibrationError("legacy terminal requires exact client IPs")
    for value in client_values:
        ipaddress.ip_address(cast(str, value))
    origin = terminal.get("allowed_origin")
    if not isinstance(origin, str) or not re.fullmatch(r"https?://[^/*]+", origin):
        raise CalibrationError("legacy terminal requires an exact Origin")
    if terminal.get("path") != "/mux":
        raise CalibrationError("legacy terminal path must be exactly /mux")
    upstream = terminal.get("upstream")
    if not isinstance(upstream, str) or not re.fullmatch(
        r"http://(?:127\.0\.0\.1|localhost):\d+/mux", upstream
    ):
        raise CalibrationError("legacy terminal upstream must be loopback /mux")
    if terminal.get("trust_model") != "single-user-trusted-lan":
        raise CalibrationError("legacy terminal requires single-user-trusted-lan")


def _validate_terminal(terminal: Mapping[str, object]) -> None:
    enabled = terminal.get("desired_enabled")
    if not isinstance(enabled, bool):
        raise CalibrationError("dashboard.terminal.desired_enabled must be boolean")
    if enabled:
        clients = terminal.get("allowed_client_ips")
        client_values = cast(list[object], clients) if isinstance(clients, list) else []
        if len(client_values) != 1 or not isinstance(client_values[0], str):
            raise CalibrationError("terminal requires exactly one client IP")
        ipaddress.ip_address(client_values[0])
        origin = terminal.get("allowed_origin")
        if not isinstance(origin, str) or not re.fullmatch(r"https?://[^/*]+", origin):
            raise CalibrationError("terminal requires an exact Origin")
        if terminal.get("path") != "/mux":
            raise CalibrationError("terminal path must be exactly /mux")
        upstream = terminal.get("upstream")
        if not isinstance(upstream, str) or not re.fullmatch(
            r"http://(?:127\.0\.0\.1|localhost):\d+", upstream
        ):
            raise CalibrationError("terminal upstream must be loopback")
        if terminal.get("trust_model") != "trusted-single-user":
            raise CalibrationError("terminal requires trusted-single-user")
        if terminal.get("origin_mode", "preserve") != "preserve":
            raise CalibrationError("Origin rewrite requires paired probe evidence")


def _quote(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        return "[" + ", ".join(_quote(item) for item in cast(list[object], value)) + "]"
    raise CalibrationError(f"unsupported TOML value: {value!r}")


def _canonical_v2(profile: Mapping[str, object]) -> dict[str, object]:
    ao = dict(_section(profile, "ao"))
    dashboard = dict(_section(profile, "dashboard"))
    terminal = dict(_section(dashboard, "terminal"))
    paths = dict(_section(profile, "paths"))
    ao.setdefault("runtime_owner", "systemd-user")
    ao.setdefault("process_containment", "assigned-workspace")
    dashboard.setdefault("mode", "read-only")
    terminal.setdefault("origin_mode", "preserve")
    dashboard["terminal"] = terminal
    return {
        "schema_version": 2,
        "ao": ao,
        "dashboard": dashboard,
        "paths": paths,
        "storage": {"boundaries": [paths["state_root"], ao["data_dir"]]},
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
    terminal: bool = False,
    client_ip: str | None = None,
    origin: str | None = None,
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
    base = DEFAULT_BASE_URL
    profile: dict[str, object] = {
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
            "listen_host": "127.0.0.1",
            "listen_port": 3001,
            "trusted_readonly_cidrs": [],
            "document_root": str(state_root / "dashboard"),
            "active_config": str(state_root / "active.conf"),
            "desired_service": str(state_root / "dashboard.service"),
            "rollback_service": str(state_root / "dashboard.rollback.service"),
            "terminal": {
                "desired_enabled": terminal,
                "trust_model": trust_model,
                "allowed_client_ips": [client_ip] if client_ip else [],
                "allowed_origin": origin or "",
                "path": "/mux",
                "upstream": base,
                "upstream_origin": origin or "",
                "require_authentication_if": [
                    "multi-user",
                    "dynamic-address",
                    "public-network",
                ],
            },
        },
        "paths": {
            "private_authority": str(private_authority),
            "desired_nginx_artifact": str(state_root / "ao-terminal.conf"),
            "desired_service_artifact": str(state_root / "ao-dashboard.env"),
            "state_root": str(state_root),
        },
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
    terminal = _section(_section(candidate, "dashboard"), "terminal")
    artifacts = ["AGENTS.md", "host.toml", "runbooks/ao.md", "MANIFEST.json"]
    if terminal["desired_enabled"]:
        artifacts.extend(["nginx/ao-terminal.conf", "service/ao-dashboard.env"])
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
    terminal = _section(_section(canonical, "dashboard"), "terminal")
    files: dict[str, bytes] = {
        "AGENTS.md": b"# AO Host Authority\n\nPrivate candidate; review before use.\n",
        "host.toml": _toml(canonical).encode(),
        "runbooks/ao.md": (
            b"# AO Host Runbook\n\nUse inspect and verify for read-only evidence.\n"
        ),
    }
    if terminal["desired_enabled"]:
        client = cast(list[str], terminal["allowed_client_ips"])[0]
        origin = cast(str, terminal["allowed_origin"])
        upstream = cast(str, terminal["upstream"])
        files["nginx/ao-terminal.conf"] = (
            "location = /mux {\n"
            f"  allow {client};\n"
            "  deny all;\n"
            "  limit_except GET { deny all; }\n"
            f'  if ($http_origin != "{origin}") {{ return 403; }}\n'
            "  proxy_set_header Upgrade $http_upgrade;\n"
            '  proxy_set_header Connection "upgrade";\n'
            f"  proxy_pass {upstream};\n"
            "}\n"
        ).encode()
        files["service/ao-dashboard.env"] = (
            b"AO_DASHBOARD_API_MODE=read-only\nAO_DASHBOARD_MUX_PATH=/mux\n"
        )
    manifest = {
        "schema_version": 1,
        "profile_sha256": hashlib.sha256(files["host.toml"]).hexdigest(),
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


def render_profile(path: Path, output: Path) -> dict[str, object]:
    """Publish a deterministic private candidate through sibling staging."""
    profile = _load_profile(path)
    files = _candidate_files(profile)
    target = _safe_path(output, may_create=True)
    if target.exists():
        if not target.is_dir() or _tree_bytes(target) != files:
            raise CalibrationError("existing output has nonempty drift")
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
        if stat.S_IMODE(root.stat().st_mode) != 0o700:
            raise CalibrationError("candidate root mode must be 0700")
        if _tree_bytes(root) != _candidate_files(profile):
            raise CalibrationError("candidate does not match canonical rendering")
        for item in root.rglob("*"):
            expected = 0o700 if item.is_dir() else 0o600
            if stat.S_IMODE(item.stat().st_mode) != expected:
                raise CalibrationError(f"{item} mode must be {expected:04o}")
    return {
        "mode": "verify",
        "valid": True,
        "schema_read": version,
        "migration_required": version == 1,
        "candidate": candidate is not None,
    }


def reconstruction_canary(root: Path, runner: Runner) -> dict[str, object]:
    """Run init through second-render verification under isolated XDG roots."""
    home = root / "home"
    config_home = root / "config"
    state_home = root / "state"
    codex_home = root / "codex"
    for directory in (home, config_home, state_home, codex_home):
        directory.mkdir(mode=0o700, parents=True)
    config = codex_home / "config.toml"
    config.write_text("[features]\napps = false\nplugins = false\n", encoding="utf-8")
    config.chmod(0o600)
    previous = {
        name: os.environ.get(name)
        for name in ("HOME", "XDG_CONFIG_HOME", "XDG_STATE_HOME", "CODEX_HOME")
    }
    os.environ.update(
        {
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(config_home),
            "XDG_STATE_HOME": str(state_home),
            "CODEX_HOME": str(codex_home),
        }
    )
    try:
        profile = config_home / "calibration" / "host.toml"
        init_profile(
            profile,
            trust_model="untrusted",
            codex_home=codex_home,
            data_dir=state_home / "ao",
            private_authority=config_home / "calibration" / "AGENTS.md",
            state_root=state_home / "calibration",
        )
        inspection = inspect_host(runner, profile=profile, context="sandbox")
        plan = plan_profile(profile)
        candidate = root / "candidate"
        first = render_profile(profile, candidate)
        second = render_profile(profile, candidate)
        verified = verify_profile(profile, candidate=candidate)
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
    return {
        "inspect": cast(dict[str, object], inspection["states"])["daemon"],
        "plan": plan["mode"],
        "first_unchanged": first["unchanged"],
        "second_unchanged": second["unchanged"],
        "verified": verified["valid"],
    }


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
    init_parser.add_argument("--terminal", action="store_true")
    init_parser.add_argument("--client-ip")
    init_parser.add_argument("--origin")
    for name in ("plan", "render", "verify"):
        child = commands.add_parser(name)
        child.add_argument("--profile", type=Path, required=True)
        if name == "render":
            child.add_argument("--output", type=Path, required=True)
        if name == "verify":
            child.add_argument("--candidate", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the fixed-schema JSON CLI with stable exit categories."""
    args = _parser().parse_args(argv)
    try:
        if args.command == "inspect":
            result = inspect_host(profile=args.profile, context=args.context)
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
                terminal=args.terminal,
                client_ip=args.client_ip,
                origin=args.origin,
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
        _emit(args.command, False, error={"kind": "invalid", "message": str(exc)})
        return EXIT_INVALID
    _emit(args.command, code == EXIT_OK, result=result)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
