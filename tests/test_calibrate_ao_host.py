from __future__ import annotations

import argparse
import json
import os
import runpy
import shutil
import socketserver
import subprocess
import sys
import threading
import tomllib
from collections.abc import Sequence
from pathlib import Path
from typing import cast

import pytest

import scripts.calibrate_ao_host as host

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LEGACY_V1_FIXTURE = REPOSITORY_ROOT / "tests/fixtures/ao_host_v1_legacy.toml"

V1_PROFILE = """
[ao]
cli = "ao"
data_dir = "/opt/example/ao-data"
codex_home = "/opt/example/codex"
daemon_service = "agent-orchestrator.service"
loopback_base_url = "http://127.0.0.1:3001"
health_path = "/healthz"
ready_path = "/readyz"

[dashboard]
listen_host = "127.0.0.1"
listen_port = 8443
trusted_readonly_cidrs = ["203.0.113.0/24"]
document_root = "/opt/example/dashboard"
active_config = "/opt/example/active.conf"
desired_service = "ao-dashboard.service"
rollback_service = "ao-dashboard-rollback.service"

[dashboard.terminal]
desired_enabled = false
trust_model = "trusted-single-user"
allowed_client_ips = []
allowed_origin = "https://console.example.test"
path = "/mux"
upstream = "http://127.0.0.1:3001"
upstream_origin = "http://127.0.0.1:3001"
require_authentication_if = ["multi-user", "dynamic-address", "public-network"]

[paths]
private_authority = "/opt/example/private/AGENTS.md"
desired_nginx_artifact = "/opt/example/nginx.conf"
desired_service_artifact = "/opt/example/service.env"
state_root = "/opt/example/state"
""".lstrip()


def completed(
    command: Sequence[str], code: int = 0, out: str = "", err: str = ""
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, code, out, err)


def websocket_response() -> str:
    return (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Connection: Upgrade\r\n"
        "Upgrade: websocket\r\n"
        "Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=\r\n\r\n"
    )


class FakeRunner:
    def __init__(self, responses: list[subprocess.CompletedProcess[str]]) -> None:
        self.responses = responses
        self.commands: list[tuple[str, ...]] = []

    def __call__(self, command: Sequence[str]) -> subprocess.CompletedProcess[str]:
        self.commands.append(tuple(command))
        if not self.responses:
            raise AssertionError(f"unexpected command: {command}")
        return self.responses.pop(0)


@pytest.fixture
def codex_home(tmp_path: Path) -> Path:
    path = tmp_path / "codex"
    path.mkdir(mode=0o700)
    config = path / "config.toml"
    config.write_text(
        'metadata = "kept"\n[features]\napps = false\nplugins = false\nextra = true\n',
        encoding="utf-8",
    )
    config.chmod(0o600)
    auth = path / "auth.json"
    auth.write_text("{}\n", encoding="utf-8")
    auth.chmod(0o600)
    return path


@pytest.fixture
def profile(tmp_path: Path, codex_home: Path) -> Path:
    path = tmp_path / "config" / "calibration" / "host.toml"
    host.init_profile(
        path,
        trust_model="untrusted",
        codex_home=codex_home,
        data_dir=tmp_path / "data",
        private_authority=tmp_path / "private" / "AGENTS.md",
        state_root=tmp_path / "state",
    )
    return path


def inspect_responses(
    *,
    status: str = (
        '{"state":"ready","pid":42,"port":3001,"health":"ok","ready":"ready"}'
    ),
    doctor: str = '{"ok":true,"checks":[]}',
    cgroup: str = "cgroup2fs",
    ready: bool = True,
) -> list[subprocess.CompletedProcess[str]]:
    return [
        completed((), out="ao version 1.2.3"),
        completed((), out="ldd (GNU libc) 2.39"),
        completed((), out="tmux 3.5"),
        completed((), out=cgroup),
        completed((), out="active"),
        completed((), out="42"),
        completed((), out=status),
        completed((), out=doctor),
        completed(
            (),
            out=json.dumps(
                {
                    "status": "ok",
                    "service": "agent-orchestrator-daemon",
                    "pid": 42,
                    "executablePath": "/opt/example/ao",
                    "workingDirectory": "/opt/example/work",
                    "startupWorkingDirectory": "/opt/example/start",
                }
            ),
        ),
        completed(
            (),
            0 if ready else 1,
            out=json.dumps(
                {
                    "status": "ready" if ready else "not-ready",
                    "service": "agent-orchestrator-daemon",
                    "pid": 42,
                    "executablePath": "/opt/example/ao",
                    "workingDirectory": "/opt/example/work",
                    "startupWorkingDirectory": "/opt/example/start",
                }
            ),
        ),
        completed((), out="HTTP/1.1 200 OK"),
        completed((), 22, out="403"),
    ]


def test_existing_v1_is_readable_and_requests_v2_candidate(tmp_path: Path) -> None:
    path = tmp_path / "host.toml"
    path.write_text(V1_PROFILE, encoding="utf-8")
    path.chmod(0o600)

    plan = host.plan_profile(path)
    verified = host.verify_profile(path)

    assert plan["schema_read"] == 1
    assert plan["schema_render"] == 2
    assert plan["migration_required"] is True
    assert verified["migration_required"] is True


def test_real_legacy_v1_shape_is_accepted_without_live_profile(
    tmp_path: Path,
) -> None:
    profile = tmp_path / "host.toml"
    profile.write_bytes(LEGACY_V1_FIXTURE.read_bytes())
    profile.chmod(0o600)

    plan = host.plan_profile(profile)
    inspected = host.inspect_host(
        FakeRunner(inspect_responses()), profile=profile, context="sandbox"
    )
    candidate = tmp_path / "candidate"
    rendered = host.render_profile(profile, candidate)
    verified = host.verify_profile(profile, candidate=candidate)

    assert plan["schema_read"] == 1
    assert plan["migration_required"] is True
    assert cast(dict[str, object], inspected["states"])["daemon"] == "indeterminate"
    assert rendered["unchanged"] is False
    assert verified["schema_read"] == 1
    assert verified["migration_required"] is True
    migrated = tomllib.loads((candidate / "host.toml").read_text())
    assert migrated["dashboard"]["desired_service"] == "ao-dashboard.service"
    assert migrated["dashboard"]["rollback_service"] == "ao-dashboard-rollback.service"


