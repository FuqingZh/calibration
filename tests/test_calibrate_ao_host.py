from __future__ import annotations

import json
import runpy
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import cast

import pytest

import scripts.calibrate_ao_host as host

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
listen_port = 3001
trusted_readonly_cidrs = ["203.0.113.0/24"]
document_root = "/opt/example/dashboard"
active_config = "/opt/example/active.conf"
desired_service = "/opt/example/dashboard.service"
rollback_service = "/opt/example/dashboard.rollback.service"

[dashboard.terminal]
desired_enabled = false
trust_model = "trusted-single-user"
allowed_client_ips = []
allowed_origin = "https://console.example.test"
path = "/mux"
upstream = "http://127.0.0.1:3001"
upstream_origin = "https://console.example.test"
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
    status: str = '{"state":"ready"}',
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
        completed((), out=status),
        completed((), out=doctor),
        completed((), out="ok"),
        completed((), 0 if ready else 1, out="ready" if ready else "no"),
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


def test_status_stale_and_doctor_readonly_do_not_override_daemon_ready() -> None:
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
        "daemon": "ready",
        "delivery": "indeterminate",
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
        terminal=True,
        client_ip="203.0.113.7",
        origin="https://console.example.test",
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
        "limit_except GET",
        "https://console.example.test",
        "Upgrade",
        "127.0.0.1:3001",
    ):
        assert phrase in nginx
    manifest = json.loads((output / "MANIFEST.json").read_text())
    assert manifest["profile_sha256"]
    assert "host.toml" in manifest["files"]


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (("version", "3"), "unsupported"),
        (("top", "extra = true"), "unknown top-level"),
        (("remove", 'cli = "ao"'), "missing keys"),
        (("ao-extra", 'surprise = "x"'), "unknown keys"),
        (("relative", 'codex_home = "relative"'), "must be absolute"),
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
        ({"desired_enabled": True}, "exactly one client"),
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
            "paired probe",
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


def test_invalid_profile_and_init_rejections(
    tmp_path: Path, codex_home: Path, profile: Path
) -> None:
    invalid = tmp_path / "invalid.toml"
    invalid.write_text("bad =", encoding="utf-8")
    invalid.chmod(0o600)
    with pytest.raises(host.CalibrationError, match="valid TOML"):
        host.plan_profile(invalid)
    assert host._profile_base_url(invalid) == host.DEFAULT_BASE_URL
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
        host._quote({"bad": True})
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


def test_reconstruction_canary_executes_full_pipeline(tmp_path: Path) -> None:
    runner = FakeRunner(inspect_responses())
    result = host.reconstruction_canary(tmp_path / "isolated", runner)
    assert result == {
        "inspect": "ready",
        "plan": "plan",
        "first_unchanged": False,
        "second_unchanged": True,
        "verified": True,
    }


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
    assert host._required_subset({"name": "x", "extra": 1}, {"name": str})
    assert not host._required_subset({}, {"name": str})


def test_pure_state_and_issue_evaluators() -> None:
    probes = {
        "ao-version": host.Evidence("ao-version", "sandbox", "pass", "ao 1"),
        "systemd-active": host.Evidence("systemd-active", "host", "pass", "active"),
        "healthz": host.Evidence("healthz", "daemon", "pass", "ok"),
        "readyz": host.Evidence("readyz", "daemon", "pass", "ok"),
        "mux": host.Evidence("mux", "daemon", "fail", "404"),
    }
    assert host.evaluate_daemon_state(probes, context="host") == "ready"
    missing_ao = dict(probes)
    missing_ao["ao-version"] = host.Evidence("ao-version", "sandbox", "fail", "missing")
    missing_ao["healthz"] = host.Evidence("healthz", "daemon", "fail", "missing")
    assert host.evaluate_daemon_state(missing_ao, context="host") == "not_installed"
    unavailable = dict(probes)
    unavailable["systemd-active"] = host.Evidence(
        "systemd-active", "host", "pass", "inactive"
    )
    unavailable["healthz"] = host.Evidence("healthz", "daemon", "fail", "down")
    unavailable["readyz"] = host.Evidence("readyz", "daemon", "fail", "down")
    assert host.evaluate_daemon_state(unavailable, context="host") == "unavailable"
    assert (
        host.evaluate_delivery_state(
            probes, daemon_state="ready", terminal_enabled=True
        )
        == "degraded"
    )
    assert (
        host.evaluate_delivery_state(
            probes, daemon_state="ready", terminal_enabled=False
        )
        == "not_applicable"
    )
    assert (
        host.evaluate_delivery_state(
            probes, daemon_state="indeterminate", terminal_enabled=True
        )
        == "indeterminate"
    )
    passing_mux = dict(probes)
    passing_mux["mux"] = host.Evidence("mux", "daemon", "pass", "101")
    assert (
        host.evaluate_delivery_state(
            passing_mux, daemon_state="ready", terminal_enabled=True
        )
        == "ready"
    )
    assert not host._version_before(None, (2, 38))
    issues = host.evaluate_known_issues(
        probes=probes,
        status={"state": "stale", "extra": "kept"},
        doctor={"ok": False, "checks": []},
        capabilities={
            "glibc_version": "2.37",
            "tmux_version": "3.4",
            "codex_home_compatible": False,
            "process_containment": "assigned-workspace",
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
