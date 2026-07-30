from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import cast

import pytest
import yaml

from scripts import run_writable_agent_eval as evaluation
from scripts.run_writable_agent_eval import CaseSpec, EvaluationError

INVALID_CASES: list[tuple[dict[str, object], str]] = [
    ({"id": ""}, "id must be a non-empty string"),
    ({"allowed_changes": []}, "allowed_changes must be a non-empty list"),
    ({"allowed_changes": [1]}, "allowed_changes entries must be"),
    ({"verify": []}, "verify must be a non-empty command list"),
    ({"verify": ["bad"]}, "verify entries must be non-empty lists"),
    ({"verify": [[]]}, "verify entries must be non-empty lists"),
    ({"verify": [[1]]}, "verify command parts must be strings"),
    ({"allowed_changes": ["other.txt"]}, "required_changes must be allowed"),
    ({"fixture": "missing"}, "missing fixture"),
]


def write_fixture(root: Path, name: str = "sample") -> Path:
    fixture = root / "fixtures" / name
    fixture.mkdir(parents=True)
    (fixture / "value.txt").write_text("before\n", encoding="utf-8")
    return fixture


def case_data(**updates: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": "T01",
        "title": "Test case",
        "fixture": "sample",
        "prompt": "Fix the fixture.",
        "verify": [["python", "-c", "print('ok')"]],
        "allowed_changes": ["value.txt"],
        "required_changes": ["value.txt"],
    }
    data.update(updates)
    return data


def write_case(path: Path, **updates: object) -> Path:
    path.write_text(
        yaml.safe_dump(case_data(**updates), sort_keys=False),
        encoding="utf-8",
    )
    return path


@pytest.fixture
def evaluation_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "evaluation"
    write_fixture(root)
    monkeypatch.setattr(evaluation, "EVALUATION_ROOT", root)
    return root


def test_load_case_accepts_valid_contract(
    tmp_path: Path, evaluation_root: Path
) -> None:
    path = write_case(tmp_path / "case.yaml")
    case = evaluation.load_case(path)
    assert case == CaseSpec(
        case_id="T01",
        title="Test case",
        fixture="sample",
        prompt="Fix the fixture.",
        verify=(("python", "-c", "print('ok')"),),
        allowed_changes=frozenset({"value.txt"}),
        required_changes=frozenset({"value.txt"}),
    )


@pytest.mark.parametrize(
    ("updates", "message"),
    INVALID_CASES,
)
def test_load_case_rejects_invalid_contracts(
    tmp_path: Path,
    evaluation_root: Path,
    updates: dict[str, object],
    message: str,
) -> None:
    path = write_case(tmp_path / "case.yaml", **updates)
    with pytest.raises(EvaluationError, match=message):
        evaluation.load_case(path)


@pytest.mark.parametrize("content", ["- item\n", ":\n"])
def test_load_case_rejects_unreadable_shapes(
    tmp_path: Path, evaluation_root: Path, content: str
) -> None:
    path = tmp_path / "case.yaml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(EvaluationError, match=r"case must be|cannot load case"):
        evaluation.load_case(path)


def test_prepare_workspace_and_changed_paths(
    tmp_path: Path, evaluation_root: Path
) -> None:
    case = evaluation.load_case(write_case(tmp_path / "case.yaml"))
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    assert evaluation.changed_paths(workspace) == frozenset()
    (workspace / "value.txt").write_text("after\n", encoding="utf-8")
    assert evaluation.changed_paths(workspace) == frozenset({"value.txt"})
    with pytest.raises(EvaluationError, match="workspace already exists"):
        evaluation.prepare_workspace(case, workspace)