def test_legacy_v1_canonicalizes_to_self_readable_v2(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy.toml"
    legacy.write_bytes(LEGACY_V1_FIXTURE.read_bytes())
    legacy.chmod(0o600)
    canonical = host._canonical_v2(host._load_profile(legacy))
    migrated = tmp_path / "migrated.toml"
    migrated.write_text(host._toml(canonical), encoding="utf-8")
    migrated.chmod(0o600)

    readback = host._load_profile(migrated)

    terminal = cast(
        dict[str, object],
        cast(dict[str, object], readback["dashboard"])["terminal"],
    )
    assert terminal["allowed_client_ips"] == ["203.0.113.7", "203.0.113.8"]
    assert terminal["origin_mode"] == "edge-validated-rewrite"
    assert terminal["upstream"] == "http://127.0.0.1:3001/mux"
    storage = cast(dict[str, object], readback["storage"])
    for boundary in cast(list[dict[str, object]], storage["boundaries"]):
        assert set(boundary) == {"path", "kind", "recursive_search"}


@pytest.mark.parametrize(
    ("update", "message"),
    [
        ({"desired_enabled": "yes"}, "boolean"),
        ({"allowed_client_ips": []}, "exact client IPs"),
        ({"allowed_origin": "not-an-origin"}, "exact Origin"),
        ({"path": "/other"}, "exactly /mux"),
        ({"upstream": "http://example.test/mux"}, "HTTP loopback URL"),
        ({"trust_model": "other"}, "single-user-trusted-lan"),
    ],
)
def test_legacy_v1_validation_failures(update: dict[str, object], message: str) -> None:
    profile = tomllib.loads(LEGACY_V1_FIXTURE.read_text(encoding="utf-8"))
    dashboard = cast(dict[str, object], profile["dashboard"])
    terminal = cast(dict[str, object], dashboard["terminal"])
    terminal.update(update)

    with pytest.raises(host.CalibrationError, match=message):
        host._validate_terminal_v1(terminal)


def test_host_status_stale_and_core_doctor_failure_block_ready() -> None:
    doctor = json.dumps(
        {
            "ok": False,
            "checks": [
                {
                    "name": "data-dir-write",
                    "level": "FAIL",
                    "message": "read-only file system",
                }
            ],
        }
    )
    runner = FakeRunner(inspect_responses(status='{"state":"stale"}', doctor=doctor))

    report = host.inspect_host(runner, context="host")

    assert report["states"] == {
        "daemon": "indeterminate",
        "delivery": "not_applicable",
    }
    assert report["known_issues"] == [
        "AO-HOST-CONTEXT-MISMATCH",
        "AO-PROCESS-CONTAINMENT-UNVERIFIED",
    ]
    capabilities = cast(dict[str, object], report["capabilities"])
    assert capabilities["loopback_base_url"] == "http://127.0.0.1:3001"
    assert capabilities["ao_version_text"] == "ao version 1.2.3"
    assert capabilities["glibc_version"] == "2.39"
    assert capabilities["tmux_version"] == "3.5"
    assert capabilities["cgroup_version"] == "v2"
    assert cast(dict[str, object], capabilities["ao_status"])["state"] == "stale"
    doctor_data = cast(dict[str, object], capabilities["ao_doctor"])
    assert doctor_data["ok"] is False
    assert set(report) == {
        "schema_version",
        "command",
        "context",
        "states",
        "capabilities",
        "probes",
        "known_issues",
        "next_actions",
    }
    assert set(cast(list[dict[str, object]], report["probes"])[0]) == {
        "id",
        "owner",
        "status",
        "detail",
    }


def test_inspect_profile_context_cgroup_and_invalid_json(
    profile: Path, codex_home: Path
) -> None:
    runner = FakeRunner(
        inspect_responses(
            status="not-json", doctor="not-json", cgroup="tmpfs", ready=False
        )
    )
    report = host.inspect_host(runner, profile=profile, context="sandbox")
    assert cast(dict[str, object], report["states"])["daemon"] == "indeterminate"
    capabilities = cast(dict[str, object], report["capabilities"])
    assert capabilities["cgroup_version"] == "v1"
    (codex_home / "config.toml").write_text("bad =", encoding="utf-8")
    conflict = host.inspect_host(
        FakeRunner(inspect_responses()), profile=profile, context="sandbox"
    )
    assert "AO-CODEX-HOME-CONFLICT" in cast(list[str], conflict["known_issues"])
    with pytest.raises(host.CalibrationError, match="context"):
        host.inspect_host(FakeRunner([]), context="remote")
    invalid_context: object = []
    with pytest.raises(host.CalibrationError, match="context"):
        host.inspect_host(FakeRunner([]), context=cast(str, invalid_context))


def test_inspect_loads_explicit_profile_once(
    monkeypatch: pytest.MonkeyPatch, profile: Path
) -> None:
    original_load = host._load_profile
    loaded: list[Path] = []

    def load_once(path: Path) -> dict[str, object]:
        loaded.append(path)
        return original_load(path)

    monkeypatch.setattr(host, "_load_profile", load_once)
    report = host.inspect_host(
        FakeRunner(inspect_responses()), profile=profile, context="sandbox"
    )

    assert loaded == [profile]
    assert cast(dict[str, object], report["capabilities"])["loopback_base_url"] == (
        "http://127.0.0.1:3001"
    )


def test_full_probe_json_is_parsed_before_display_truncation() -> None:
    extension = "x" * 3000
    status = json.dumps(
        {
            "state": "ready",
            "pid": 42,
            "port": 3001,
            "health": "ok",
            "ready": "ready",
            "extension": extension,
        }
    )
    doctor = json.dumps({"ok": True, "checks": [], "extension": extension})
    report = host.inspect_host(
        FakeRunner(inspect_responses(status=status, doctor=doctor)),
        context="host",
    )
    capabilities = cast(dict[str, object], report["capabilities"])
    assert cast(dict[str, object], capabilities["ao_status"])["extension"] == extension
    assert cast(dict[str, object], capabilities["ao_doctor"])["extension"] == extension
    probes = cast(list[dict[str, object]], report["probes"])
    assert all(len(cast(str, probe["detail"])) <= 1000 for probe in probes)


def test_profile_free_dashboard_delivery_is_explicitly_unknown() -> None:
    runner = FakeRunner(inspect_responses())
    report = host.inspect_host(runner, context="host")
    probes = {
        cast(str, probe["id"]): probe
        for probe in cast(list[dict[str, object]], report["probes"])
    }
    assert probes["dashboard"]["status"] == "unknown"
    assert probes["mux"]["status"] == "unknown"
    assert len(runner.commands) == 10


@pytest.mark.parametrize(
    ("context", "expected"),
    [
        (
            "host",
            {
                "healthz": "daemon",
                "readyz": "daemon",
                "dashboard": "host",
                "mux": "host",
            },
        ),
        (
            "sandbox",
            {
                "healthz": "sandbox",
                "readyz": "sandbox",
                "dashboard": "sandbox",
                "mux": "sandbox",
            },
        ),
    ],
)
def test_ao_and_dashboard_probe_owners_are_separate(
    tmp_path: Path, context: str, expected: dict[str, str]
) -> None:
    profile = tmp_path / "host.toml"
    profile.write_text(
        LEGACY_V1_FIXTURE.read_text(encoding="utf-8")
        .replace(
            'trusted_readonly_cidrs = ["203.0.113.0/24"]',
            'trusted_readonly_cidrs = ["127.0.0.1/32"]',
        )
        .replace(
            'allowed_client_ips = ["203.0.113.7", "203.0.113.8"]',
            'allowed_client_ips = ["127.0.0.1"]',
        ),
        encoding="utf-8",
    )
    profile.chmod(0o600)
    runner = FakeRunner(
        [
            *inspect_responses(),
            completed((), out="ok"),
            completed((), out=websocket_response()),
        ]
    )
    report = host.inspect_host(runner, profile=profile, context=context)
    owners = {
        cast(str, probe["id"]): cast(str, probe["owner"])
        for probe in cast(list[dict[str, object]], report["probes"])
    }
    assert {probe: owners[probe] for probe in expected} == expected


def test_unauthorized_local_probe_source_is_unknown_not_degraded(
    tmp_path: Path,
) -> None:
    profile = tmp_path / "host.toml"
    profile.write_text(LEGACY_V1_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    profile.chmod(0o600)
    runner = FakeRunner(inspect_responses())
    report = host.inspect_host(runner, profile=profile, context="host")
    probes = {
        cast(str, probe["id"]): probe
        for probe in cast(list[dict[str, object]], report["probes"])
    }
    assert probes["dashboard"]["status"] == "unknown"
    assert probes["mux"]["status"] == "unknown"
    assert cast(dict[str, object], report["states"]) == {
        "daemon": "ready",
        "delivery": "indeterminate",
    }
    assert len(runner.commands) == 10


@pytest.mark.parametrize(
    ("listen_host", "readonly_cidr"),
    [("0.0.0.0", "0.0.0.0/0"), ("224.0.0.1", "224.0.0.0/4")],
)
def test_unspecified_or_multicast_listener_is_not_a_proven_source(
    tmp_path: Path, listen_host: str, readonly_cidr: str
) -> None:
    profile = tmp_path / "host.toml"
    profile.write_text(
        LEGACY_V1_FIXTURE.read_text(encoding="utf-8")
        .replace('listen_host = "127.0.0.1"', f'listen_host = "{listen_host}"')
        .replace(
            'trusted_readonly_cidrs = ["203.0.113.0/24"]',
            f'trusted_readonly_cidrs = ["{readonly_cidr}"]',
        )
        .replace(
            'allowed_client_ips = ["203.0.113.7", "203.0.113.8"]',
            f'allowed_client_ips = ["{listen_host}"]',
        ),
        encoding="utf-8",
    )
    profile.chmod(0o600)
    runner = FakeRunner(inspect_responses())
    report = host.inspect_host(runner, profile=profile, context="host")
    probes = {
        cast(str, probe["id"]): probe
        for probe in cast(list[dict[str, object]], report["probes"])
    }
    assert probes["dashboard"]["status"] == "unknown"
    assert probes["mux"]["status"] == "unknown"
    assert len(runner.commands) == 10


def test_ipv6_canonical_client_identity_authorizes_source_probe(
    tmp_path: Path,
) -> None:
    profile = tmp_path / "host.toml"
    profile.write_text(
        LEGACY_V1_FIXTURE.read_text(encoding="utf-8")
        .replace('listen_host = "127.0.0.1"', 'listen_host = "::1"')
        .replace(
            'trusted_readonly_cidrs = ["203.0.113.0/24"]',
            'trusted_readonly_cidrs = ["::1/128"]',
        )
        .replace(
            'allowed_client_ips = ["203.0.113.7", "203.0.113.8"]',
            'allowed_client_ips = ["0:0:0:0:0:0:0:1"]',
        ),
        encoding="utf-8",
    )
    profile.chmod(0o600)
    responses = inspect_responses()
    responses[-1] = completed((), out=websocket_response())
    runner = FakeRunner(responses)
    report = host.inspect_host(runner, profile=profile, context="host")
    assert runner.commands[10][3:5] == ("--interface", "::1")
    assert runner.commands[11][-3:-1] == ("--interface", "::1")
    assert cast(dict[str, object], report["states"])["delivery"] == "ready"


def test_bound_source_curl_45_is_unknown_but_external_failure_still_degrades(
    tmp_path: Path,
) -> None:
    profile = tmp_path / "host.toml"
    profile.write_text(
        LEGACY_V1_FIXTURE.read_text(encoding="utf-8")
        .replace(
            'trusted_readonly_cidrs = ["203.0.113.0/24"]',
            'trusted_readonly_cidrs = ["127.0.0.1/32"]',
        )
        .replace(
            'allowed_client_ips = ["203.0.113.7", "203.0.113.8"]',
            'allowed_client_ips = ["127.0.0.1"]',
        ),
        encoding="utf-8",
    )
    profile.chmod(0o600)
    external = json.dumps(
        {
            "ok": False,
            "failures": 1,
            "checks": [{"name": "github-token", "level": "FAIL"}],
        }
    )
    responses = inspect_responses(doctor=external)
    responses[-2] = completed((), code=45, err="localized bind detail")
    responses[-1] = completed((), code=45, err="localized bind detail")
    report = host.inspect_host(FakeRunner(responses), profile=profile, context="host")
    probes = {
        cast(str, probe["id"]): probe
        for probe in cast(list[dict[str, object]], report["probes"])
    }
    assert probes["dashboard"]["status"] == "unknown"
    assert probes["mux"]["status"] == "unknown"
    assert cast(dict[str, object], report["states"]) == {
        "daemon": "ready",
        "delivery": "degraded",
    }


def test_init_render_verify_round_trip_and_manifest(
    tmp_path: Path, codex_home: Path
) -> None:
    profile = tmp_path / "private" / "host.toml"
    created = host.init_profile(
        profile,
        trust_model="trusted-single-user",
        codex_home=codex_home,
        data_dir=tmp_path / "data",
        private_authority=tmp_path / "authority" / "AGENTS.md",
        state_root=tmp_path / "state",
        dashboard_enabled=True,
        dashboard_listen_host="127.0.0.1",
        dashboard_listen_port=8443,
        readonly_cidrs=("203.0.113.0/24",),
        document_root=tmp_path / "dashboard",
        nginx_executable=Path("/usr/sbin/nginx"),
        nginx_pid_file=tmp_path / "state/nginx.pid",
        active_config=tmp_path / "state/active.conf",
        desired_service="ao-dashboard.service",
        rollback_service="ao-dashboard-rollback.service",
        desired_nginx_artifact=tmp_path / "state/nginx.conf",
        desired_service_artifact=tmp_path / "state/nginx.service",
        terminal=True,
        client_ips=("203.0.113.7", "203.0.113.8"),
        origin="https://console.example.test",
        upstream="http://127.0.0.1:3001/mux",
        upstream_origin="http://127.0.0.1:3001",
        origin_mode="edge-validated-rewrite",
    )
    assert created["schema_version"] == 2
    assert profile.stat().st_mode & 0o777 == 0o600
    assert "nginx/ao-terminal.conf" in cast(
        list[str], host.plan_profile(profile)["artifacts"]
    )
    output = tmp_path / "candidate"
    assert host.render_profile(profile, output)["unchanged"] is False
    assert host.render_profile(profile, output)["unchanged"] is True
    assert host.verify_profile(profile, candidate=output)["valid"] is True
    candidate_profile = (output / "host.toml").read_text()
    assert str(codex_home) in candidate_profile
    nginx = (output / "nginx/ao-terminal.conf").read_text()
    for phrase in (
        "location = /mux",
        "allow 203.0.113.7",
        "return 405",
        "https://console.example.test",
        "Upgrade",
        "    websocket 1;",
        "127.0.0.1:3001",
    ):
        assert phrase in nginx
    manifest = json.loads((output / "MANIFEST.json").read_text())
    assert manifest["profile_sha256"]
    assert manifest["generator"] == "calibrate_ao_host.py"
    assert manifest["profile_schema"] == 2
    assert manifest["expected_modes"]["."] == "0700"
    assert manifest["expected_modes"]["MANIFEST.json"] == "0600"
    assert "host.toml" in manifest["files"]
    service = (output / "service/ao-dashboard.service").read_text()
    for phrase in (
        "Type=forking",
        "ExecStart=",
        "ExecReload=",
        "ExecStop=",
        "PIDFile=",
        "Restart=on-failure",
        "UMask=0077",
        "ReadWritePaths=",
        "[Install]",
        "WantedBy=default.target",
    ):
        assert phrase in service
    authority = (output / "AGENTS.md").read_text()
    runbook = (output / "runbooks/ao.md").read_text()
    for phrase in (
        str(tmp_path / "state"),
        "Storage routing",
        "matching MainPID",
        "does not mutate active host state",
    ):
        assert phrase in authority
    for phrase in (
        "inspect --context host",
        "plan --profile",
        "render --profile",
        "verify --profile",
        "ao-dashboard-rollback.service",
        "unreadable doctor result",
    ):
        assert phrase in runbook


def test_non_bmp_toml_round_trips_through_render_plan_and_verify(
    profile: Path, tmp_path: Path
) -> None:
    parsed = host._load_profile(profile)
    dashboard = cast(dict[str, object], parsed["dashboard"])
    terminal = cast(dict[str, object], dashboard["terminal"])
    terminal["require_authentication_if"] = ["future-\U0001f680-policy", "del-\x7f"]
    profile.write_text(host._toml(parsed), encoding="utf-8")
    candidate = tmp_path / "unicode-candidate"
    host.render_profile(profile, candidate)
    rendered = candidate / "host.toml"
    rendered_text = rendered.read_text(encoding="utf-8")
    assert "\U0001f680" in rendered_text
    assert "\\u007f" in rendered_text
    assert "\x7f" not in rendered_text
    reloaded = host._load_profile(rendered)
    reloaded_terminal = cast(
        dict[str, object], cast(dict[str, object], reloaded["dashboard"])["terminal"]
    )
    assert reloaded_terminal["require_authentication_if"] == [
        "future-\U0001f680-policy",
        "del-\x7f",
    ]
    assert host.plan_profile(rendered)["schema_read"] == 2
    assert host.verify_profile(profile, candidate=candidate)["valid"] is True
    second = tmp_path / "unicode-candidate-second"
    host.render_profile(rendered, second)
    assert host.verify_profile(rendered, candidate=second)["valid"] is True
    assert host.render_profile(rendered, second)["unchanged"] is True
    with pytest.raises(host.CalibrationError, match="lone surrogates"):
        host._quote("\ud800")


def test_init_lone_surrogate_fails_before_target_and_json_envelope_is_printable(
    tmp_path: Path,
    codex_home: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "direct.toml"
    with pytest.raises(host.CalibrationError):
        host.init_profile(
            target,
            trust_model="\ud800",
            codex_home=codex_home,
            data_dir=tmp_path / "data",
            private_authority=tmp_path / "authority/AGENTS.md",
            state_root=tmp_path / "state",
        )
    assert not target.exists()
    cli_target = tmp_path / "cli.toml"
    assert (
        host.main(
            [
                "init",
                "--profile",
                str(cli_target),
                "--trust-model",
                "untrusted",
                "--codex-home",
                str(codex_home),
                "--data-dir",
                str(tmp_path / "cli-data"),
                "--private-authority",
                "/tmp/\ud800/AGENTS.md",
                "--state-root",
                str(tmp_path / "cli-state"),
            ]
        )
        == host.EXIT_INVALID
    )
    assert json.loads(capsys.readouterr().out)["capabilities"]["error"]["kind"] == (
        "invalid"
    )
    assert not cli_target.exists()


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (("version", "3"), "unsupported"),
        (("top", "extra = true"), "unknown top-level"),
        (("remove", 'cli = "ao"'), "missing keys"),
        (("ao-extra", 'surprise = "x"'), "unknown keys"),
        (("relative", 'codex_home = "relative"'), "absolute path"),
    ],
)
def test_profile_shape_rejections(
    tmp_path: Path, change: tuple[str, str], message: str
) -> None:
    text = V1_PROFILE
    kind, value = change
    if kind == "version":
        text = f"schema_version = {value}\n" + text
    elif kind == "top":
        text = value + "\n" + text
    elif kind == "remove":
        text = text.replace(value + "\n", "")
    elif kind == "ao-extra":
        text = text.replace("[ao]\n", f"[ao]\n{value}\n")
    else:
        text = text.replace('codex_home = "/opt/example/codex"', value)
    path = tmp_path / "host.toml"
    path.write_text(text, encoding="utf-8")
    path.chmod(0o600)
    with pytest.raises(host.CalibrationError, match=message):
        host.plan_profile(path)


@pytest.mark.parametrize(
    ("update", "message"),
    [
        ({"desired_enabled": "yes"}, "boolean"),
        ({"desired_enabled": True}, "exact client IPs"),
        (
            {"desired_enabled": True, "allowed_client_ips": ["203.0.113.1"]},
            "exact Origin",
        ),
        (
            {
                "desired_enabled": True,
                "allowed_client_ips": ["203.0.113.1"],
                "allowed_origin": "https://x.test",
                "path": "/other",
            },
            "exactly /mux",
        ),
        (
            {
                "desired_enabled": True,
                "allowed_client_ips": ["203.0.113.1"],
                "allowed_origin": "https://x.test",
                "upstream": "http://example.test",
            },
            "loopback",
        ),
        (
            {
                "desired_enabled": True,
                "allowed_client_ips": ["203.0.113.1"],
                "allowed_origin": "https://x.test",
                "trust_model": "untrusted",
            },
            "trusted-single-user",
        ),
        (
            {
                "desired_enabled": True,
                "allowed_client_ips": ["203.0.113.1"],
                "allowed_origin": "https://x.test",
                "origin_mode": "rewrite",
            },
            "explicit Origin mode",
        ),
    ],
)
def test_terminal_rejections(update: dict[str, object], message: str) -> None:
    terminal: dict[str, object] = {
        "desired_enabled": False,
        "trust_model": "trusted-single-user",
        "allowed_client_ips": [],
        "allowed_origin": "",
        "path": "/mux",
        "upstream": "http://127.0.0.1:3001",
        "upstream_origin": "",
        "require_authentication_if": [],
        "origin_mode": "preserve",
    }
    terminal.update(update)
    with pytest.raises((host.CalibrationError, ValueError), match=message):
        host._validate_terminal(terminal)


def test_codex_home_extensible_subset_and_rejections(
    codex_home: Path, tmp_path: Path
) -> None:
    assert host._validate_codex_home(codex_home) == codex_home
    config = codex_home / "config.toml"
    config.chmod(0o644)
    with pytest.raises(host.CalibrationError, match="group or other"):
        host._validate_codex_home(codex_home)
    config.chmod(0o600)
    config.write_text("[features]\napps = true\nplugins = false\n", encoding="utf-8")
    with pytest.raises(host.CalibrationError, match="apps=false"):
        host._validate_codex_home(codex_home)
    config.write_text("bad =", encoding="utf-8")
    with pytest.raises(host.CalibrationError, match="valid TOML"):
        host._validate_codex_home(codex_home)
    config.write_text("value = true\n", encoding="utf-8")
    with pytest.raises(host.CalibrationError, match=r"define \[features\]"):
        host._validate_codex_home(codex_home)
    config.write_text(
        "[features]\napps = false\nplugins = false\n[mcp_servers.x]\n",
        encoding="utf-8",
    )
    with pytest.raises(host.CalibrationError, match="mcp_servers"):
        host._validate_codex_home(codex_home)
    config.unlink()
    with pytest.raises(host.CalibrationError, match="regular file"):
        host._validate_codex_home(codex_home)
    file_home = tmp_path / "file"
    file_home.write_text("x")
    file_home.chmod(0o600)
    with pytest.raises(host.CalibrationError, match="directory"):
        host._validate_codex_home(file_home)


def test_codex_auth_file_type_json_and_permissions(codex_home: Path) -> None:
    auth = codex_home / "auth.json"
    auth.chmod(0o644)
    with pytest.raises(host.CalibrationError, match="group or other"):
        host._validate_codex_home(codex_home)
    auth.chmod(0o600)
    auth.write_text("[]\n", encoding="utf-8")
    with pytest.raises(host.CalibrationError, match="JSON object"):
        host._validate_codex_home(codex_home)
    auth.write_text("bad", encoding="utf-8")
    with pytest.raises(host.CalibrationError, match="valid JSON"):
        host._validate_codex_home(codex_home)
    auth.unlink()
    with pytest.raises(host.CalibrationError, match="authentication file"):
        host._validate_codex_home(codex_home)


def test_safe_path_and_render_drift_rejections(tmp_path: Path, profile: Path) -> None:
    with pytest.raises(host.CalibrationError, match="absolute"):
        host._safe_path(Path("relative"), may_create=True)
    symlink = tmp_path / "link"
    symlink.symlink_to(profile)
    with pytest.raises(host.CalibrationError, match="symlink"):
        host._safe_path(symlink, may_create=False)
    missing = tmp_path / "missing"
    with pytest.raises(host.CalibrationError, match="does not exist"):
        host._safe_path(missing, may_create=False)
    unsafe = tmp_path / "unsafe"
    unsafe.write_text("x")
    unsafe.chmod(0o644)
    with pytest.raises(host.CalibrationError, match="group or other"):
        host._safe_path(unsafe, may_create=False)
    directory = tmp_path / "directory"
    directory.mkdir(mode=0o700)
    with pytest.raises(host.CalibrationError, match="regular file"):
        host._safe_path(directory, may_create=False, directory=False)
    output = tmp_path / "candidate"
    output.mkdir(mode=0o700)
    (output / "drift").write_text("x")
    with pytest.raises(host.CalibrationError, match="drift"):
        host.render_profile(profile, output)
    staging = tmp_path / ".new.staging"
    staging.mkdir(mode=0o700)
    with pytest.raises(host.CalibrationError, match="staging"):
        host.render_profile(profile, tmp_path / "new")
    tree = tmp_path / "tree"
    tree.mkdir(mode=0o700)
    (tree / "link").symlink_to(profile)
    with pytest.raises(host.CalibrationError, match="symlinks"):
        host._tree_bytes(tree)
    unsafe_parent = tmp_path / "writable-parent"
    unsafe_parent.mkdir(mode=0o777)
    unsafe_parent.chmod(0o777)
    with pytest.raises(host.CalibrationError, match="without sticky bit"):
        host.render_profile(profile, unsafe_parent / "candidate")
    unsafe_parent.chmod(0o1777)
    assert (
        host.render_profile(profile, unsafe_parent / "sticky-candidate")["unchanged"]
        is False
    )
    with pytest.raises(host.CalibrationError, match="parent must exist"):
        host.render_profile(profile, tmp_path / "missing" / "candidate")


def test_invalid_profile_and_init_rejections(
    tmp_path: Path, codex_home: Path, profile: Path
) -> None:
    invalid = tmp_path / "invalid.toml"
    invalid.write_text("bad =", encoding="utf-8")
    invalid.chmod(0o600)
    with pytest.raises(host.CalibrationError, match="valid TOML"):
        host.plan_profile(invalid)
    with pytest.raises(host.CalibrationError, match=r"define \[dashboard\]"):
        host._section({"ao": {}}, "dashboard")
    nonstring = tmp_path / "nonstring.toml"
    nonstring.write_text(
        V1_PROFILE.replace('codex_home = "/opt/example/codex"', "codex_home = 4"),
        encoding="utf-8",
    )
    nonstring.chmod(0o600)
    with pytest.raises(host.CalibrationError, match="must be a string"):
        host.plan_profile(nonstring)
    with pytest.raises(host.CalibrationError, match="unsupported TOML"):
        host._quote(("bad",))
    with pytest.raises(host.CalibrationError, match="already exists"):
        host.init_profile(
            profile,
            trust_model="untrusted",
            codex_home=codex_home,
            data_dir=tmp_path / "data",
            private_authority=tmp_path / "private" / "AGENTS.md",
            state_root=tmp_path / "state",
        )
    unsafe_parent = tmp_path / "unsafe-parent"
    unsafe_parent.mkdir(mode=0o755)
    unsafe_parent.chmod(0o755)
    with pytest.raises(host.CalibrationError, match="group or other"):
        host.init_profile(
            unsafe_parent / "host.toml",
            trust_model="untrusted",
            codex_home=codex_home,
            data_dir=tmp_path / "data2",
            private_authority=tmp_path / "private2" / "AGENTS.md",
            state_root=tmp_path / "state2",
        )


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ('listen_host = "127.0.0.1"', "listen_host = 1", "listen_host"),
        ('listen_host = "127.0.0.1"', 'listen_host = "bad host"', "listen_host"),
        ("listen_port = 8443", "listen_port = true", "listen_port"),
        (
            'trusted_readonly_cidrs = ["203.0.113.0/24"]',
            "trusted_readonly_cidrs = [1]",
            "CIDR strings",
        ),
        (
            'trusted_readonly_cidrs = ["203.0.113.0/24"]',
            "trusted_readonly_cidrs = 7",
            "CIDR strings",
        ),
        (
            'trusted_readonly_cidrs = ["203.0.113.0/24"]',
            "trusted_readonly_cidrs = []",
            "requires trusted_readonly_cidrs",
        ),
        (
            'trusted_readonly_cidrs = ["203.0.113.0/24"]',
            'trusted_readonly_cidrs = ["bad"]',
            "valid CIDRs",
        ),
        (
            'trusted_readonly_cidrs = ["203.0.113.0/24"]',
            'trusted_readonly_cidrs = ["203.0.113.7/255.255.255.0"]',
            "valid CIDRs",
        ),
        (
            'trusted_readonly_cidrs = ["203.0.113.0/24"]',
            'trusted_readonly_cidrs = ["203.0.113.7/0.0.0.255"]',
            "valid CIDRs",
        ),
    ],
)
def test_dashboard_network_fields_fail_closed(
    tmp_path: Path, old: str, new: str, message: str
) -> None:
    profile = tmp_path / "host.toml"
    profile.write_text(V1_PROFILE.replace(old, new), encoding="utf-8")
    profile.chmod(0o600)
    with pytest.raises(host.CalibrationError, match=message):
        host.plan_profile(profile)


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (
            'listen_host = "127.0.0.1"',
            'listen_host = "fe80::1%eth0;\\n      allow all;\\n      #"',
        ),
        (
            'trusted_readonly_cidrs = ["203.0.113.0/24"]',
            'trusted_readonly_cidrs = ["fe80::1%eth0;\\n      allow all;\\n      #/0"]',
        ),
        (
            "allowed_client_ips = []",
            'allowed_client_ips = ["fe80::1%eth0;\\n      allow all;\\n      #"]',
        ),
    ],
)
def test_scoped_ipv6_values_cannot_reach_nginx_rendering(
    tmp_path: Path, old: str, new: str
) -> None:
    profile = tmp_path / "scoped-ipv6.toml"
    profile.write_text(V1_PROFILE.replace(old, new), encoding="utf-8")
    profile.chmod(0o600)
    with pytest.raises(host.CalibrationError):
        host.plan_profile(profile)
    with pytest.raises(host.CalibrationError):
        host.render_profile(profile, tmp_path / "candidate")
    assert not (tmp_path / "candidate").exists()


