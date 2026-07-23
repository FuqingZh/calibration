from __future__ import annotations

import json
import runpy
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

import scripts.adopt_ao_repository as adoption
from scripts.adopt_ao_repository import (
    AdoptionError,
    AdoptionReport,
    AdoptionRequest,
    _command,
    _contains,
    _doctor_check,
    _json_output,
    _mapping,
    _merge,
    _project_config,
    _project_get,
    _reject_tracker_intake,
    _run,
    _validate_codex_home,
    _verify_project_path,
    adopt_repository,
    main,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def completed(
    command: Sequence[str],
    *,
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, returncode, stdout, stderr)


def no_sleep(_seconds: float) -> None:
    pass


class FakeRunner:
    def __init__(
        self,
        responses: dict[tuple[str, ...], list[subprocess.CompletedProcess[str]]],
    ) -> None:
        self.responses = responses
        self.commands: list[tuple[str, ...]] = []

    def __call__(self, command: Sequence[str]) -> subprocess.CompletedProcess[str]:
        key = tuple(command)
        self.commands.append(key)
        queue = self.responses.get(key)
        if not queue:
            raise AssertionError(f"unexpected command: {key}")
        return queue.pop(0)


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    path = tmp_path / "repository"
    (path / ".git").mkdir(parents=True)
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir(mode=0o700)
    config = codex_home / "config.toml"
    config.write_text(
        "[features]\napps = false\nplugins = false\n",
        encoding="utf-8",
    )
    config.chmod(0o600)
    auth = codex_home / "auth.json"
    auth.write_text("{}\n", encoding="utf-8")
    auth.chmod(0o600)
    return path


def request(repository: Path) -> AdoptionRequest:
    return AdoptionRequest(
        path=repository,
        name="sample",
        default_branch="main",
        session_prefix="sample",
        codex_home=repository.parent / "codex-home",
        permission="bypass-permissions",
        bot_review_author="chatgpt-codex-connector",
    )


def project_payload(config: object, path: str = "/tmp/repository") -> str:
    return json.dumps(
        {
            "status": "ok",
            "project": {"id": "sample", "path": path, "config": config},
        }
    )


def successful_responses(
    repository: Path,
    *,
    existing: bool,
    readback_config: object | None = None,
) -> dict[tuple[str, ...], list[subprocess.CompletedProcess[str]]]:
    required = {
        "defaultBranch": "main",
        "sessionPrefix": "sample",
        "env": {"CODEX_HOME": str((repository.parent / "codex-home").resolve())},
        "worker": {
            "agent": "codex",
            "agentConfig": {"permissions": "bypass-permissions"},
        },
        "botReviewFeedback": {
            "allowAuthors": ["chatgpt-codex-connector"],
        },
    }
    project_get = ("ao", "project", "get", "sample", "--json")
    initial = completed(
        project_get,
        stdout=project_payload({"unrelated": True}, str(repository.resolve())),
    )
    responses: dict[tuple[str, ...], list[subprocess.CompletedProcess[str]]] = {
        (
            "systemctl",
            "--user",
            "enable",
            "--now",
            "agent-orchestrator.service",
        ): [completed(("systemctl",))],
        (
            "systemctl",
            "--user",
            "is-enabled",
            "agent-orchestrator.service",
        ): [completed(("systemctl",), stdout="enabled\n")],
        (
            "systemctl",
            "--user",
            "is-active",
            "agent-orchestrator.service",
        ): [completed(("systemctl",), stdout="active\n")],
        ("ao", "status", "--json"): [completed(("ao",), stdout='{"state":"ready"}')],
        ("ao", "doctor", "--json"): [
            completed(
                ("ao",),
                stdout=json.dumps(
                    {
                        "ok": True,
                        "failures": 0,
                        "checks": [
                            {
                                "name": "tmux",
                                "message": "/usr/bin/tmux (tmux 3.5)",
                            }
                        ],
                    }
                ),
            )
        ],
        project_get: [
            initial if existing else completed(project_get, returncode=1),
            *([] if existing else [initial]),
            completed(
                project_get,
                stdout=project_payload(
                    readback_config or required,
                    str(repository.resolve()),
                ),
            ),
        ],
        (
            "ao",
            "project",
            "add",
            "--path",
            str(repository.resolve()),
            "--id",
            "sample",
            "--name",
            "sample",
            "--worker-agent",
            "codex",
        ): [completed(("ao",))],
    }
    merged: dict[str, object] = dict(required)
    merged["unrelated"] = True
    responses[
        (
            "ao",
            "project",
            "set-config",
            "sample",
            "--config-json",
            json.dumps(merged, separators=(",", ":"), sort_keys=True),
            "--json",
        )
    ] = [completed(("ao",), stdout="{}")]
    return responses


def test_plan_is_read_only_and_reports_unproven_continuation(
    repository: Path,
) -> None:
    runner = FakeRunner({})
    report = adopt_repository(request(repository), apply=False, runner=runner)

    assert report.mode == "plan"
    assert report.state == "not-applied"
    assert report.continuation_proven is False
    assert report.project_registered is False
    assert runner.commands == []


def test_rejects_default_codex_permission(repository: Path) -> None:
    unsafe_request = replace(request(repository), permission="default")
    with pytest.raises(AdoptionError, match="Codex permission"):
        adopt_repository(unsafe_request, apply=False)


@pytest.mark.parametrize("unsafe", ["file", "symlink"])
def test_rejects_unsafe_codex_path(repository: Path, unsafe: str) -> None:
    codex_path = repository / ".codex"
    if unsafe == "file":
        codex_path.write_text("unsafe\n", encoding="utf-8")
    else:
        codex_path.symlink_to(repository.parent)

    with pytest.raises(AdoptionError, match="non-symlinked directory"):
        adopt_repository(request(repository), apply=False)


def test_rejects_non_repository(tmp_path: Path) -> None:
    with pytest.raises(AdoptionError, match="not a Git repository"):
        adopt_repository(request(tmp_path), apply=False)


def test_rejects_unsafe_codex_home(repository: Path) -> None:
    codex_home = repository.parent / "codex-home"
    codex_home.chmod(0o755)
    with pytest.raises(AdoptionError, match="group or other"):
        adopt_repository(request(repository), apply=True)

    codex_home.chmod(0o700)
    config = codex_home / "config.toml"
    config.chmod(0o644)
    with pytest.raises(AdoptionError, match="config.toml.*group or other"):
        adopt_repository(request(repository), apply=True)

    config.chmod(0o600)
    config.unlink()
    with pytest.raises(AdoptionError, match="regular file"):
        _validate_codex_home(codex_home)

    config.symlink_to(codex_home / "auth.json")
    with pytest.raises(AdoptionError, match="regular file"):
        _validate_codex_home(codex_home)


def test_rejects_missing_or_symlinked_codex_home(repository: Path) -> None:
    codex_home = repository.parent / "codex-home"
    auth = codex_home / "auth.json"
    auth.unlink()
    with pytest.raises(AdoptionError, match="authentication file"):
        _validate_codex_home(codex_home)

    config = codex_home / "config.toml"
    config.unlink()
    replacement = repository.parent / "replacement-home"
    replacement.mkdir(mode=0o700)
    codex_home.rmdir()
    codex_home.symlink_to(replacement)
    with pytest.raises(AdoptionError, match="non-symlinked Codex home"):
        _validate_codex_home(codex_home)


def test_rejects_public_authentication_file(repository: Path) -> None:
    codex_home = repository.parent / "codex-home"
    auth = codex_home / "auth.json"
    auth.chmod(0o644)
    with pytest.raises(AdoptionError, match="auth.json.*group or other"):
        _validate_codex_home(codex_home)


@pytest.mark.parametrize(
    "content",
    [
        "unrelated = true\n",
        "[features]\napps = false\n",
        "[features]\napps = false\nplugins = true\n",
        "[features]\napps = true\nplugins = false\n",
        "invalid = [\n",
    ],
)
def test_rejects_unsafe_codex_features(repository: Path, content: str) -> None:
    config = repository.parent / "codex-home" / "config.toml"
    config.write_text(content, encoding="utf-8")

    with pytest.raises(AdoptionError, match="valid TOML|apps = false"):
        _validate_codex_home(repository.parent / "codex-home")


@pytest.mark.parametrize("existing", [False, True])
def test_apply_registers_or_reuses_project_and_verifies_readback(
    repository: Path,
    existing: bool,
) -> None:
    runner = FakeRunner(successful_responses(repository, existing=existing))

    report = adopt_repository(request(repository), apply=True, runner=runner)

    assert report.state == "runtime-ready"
    assert report.project_registered is True
    assert report.configuration_verified is True
    assert report.continuation_proven is False
    add_commands = [
        command
        for command in runner.commands
        if command[0:3] == ("ao", "project", "add")
    ]
    assert bool(add_commands) is not existing


def test_preserves_nested_existing_configuration() -> None:
    assert _merge(
        {"env": {"OTHER": "kept"}, "top": True},
        {"env": {"CODEX_HOME": "/tmp/home"}},
    ) == {
        "env": {"OTHER": "kept", "CODEX_HOME": "/tmp/home"},
        "top": True,
    }
    assert _contains(
        {"env": {"OTHER": "kept", "CODEX_HOME": "/tmp/home"}},
        {"env": {"CODEX_HOME": "/tmp/home"}},
    )
    assert not _contains({}, {"missing": True})
    assert not _contains({"env": "wrong"}, {"env": {"key": "value"}})
    assert not _contains({"value": 1}, {"value": 2})


def test_project_config_accepts_encoded_json_and_rejects_bad_shapes() -> None:
    assert _project_config({"config": '{"worker":{"agent":"codex"}}'}) == {
        "worker": {"agent": "codex"}
    }
    with pytest.raises(AdoptionError, match="invalid JSON"):
        _project_config({"config": "{"})
    with pytest.raises(AdoptionError, match="must be a JSON object"):
        _project_config({"config": []})
    with pytest.raises(AdoptionError, match="must be a JSON object"):
        _mapping([], "value")


def test_rejects_enabled_tracker_intake() -> None:
    _reject_tracker_intake({})
    _reject_tracker_intake({"trackerIntake": {"enabled": False}})
    with pytest.raises(AdoptionError, match="trackerIntake.enabled"):
        _reject_tracker_intake({"trackerIntake": {"enabled": True}})


def test_project_path_must_match_selected_repository(repository: Path) -> None:
    _verify_project_path({"path": str(repository)}, repository.resolve())
    with pytest.raises(AdoptionError, match="does not match repository"):
        _verify_project_path({"path": str(repository.parent)}, repository.resolve())
    with pytest.raises(AdoptionError, match="does not match repository"):
        _verify_project_path({}, repository.resolve())


def test_project_get_accepts_wrapped_and_legacy_bare_payloads() -> None:
    payloads: tuple[dict[str, object], ...] = (
        {"status": "ok", "project": {"id": "sample", "config": {}}},
        {"id": "sample", "config": {}},
    )
    for payload in payloads:
        output = json.dumps(payload)
        found, project = _project_get(
            lambda received: completed(received, stdout=output),
            "sample",
        )
        assert found is True
        assert project == {"id": "sample", "config": {}}

    found, project = _project_get(
        lambda received: completed(received, returncode=1),
        "sample",
    )
    assert found is False
    assert project is None


def test_command_and_json_error_messages_include_external_failure() -> None:
    with pytest.raises(AdoptionError, match="failure detail"):
        _command(
            lambda command: completed(command, returncode=1, stderr="failure detail"),
            ("ao", "status"),
        )
    with pytest.raises(AdoptionError, match="no output"):
        _command(
            lambda command: completed(command, returncode=1),
            ("ao", "status"),
        )
    with pytest.raises(AdoptionError, match="expected 'active'"):
        _command(
            lambda command: completed(command, stdout="inactive"),
            ("systemctl", "--user", "is-active"),
            expected="active",
        )
    with pytest.raises(AdoptionError, match="invalid JSON"):
        _json_output(completed(("ao",), stdout="{"), "ao status")


def test_doctor_retries_one_transient_failure() -> None:
    command = ("ao", "doctor", "--json")
    runner = FakeRunner(
        {
            command: [
                completed(
                    command,
                    returncode=1,
                    stdout='{"ok":false,"failures":1}',
                ),
                completed(
                    command,
                    stdout=json.dumps(
                        {
                            "ok": True,
                            "failures": 0,
                            "checks": [{"name": "tmux", "message": "tmux 3.5"}],
                        }
                    ),
                ),
            ]
        }
    )
    assert _doctor_check(runner) is True


@pytest.mark.parametrize(
    ("doctor", "message"),
    [
        ({"ok": True, "failures": 0}, "tool checks"),
        ({"ok": True, "failures": 0, "checks": []}, "exactly one tmux"),
        (
            {
                "ok": True,
                "failures": 0,
                "checks": [{"name": "tmux", "message": "tmux 2.7"}],
            },
            "3.5 or later",
        ),
    ],
)
def test_doctor_rejects_missing_or_old_tmux(
    doctor: dict[str, object],
    message: str,
) -> None:
    runner = FakeRunner(
        {("ao", "doctor", "--json"): [completed(("ao",), stdout=json.dumps(doctor))]}
    )
    with pytest.raises(AdoptionError, match=message):
        _doctor_check(runner)


def test_runtime_polls_until_daemon_is_ready(
    repository: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = successful_responses(repository, existing=True)
    responses[("ao", "status", "--json")] = [
        completed(("ao",), stdout='{"state":"not_ready"}'),
        completed(("ao",), stdout='{"state":"ready"}'),
    ]
    monkeypatch.setattr(adoption.time, "sleep", no_sleep)

    report = adopt_repository(
        request(repository), apply=True, runner=FakeRunner(responses)
    )

    assert report.daemon_ready is True


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        (
            {
                ("ao", "status", "--json"): [
                    completed(("ao",), stdout='{"state":"stale"}')
                ]
            },
            "daemon is not ready",
        ),
        (
            {
                ("ao", "doctor", "--json"): [
                    completed(
                        ("ao",),
                        returncode=1,
                        stdout='{"ok":false,"failures":1}',
                    ),
                    completed(("ao",), returncode=1, stderr="still failing"),
                ]
            },
            "after two attempts",
        ),
    ],
)
def test_apply_rejects_unhealthy_runtime(
    repository: Path,
    overrides: dict[tuple[str, ...], list[subprocess.CompletedProcess[str]]],
    message: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = successful_responses(repository, existing=True)
    if ("ao", "status", "--json") in overrides:
        overrides[("ao", "status", "--json")] *= adoption.STATUS_ATTEMPTS
    responses.update(overrides)
    monkeypatch.setattr(adoption.time, "sleep", no_sleep)

    with pytest.raises(AdoptionError, match=message):
        adopt_repository(request(repository), apply=True, runner=FakeRunner(responses))


def test_apply_rejects_registration_or_configuration_readback_failure(
    repository: Path,
) -> None:
    responses = successful_responses(repository, existing=False)
    project_get = ("ao", "project", "get", "sample", "--json")
    responses[project_get][1] = completed(project_get, returncode=1)
    with pytest.raises(AdoptionError, match="after registration"):
        adopt_repository(request(repository), apply=True, runner=FakeRunner(responses))

    responses = successful_responses(repository, existing=True)
    responses[project_get][-1] = completed(project_get, returncode=1)
    with pytest.raises(AdoptionError, match="after configuration"):
        adopt_repository(request(repository), apply=True, runner=FakeRunner(responses))

    responses = successful_responses(
        repository,
        existing=True,
        readback_config={"worker": {"agent": "wrong"}},
    )
    with pytest.raises(AdoptionError, match="did not match"):
        adopt_repository(request(repository), apply=True, runner=FakeRunner(responses))


def test_apply_rejects_existing_tracker_intake(repository: Path) -> None:
    responses = successful_responses(repository, existing=True)
    project_get = ("ao", "project", "get", "sample", "--json")
    responses[project_get][0] = completed(
        project_get,
        stdout=project_payload(
            {"trackerIntake": {"enabled": True}},
            str(repository.resolve()),
        ),
    )
    with pytest.raises(AdoptionError, match="trackerIntake.enabled"):
        adopt_repository(request(repository), apply=True, runner=FakeRunner(responses))


def test_run_executes_a_command_and_sanitizes_ao_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AO_RUN_FILE", "/tmp/alternate-run.json")
    monkeypatch.setenv("AO_DATA_DIR", "/tmp/alternate-data")
    result = _run(("printf", "ok"))
    assert result.returncode == 0
    assert result.stdout == "ok"

    result = _run(
        (
            sys.executable,
            "-c",
            "import os; print('AO_RUN_FILE' in os.environ, 'AO_DATA_DIR' in os.environ)",
        )
    )
    assert result.stdout.strip() == "False False"


def test_main_renders_plan_json_and_human_output(
    repository: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = [
        "--path",
        str(repository),
        "--name",
        "sample",
        "--codex-home",
        str(repository.parent / "codex-home"),
        "--permission",
        "auto",
    ]
    assert main([*args, "--json"]) == 0
    assert '"state": "not-applied"' in capsys.readouterr().out

    assert main(args) == 0
    output = capsys.readouterr().out
    assert "AO repository adoption: not-applied" in output
    assert "NEXT:" in output


def test_main_renders_json_and_human_errors(
    repository: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail(
        request: AdoptionRequest,
        *,
        apply: bool,
        runner: adoption.CommandRunner = adoption._run,
    ) -> AdoptionReport:
        del request, apply, runner
        raise AdoptionError("broken")

    monkeypatch.setattr(adoption, "adopt_repository", fail)
    args = [
        "--path",
        str(repository),
        "--name",
        "sample",
        "--codex-home",
        str(repository.parent / "codex-home"),
        "--permission",
        "auto",
    ]
    assert main([*args, "--json"]) == 1
    assert json.loads(capsys.readouterr().out) == {
        "error": "broken",
        "state": "failed",
    }

    assert main(args) == 1
    assert "ERROR: broken" in capsys.readouterr().err


def test_script_entrypoint_exits_with_main_result(
    repository: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "adopt_ao_repository.py",
            "--path",
            str(repository),
            "--name",
            "sample",
            "--codex-home",
            str(repository.parent / "codex-home"),
            "--permission",
            "auto",
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(
            str(REPOSITORY_ROOT / "scripts/adopt_ao_repository.py"),
            run_name="__main__",
        )
    assert cast(int, exc_info.value.code) == 0
