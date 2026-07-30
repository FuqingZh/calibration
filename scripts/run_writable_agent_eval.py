#!/usr/bin/env python3
"""Run one isolated writable calibration evaluation case."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVALUATION_ROOT = REPOSITORY_ROOT / "evaluations/ai-native-implementation"


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


class EvaluationError(RuntimeError):
    """Raised when an evaluation input or environment is invalid."""


def _required_string(data: dict[str, object], key: str, path: Path) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise EvaluationError(f"{path}: {key} must be a non-empty string")
    return value.strip()


def _string_set(data: dict[str, object], key: str, path: Path) -> frozenset[str]:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise EvaluationError(f"{path}: {key} must be a non-empty list")
    items = cast(list[object], value)
    if not all(isinstance(item, str) and item.strip() for item in items):
        raise EvaluationError(f"{path}: {key} entries must be non-empty strings")
    return frozenset(cast(str, item).strip() for item in items)


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


def load_case(path: Path) -> CaseSpec:
    """Load and validate one case definition."""
    try:
        raw = cast(object, yaml.safe_load(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise EvaluationError(f"{path}: cannot load case: {exc}") from exc
    if not isinstance(raw, dict):
        raise EvaluationError(f"{path}: case must be a mapping")
    data = cast(dict[str, object], raw)
    case = CaseSpec(
        case_id=_required_string(data, "id", path),
        title=_required_string(data, "title", path),
        fixture=_required_string(data, "fixture", path),
        prompt=_required_string(data, "prompt", path),
        verify=_commands(data, "verify", path),
        allowed_changes=_string_set(data, "allowed_changes", path),
        required_changes=_string_set(data, "required_changes", path),
    )
    if not case.required_changes <= case.allowed_changes:
        raise EvaluationError(f"{path}: required_changes must be allowed")
    fixture = EVALUATION_ROOT / "fixtures" / case.fixture
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


def prepare_workspace(case: CaseSpec, workspace: Path) -> None:
    """Copy and commit one pristine fixture repository."""
    if workspace.exists():
        raise EvaluationError(f"workspace already exists: {workspace}")
    fixture = EVALUATION_ROOT / "fixtures" / case.fixture
    shutil.copytree(fixture, workspace)
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
        result = _run(command, workspace)
        checks.append(
            {
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


def build_codex_command(
    case: CaseSpec,
    workspace: Path,
    final_message: Path,
    model: str,
    reasoning_effort: str,
) -> list[str]:
    """Build the frozen non-interactive Codex command."""
    return [
        "codex",
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--disable",
        "apps",
        "--disable",
        "plugins",
        "--json",
        "--color",
        "never",
        "--model",
        model,
        "--config",
        f'model_reasoning_effort="{reasoning_effort}"',
        "--sandbox",
        "workspace-write",
        "--cd",
        str(workspace),
        "--output-last-message",
        str(final_message),
        case.prompt,
    ]


def install_arm_home(source_root: Path, auth_file: Path, codex_home: Path) -> None:
    """Install one arm into an isolated Codex home."""
    if not (source_root / "install.sh").is_file():
        raise EvaluationError(f"missing arm installer: {source_root / 'install.sh'}")
    if not auth_file.is_file():
        raise EvaluationError(f"missing Codex auth file: {auth_file}")
    codex_home.mkdir(mode=0o700, parents=True)
    (codex_home / "auth.json").symlink_to(auth_file)
    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)
    result = _run(("bash", "install.sh"), source_root, env=env)
    if result.returncode:
        raise EvaluationError(f"arm install failed: {result.stderr.strip()}")


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
    output_dir.mkdir(parents=True)
    final_message = output_dir / "final-message.txt"
    trajectory = output_dir / "trajectory.jsonl"
    stderr_path = output_dir / "codex.stderr"
    codex_home = output_dir / "codex-home"
    install_arm_home(source_root, auth_file, codex_home)
    command = build_codex_command(
        case, workspace, final_message, model, reasoning_effort
    )
    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)
    started = time.monotonic()
    result = _run(command, workspace, env=env)
    elapsed = time.monotonic() - started
    trajectory.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    verification = verify_workspace(case, workspace)
    payload: dict[str, object] = {
        "case_id": case.case_id,
        "model": model,
        "reasoning_effort": reasoning_effort,
        "codex_exit_code": result.returncode,
        "elapsed_seconds": elapsed,
        "verification": verification,
    }
    (output_dir / "result.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
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