def test_dashboard_listener_family_and_collision_fail_closed(
    tmp_path: Path, codex_home: Path
) -> None:
    mismatch = tmp_path / "mismatch.toml"
    mismatch.write_text(
        V1_PROFILE.replace(
            'trusted_readonly_cidrs = ["203.0.113.0/24"]',
            'trusted_readonly_cidrs = ["2001:db8::/32"]',
        ),
        encoding="utf-8",
    )
    mismatch.chmod(0o600)
    with pytest.raises(host.CalibrationError, match="listener family"):
        host.plan_profile(mismatch)

    mixed_cidrs = tmp_path / "mixed-cidrs.toml"
    mixed_cidrs.write_text(
        V1_PROFILE.replace(
            'trusted_readonly_cidrs = ["203.0.113.0/24"]',
            'trusted_readonly_cidrs = ["203.0.113.0/24", "2001:db8::/32"]',
        ),
        encoding="utf-8",
    )
    mixed_cidrs.chmod(0o600)
    with pytest.raises(host.CalibrationError, match="listener family"):
        host.plan_profile(mixed_cidrs)

    terminal_mismatch = tmp_path / "terminal-mismatch.toml"
    terminal_mismatch.write_text(
        LEGACY_V1_FIXTURE.read_text(encoding="utf-8").replace(
            'allowed_client_ips = ["203.0.113.7", "203.0.113.8"]',
            'allowed_client_ips = ["2001:db8::7"]',
        ),
        encoding="utf-8",
    )
    terminal_mismatch.chmod(0o600)
    with pytest.raises(host.CalibrationError, match="listener family"):
        host.plan_profile(terminal_mismatch)

    mixed_clients = tmp_path / "mixed-clients.toml"
    mixed_clients.write_text(
        LEGACY_V1_FIXTURE.read_text(encoding="utf-8").replace(
            'allowed_client_ips = ["203.0.113.7", "203.0.113.8"]',
            'allowed_client_ips = ["203.0.113.7", "2001:db8::7"]',
        ),
        encoding="utf-8",
    )
    mixed_clients.chmod(0o600)
    with pytest.raises(host.CalibrationError, match="listener family"):
        host.plan_profile(mixed_clients)

    collision = tmp_path / "collision.toml"
    with pytest.raises(host.CalibrationError, match="must not collide"):
        host.init_profile(
            collision,
            trust_model="trusted-single-user",
            codex_home=codex_home,
            data_dir=tmp_path / "data",
            private_authority=tmp_path / "authority/AGENTS.md",
            state_root=tmp_path / "state",
            dashboard_enabled=True,
            dashboard_listen_host="127.0.0.1",
            dashboard_listen_port=3001,
            readonly_cidrs=("127.0.0.1/32",),
            document_root=tmp_path / "dashboard",
            nginx_executable=Path("/usr/sbin/nginx"),
            nginx_pid_file=tmp_path / "state/nginx.pid",
            active_config=tmp_path / "state/active.conf",
            desired_service="ao-dashboard.service",
            rollback_service="ao-dashboard-rollback.service",
            desired_nginx_artifact=tmp_path / "state/nginx.conf",
            desired_service_artifact=tmp_path / "state/nginx.service",
        )
    assert not collision.exists()

    legacy = tmp_path / "legacy-collision.toml"
    legacy.write_text(
        V1_PROFILE.replace("listen_port = 8443", "listen_port = 3001"),
        encoding="utf-8",
    )
    legacy.chmod(0o600)
    with pytest.raises(host.CalibrationError, match="must not collide"):
        host.plan_profile(legacy)
    with pytest.raises(host.CalibrationError, match="must not collide"):
        host.verify_profile(legacy)
    with pytest.raises(host.CalibrationError, match="must not collide"):
        host.render_profile(legacy, tmp_path / "candidate")
    canonical = host._canonical_v2(tomllib.loads(V1_PROFILE))
    cast(dict[str, object], canonical["dashboard"])["listen_port"] = 3001
    cast(dict[str, object], canonical["ao"])["loopback_base_url"] = (
        "http://localhost:3001"
    )
    with pytest.raises(host.CalibrationError, match="must not collide"):
        host._validate_no_listener_collision(canonical)


@pytest.mark.parametrize(
    ("dashboard_host", "readonly_cidr", "ao_base"),
    [
        ("0.0.0.0", "0.0.0.0/0", "http://127.0.0.1:3001"),
        ("::", "::/0", "http://[::1]:3001"),
    ],
)
def test_unspecified_dashboard_listener_collision_fails_closed(
    tmp_path: Path, dashboard_host: str, readonly_cidr: str, ao_base: str
) -> None:
    profile = tmp_path / "wildcard-collision.toml"
    profile.write_text(
        V1_PROFILE.replace(
            'listen_host = "127.0.0.1"', f'listen_host = "{dashboard_host}"'
        )
        .replace("listen_port = 8443", "listen_port = 3001")
        .replace(
            'trusted_readonly_cidrs = ["203.0.113.0/24"]',
            f'trusted_readonly_cidrs = ["{readonly_cidr}"]',
        )
        .replace("http://127.0.0.1:3001", ao_base),
        encoding="utf-8",
    )
    profile.chmod(0o600)
    with pytest.raises(host.CalibrationError, match="must not collide"):
        host.render_profile(profile, tmp_path / "candidate")


@pytest.mark.parametrize("field", ["data_dir", "state_root"])
def test_existing_files_are_rejected_for_directory_fields(
    tmp_path: Path, codex_home: Path, profile: Path, field: str
) -> None:
    regular = tmp_path / f"{field}.file"
    regular.write_text("x", encoding="utf-8")
    regular.chmod(0o600)
    if field == "data_dir":
        with pytest.raises(host.CalibrationError, match="directory"):
            host.init_profile(
                tmp_path / "init.toml",
                trust_model="untrusted",
                codex_home=codex_home,
                data_dir=regular,
                private_authority=tmp_path / "authority/AGENTS.md",
                state_root=tmp_path / "state",
            )
        old = f'data_dir = "{tmp_path / "data"}"'
    else:
        old = f'state_root = "{tmp_path / "state"}"'
    profile.write_text(
        profile.read_text(encoding="utf-8").replace(old, f'{field} = "{regular}"'),
        encoding="utf-8",
    )
    with pytest.raises(host.CalibrationError, match="directory"):
        host.plan_profile(profile)
    with pytest.raises(host.CalibrationError, match="directory"):
        host.render_profile(profile, tmp_path / f"{field}-candidate")


def test_init_rejects_pid_file_outside_state_root(
    tmp_path: Path, codex_home: Path
) -> None:
    target = tmp_path / "host.toml"
    with pytest.raises(host.CalibrationError, match=r"beneath paths\.state_root"):
        host.init_profile(
            target,
            trust_model="untrusted",
            codex_home=codex_home,
            data_dir=tmp_path / "data",
            private_authority=tmp_path / "authority/AGENTS.md",
            state_root=tmp_path / "state",
            nginx_pid_file=tmp_path / "outside/nginx.pid",
        )
    assert not target.exists()