def test_prepare_workspace_reports_git_failure(
    tmp_path: Path,
    evaluation_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = evaluation.load_case(write_case(tmp_path / "case.yaml"))

    def failed_run(
        command: tuple[str, ...] | list[str],
        cwd: Path,
        *,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=command, returncode=1, stdout="", stderr="broken"
        )

    monkeypatch.setattr(
        evaluation,
        "_run",
        failed_run,
    )
    with pytest.raises(EvaluationError, match=r"git init.*broken"):
        evaluation.prepare_workspace(case, tmp_path / "workspace")


def test_changed_paths_handles_rename_and_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def renamed_run(
        command: tuple[str, ...] | list[str],
        cwd: Path,
        *,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="R  old.txt -> new.txt\n?? extra.txt\n",
            stderr="",
        )

    monkeypatch.setattr(
        evaluation,
        "_run",
        renamed_run,
    )
    assert evaluation.changed_paths(tmp_path) == frozenset({"new.txt", "extra.txt"})

    def failed_run(
        command: tuple[str, ...] | list[str],
        cwd: Path,
        *,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=command, returncode=1, stdout="", stderr="no repository"
        )

    monkeypatch.setattr(
        evaluation,
        "_run",
        failed_run,
    )
    with pytest.raises(EvaluationError, match="git status failed"):
        evaluation.changed_paths(tmp_path)


def test_verify_workspace_classifies_pass_and_scope_failures(
    tmp_path: Path, evaluation_root: Path
) -> None:
    case = evaluation.load_case(write_case(tmp_path / "case.yaml"))
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    (workspace / "value.txt").write_text("after\n", encoding="utf-8")
    result = evaluation.verify_workspace(case, workspace)
    assert result["passed"] is True
    assert result["changed_paths"] == ["value.txt"]
    (workspace / "extra.txt").write_text("extra\n", encoding="utf-8")
    result = evaluation.verify_workspace(case, workspace)
    assert result["passed"] is False
    assert result["unexpected_changes"] == ["extra.txt"]


def test_verify_workspace_reports_missing_change_and_command_failure(
    tmp_path: Path, evaluation_root: Path
) -> None:
    path = write_case(
        tmp_path / "case.yaml",
        verify=[["python", "-c", "raise SystemExit(2)"]],
    )
    case = evaluation.load_case(path)
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    result = evaluation.verify_workspace(case, workspace)
    assert result["passed"] is False
    assert result["missing_required_changes"] == ["value.txt"]
    checks = cast(list[dict[str, object]], result["checks"])
    assert checks[0]["exit_code"] == 2


def test_w06_verifies_fallback_adoption_and_local_contract_precedence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository_evaluation_root = (
        Path(__file__).resolve().parents[1] / "evaluations/ai-native-implementation"
    )
    monkeypatch.setattr(evaluation, "EVALUATION_ROOT", repository_evaluation_root)
    case = evaluation.load_case(repository_evaluation_root / "cases/W06.yaml")
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)

    before = evaluation.verify_workspace(case, workspace)
    assert before["passed"] is False

    fallback = workspace / "fallback-project/pyproject.toml"
    fallback.write_text(
        fallback.read_text(encoding="utf-8")
        + '\n[tool.ruff.lint]\nselect = ["E", "F", "I", "UP", "B", "SIM", "RUF"]\n',
        encoding="utf-8",
    )

    fallback.write_text(
        fallback.read_text(encoding="utf-8") + "preview = true\n",
        encoding="utf-8",
    )
    lint_preview = evaluation.verify_workspace(case, workspace)
    assert lint_preview["passed"] is False
    checks = cast(list[dict[str, object]], lint_preview["checks"])
    assert "must not enable Ruff preview" in cast(str, checks[0]["stderr"])

    fallback.write_text(
        fallback.read_text(encoding="utf-8").replace("preview = true\n", ""),
        encoding="utf-8",
    )
    after = evaluation.verify_workspace(case, workspace)
    assert after["passed"] is True
    assert after["changed_paths"] == ["fallback-project/pyproject.toml"]


@pytest.mark.parametrize(
    ("modifier", "configuration"),
    [
        ("extend-select", 'extend-select = ["S"]\n'),
        ("ignore", 'ignore = ["F"]\n'),
        (
            "per-file-ignores",
            'per-file-ignores = {"*.py" = ["E", "F", "I", "UP", "B", "SIM", "RUF"]}\n',
        ),
    ],
)
def test_w06_rejects_effective_rule_selection_modifiers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    modifier: str,
    configuration: str,
) -> None:
    repository_evaluation_root = (
        Path(__file__).resolve().parents[1] / "evaluations/ai-native-implementation"
    )
    monkeypatch.setattr(evaluation, "EVALUATION_ROOT", repository_evaluation_root)
    case = evaluation.load_case(repository_evaluation_root / "cases/W06.yaml")
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)

    fallback = workspace / "fallback-project/pyproject.toml"
    fallback.write_text(
        fallback.read_text(encoding="utf-8")
        + "\n[tool.ruff.lint]\n"
        + 'select = ["E", "F", "I", "UP", "B", "SIM", "RUF"]\n'
        + configuration,
        encoding="utf-8",
    )

    result = evaluation.verify_workspace(case, workspace)
    assert result["passed"] is False
    checks = cast(list[dict[str, object]], result["checks"])
    assert modifier in cast(str, checks[0]["stderr"])


def test_build_codex_command_contains_frozen_controls(tmp_path: Path) -> None:
    case = CaseSpec(
        "T01",
        "title",
        "fixture",
        "do work",
        (("true",),),
        frozenset({"value.txt"}),
        frozenset({"value.txt"}),
    )
    command = evaluation.build_codex_command(
        case, tmp_path / "work", tmp_path / "final", "model", "high"
    )
    assert command[0:2] == ["codex", "exec"]
    assert "--ephemeral" in command
    assert "--ignore-user-config" in command
    assert "--ignore-rules" not in command
    assert command.count("--disable") == 2
    assert "workspace-write" in command
    assert 'model_reasoning_effort="high"' in command
    assert command[-1] == "do work"


