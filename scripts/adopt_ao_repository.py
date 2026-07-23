#!/usr/bin/env python3
"""Plan, apply, and audit AO adoption for one explicitly opted-in repository."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
import time
import tomllib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast


CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]
PERMISSIONS = ("accept-edits", "auto", "bypass-permissions")
AO_ENVIRONMENT_OVERRIDES = ("AO_DATA_DIR", "AO_PORT", "AO_RUN_FILE")
STATUS_ATTEMPTS = 5


class AdoptionError(RuntimeError):
    """Report a failed precondition or external AO operation."""


@dataclass(frozen=True)
class AdoptionRequest:
    """Explicit repository and accepted-host settings for one AO project."""

    path: Path
    name: str
    default_branch: str
    session_prefix: str
    codex_home: Path
    permission: str
    bot_review_author: str


@dataclass(frozen=True)
class AdoptionReport:
    """Machine-readable result without overstating real-event verification."""

    project: str
    repository: str
    mode: str
    state: str
    service_enabled: bool
    service_active: bool
    daemon_ready: bool
    doctor_ok: bool
    project_registered: bool
    configuration_verified: bool
    continuation_proven: bool
    next_evidence: tuple[str, ...]


def _run(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    for name in AO_ENVIRONMENT_OVERRIDES:
        environment.pop(name, None)
    return subprocess.run(
        list(command),
        check=False,
        capture_output=True,
        env=environment,
        text=True,
    )


def _command(
    runner: CommandRunner,
    command: Sequence[str],
    *,
    expected: str | None = None,
) -> subprocess.CompletedProcess[str]:
    result = runner(command)
    display_command = list(command)
    if "--config-json" in display_command:
        value_index = display_command.index("--config-json") + 1
        if value_index < len(display_command):
            display_command[value_index] = "<redacted>"
    rendered_command = " ".join(display_command)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        raise AdoptionError(f"{rendered_command} failed: {detail}")
    if expected is not None and result.stdout.strip() != expected:
        raise AdoptionError(
            f"{rendered_command} returned {result.stdout.strip()!r}; "
            f"expected {expected!r}"
        )
    return result


def _json_output(result: subprocess.CompletedProcess[str], label: str) -> object:
    try:
        return cast(object, json.loads(result.stdout))
    except json.JSONDecodeError as exc:
        raise AdoptionError(f"{label} returned invalid JSON: {exc}") from exc


def _mapping(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AdoptionError(f"{label} must be a JSON object")
    return cast(dict[str, object], value)


def _validate_repository(path: Path) -> Path:
    repository = path.expanduser().resolve()
    if not repository.is_dir() or not (repository / ".git").exists():
        raise AdoptionError(f"{repository} is not a Git repository")
    codex_path = repository / ".codex"
    if codex_path.is_symlink() or (codex_path.exists() and not codex_path.is_dir()):
        raise AdoptionError(".codex must be absent or a non-symlinked directory")
    return repository


def _validate_codex_home(path: Path) -> Path:
    codex_home = path.expanduser().resolve()
    if path.expanduser().is_symlink() or not codex_home.is_dir():
        raise AdoptionError(f"{codex_home} must be a non-symlinked Codex home")
    if stat.S_IMODE(codex_home.stat().st_mode) & 0o077:
        raise AdoptionError(f"{codex_home} must not be accessible by group or other")

    config = codex_home / "config.toml"
    if config.is_symlink() or not config.is_file():
        raise AdoptionError(f"{config} must be a regular file")
    if stat.S_IMODE(config.stat().st_mode) & 0o077:
        raise AdoptionError(f"{config} must not be accessible by group or other")
    try:
        parsed_config = tomllib.loads(config.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise AdoptionError(f"{config} must contain valid TOML: {exc}") from exc
    features = parsed_config.get("features")
    if not isinstance(features, dict):
        raise AdoptionError(
            f"{config} must set [features] apps = false and plugins = false"
        )
    feature_config = cast(dict[str, object], features)
    if (
        set(parsed_config) != {"features"}
        or set(feature_config) != {"apps", "plugins"}
        or feature_config.get("apps") is not False
        or feature_config.get("plugins") is not False
    ):
        raise AdoptionError(
            f"{config} must set [features] apps = false and plugins = false"
        )

    auth = codex_home / "auth.json"
    if not auth.is_file():
        raise AdoptionError(f"{auth} must resolve to an authentication file")
    if stat.S_IMODE(auth.stat().st_mode) & 0o077:
        raise AdoptionError(f"{auth} must not be accessible by group or other")
    return codex_home


def _validate_codex_home_location(codex_home: Path, repository: Path) -> None:
    if codex_home == repository or codex_home.is_relative_to(repository):
        raise AdoptionError(
            f"{codex_home} must be outside the selected repository {repository}"
        )


def _validate_codex_login(runner: CommandRunner, codex_home: Path) -> None:
    _command(
        runner,
        (
            "env",
            f"CODEX_HOME={codex_home}",
            "codex",
            "login",
            "status",
        ),
    )


def _required_config(request: AdoptionRequest) -> dict[str, object]:
    return {
        "defaultBranch": request.default_branch,
        "sessionPrefix": request.session_prefix,
        "env": {"CODEX_HOME": str(request.codex_home.expanduser().resolve())},
        "worker": {
            "agent": "codex",
            "agentConfig": {"permissions": request.permission},
        },
        "botReviewFeedback": {"allowAuthors": [request.bot_review_author]},
    }


def _merge(
    current: Mapping[str, object], required: Mapping[str, object]
) -> dict[str, object]:
    merged = dict(current)
    for key, value in required.items():
        current_value = merged.get(key)
        if isinstance(current_value, dict) and isinstance(value, dict):
            merged[key] = _merge(
                cast(dict[str, object], current_value),
                cast(dict[str, object], value),
            )
        else:
            merged[key] = value
    return merged


def _contains(actual: Mapping[str, object], expected: Mapping[str, object]) -> bool:
    for key, expected_value in expected.items():
        if key not in actual:
            return False
        actual_value = actual[key]
        if isinstance(expected_value, dict):
            if not isinstance(actual_value, dict) or not _contains(
                cast(dict[str, object], actual_value),
                cast(dict[str, object], expected_value),
            ):
                return False
        elif actual_value != expected_value:
            return False
    return True


def _project_config(project: Mapping[str, object]) -> dict[str, object]:
    raw_config = project.get("config", {})
    if isinstance(raw_config, str):
        try:
            raw_config = cast(object, json.loads(raw_config))
        except json.JSONDecodeError as exc:
            raise AdoptionError(f"AO project config is invalid JSON: {exc}") from exc
    return _mapping(raw_config, "AO project config")


def _reject_tracker_intake(config: Mapping[str, object]) -> None:
    tracker_intake = config.get("trackerIntake")
    if (
        isinstance(tracker_intake, dict)
        and cast(dict[str, object], tracker_intake).get("enabled") is True
    ):
        raise AdoptionError(
            "AO project trackerIntake.enabled must not be true for repository adoption"
        )


def _reject_bot_review_conflict(
    config: Mapping[str, object],
    author: str,
) -> None:
    feedback = config.get("botReviewFeedback")
    if not isinstance(feedback, dict):
        return
    deny_authors = cast(dict[str, object], feedback).get("denyAuthors")
    if not isinstance(deny_authors, list):
        return
    normalized_author = author.strip().casefold()
    if any(
        isinstance(denied, str) and denied.strip().casefold() == normalized_author
        for denied in cast(list[object], deny_authors)
    ):
        raise AdoptionError(
            f"AO project botReviewFeedback.denyAuthors blocks {author!r}"
        )


def _reject_auto_merge(value: object) -> None:
    if isinstance(value, dict):
        mapping = cast(dict[str, object], value)
        for key, nested in mapping.items():
            normalized_key = key.replace("-", "").replace("_", "").casefold()
            if (
                normalized_key == "automerge"
                and nested is not False
                and nested is not None
                and nested != ""
            ):
                raise AdoptionError(
                    "AO project configuration must not enable auto-merge"
                )
            if key.casefold() == "action" and isinstance(nested, str):
                if nested.strip().casefold() == "auto-merge":
                    raise AdoptionError(
                        "AO project configuration must not enable auto-merge"
                    )
            _reject_auto_merge(nested)
    elif isinstance(value, list):
        for nested in cast(list[object], value):
            _reject_auto_merge(nested)


def _verify_project_path(project: Mapping[str, object], repository: Path) -> None:
    raw_path = project.get("path")
    if (
        not isinstance(raw_path, str)
        or Path(raw_path).expanduser().resolve() != repository
    ):
        raise AdoptionError(
            f"AO project path {raw_path!r} does not match repository {repository}"
        )


def _project_get(
    runner: CommandRunner, name: str
) -> tuple[bool, dict[str, object] | None]:
    result = runner(("ao", "project", "get", name, "--json"))
    if result.returncode != 0:
        return False, None
    payload = _mapping(_json_output(result, "ao project get"), "AO project response")
    wrapped_project = payload.get("project")
    if wrapped_project is not None:
        if payload.get("status") != "ok":
            raise AdoptionError(
                f"AO project status must be 'ok'; got {payload.get('status')!r}"
            )
        project = _mapping(wrapped_project, "AO project")
    else:
        project = payload
    resolve_error = project.get("resolveError")
    if isinstance(resolve_error, str) and resolve_error.strip():
        raise AdoptionError(f"AO project is degraded: {resolve_error}")
    return True, project


def _doctor_check(runner: CommandRunner) -> bool:
    last_detail = "no output"
    for _attempt in range(2):
        result = runner(("ao", "doctor", "--json"))
        if result.stdout.strip():
            doctor = _mapping(_json_output(result, "ao doctor"), "AO doctor")
            doctor_ok = (
                result.returncode == 0
                and doctor.get("ok") is True
                and doctor.get("failures") == 0
            )
            if doctor_ok:
                checks = doctor.get("checks")
                if not isinstance(checks, list):
                    raise AdoptionError("AO doctor did not report tool checks")
                check_items = cast(list[object], checks)
                required_checks = {
                    "codex",
                    "codex-launch-flags",
                    "github-token",
                    "tmux",
                }
                passing_checks = {
                    cast(dict[str, object], item).get("name")
                    for item in check_items
                    if isinstance(item, dict)
                    and cast(dict[str, object], item).get("level") == "PASS"
                }
                missing_checks = required_checks - passing_checks
                if missing_checks:
                    raise AdoptionError(
                        "AO doctor required checks did not pass: "
                        + ", ".join(sorted(missing_checks))
                    )
                tmux_checks = [
                    cast(dict[str, object], item)
                    for item in check_items
                    if isinstance(item, dict)
                    and cast(dict[str, object], item).get("name") == "tmux"
                ]
                if len(tmux_checks) != 1:
                    raise AdoptionError(
                        "AO doctor did not report exactly one tmux check"
                    )
                message = tmux_checks[0].get("message")
                match = (
                    re.search(r"\btmux\s+(\d+)\.(\d+)", message)
                    if isinstance(message, str)
                    else None
                )
                if match is None or tuple(map(int, match.groups())) < (3, 5):
                    raise AdoptionError(
                        f"AO requires tmux 3.5 or later; doctor reported {message!r}"
                    )
                return True
            last_detail = result.stdout.strip()
        else:
            last_detail = result.stderr.strip() or last_detail
    raise AdoptionError(
        "AO doctor did not report ok=true and failures=0 after two attempts: "
        f"{last_detail}"
    )


def _runtime_checks(runner: CommandRunner) -> tuple[bool, bool, bool, bool]:
    _command(
        runner,
        ("systemctl", "--user", "enable", "--now", "agent-orchestrator.service"),
    )
    _command(
        runner,
        ("systemctl", "--user", "is-enabled", "agent-orchestrator.service"),
        expected="enabled",
    )
    _command(
        runner,
        ("systemctl", "--user", "is-active", "agent-orchestrator.service"),
        expected="active",
    )
    status: dict[str, object] = {}
    daemon_ready = False
    for attempt in range(STATUS_ATTEMPTS):
        result = runner(("ao", "status", "--json"))
        if result.returncode == 0:
            status = _mapping(_json_output(result, "ao status"), "AO status")
            daemon_ready = status.get("state") in {"ready", "running"}
            if daemon_ready:
                break
        if attempt + 1 < STATUS_ATTEMPTS:
            time.sleep(1)
    if not daemon_ready:
        raise AdoptionError(f"AO daemon is not ready: {status.get('state')!r}")
    doctor_ok = _doctor_check(runner)
    return True, True, daemon_ready, doctor_ok


def adopt_repository(
    request: AdoptionRequest,
    *,
    apply: bool,
    runner: CommandRunner = _run,
) -> AdoptionReport:
    """Plan or apply one repository's accepted AO configuration."""
    repository = _validate_repository(request.path)
    if request.permission not in PERMISSIONS:
        raise AdoptionError(
            f"Codex permission must be one of {', '.join(PERMISSIONS)}; "
            f"got {request.permission!r}"
        )
    required = _required_config(request)
    next_evidence = (
        "commit the repository-specific AO adoption increment in AGENTS.md",
        "start a task-specific worker before creating the implementation branch or PR",
        "prove one anchored Automatic Codex Review finding returns to that worker",
    )
    if not apply:
        return AdoptionReport(
            project=request.name,
            repository=str(repository),
            mode="plan",
            state="not-applied",
            service_enabled=False,
            service_active=False,
            daemon_ready=False,
            doctor_ok=False,
            project_registered=False,
            configuration_verified=False,
            continuation_proven=False,
            next_evidence=next_evidence,
        )

    codex_home = _validate_codex_home(request.codex_home)
    _validate_codex_home_location(codex_home, repository)
    _validate_codex_login(runner, codex_home)
    service_enabled, service_active, daemon_ready, doctor_ok = _runtime_checks(runner)
    registered, project = _project_get(runner, request.name)
    if not registered:
        _command(
            runner,
            (
                "ao",
                "project",
                "add",
                "--path",
                str(repository),
                "--id",
                request.name,
                "--name",
                request.name,
                "--worker-agent",
                "codex",
            ),
        )
        registered, project = _project_get(runner, request.name)
        if not registered or project is None:
            raise AdoptionError("AO project was not readable after registration")
    assert project is not None
    _verify_project_path(project, repository)

    current_config = _project_config(project)
    _reject_tracker_intake(current_config)
    _reject_bot_review_conflict(current_config, request.bot_review_author)
    _reject_auto_merge(current_config)
    merged = _merge(current_config, required)
    _command(
        runner,
        (
            "ao",
            "project",
            "set-config",
            request.name,
            "--config-json",
            json.dumps(merged, separators=(",", ":"), sort_keys=True),
            "--json",
        ),
    )
    readback_registered, readback = _project_get(runner, request.name)
    if not readback_registered or readback is None:
        raise AdoptionError("AO project was not readable after configuration")
    _verify_project_path(readback, repository)
    readback_config = _project_config(readback)
    _reject_tracker_intake(readback_config)
    _reject_bot_review_conflict(readback_config, request.bot_review_author)
    _reject_auto_merge(readback_config)
    configuration_verified = _contains(readback_config, required)
    if not configuration_verified:
        raise AdoptionError("AO project configuration readback did not match request")

    return AdoptionReport(
        project=request.name,
        repository=str(repository),
        mode="apply",
        state="runtime-ready",
        service_enabled=service_enabled,
        service_active=service_active,
        daemon_ready=daemon_ready,
        doctor_ok=doctor_ok,
        project_registered=True,
        configuration_verified=configuration_verified,
        continuation_proven=False,
        next_evidence=next_evidence,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan or apply AO adoption for one explicitly opted-in repository."
    )
    parser.add_argument("--path", type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--default-branch", default="main")
    parser.add_argument("--session-prefix")
    parser.add_argument("--codex-home", type=Path, required=True)
    parser.add_argument("--permission", choices=PERMISSIONS, required=True)
    parser.add_argument(
        "--bot-review-author",
        default="chatgpt-codex-connector",
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit status."""
    args = _parser().parse_args(argv)
    request = AdoptionRequest(
        path=cast(Path, args.path),
        name=cast(str, args.name),
        default_branch=cast(str, args.default_branch),
        session_prefix=cast(str | None, args.session_prefix) or cast(str, args.name),
        codex_home=cast(Path, args.codex_home),
        permission=cast(str, args.permission),
        bot_review_author=cast(str, args.bot_review_author),
    )
    try:
        report = adopt_repository(request, apply=cast(bool, args.apply))
    except AdoptionError as exc:
        if cast(bool, args.json):
            print(json.dumps({"error": str(exc), "state": "failed"}, sort_keys=True))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload = asdict(report)
    if cast(bool, args.json):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"AO repository adoption: {report.state}")
        print(f"Project: {report.project}")
        print(f"Repository: {report.repository}")
        for item in report.next_evidence:
            print(f"NEXT: {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