def test_init_rejects_state_root_as_pid_file(tmp_path: Path, codex_home: Path) -> None:
    state_root = tmp_path / "state"
    with pytest.raises(host.CalibrationError, match="must be a file beneath"):
        host.init_profile(
            tmp_path / "host.toml",
            trust_model="untrusted",
            codex_home=codex_home,
            data_dir=tmp_path / "data",
            private_authority=tmp_path / "authority/AGENTS.md",
            state_root=state_root,
            nginx_pid_file=state_root,
        )


def test_v2_profile_rejects_pid_file_outside_state_root(
    tmp_path: Path, profile: Path
) -> None:
    original = f'pid_file = "{tmp_path / "state/nginx.pid"}"'
    external = f'pid_file = "{tmp_path / "outside/nginx.pid"}"'
    profile.write_text(
        profile.read_text(encoding="utf-8").replace(original, external),
        encoding="utf-8",
    )
    for operation in (
        lambda: host.plan_profile(profile),
        lambda: host.verify_profile(profile),
        lambda: host.render_profile(profile, tmp_path / "candidate"),
    ):
        with pytest.raises(host.CalibrationError, match=r"beneath paths\.state_root"):
            operation()


def test_disabled_terminal_rejects_explicit_unknown_origin_mode(
    tmp_path: Path, profile: Path
) -> None:
    profile.write_text(
        profile.read_text(encoding="utf-8").replace(
            'origin_mode = "preserve"',
            'origin_mode = "future-mode"',
        ),
        encoding="utf-8",
    )
    for operation in (
        lambda: host.plan_profile(profile),
        lambda: host.verify_profile(profile),
        lambda: host.render_profile(profile, tmp_path / "candidate"),
    ):
        with pytest.raises(host.CalibrationError, match="explicit Origin mode"):
            operation()


def test_init_creates_every_missing_profile_ancestor_private(
    tmp_path: Path, codex_home: Path
) -> None:
    target = tmp_path / "one/two/three/host.toml"
    previous_umask = os.umask(0o002)
    try:
        host.init_profile(
            target,
            trust_model="untrusted",
            codex_home=codex_home,
            data_dir=tmp_path / "data",
            private_authority=tmp_path / "authority/AGENTS.md",
            state_root=tmp_path / "state",
        )
    finally:
        os.umask(previous_umask)
    for directory in (
        tmp_path / "one",
        tmp_path / "one/two",
        tmp_path / "one/two/three",
    ):
        assert directory.stat().st_mode & 0o777 == 0o700


@pytest.mark.parametrize(
    ("boundaries", "message"),
    [
        ([], "must not be empty"),
        (["bad"], "entries must be objects"),
        ([{"path": "/tmp", "kind": "state"}], "requires path"),
    ],
)
def test_v2_storage_boundary_shape_rejections(
    tmp_path: Path, profile: Path, boundaries: list[object], message: str
) -> None:
    parsed = host._canonical_v2(host._load_profile(profile))
    cast(dict[str, object], parsed["storage"])["boundaries"] = boundaries
    text = host._toml(parsed)
    target = tmp_path / f"boundary-{len(boundaries)}.toml"
    target.write_text(text, encoding="utf-8")
    target.chmod(0o600)
    with pytest.raises(host.CalibrationError, match=message):
        host.plan_profile(target)


def test_init_rejects_incomplete_or_invalid_dashboard_trust(
    tmp_path: Path, codex_home: Path
) -> None:
    with pytest.raises(host.CalibrationError, match="exact listen IP"):
        host.init_profile(
            tmp_path / "disabled-host.toml",
            trust_model="untrusted",
            codex_home=codex_home,
            data_dir=tmp_path / "data",
            private_authority=tmp_path / "authority/AGENTS.md",
            state_root=tmp_path / "state",
            dashboard_listen_host="not-an-ip",
        )
    with pytest.raises(host.CalibrationError, match="listen port"):
        host.init_profile(
            tmp_path / "disabled-port.toml",
            trust_model="untrusted",
            codex_home=codex_home,
            data_dir=tmp_path / "data",
            private_authority=tmp_path / "authority/AGENTS.md",
            state_root=tmp_path / "state",
            dashboard_listen_port=70000,
        )
    assert not (tmp_path / "disabled-host.toml").exists()
    assert not (tmp_path / "disabled-port.toml").exists()

    with pytest.raises(host.CalibrationError, match="explicit listen"):
        host.init_profile(
            tmp_path / "missing.toml",
            trust_model="trusted-single-user",
            codex_home=codex_home,
            data_dir=tmp_path / "data",
            private_authority=tmp_path / "authority/AGENTS.md",
            state_root=tmp_path / "state",
            dashboard_enabled=True,
        )

    def initialize(
        name: str,
        *,
        listen_host: str = "127.0.0.1",
        listen_port: int = 8443,
        cidrs: Sequence[str] = ("203.0.113.0/24",),
        terminal: bool = False,
        document_root: Path | None = None,
        client_ips: Sequence[str] = (),
        origin: str | None = None,
        upstream: str | None = None,
        upstream_origin: str | None = None,
        origin_mode: str | None = None,
    ) -> None:
        host.init_profile(
            tmp_path / name,
            trust_model="trusted-single-user",
            codex_home=codex_home,
            data_dir=tmp_path / "data",
            private_authority=tmp_path / "authority/AGENTS.md",
            state_root=tmp_path / "state",
            dashboard_enabled=True,
            dashboard_listen_host=listen_host,
            dashboard_listen_port=listen_port,
            readonly_cidrs=cidrs,
            document_root=document_root or tmp_path / "dashboard",
            nginx_executable=Path("/usr/sbin/nginx"),
            nginx_pid_file=tmp_path / "state/nginx.pid",
            active_config=tmp_path / "state/active.conf",
            desired_service="ao-dashboard.service",
            rollback_service="ao-dashboard-rollback.service",
            desired_nginx_artifact=tmp_path / "state/nginx.conf",
            desired_service_artifact=tmp_path / "state/nginx.service",
            terminal=terminal,
            client_ips=client_ips,
            origin=origin,
            upstream=upstream,
            upstream_origin=upstream_origin,
            origin_mode=origin_mode,
        )

    with pytest.raises(host.CalibrationError, match="listen port"):
        initialize("port.toml", listen_port=0)
    with pytest.raises(host.CalibrationError, match="listen port"):
        initialize("bool-port.toml", listen_port=True)
    assert not (tmp_path / "bool-port.toml").exists()
    with pytest.raises(host.CalibrationError, match="exact listen IP"):
        initialize("host.toml", listen_host="bad host")
    with pytest.raises(host.CalibrationError, match="enabled terminal"):
        initialize("terminal.toml", terminal=True)
    with pytest.raises(host.CalibrationError, match="valid networks"):
        initialize("cidr.toml", cidrs=("bad",))
    with pytest.raises(host.CalibrationError, match="valid networks"):
        initialize("netmask-cidr.toml", cidrs=("203.0.113.7/255.255.255.0",))
    with pytest.raises(host.CalibrationError, match="listener family"):
        initialize("cidr-family.toml", cidrs=("2001:db8::/32",))
    with pytest.raises(host.CalibrationError, match="listener family"):
        initialize(
            "mixed-cidr-family.toml",
            cidrs=("203.0.113.0/24", "2001:db8::/32"),
        )

    def initialize_terminal(
        name: str,
        client_ips: Sequence[str],
        *,
        origin_mode: str = "preserve",
    ) -> None:
        rewrite = origin_mode == "edge-validated-rewrite"
        initialize(
            name,
            terminal=True,
            client_ips=client_ips,
            origin="https://console.example.test",
            upstream=(
                "http://127.0.0.1:3001/mux" if rewrite else "http://127.0.0.1:3001"
            ),
            upstream_origin="http://127.0.0.1:3001" if rewrite else None,
            origin_mode=origin_mode,
        )

    with pytest.raises(host.CalibrationError, match="listener family"):
        initialize_terminal("client-family.toml", ("2001:db8::7",))
    with pytest.raises(host.CalibrationError, match="listener family"):
        initialize_terminal(
            "mixed-client-family.toml",
            ("203.0.113.7", "2001:db8::7"),
            origin_mode="edge-validated-rewrite",
        )
    scoped = "fe80::1%eth0;\n      allow all;\n      #"
    with pytest.raises(host.CalibrationError, match="exact listen IP"):
        initialize("scoped-listener.toml", listen_host=scoped)
    with pytest.raises(host.CalibrationError, match="valid networks"):
        initialize("scoped-cidr.toml", cidrs=(f"{scoped}/128",))
    with pytest.raises(host.CalibrationError, match="valid networks"):
        initialize("scoped-cidr-zero.toml", cidrs=(f"{scoped}/0",))
    with pytest.raises(host.CalibrationError, match="valid IPs"):
        initialize_terminal("scoped-client.toml", (scoped,))
    assert not any(tmp_path.glob("scoped-*.toml"))
    with pytest.raises(host.CalibrationError, match="must be absolute"):
        initialize("relative.toml", document_root=Path("relative"))


def test_terminal_requires_explicit_origin_mode(
    tmp_path: Path, codex_home: Path
) -> None:
    state = tmp_path / "state"
    with pytest.raises(host.CalibrationError, match="enabled terminal"):
        host.init_profile(
            tmp_path / "host.toml",
            trust_model="trusted-single-user",
            codex_home=codex_home,
            data_dir=tmp_path / "data",
            private_authority=tmp_path / "authority/AGENTS.md",
            state_root=state,
            dashboard_enabled=True,
            dashboard_listen_host="127.0.0.1",
            dashboard_listen_port=8443,
            readonly_cidrs=("203.0.113.0/24",),
            document_root=tmp_path / "dashboard",
            nginx_executable=Path("/usr/sbin/nginx"),
            nginx_pid_file=state / "nginx.pid",
            active_config=state / "active.conf",
            desired_service="ao-dashboard.service",
            rollback_service="ao-dashboard-rollback.service",
            desired_nginx_artifact=state / "nginx.conf",
            desired_service_artifact=state / "nginx.service",
            terminal=True,
            client_ips=("203.0.113.7",),
            origin="https://console.example.test",
            upstream="http://127.0.0.1:3001",
        )


def test_v2_terminal_profile_requires_origin_mode(
    tmp_path: Path, codex_home: Path
) -> None:
    profile = tmp_path / "host.toml"
    state = tmp_path / "state"
    host.init_profile(
        profile,
        trust_model="trusted-single-user",
        codex_home=codex_home,
        data_dir=tmp_path / "data",
        private_authority=tmp_path / "authority/AGENTS.md",
        state_root=state,
        dashboard_enabled=True,
        dashboard_listen_host="127.0.0.1",
        dashboard_listen_port=8443,
        readonly_cidrs=("203.0.113.0/24",),
        document_root=tmp_path / "dashboard",
        nginx_executable=Path("/usr/sbin/nginx"),
        nginx_pid_file=state / "nginx.pid",
        active_config=state / "active.conf",
        desired_service="ao-dashboard.service",
        rollback_service="ao-dashboard-rollback.service",
        desired_nginx_artifact=state / "nginx.conf",
        desired_service_artifact=state / "nginx.service",
        terminal=True,
        client_ips=("203.0.113.7",),
        origin="https://console.example.test",
        upstream="http://127.0.0.1:3001",
        origin_mode="preserve",
    )
    profile.write_text(
        "\n".join(
            line
            for line in profile.read_text().splitlines()
            if not line.startswith("origin_mode =")
        )
        + "\n"
    )
    with pytest.raises(host.CalibrationError, match="explicit Origin mode"):
        host.plan_profile(profile)


def test_enabled_v2_dashboard_rejects_port_zero(profile: Path) -> None:
    text = profile.read_text()
    profile.write_text(
        text.replace('mode = "disabled"', 'mode = "read-only"'),
        encoding="utf-8",
    )
    with pytest.raises(host.CalibrationError, match="1 through 65535"):
        host.plan_profile(profile)


def test_storage_boundary_cli_argument_fails_closed() -> None:
    with pytest.raises(argparse.ArgumentTypeError, match="must be JSON"):
        host._storage_boundary_argument("not-json")
    with pytest.raises(argparse.ArgumentTypeError, match="must be false"):
        host._storage_boundary_argument(
            json.dumps(
                {
                    "path": "/opt/example/aggregation",
                    "kind": "aggregation-root",
                    "recursive_search": True,
                }
            )
        )
    with pytest.raises(argparse.ArgumentTypeError, match="kind is invalid"):
        host._storage_boundary_argument(
            json.dumps(
                {
                    "path": "/opt/example/aggregation",
                    "kind": "bad kind",
                    "recursive_search": False,
                }
            )
        )