def test_install_arm_home_validates_inputs_and_installs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    auth = tmp_path / "auth.json"
    home = tmp_path / "home"
    with pytest.raises(EvaluationError, match="missing arm installer"):
        evaluation.install_arm_home(source, auth, home)
    (source / "install.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    with pytest.raises(EvaluationError, match="missing Codex auth"):
        evaluation.install_arm_home(source, auth, home)
    auth.write_text("{}\n", encoding="utf-8")
    evaluation.install_arm_home(source, auth, home)
    assert (home / "auth.json").resolve() == auth

    def failed_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="install failed"
        )

    monkeypatch.setattr(evaluation, "_run", failed_run)
    with pytest.raises(EvaluationError, match="arm install failed"):
        evaluation.install_arm_home(source, auth, tmp_path / "failed-home")


def test_run_case_writes_private_evidence_and_result(
    tmp_path: Path,
    evaluation_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = evaluation.load_case(
        write_case(tmp_path / "case.yaml", verify=[["python", "-c", "print('ok')"]])
    )
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    (workspace / "value.txt").write_text("after\n", encoding="utf-8")
    source = tmp_path / "source"
    source.mkdir()
    auth = tmp_path / "auth.json"
    auth.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "output"

    def no_install(source_root: Path, auth_file: Path, codex_home: Path) -> None:
        return None

    monkeypatch.setattr(evaluation, "install_arm_home", no_install)
    original_run = evaluation._run

    def fake_codex(
        command: tuple[str, ...] | list[str],
        cwd: Path,
        *,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        if command[0] == "codex":
            return subprocess.CompletedProcess(
                args=command, returncode=0, stdout='{"type":"done"}\n', stderr=""
            )
        return original_run(command, cwd, env=env)

    monkeypatch.setattr(evaluation, "_run", fake_codex)
    result = evaluation.run_case(
        case, workspace, source, auth, output, "model", "medium"
    )
    assert result["codex_exit_code"] == 0
    assert cast(dict[str, object], result["verification"])["passed"] is True
    assert (output / "trajectory.jsonl").read_text(encoding="utf-8")
    assert (output / "codex.stderr").read_text(encoding="utf-8") == ""
    assert (
        json.loads((output / "result.json").read_text(encoding="utf-8"))["case_id"]
        == "T01"
    )
    with pytest.raises(EvaluationError, match="output directory already exists"):
        evaluation.run_case(case, workspace, source, auth, output, "model", "medium")


def test_run_case_rejects_unprepared_workspace(
    tmp_path: Path, evaluation_root: Path
) -> None:
    case = evaluation.load_case(write_case(tmp_path / "case.yaml"))
    with pytest.raises(EvaluationError, match="workspace is not prepared"):
        evaluation.run_case(
            case,
            tmp_path / "workspace",
            tmp_path,
            tmp_path / "auth",
            tmp_path / "output",
            "model",
            "medium",
        )


def test_main_prepare_verify_run_and_error(
    tmp_path: Path,
    evaluation_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    case_path = write_case(tmp_path / "case.yaml")
    workspace = tmp_path / "workspace"
    assert (
        evaluation.main(
            ["prepare", "--case", str(case_path), "--workspace", str(workspace)]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["state"] == "prepared"
    assert (
        evaluation.main(
            ["verify", "--case", str(case_path), "--workspace", str(workspace)]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["passed"] is False

    def successful_run(
        case: CaseSpec,
        workspace: Path,
        source_root: Path,
        auth_file: Path,
        output_dir: Path,
        model: str,
        reasoning_effort: str,
    ) -> dict[str, object]:
        return {"case_id": case.case_id, "verification": {"passed": True}}

    monkeypatch.setattr(evaluation, "run_case", successful_run)
    run_args = [
        "run",
        "--case",
        str(case_path),
        "--workspace",
        str(workspace),
        "--source-root",
        str(tmp_path),
        "--auth-file",
        str(tmp_path / "auth"),
        "--output-dir",
        str(tmp_path / "output"),
        "--model",
        "model",
    ]
    assert evaluation.main(run_args) == 0
    assert json.loads(capsys.readouterr().out)["case_id"] == "T01"

    def failed_load(path: Path) -> CaseSpec:
        raise EvaluationError("bad case")

    monkeypatch.setattr(evaluation, "load_case", failed_load)
    assert evaluation.main(run_args) == 1
    assert json.loads(capsys.readouterr().out)["state"] == "failed"