@pytest.mark.parametrize("stdout", ["not-json", "[]"])
def test_subprocess_canary_json_boundary_fails_closed(
    monkeypatch: pytest.MonkeyPatch, stdout: str
) -> None:
    def fake_run(
        _command: object, **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        return completed((), out=stdout)

    monkeypatch.setattr(host.subprocess, "run", fake_run)
    with pytest.raises(host.CalibrationError, match="canary CLI"):
        host._invoke_subprocess_cli(("plan",), {})


def test_render_cleans_failed_staging(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, profile: Path
) -> None:
    target = tmp_path / "failed"

    def fail_replace(_source: Path, _target: Path) -> None:
        raise OSError("publish failed")

    monkeypatch.setattr(host.os, "replace", fail_replace)
    with pytest.raises(OSError, match="publish failed"):
        host.render_profile(profile, target)
    assert not (tmp_path / ".failed.staging").exists()


def test_verify_rejects_content_and_modes(tmp_path: Path, profile: Path) -> None:
    output = tmp_path / "candidate"
    host.render_profile(profile, output)
    (output / "AGENTS.md").write_text("changed")
    with pytest.raises(host.CalibrationError, match="canonical"):
        host.verify_profile(profile, candidate=output)
    host.render_profile(profile, tmp_path / "clean")
    clean = tmp_path / "clean"
    clean.chmod(0o500)
    with pytest.raises(host.CalibrationError, match="root mode"):
        host.verify_profile(profile, candidate=clean)
    clean.chmod(0o700)
    agents = clean / "AGENTS.md"
    agents.chmod(0o644)
    with pytest.raises(host.CalibrationError, match="mode must be 0600"):
        host.verify_profile(profile, candidate=clean)
    agents.chmod(0o600)
    extra = clean / "extra"
    extra.mkdir(mode=0o700)
    with pytest.raises(host.CalibrationError, match="tree shape"):
        host.verify_profile(profile, candidate=clean)
    extra.rmdir()
    wrong_type = tmp_path / "wrong-type"
    wrong_type.mkdir(mode=0o700)
    (wrong_type / "expected").mkdir(mode=0o700)
    with pytest.raises(host.CalibrationError, match="regular file"):
        host._validate_tree_shape(wrong_type, {"expected": b"content"})


def test_reconstruction_canary_executes_full_pipeline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def missing_executable(_name: str) -> None:
        return None

    monkeypatch.setattr(host.shutil, "which", missing_executable)
    runner = FakeRunner(
        [
            completed((), out="nginx version"),
            completed((), out="syntax is ok"),
        ]
    )
    result = host.reconstruction_canary(tmp_path / "isolated", runner)
    assert result == {
        "init_exit": 0,
        "inspect_exit": 3,
        "plan_exit": 0,
        "first_exit": 0,
        "second_exit": 0,
        "verify_exit": 0,
        "first_unchanged": False,
        "second_unchanged": True,
        "nginx_checked": True,
    }


def test_reconstruction_canary_is_private_under_group_writable_umask(
    tmp_path: Path,
) -> None:
    runner = FakeRunner(
        [
            completed((), out="nginx version"),
            completed((), out="syntax is ok"),
        ]
    )
    root = tmp_path / "umask-isolated"
    previous_umask = os.umask(0o002)
    try:
        result = host.reconstruction_canary(root, runner)
    finally:
        os.umask(previous_umask)
    assert result["second_unchanged"] is True
    assert root.stat().st_mode & 0o777 == 0o700
    assert (root / "nginx-prefix").stat().st_mode & 0o777 == 0o700


def test_reconstruction_canary_validates_existing_root_and_stage_payloads(
    tmp_path: Path,
) -> None:
    not_directory = tmp_path / "file"
    not_directory.write_text("x", encoding="utf-8")
    with pytest.raises(host.CalibrationError, match="real directory"):
        host.reconstruction_canary(not_directory, FakeRunner([]))

    unsafe = tmp_path / "unsafe"
    unsafe.mkdir(mode=0o775)
    unsafe.chmod(0o775)
    with pytest.raises(host.CalibrationError, match="root mode must be 0700"):
        host.reconstruction_canary(unsafe, FakeRunner([]))

    with pytest.raises(host.CalibrationError, match="canary render failed with exit 1"):
        host._require_canary_stage(
            "render",
            (1, {"command": "render", "capabilities": {}}),
        )
    with pytest.raises(host.CalibrationError, match="invalid command payload"):
        host._require_canary_stage(
            "render",
            (0, {"command": "plan", "capabilities": {}}),
        )
    with pytest.raises(host.CalibrationError, match="invalid capabilities"):
        host._require_canary_stage("render", (0, {"command": "render"}))


def test_reconstruction_canary_passes_real_nginx_when_available(
    tmp_path: Path,
) -> None:
    if shutil.which("nginx") is None:
        pytest.skip("nginx is unavailable")
    result = host.reconstruction_canary(tmp_path / "real-isolated")
    assert result["nginx_checked"] is True
    assert result["first_unchanged"] is False
    assert result["second_unchanged"] is True


def test_reconstruction_canary_rejects_nginx_failure(tmp_path: Path) -> None:
    runner = FakeRunner(
        [
            completed((), out="nginx version"),
            completed((), code=1, err="invalid candidate"),
        ]
    )
    with pytest.raises(host.CalibrationError, match="invalid candidate"):
        host.reconstruction_canary(tmp_path / "isolated", runner)


def test_cli_fixed_json_schema_and_exit_codes(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    profile: Path,
    tmp_path: Path,
) -> None:
    assert host.main(["plan", "--profile", str(profile)]) == host.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == 1
    assert payload["command"] == "plan"
    assert set(payload) == {
        "schema_version",
        "command",
        "context",
        "states",
        "capabilities",
        "probes",
        "known_issues",
        "next_actions",
    }
    assert host.main(["verify", "--profile", str(tmp_path / "missing")]) == 1
    failed = json.loads(capsys.readouterr().out)
    assert failed["capabilities"]["error"]["kind"] == "invalid"

    def fake_inspect(
        _runner: host.Runner = host._run,
        *,
        profile: Path | None = None,
        context: str = "auto",
    ) -> dict[str, object]:
        del _runner, profile, context
        return {"states": {"daemon": "indeterminate"}}

    monkeypatch.setattr(host, "inspect_host", fake_inspect)
    assert host.main(["inspect"]) == host.EXIT_PROBE
    assert json.loads(capsys.readouterr().out)["states"]["daemon"] == "indeterminate"
    with pytest.raises(SystemExit, match="2"):
        host.main(["plan"])
    usage = json.loads(capsys.readouterr().out)
    assert usage["capabilities"]["error"]["kind"] == "usage"
    output = tmp_path / "cli-candidate"
    assert (
        host.main(["render", "--profile", str(profile), "--output", str(output)]) == 0
    )
    capsys.readouterr()


def test_cli_init_path(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, codex_home: Path
) -> None:
    argv = [
        "init",
        "--profile",
        str(tmp_path / "cli.toml"),
        "--trust-model",
        "untrusted",
        "--codex-home",
        str(codex_home),
        "--data-dir",
        str(tmp_path / "data"),
        "--private-authority",
        str(tmp_path / "private" / "AGENTS.md"),
        "--state-root",
        str(tmp_path / "state"),
    ]
    assert host.main(argv) == 0
    assert json.loads(capsys.readouterr().out)["command"] == "init"


def test_subprocess_init_preserves_requested_v2_origin_mode(
    tmp_path: Path, codex_home: Path
) -> None:
    profile = tmp_path / "subprocess.toml"
    result = subprocess.run(
        [
            sys.executable,
            str(REPOSITORY_ROOT / "scripts/calibrate_ao_host.py"),
            "init",
            "--profile",
            str(profile),
            "--trust-model",
            "untrusted",
            "--codex-home",
            str(codex_home),
            "--data-dir",
            str(tmp_path / "data"),
            "--private-authority",
            str(tmp_path / "authority/AGENTS.md"),
            "--state-root",
            str(tmp_path / "state"),
            "--origin-mode",
            "preserve",
            "--storage-boundary",
            json.dumps(
                {
                    "path": str(tmp_path / "state"),
                    "kind": "host-state",
                    "recursive_search": False,
                }
            ),
            "--storage-boundary",
            json.dumps(
                {
                    "path": str(tmp_path / "aggregation"),
                    "kind": "aggregation-root",
                    "recursive_search": False,
                }
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == host.EXIT_OK, result.stdout
    terminal = tomllib.loads(profile.read_text())["dashboard"]["terminal"]
    assert terminal["origin_mode"] == "preserve"
    boundaries = tomllib.loads(profile.read_text())["storage"]["boundaries"]
    assert [boundary["kind"] for boundary in boundaries] == [
        "host-state",
        "aggregation-root",
    ]


def test_cli_init_accepts_explicit_single_user_dashboard_contract(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, codex_home: Path
) -> None:
    profile = tmp_path / "private" / "host.toml"
    state = tmp_path / "state"
    argv = [
        "init",
        "--profile",
        str(profile),
        "--trust-model",
        "trusted-single-user",
        "--codex-home",
        str(codex_home),
        "--data-dir",
        str(tmp_path / "ao-data"),
        "--private-authority",
        str(tmp_path / "authority" / "AGENTS.md"),
        "--state-root",
        str(state),
        "--enable-dashboard",
        "--dashboard-listen-host",
        "127.0.0.1",
        "--dashboard-listen-port",
        "8443",
        "--readonly-cidr",
        "203.0.113.0/24",
        "--document-root",
        str(tmp_path / "dashboard"),
        "--nginx-executable",
        "/usr/sbin/nginx",
        "--nginx-pid-file",
        str(state / "nginx.pid"),
        "--active-config",
        str(state / "active.conf"),
        "--desired-service",
        "ao-dashboard.service",
        "--rollback-service",
        "ao-dashboard-rollback.service",
        "--desired-nginx-artifact",
        str(state / "nginx.conf"),
        "--desired-service-artifact",
        str(state / "nginx.service"),
        "--terminal",
        "--client-ip",
        "203.0.113.7",
        "--client-ip",
        "203.0.113.8",
        "--origin",
        "https://console.example.test",
        "--upstream",
        "http://127.0.0.1:3001/mux",
        "--upstream-origin",
        "http://127.0.0.1:3001",
        "--origin-mode",
        "edge-validated-rewrite",
    ]
    assert host.main(argv) == host.EXIT_OK
    capsys.readouterr()
    parsed = host._load_profile(profile)
    dashboard = cast(dict[str, object], parsed["dashboard"])
    terminal = cast(dict[str, object], dashboard["terminal"])
    assert dashboard["listen_port"] == 8443
    assert terminal["allowed_client_ips"] == ["203.0.113.7", "203.0.113.8"]
    assert terminal["origin_mode"] == "edge-validated-rewrite"


def test_generated_terminal_candidate_passes_nginx_test_when_available(
    tmp_path: Path, codex_home: Path
) -> None:
    nginx = shutil.which("nginx")
    if nginx is None:
        pytest.skip("nginx is unavailable")
    state = tmp_path / "state"
    dashboard_root = tmp_path / "dashboard"
    state.mkdir(mode=0o700)
    dashboard_root.mkdir(mode=0o700)
    profile = tmp_path / "host.toml"
    host.init_profile(
        profile,
        trust_model="trusted-single-user",
        codex_home=codex_home,
        data_dir=tmp_path / "ao-data",
        private_authority=tmp_path / "authority/AGENTS.md",
        state_root=state,
        dashboard_enabled=True,
        dashboard_listen_host="::1",
        dashboard_listen_port=18443,
        readonly_cidrs=("2001:db8::/32",),
        document_root=dashboard_root,
        nginx_executable=Path(nginx),
        nginx_pid_file=state / "nginx.pid",
        active_config=state / "active.conf",
        desired_service="ao-dashboard.service",
        rollback_service="ao-dashboard-rollback.service",
        desired_nginx_artifact=state / "nginx.conf",
        desired_service_artifact=state / "nginx.service",
        terminal=True,
        client_ips=("2001:db8::7", "2001:db8::8"),
        origin="https://console.example.test",
        upstream="http://127.0.0.1:3001/mux",
        upstream_origin="http://127.0.0.1:3001",
        origin_mode="edge-validated-rewrite",
    )
    candidate = tmp_path / "candidate"
    host.render_profile(profile, candidate)
    prefix = tmp_path / "nginx-prefix"
    (prefix / "logs").mkdir(mode=0o700, parents=True)
    result = subprocess.run(
        [
            nginx,
            "-t",
            "-p",
            str(prefix) + "/",
            "-c",
            str(candidate / "nginx/ao-terminal.conf"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "listen [::1]:18443;" in (candidate / "nginx/ao-terminal.conf").read_text()


def test_preserve_origin_mode_forwards_validated_client_origin(
    tmp_path: Path, codex_home: Path
) -> None:
    profile = tmp_path / "host.toml"
    state = tmp_path / "state"
    host.init_profile(
        profile,
        trust_model="trusted-single-user",
        codex_home=codex_home,
        data_dir=tmp_path / "ao-data",
        private_authority=tmp_path / "authority/AGENTS.md",
        state_root=state,
        dashboard_enabled=True,
        dashboard_listen_host="127.0.0.1",
        dashboard_listen_port=18443,
        readonly_cidrs=("203.0.113.0/24",),
        document_root=tmp_path / "dashboard",
        nginx_executable=Path("/usr/sbin/nginx"),
        nginx_pid_file=state / "nginx.pid",
        active_config=state / "active.conf",
        desired_service="ao-dashboard.service",
        rollback_service="ao-dashboard-rollback.service",
        desired_nginx_artifact=state / "nginx.conf",
        desired_service_artifact=state / "nginx.service",
        terminal=True,
        client_ips=("203.0.113.7",),
        origin="https://console.example.test",
        upstream="http://127.0.0.1:3001",
        origin_mode="preserve",
    )
    candidate = tmp_path / "candidate"
    host.render_profile(profile, candidate)
    nginx = (candidate / "nginx/ao-terminal.conf").read_text()
    assert "proxy_set_header Origin $http_origin;" in nginx
    assert 'proxy_set_header Origin "";' not in nginx


def test_dashboard_only_profile_renders_base_nginx_and_service(
    tmp_path: Path, codex_home: Path
) -> None:
    profile = tmp_path / "host.toml"
    state = tmp_path / "state"
    host.init_profile(
        profile,
        trust_model="trusted-single-user",
        codex_home=codex_home,
        data_dir=tmp_path / "data",
        private_authority=tmp_path / "authority/AGENTS.md",
        state_root=state,
        dashboard_enabled=True,
        dashboard_listen_host="127.0.0.1",
        dashboard_listen_port=18443,
        readonly_cidrs=("203.0.113.0/24",),
        document_root=tmp_path / "dashboard",
        nginx_executable=Path("/usr/sbin/nginx"),
        nginx_pid_file=state / "nginx.pid",
        active_config=state / "active.conf",
        desired_service="ao-dashboard.service",
        rollback_service="ao-dashboard-rollback.service",
        desired_nginx_artifact=state / "nginx.conf",
        desired_service_artifact=state / "nginx.service",
    )
    assert "nginx/ao-terminal.conf" in cast(
        list[str], host.plan_profile(profile)["artifacts"]
    )
    candidate = tmp_path / "candidate"
    host.render_profile(profile, candidate)
    nginx = (candidate / "nginx/ao-terminal.conf").read_text()
    service = (candidate / "service/ao-dashboard.service").read_text()
    assert "location /api/" in nginx
    assert "location = /mux" not in nginx
    assert f"ReadWritePaths={state}" in service


@pytest.mark.parametrize("command", ["plan", "verify", "render"])
def test_disabled_terminal_malformed_shape_returns_json_invalid(
    tmp_path: Path, codex_home: Path, command: str
) -> None:
    profile = tmp_path / f"{command}.toml"
    state = tmp_path / "state"
    host.init_profile(
        profile,
        trust_model="trusted-single-user",
        codex_home=codex_home,
        data_dir=tmp_path / "data",
        private_authority=tmp_path / "authority/AGENTS.md",
        state_root=state,
        dashboard_enabled=True,
        dashboard_listen_host="127.0.0.1",
        dashboard_listen_port=18443,
        readonly_cidrs=("203.0.113.0/24",),
        document_root=tmp_path / "dashboard",
        nginx_executable=Path("/usr/sbin/nginx"),
        nginx_pid_file=state / "nginx.pid",
        active_config=state / "active.conf",
        desired_service="ao-dashboard.service",
        rollback_service="ao-dashboard-rollback.service",
        desired_nginx_artifact=state / "nginx.conf",
        desired_service_artifact=state / "nginx.service",
    )
    profile.write_text(
        profile.read_text(encoding="utf-8").replace(
            "allowed_client_ips = []", "allowed_client_ips = 7"
        ),
        encoding="utf-8",
    )
    argv = [
        sys.executable,
        str(REPOSITORY_ROOT / "scripts/calibrate_ao_host.py"),
        command,
        "--profile",
        str(profile),
    ]
    if command == "render":
        argv.extend(("--output", str(tmp_path / "candidate")))
    result = subprocess.run(argv, check=False, capture_output=True, text=True)
    payload = json.loads(result.stdout)
    assert result.returncode == host.EXIT_INVALID
    assert payload["command"] == command
    assert payload["states"]["operation"] == "unavailable"
    assert payload["capabilities"]["error"]["kind"] == "invalid"
    assert (
        "allowed_client_ips must be IP strings"
        in payload["capabilities"]["error"]["message"]
    )
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    ("replacement", "message"),
    [
        ("trusted_readonly_cidrs = 7", "must be CIDR strings"),
        ("trusted_readonly_cidrs = []", "requires trusted_readonly_cidrs"),
    ],
)
def test_dashboard_cidr_shape_render_returns_json_invalid(
    tmp_path: Path,
    codex_home: Path,
    replacement: str,
    message: str,
) -> None:
    profile = tmp_path / "dashboard.toml"
    state = tmp_path / "state"
    host.init_profile(
        profile,
        trust_model="trusted-single-user",
        codex_home=codex_home,
        data_dir=tmp_path / "data",
        private_authority=tmp_path / "authority/AGENTS.md",
        state_root=state,
        dashboard_enabled=True,
        dashboard_listen_host="127.0.0.1",
        dashboard_listen_port=18443,
        readonly_cidrs=("203.0.113.0/24",),
        document_root=tmp_path / "dashboard",
        nginx_executable=Path("/usr/sbin/nginx"),
        nginx_pid_file=state / "nginx.pid",
        active_config=state / "active.conf",
        desired_service="ao-dashboard.service",
        rollback_service="ao-dashboard-rollback.service",
        desired_nginx_artifact=state / "nginx.conf",
        desired_service_artifact=state / "nginx.service",
    )
    profile.write_text(
        profile.read_text(encoding="utf-8").replace(
            'trusted_readonly_cidrs = ["203.0.113.0/24"]',
            replacement,
        ),
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(REPOSITORY_ROOT / "scripts/calibrate_ao_host.py"),
            "render",
            "--profile",
            str(profile),
            "--output",
            str(tmp_path / "candidate"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert result.returncode == host.EXIT_INVALID
    assert payload["capabilities"]["error"]["kind"] == "invalid"
    assert message in payload["capabilities"]["error"]["message"]
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("trust_model", 7, "trust_model must be a string"),
        ("allowed_client_ips", 7, "allowed_client_ips must be IP strings"),
        ("allowed_client_ips", ["bad"], "allowed_client_ips must be valid IPs"),
        (
            "require_authentication_if",
            7,
            "require_authentication_if must be strings",
        ),
        ("origin_mode", 7, "origin_mode must be a string"),
    ],
)
def test_disabled_terminal_all_shapes_fail_closed(
    field: str, value: object, message: str
) -> None:
    terminal: dict[str, object] = {
        "desired_enabled": False,
        "trust_model": "untrusted",
        "allowed_client_ips": [],
        "allowed_origin": "",
        "path": "/mux",
        "upstream": "",
        "upstream_origin": "",
        "require_authentication_if": [],
        "origin_mode": "preserve",
    }
    terminal[field] = value
    with pytest.raises(host.CalibrationError, match=message):
        host._validate_terminal_shapes(terminal)


@pytest.mark.parametrize("schema_version", [1, 2])
@pytest.mark.parametrize(
    "field",
    ["loopback_base_url", "upstream", "upstream_origin"],
)
def test_loopback_port_zero_is_rejected_before_plan_or_render(
    tmp_path: Path, schema_version: int, field: str
) -> None:
    source = tmp_path / "source.toml"
    source.write_text(LEGACY_V1_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    source.chmod(0o600)
    if schema_version == 1:
        content = source.read_text(encoding="utf-8")
    else:
        content = host._toml(host._canonical_v2(host._load_profile(source)))
    originals = {
        "loopback_base_url": 'loopback_base_url = "http://127.0.0.1:3001"',
        "upstream": 'upstream = "http://127.0.0.1:3001/mux"',
        "upstream_origin": 'upstream_origin = "http://127.0.0.1:3001"',
    }
    invalid = tmp_path / f"v{schema_version}-{field}.toml"
    invalid.write_text(
        content.replace(originals[field], originals[field].replace(":3001", ":0")),
        encoding="utf-8",
    )
    invalid.chmod(0o600)
    with pytest.raises(host.CalibrationError, match="HTTP loopback URL"):
        host.plan_profile(invalid)
    with pytest.raises(host.CalibrationError, match="HTTP loopback URL"):
        host.render_profile(invalid, tmp_path / f"candidate-v{schema_version}-{field}")


@pytest.mark.parametrize(
    ("field", "suffix"),
    [
        ("loopback_base_url", "?"),
        ("loopback_base_url", "#"),
        ("upstream", "#"),
    ],
)
def test_empty_url_delimiters_are_rejected_before_render(
    tmp_path: Path, field: str, suffix: str
) -> None:
    originals = {
        "loopback_base_url": 'loopback_base_url = "http://127.0.0.1:3001"',
        "upstream": 'upstream = "http://127.0.0.1:3001/mux"',
    }
    original = originals[field]
    profile = tmp_path / "empty-delimiter.toml"
    profile.write_text(
        LEGACY_V1_FIXTURE.read_text(encoding="utf-8").replace(
            original,
            f'{original[:-1]}{suffix}"',
        ),
        encoding="utf-8",
    )
    profile.chmod(0o600)
    with pytest.raises(host.CalibrationError, match="HTTP loopback URL"):
        host.plan_profile(profile)
    with pytest.raises(host.CalibrationError, match="HTTP loopback URL"):
        host.render_profile(profile, tmp_path / "candidate")


def test_module_entrypoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["calibrate_ao_host.py", "plan"])
    with pytest.raises(SystemExit, match="2"):
        runpy.run_module("scripts.calibrate_ao_host", run_name="__main__")


def test_run_and_json_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CALIBRATION_TEST_MARKER", "yes")
    result = host._run(
        (
            "python",
            "-c",
            "import os; print(os.environ['CALIBRATION_TEST_MARKER'])",
        )
    )
    assert result.stdout.strip() == "yes"
    assert host._json_object("[]") == {}
    assert host._json_object('{"value": 1.5}') == {"value": 1.5}
    for non_finite in ("NaN", "Infinity", "-Infinity", "1e400"):
        assert host._json_object(f'{{"value": {non_finite}}}') == {}
    assert host._required_subset({"name": "x", "extra": 1}, {"name": str})
    assert not host._required_subset({}, {"name": str})


def test_pure_state_and_issue_evaluators() -> None:
    status: dict[str, object] = {
        "state": "ready",
        "pid": 42,
        "port": 3001,
        "health": "ok",
        "ready": "ready",
    }
    health = {
        "status": "ok",
        "service": "agent-orchestrator-daemon",
        "pid": 42,
        "executablePath": "/opt/example/ao",
        "workingDirectory": "/opt/example/work",
        "startupWorkingDirectory": "/opt/example/start",
    }
    ready = {
        "status": "ready",
        "service": "agent-orchestrator-daemon",
        "pid": 42,
        "executablePath": "/opt/example/ao",
        "workingDirectory": "/opt/example/work",
        "startupWorkingDirectory": "/opt/example/start",
    }
    probes = {
        "ao-version": host.Evidence("ao-version", "sandbox", "pass", "ao 1"),
        "systemd-active": host.Evidence("systemd-active", "host", "pass", "active"),
        "main-pid": host.Evidence("main-pid", "host", "pass", "42"),
        "status": host.Evidence("status", "host", "pass", "ready"),
        "healthz": host.Evidence("healthz", "daemon", "pass", "ok"),
        "readyz": host.Evidence("readyz", "daemon", "pass", "ok"),
        "dashboard": host.Evidence("dashboard", "daemon", "pass", "ok"),
        "mux": host.Evidence("mux", "daemon", "fail", "404"),
    }
    assert (
        host.evaluate_daemon_state(
            probes,
            context="host",
            status=status,
            health=health,
            ready=ready,
        )
        == "ready"
    )
    incomplete_health = dict(health)
    incomplete_health.pop("executablePath")
    assert (
        host.evaluate_daemon_state(
            probes,
            context="host",
            status=status,
            health=incomplete_health,
            ready=ready,
        )
        == "indeterminate"
    )
    missing_ao = dict(probes)
    missing_ao["ao-version"] = host.Evidence(
        "ao-version", "host", "fail", "FileNotFoundError: missing"
    )
    assert (
        host.evaluate_daemon_state(
            missing_ao,
            context="host",
            status=status,
            health=health,
            ready=ready,
        )
        == "not_installed"
    )
    missing_ao["healthz"] = host.Evidence("healthz", "daemon", "fail", "missing")
    assert (
        host.evaluate_daemon_state(
            missing_ao,
            context="host",
            status=status,
            health=health,
            ready=ready,
        )
        == "not_installed"
    )
    denied_ao = dict(missing_ao)
    denied_ao["ao-version"] = host.Evidence(
        "ao-version", "host", "fail", "permission denied"
    )
    denied_ao["healthz"] = probes["healthz"]
    assert (
        host.evaluate_daemon_state(
            denied_ao,
            context="host",
            status=status,
            health=health,
            ready=ready,
        )
        == "indeterminate"
    )
    denied_ao["healthz"] = missing_ao["healthz"]
    assert (
        host.evaluate_daemon_state(
            denied_ao,
            context="host",
            status=status,
            health=health,
            ready=ready,
        )
        == "indeterminate"
    )
    failed_main_pid = dict(probes)
    failed_main_pid["main-pid"] = host.Evidence("main-pid", "host", "fail", "42")
    assert (
        host.evaluate_daemon_state(
            failed_main_pid,
            context="host",
            status=status,
            health=health,
            ready=ready,
        )
        == "indeterminate"
    )
    for invalid_port in (True, -1, 0, 3002, 65536):
        invalid_status = dict(status)
        invalid_status["port"] = invalid_port
        assert (
            host.evaluate_daemon_state(
                probes,
                context="host",
                status=invalid_status,
                health=health,
                ready=ready,
            )
            == "indeterminate"
        )
    invalid_status = dict(status)
    invalid_status["pid"] = True
    assert (
        host.evaluate_daemon_state(
            probes,
            context="host",
            status=invalid_status,
            health=health,
            ready=ready,
        )
        == "indeterminate"
    )
    unicode_main_pid = dict(probes)
    unicode_main_pid["main-pid"] = host.Evidence(
        "main-pid", "host", "pass", "\uff14\uff12"
    )
    assert (
        host.evaluate_daemon_state(
            unicode_main_pid,
            context="host",
            status=status,
            health=health,
            ready=ready,
        )
        == "indeterminate"
    )
    unhashable_status = dict(status)
    unhashable_status["state"] = []
    assert (
        host.evaluate_daemon_state(
            probes,
            context="host",
            status=unhashable_status,
            health=health,
            ready=ready,
        )
        == "indeterminate"
    )
    for identity_field in (
        "executablePath",
        "workingDirectory",
        "startupWorkingDirectory",
    ):
        empty_health = dict(health)
        empty_ready = dict(ready)
        empty_health[identity_field] = ""
        empty_ready[identity_field] = ""
        assert (
            host.evaluate_daemon_state(
                probes,
                context="host",
                status=status,
                health=empty_health,
                ready=empty_ready,
            )
            == "indeterminate"
        )
    unavailable = dict(probes)
    unavailable["systemd-active"] = host.Evidence(
        "systemd-active", "host", "fail", "inactive"
    )
    unavailable["healthz"] = host.Evidence("healthz", "daemon", "fail", "down")
    unavailable["readyz"] = host.Evidence("readyz", "daemon", "fail", "down")
    assert (
        host.evaluate_daemon_state(
            unavailable,
            context="host",
            status=status,
            health=health,
            ready=ready,
        )
        == "unavailable"
    )
    assert (
        host.evaluate_delivery_state(
            probes,
            daemon_state="ready",
            dashboard_enabled=True,
            terminal_enabled=True,
        )
        == "degraded"
    )
    assert (
        host.evaluate_delivery_state(
            probes,
            daemon_state="ready",
            dashboard_enabled=False,
            terminal_enabled=False,
        )
        == "not_applicable"
    )
    assert (
        host.evaluate_delivery_state(
            probes,
            daemon_state="indeterminate",
            dashboard_enabled=True,
            terminal_enabled=True,
        )
        == "indeterminate"
    )
    passing_mux = dict(probes)
    passing_mux["mux"] = host.Evidence("mux", "daemon", "pass", "101")
    assert (
        host.evaluate_delivery_state(
            passing_mux,
            daemon_state="ready",
            dashboard_enabled=True,
            terminal_enabled=True,
        )
        == "ready"
    )
    unknown_mux = dict(passing_mux)
    unknown_mux["mux"] = host.Evidence("mux", "host", "unknown", "source unknown")
    assert (
        host.evaluate_delivery_state(
            unknown_mux,
            daemon_state="ready",
            dashboard_enabled=True,
            terminal_enabled=True,
        )
        == "indeterminate"
    )
    failed_dashboard = dict(passing_mux)
    failed_dashboard["dashboard"] = host.Evidence("dashboard", "daemon", "fail", "down")
    assert (
        host.evaluate_delivery_state(
            failed_dashboard,
            daemon_state="ready",
            dashboard_enabled=True,
            terminal_enabled=False,
        )
        == "degraded"
    )
    assert (
        host.evaluate_delivery_state(
            probes,
            daemon_state="ready",
            dashboard_enabled=True,
            terminal_enabled=False,
        )
        == "ready"
    )
    assert not host._version_before(None, (2, 38))
    assert not host._doctor_checks_structurally_valid({"ok": True})
    invalid_doctor_level: list[object] = []
    assert host._doctor_failure_classes(
        {"checks": [{"name": "config", "level": invalid_doctor_level}]}
    ) == (False, False)
    issues = host.evaluate_known_issues(
        probes=probes,
        status={"state": "stale", "extra": "kept"},
        doctor={"ok": False, "checks": []},
        capabilities={
            "glibc_version": "2.37",
            "tmux_version": "3.4",
            "codex_home_compatible": False,
            "effective_process_containment": "unverified",
        },
        terminal={
            "desired_enabled": True,
            "origin_mode": "rewrite",
        },
    )
    assert issues == [
        "AO-HOST-CONTEXT-MISMATCH",
        "AO-GLIBC-INCOMPATIBLE",
        "AO-TMUX-TOO-OLD",
        "AO-CODEX-HOME-CONFLICT",
        "AO-DASHBOARD-MUX-NOT-PROXIED",
        "AO-DASHBOARD-UPSTREAM-ORIGIN-REWRITE",
        "AO-PROCESS-CONTAINMENT-UNVERIFIED",
    ]
    malformed_issues = host.evaluate_known_issues(
        probes=probes,
        status={"state": []},
        doctor={"ok": True, "checks": []},
        capabilities={
            "glibc_version": "2.38",
            "tmux_version": "3.5",
            "codex_home_compatible": True,
            "effective_process_containment": "systemd-scope-verified",
        },
        terminal=None,
    )
    assert malformed_issues == ["AO-HOST-CONTEXT-MISMATCH"]


def test_probe_oserror_becomes_failed_evidence() -> None:
    def missing(_command: Sequence[str]) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError("missing-tool")

    evidence = host._probe(missing, "sandbox", "ao-version", ("missing",))

    assert evidence.status == "fail"
    assert "FileNotFoundError" in evidence.detail

    def timed_out(_command: Sequence[str]) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(("missing",), 10)

    timeout = host._probe(timed_out, "sandbox", "ao-version", ("missing",))
    assert timeout.status == "fail"
    assert "TimeoutExpired" in timeout.detail


def test_mux_probe_requires_bounded_http_101_handshake() -> None:
    handshake = host._probe_mux(
        FakeRunner([completed((), code=28, out=websocket_response())]),
        "daemon",
        ("curl",),
    )
    generic = host._probe_mux(
        FakeRunner([completed((), out="200")]), "daemon", ("curl",)
    )
    incomplete = host._probe_mux(
        FakeRunner([completed((), out="HTTP/1.1 101 Switching Protocols")]),
        "daemon",
        ("curl",),
    )
    assert handshake.status == "pass"
    assert (
        host._probe_mux(
            FakeRunner(
                [
                    completed(
                        (),
                        out=websocket_response().replace(
                            "Connection: Upgrade",
                            "malformed-header\r\nConnection: Upgrade",
                        ),
                    )
                ]
            ),
            "daemon",
            ("curl",),
        ).status
        == "fail"
    )
    for malformed_response in (
        websocket_response().replace("Upgrade:", "Upgrade :"),
        websocket_response().replace("Upgrade:", " Upgrade:"),
        websocket_response().replace(
            "Connection: Upgrade",
            "Bad Name: value\r\nConnection: Upgrade",
        ),
        websocket_response().replace(
            "Connection: Upgrade",
            "X-Test: value\x00tail\r\nConnection: Upgrade",
        ),
        websocket_response().replace(
            "HTTP/1.1 101",
            "HTTP/1.1\t101",
        ),
    ):
        assert (
            host._probe_mux(
                FakeRunner([completed((), out=malformed_response)]),
                "daemon",
                ("curl",),
            ).status
            == "fail"
        )
    for false_line_break in ("\u0085", "\u2028", "\v", "\f"):
        spliced_headers = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            f"X-Test: value{false_line_break}"
            f"Upgrade: websocket{false_line_break}"
            f"Connection: Upgrade{false_line_break}"
            "Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=\r\n\r\n"
        )
        assert (
            host._probe_mux(
                FakeRunner([completed((), out=spliced_headers)]),
                "daemon",
                ("curl",),
            ).status
            == "fail"
        )
    assert generic.status == "fail"
    assert incomplete.status == "fail"
    header_only_200 = websocket_response().replace(
        "HTTP/1.1 101 Switching Protocols", "HTTP/1.1 200 OK"
    )
    for transcript in (
        f"HTTP/1.1 101 Switching Protocols\r\n\r\n{header_only_200}",
        f"{header_only_200}\r\nHTTP/1.1 101 Switching Protocols\r\n\r\n",
    ):
        assert (
            host._probe_mux(
                FakeRunner([completed((), out=transcript)]), "daemon", ("curl",)
            ).status
            == "fail"
        )
    assert (
        host._probe_mux(
            FakeRunner(
                [
                    completed(
                        (),
                        out=f"HTTP/1.1 200 Connection established\r\n\r\n"
                        f"{websocket_response()}",
                    )
                ]
            ),
            "daemon",
            ("curl",),
        ).status
        == "pass"
    )
    assert (
        host._probe_mux(
            FakeRunner([completed((), code=22, out=websocket_response())]),
            "daemon",
            ("curl",),
        ).status
        == "fail"
    )
    assert (
        host._probe_mux(
            FakeRunner(
                [
                    completed(
                        (),
                        out=websocket_response().replace("HTTP/1.1", "HTTP/2"),
                    )
                ]
            ),
            "daemon",
            ("curl",),
        ).status
        == "fail"
    )
    for connection in ("X-Upgrade", "not-upgrade"):
        assert (
            host._probe_mux(
                FakeRunner(
                    [
                        completed(
                            (),
                            out=websocket_response().replace(
                                "Connection: Upgrade",
                                f"Connection: {connection}",
                            ),
                        )
                    ]
                ),
                "daemon",
                ("curl",),
            ).status
            == "fail"
        )
    duplicate_accept = websocket_response().replace(
        "Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=",
        "Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=\r\n"
        "Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=",
    )
    assert (
        host._probe_mux(
            FakeRunner([completed((), out=duplicate_accept)]),
            "daemon",
            ("curl",),
        ).status
        == "fail"
    )
    wrong_case = websocket_response().replace(
        "s3pPLMBiTxaQ9kYGzzhZRbK+xOo=", "S3pPLMBiTxaQ9kYGzzhZRbK+xOo="
    )
    assert (
        host._probe_mux(
            FakeRunner([completed((), out=wrong_case)]), "daemon", ("curl",)
        ).status
        == "fail"
    )
    missing = host._probe_mux(
        lambda _command: (_ for _ in ()).throw(FileNotFoundError("curl")),
        "daemon",
        ("curl",),
    )
    assert missing.status == "fail"
    missing_dashboard = host._probe_dashboard(
        lambda _command: (_ for _ in ()).throw(FileNotFoundError("curl")),
        "host",
        ("curl",),
    )
    assert missing_dashboard.status == "fail"


def test_real_curl_mux_probe_sends_rfc6455_headers() -> None:
    requests: list[str] = []

    class Handler(socketserver.BaseRequestHandler):
        def handle(self) -> None:
            request = self.request.recv(8192).decode("ascii")
            requests.append(request)
            self.request.sendall(
                b"HTTP/1.1 101 Switching Protocols\r\n"
                b"Connection: Upgrade\r\n"
                b"Upgrade: websocket\r\n"
                b"X-Test: \xff\r\n"
                b"Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=\r\n\r\n"
            )

    with socketserver.TCPServer(("127.0.0.1", 0), Handler) as server:
        port = server.server_address[1]
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        evidence = host._probe_mux(
            host._run,
            "daemon",
            host._mux_probe_command(
                f"http://127.0.0.1:{port}", "https://console.example.test"
            ),
        )
        thread.join(timeout=3)
    assert evidence.status == "pass"
    request = requests[0]
    assert "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" in request
    assert "Sec-WebSocket-Version: 13" in request
    assert host._mux_probe_command("http://127.0.0.1:3001", "https://example.test")[
        :3
    ] == ("curl", "--noproxy", "*")


def test_sandbox_probe_ownership_cannot_claim_host_ready() -> None:
    report = host.inspect_host(FakeRunner(inspect_responses()), context="sandbox")
    states = cast(dict[str, object], report["states"])
    assert states["daemon"] == "indeterminate"
    probes = cast(list[dict[str, object]], report["probes"])
    owned = {probe["id"]: probe["owner"] for probe in probes}
    for probe_id in (
        "systemd-active",
        "doctor",
        "healthz",
        "readyz",
        "dashboard",
        "mux",
    ):
        assert owned[probe_id] == "sandbox"


def test_inspect_rejects_missing_explicit_profile(tmp_path: Path) -> None:
    with pytest.raises(host.CalibrationError, match="does not exist"):
        host.inspect_host(FakeRunner([]), profile=tmp_path / "missing.toml")


def test_inspect_error_envelope_preserves_requested_context(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    assert (
        host.main(
            [
                "inspect",
                "--context",
                "host",
                "--profile",
                str(tmp_path / "missing.toml"),
            ]
        )
        == host.EXIT_INVALID
    )
    assert json.loads(capsys.readouterr().out)["context"] == "host"


def test_inspect_uses_profile_ao_cli(tmp_path: Path) -> None:
    profile = tmp_path / "host.toml"
    profile.write_text(
        LEGACY_V1_FIXTURE.read_text()
        .replace('cli = "ao"', 'cli = "/opt/example/ao-wrapper"')
        .replace("listen_port = 3001", "listen_port = 8443")
        .replace(
            'trusted_readonly_cidrs = ["203.0.113.0/24"]',
            'trusted_readonly_cidrs = ["127.0.0.1/32"]',
        )
        .replace(
            'allowed_client_ips = ["203.0.113.7", "203.0.113.8"]',
            'allowed_client_ips = ["127.0.0.1"]',
        ),
        encoding="utf-8",
    )
    profile.chmod(0o600)
    responses = inspect_responses()
    responses[-1] = completed((), code=28, out=websocket_response())
    runner = FakeRunner(responses)

    report = host.inspect_host(runner, profile=profile, context="host")

    assert runner.commands[0] == ("/opt/example/ao-wrapper", "version")
    assert runner.commands[6] == (
        "/opt/example/ao-wrapper",
        "status",
        "--json",
    )
    assert runner.commands[7] == (
        "/opt/example/ao-wrapper",
        "doctor",
        "--json",
    )
    assert runner.commands[10] == (
        "curl",
        "--noproxy",
        "*",
        "--interface",
        "127.0.0.1",
        "-fsS",
        "http://127.0.0.1:8443/dashboard-health",
    )
    assert runner.commands[11][-13:] == (
        "-H",
        "Origin: https://console.example.test",
        "-H",
        "Connection: Upgrade",
        "-H",
        "Upgrade: websocket",
        "-H",
        "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==",
        "-H",
        "Sec-WebSocket-Version: 13",
        "--interface",
        "127.0.0.1",
        "http://127.0.0.1:8443/mux",
    )
    assert runner.commands[8][:3] == ("curl", "--noproxy", "*")
    assert runner.commands[9][:3] == ("curl", "--noproxy", "*")
    assert cast(dict[str, object], report["states"])["delivery"] == "ready"
    assert cast(list[dict[str, object]], report["probes"])[0]["owner"] == "host"


def test_sandbox_ao_version_failure_cannot_declare_not_installed() -> None:
    responses = inspect_responses()
    responses[0] = completed((), code=127, err="ao missing in sandbox")
    report = host.inspect_host(FakeRunner(responses), context="sandbox")
    assert cast(dict[str, object], report["states"])["daemon"] == "indeterminate"


@pytest.mark.parametrize(
    ("replacement", "message"),
    [
        (
            'loopback_base_url = "https://example.test:3001"',
            "HTTP loopback URL",
        ),
        ("health_path = 1", "ao.health_path must be a string"),
        ('data_dir = "../data"', "ao.data_dir must be an absolute path"),
        ('cli = "relative/wrapper"', "ao.cli path must be absolute"),
    ],
)
def test_profile_probe_and_path_fields_fail_closed(
    tmp_path: Path, replacement: str, message: str
) -> None:
    originals = {
        "loopback_base_url": 'loopback_base_url = "http://127.0.0.1:3001"',
        "health_path": 'health_path = "/healthz"',
        "data_dir": 'data_dir = "/opt/example/ao-data"',
        "cli": 'cli = "ao"',
    }
    key = replacement.split(" =", maxsplit=1)[0]
    profile = tmp_path / "host.toml"
    profile.write_text(
        V1_PROFILE.replace(originals[key], replacement),
        encoding="utf-8",
    )
    profile.chmod(0o600)
    with pytest.raises(host.CalibrationError, match=message):
        host.plan_profile(profile)


@pytest.mark.parametrize(
    ("field", "original"),
    [
        ("daemon_service", 'daemon_service = "agent-orchestrator.service"'),
        ("desired_service", 'desired_service = "ao-dashboard.service"'),
        ("rollback_service", 'rollback_service = "ao-dashboard-rollback.service"'),
    ],
)
@pytest.mark.parametrize("unsafe", ["--system", "--system.service", "/tmp/x.service"])
def test_service_fields_require_safe_unit_identifiers(
    tmp_path: Path, field: str, original: str, unsafe: str
) -> None:
    profile = tmp_path / "host.toml"
    profile.write_text(
        V1_PROFILE.replace(original, f'{field} = "{unsafe}"'),
        encoding="utf-8",
    )
    profile.chmod(0o600)
    with pytest.raises(host.CalibrationError, match="systemd service unit"):
        host.plan_profile(profile)


@pytest.mark.parametrize("value", ["true", "1.0"])
def test_schema_version_requires_exact_integer(tmp_path: Path, value: str) -> None:
    profile = tmp_path / "host.toml"
    profile.write_text(f"schema_version = {value}\n" + V1_PROFILE, encoding="utf-8")
    profile.chmod(0o600)
    with pytest.raises(host.CalibrationError, match="unsupported schema_version"):
        host.plan_profile(profile)


@pytest.mark.parametrize(
    "origin",
    [
        'https://host"; return 200; #',
        "https://host name",
        "https://user@example.test",
        "https://example.test/path",
        "https://example{test}",
        "https://example.test?",
    ],
)
def test_origin_rejects_nginx_metacharacters_and_non_origin_forms(
    origin: str,
) -> None:
    with pytest.raises(host.CalibrationError, match="exact Origin"):
        host._validate_origin(origin, "terminal Origin")


def test_url_validators_reject_types_and_invalid_ports() -> None:
    with pytest.raises(host.CalibrationError, match="must be a string"):
        host._validate_loopback_url(1, "base")
    with pytest.raises(host.CalibrationError, match="valid loopback URL"):
        host._validate_loopback_url("http://127.0.0.1:bad", "base")
    with pytest.raises(host.CalibrationError, match="exact Origin"):
        host._validate_origin(1, "origin")
    with pytest.raises(host.CalibrationError, match="exact Origin"):
        host._validate_origin("https://example.test:bad", "origin")
    with pytest.raises(host.CalibrationError, match="exact Origin"):
        host._validate_origin("https://example.test:0", "origin")
    with pytest.raises(host.CalibrationError, match="whitespace or controls"):
        host._validate_loopback_url("http://127.0.0.1:3001\n", "base")


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        (
            'data_dir = "/opt/example/ao-data"',
            'data_dir = "/opt/example/ao-data;evil"',
            "unsafe configuration syntax",
        ),
        (
            'upstream_origin = "http://127.0.0.1:3001"',
            'upstream_origin = "https://external.example.test"',
            "HTTP loopback URL",
        ),
        (
            'loopback_base_url = "http://127.0.0.1:3001"',
            'loopback_base_url = "http://127.0.0.1:3001\\t"',
            "whitespace or controls",
        ),
    ],
)
def test_v1_rejects_interpolated_configuration_injection(
    tmp_path: Path, old: str, new: str, message: str
) -> None:
    profile = tmp_path / "host.toml"
    profile.write_text(
        LEGACY_V1_FIXTURE.read_text().replace(old, new), encoding="utf-8"
    )
    profile.chmod(0o600)
    with pytest.raises(host.CalibrationError, match=message):
        host.plan_profile(profile)


def test_safe_path_rejects_symlink_in_any_ancestor(tmp_path: Path) -> None:
    real = tmp_path / "real"
    (real / "child").mkdir(parents=True)
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(host.CalibrationError, match="symlink"):
        host._safe_path(link / "child" / "output", may_create=True)


def test_unchanged_render_rejects_insecure_modes(tmp_path: Path, profile: Path) -> None:
    output = tmp_path / "candidate"
    host.render_profile(profile, output)
    agents = output / "AGENTS.md"
    agents.chmod(0o644)
    with pytest.raises(host.CalibrationError, match="mode must be 0600"):
        host.render_profile(profile, output)
    agents.chmod(0o600)


def test_v2_preserves_storage_boundaries(profile: Path, tmp_path: Path) -> None:
    extra = tmp_path / "extra-boundary"
    content = profile.read_text(encoding="utf-8")
    content = content.replace(
        "boundaries = [",
        (
            "boundaries = [{ "
            f'path = {json.dumps(str(extra))}, kind = "shared", '
            "recursive_search = false }, "
        ),
    )
    profile.write_text(content, encoding="utf-8")
    parsed = host._load_profile(profile)

    canonical = host._canonical_v2(parsed)

    storage = cast(dict[str, object], canonical["storage"])
    boundaries = cast(list[dict[str, object]], storage["boundaries"])
    assert any(boundary["path"] == str(extra) for boundary in boundaries)


def test_v2_terminal_requires_read_only_dashboard(
    tmp_path: Path, codex_home: Path
) -> None:
    profile = tmp_path / "host.toml"
    host.init_profile(
        profile,
        trust_model="trusted-single-user",
        codex_home=codex_home,
        data_dir=tmp_path / "data",
        private_authority=tmp_path / "private" / "AGENTS.md",
        state_root=tmp_path / "state",
        dashboard_enabled=True,
        dashboard_listen_host="127.0.0.1",
        dashboard_listen_port=8443,
        readonly_cidrs=("203.0.113.0/24",),
        document_root=tmp_path / "dashboard",
        nginx_executable=Path("/usr/sbin/nginx"),
        nginx_pid_file=tmp_path / "state/nginx.pid",
        active_config=tmp_path / "state/active.conf",
        desired_service="ao-dashboard.service",
        rollback_service="ao-dashboard-rollback.service",
        desired_nginx_artifact=tmp_path / "state/nginx.conf",
        desired_service_artifact=tmp_path / "state/nginx.service",
        terminal=True,
        client_ips=("203.0.113.9",),
        origin="https://console.example.test",
        upstream="http://127.0.0.1:3001/mux",
        upstream_origin="http://127.0.0.1:3001",
        origin_mode="edge-validated-rewrite",
    )
    profile.write_text(
        profile.read_text(encoding="utf-8").replace(
            'mode = "read-only"', 'mode = "write"'
        ),
        encoding="utf-8",
    )
    with pytest.raises(host.CalibrationError, match="must be read-only"):
        host.verify_profile(profile)


@pytest.mark.parametrize(
    ("original", "replacement", "message"),
    [
        (
            'runtime_owner = "systemd-user"',
            'runtime_owner = "process"',
            "runtime_owner",
        ),
        (
            'process_containment = "legacy"',
            'process_containment = "profile-certified"',
            "process_containment",
        ),
        ('mode = "read-only"', 'mode = "disabled"', "terminal is enabled"),
        ('mode = "read-only"', 'mode = ["read-only"]', "must be read-only"),
    ],
)
def test_v2_runtime_contract_values_fail_closed(
    tmp_path: Path,
    codex_home: Path,
    original: str,
    replacement: str,
    message: str,
) -> None:
    profile = tmp_path / "host.toml"
    host.init_profile(
        profile,
        trust_model="trusted-single-user",
        codex_home=codex_home,
        data_dir=tmp_path / "data",
        private_authority=tmp_path / "private" / "AGENTS.md",
        state_root=tmp_path / "state",
        dashboard_enabled=True,
        dashboard_listen_host="127.0.0.1",
        dashboard_listen_port=8443,
        readonly_cidrs=("203.0.113.0/24",),
        document_root=tmp_path / "dashboard",
        nginx_executable=Path("/usr/sbin/nginx"),
        nginx_pid_file=tmp_path / "state/nginx.pid",
        active_config=tmp_path / "state/active.conf",
        desired_service="ao-dashboard.service",
        rollback_service="ao-dashboard-rollback.service",
        desired_nginx_artifact=tmp_path / "state/nginx.conf",
        desired_service_artifact=tmp_path / "state/nginx.service",
        terminal=True,
        client_ips=("203.0.113.9",),
        origin="https://console.example.test",
        upstream="http://127.0.0.1:3001/mux",
        upstream_origin="http://127.0.0.1:3001",
        origin_mode="edge-validated-rewrite",
    )
    profile.write_text(
        profile.read_text(encoding="utf-8").replace(original, replacement),
        encoding="utf-8",
    )
    with pytest.raises(host.CalibrationError, match=message):
        host.verify_profile(profile)


def test_external_doctor_failure_degrades_delivery() -> None:
    doctor = json.dumps(
        {
            "ok": False,
            "checks": [
                {
                    "name": "github-token",
                    "level": "FAIL",
                    "message": "authentication failed",
                }
            ],
        }
    )
    report = host.inspect_host(
        FakeRunner(inspect_responses(doctor=doctor)), context="host"
    )
    states = cast(dict[str, object], report["states"])
    assert states == {"daemon": "ready", "delivery": "degraded"}


def test_nonzero_external_doctor_json_degrades_without_blocking_daemon() -> None:
    doctor = json.dumps(
        {
            "ok": False,
            "checks": [{"name": "github-token", "level": "FAIL"}],
        }
    )
    responses = inspect_responses(doctor=doctor)
    responses[7] = completed((), code=1, out=doctor)
    report = host.inspect_host(FakeRunner(responses), context="host")
    assert cast(dict[str, object], report["states"]) == {
        "daemon": "ready",
        "delivery": "degraded",
    }


def test_doctor_three_way_classification_matrix() -> None:
    readonly = json.dumps(
        {
            "ok": False,
            "checks": [
                {
                    "name": "data-dir-write",
                    "level": "FAIL",
                    "message": "read-only file system",
                }
            ],
        }
    )
    sandbox = host.inspect_host(
        FakeRunner(inspect_responses(doctor=readonly)), context="sandbox"
    )
    assert cast(dict[str, object], sandbox["states"])["daemon"] == "indeterminate"
    assert "AO-HOST-CONTEXT-MISMATCH" in cast(list[str], sandbox["known_issues"])

    core = host.inspect_host(
        FakeRunner(inspect_responses(doctor=readonly)), context="host"
    )
    assert cast(dict[str, object], core["states"])["daemon"] == "indeterminate"
    assert "AO-HOST-CONTEXT-MISMATCH" not in cast(list[str], core["known_issues"])

    external = json.dumps(
        {
            "ok": False,
            "checks": [{"name": "future-auth-integration", "level": "ERROR"}],
        }
    )
    degraded = host.inspect_host(
        FakeRunner(inspect_responses(doctor=external)), context="host"
    )
    assert cast(dict[str, object], degraded["states"]) == {
        "daemon": "ready",
        "delivery": "degraded",
    }


def test_auto_remains_indeterminate_without_explicit_host_attestation() -> None:
    report = host.inspect_host(FakeRunner(inspect_responses()), context="auto")
    assert cast(dict[str, object], report["states"])["daemon"] == "indeterminate"
    assert "AO-HOST-CONTEXT-MISMATCH" in cast(list[str], report["known_issues"])
    probes = cast(list[dict[str, object]], report["probes"])
    assert {
        cast(str, probe["owner"])
        for probe in probes
        if probe["id"] in {"systemd-active", "status", "doctor", "healthz", "readyz"}
    } == {"sandbox"}


def test_endpoint_identity_fields_must_match() -> None:
    responses = inspect_responses()
    ready = json.loads(responses[9].stdout)
    ready["workingDirectory"] = "/opt/example/other-work"
    responses[9] = completed((), out=json.dumps(ready))
    report = host.inspect_host(FakeRunner(responses), context="host")
    assert cast(dict[str, object], report["states"])["daemon"] == "indeterminate"


@pytest.mark.parametrize("doctor", ["not-json", "[]"])
def test_unreadable_doctor_cannot_prove_host_ready(doctor: str) -> None:
    report = host.inspect_host(
        FakeRunner(inspect_responses(doctor=doctor)),
        context="host",
    )
    assert cast(dict[str, object], report["states"])["daemon"] == "indeterminate"


@pytest.mark.parametrize(
    "checks",
    [
        ["not-an-object"],
        [{"name": 7, "level": "PASS"}],
        [{"name": "config", "level": 7}],
        [{"name": "", "level": "PASS"}],
        [{"name": "   ", "level": "PASS"}],
        [{"name": "config", "level": ""}],
        [{"name": "config", "level": "MAYBE"}],
    ],
)
def test_malformed_doctor_checks_cannot_prove_host_ready(
    checks: list[object],
) -> None:
    doctor = json.dumps(
        {
            "ok": True,
            "checks": checks,
            "extension": {"future": "preserved"},
        }
    )
    report = host.inspect_host(
        FakeRunner(inspect_responses(doctor=doctor)),
        context="host",
    )
    assert cast(dict[str, object], report["states"])["daemon"] == "indeterminate"
    capabilities = cast(dict[str, object], report["capabilities"])
    assert capabilities["doctor_required_subset_valid"] is False
    assert cast(dict[str, object], capabilities["ao_doctor"])["extension"] == {
        "future": "preserved"
    }


@pytest.mark.parametrize(
    "doctor",
    [
        {"ok": True, "checks": [], "failures": -1},
        {"ok": True, "checks": [], "failures": True},
        {"ok": True, "checks": [], "failures": None},
        {
            "ok": True,
            "checks": [{"name": "config", "level": "FAIL"}],
            "failures": 1,
        },
        {
            "ok": False,
            "checks": [{"name": "config", "level": "FAIL"}],
            "failures": 0,
        },
    ],
)
def test_doctor_failure_summary_contradictions_block_readiness(
    doctor: dict[str, object],
) -> None:
    report = host.inspect_host(
        FakeRunner(inspect_responses(doctor=json.dumps(doctor))),
        context="host",
    )
    assert cast(dict[str, object], report["states"])["daemon"] == "indeterminate"
    assert (
        cast(dict[str, object], report["capabilities"])["doctor_required_subset_valid"]
        is False
    )


def test_doctor_not_ok_without_external_failure_blocks_readiness() -> None:
    doctor = json.dumps({"ok": False, "checks": []})
    report = host.inspect_host(
        FakeRunner(inspect_responses(doctor=doctor)),
        context="host",
    )
    assert cast(dict[str, object], report["states"])["daemon"] == "indeterminate"


def test_additional_profile_field_validation(tmp_path: Path, profile: Path) -> None:
    probes = {
        "ao-version": host.Evidence("ao-version", "host", "pass", "ao 1"),
        "systemd-active": host.Evidence("systemd-active", "host", "fail", "unknown"),
        "main-pid": host.Evidence("main-pid", "host", "fail", "unknown"),
        "status": host.Evidence("status", "host", "fail", "unknown"),
        "healthz": host.Evidence("healthz", "daemon", "fail", "down"),
        "readyz": host.Evidence("readyz", "daemon", "pass", "up"),
    }
    assert (
        host.evaluate_daemon_state(
            probes, context="host", status={}, health={}, ready={}
        )
        == "indeterminate"
    )

    bad_cli = tmp_path / "bad-cli.toml"
    bad_cli.write_text(
        V1_PROFILE.replace('cli = "ao"', 'cli = "bad name"'),
        encoding="utf-8",
    )
    bad_cli.chmod(0o600)
    with pytest.raises(host.CalibrationError, match="executable name"):
        host.plan_profile(bad_cli)

    bad_health = tmp_path / "bad-health.toml"
    bad_health.write_text(
        V1_PROFILE.replace('health_path = "/healthz"', 'health_path = "healthz"'),
        encoding="utf-8",
    )
    bad_health.chmod(0o600)
    with pytest.raises(host.CalibrationError, match="absolute URL path"):
        host.plan_profile(bad_health)

    profile.write_text(
        profile.read_text(encoding="utf-8").replace(
            "boundaries = [",
            (
                'boundaries = [{ path = "relative", kind = "shared", '
                "recursive_search = false }, "
            ),
        ),
        encoding="utf-8",
    )
    with pytest.raises(host.CalibrationError, match="invalid types"):
        host.plan_profile(profile)
