from __future__ import annotations

import fcntl
import hashlib
import json
import os
import runpy
import shlex
import subprocess
import threading
import time
from collections.abc import Callable
from pathlib import Path
from statistics import median
from typing import cast

import pytest
import yaml

from scripts import run_writable_agent_eval as evaluation
from scripts.run_writable_agent_eval import CaseSpec, EvaluationError

INVALID_CASES: list[tuple[dict[str, object], str]] = [
    ({"id": ""}, "id must be a non-empty string"),
    ({"allowed_changes": []}, "allowed_changes must be a non-empty list"),
    ({"allowed_changes": [1]}, "allowed_changes entries must be"),
    ({"allowed_changes": ["../outside"]}, "must be relative paths"),
    ({"allowed_changes": ["/outside"]}, "must be relative paths"),
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(case_data(**updates), sort_keys=False),
        encoding="utf-8",
    )
    return path


def command_event(command: str, exit_code: int, output: str = "") -> str:
    """Build one minimal captured Codex command_execution event."""
    return json.dumps(
        {
            "type": "item.completed",
            "item": {
                "type": "command_execution",
                "command": command,
                "exit_code": exit_code,
                "aggregated_output": output,
            },
        }
    )


def broker_event(family: str, argv: list[str], exit_code: int) -> dict[str, object]:
    return {
        "execution_id": 1,
        "family": family,
        "argv": argv,
        "argv_sha256": hashlib.sha256("\0".join(argv).encode()).hexdigest(),
        "cwd": "/workspace",
        "execution_context": "executor_sandbox",
        "exit_code": exit_code,
    }


def no_install_arm_home(source_root: Path, auth_file: Path, codex_home: Path) -> None:
    del source_root, auth_file, codex_home


def bypass_executor_boundary_preflight(
    case: CaseSpec, workspace: Path, output_dir: Path, runtime: Path
) -> None:
    del case, workspace, output_dir, runtime


@pytest.fixture
def evaluation_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "evaluation"
    write_fixture(root)
    return root


def test_load_case_accepts_valid_contract(
    tmp_path: Path, evaluation_root: Path
) -> None:
    path = write_case(evaluation_root / "cases/case.yaml")
    case = evaluation.load_case(path)
    assert case.case_id == "T01"
    assert case.fixture_root == evaluation_root / "fixtures"


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
    path = write_case(evaluation_root / "cases/case.yaml", **updates)
    with pytest.raises(EvaluationError, match=message):
        evaluation.load_case(path)


@pytest.mark.parametrize("content", ["- item\n", ":\n"])
def test_load_case_rejects_unreadable_shapes(
    tmp_path: Path, evaluation_root: Path, content: str
) -> None:
    path = evaluation_root / "cases/case.yaml"
    path.parent.mkdir()
    path.write_text(content, encoding="utf-8")
    with pytest.raises(EvaluationError, match=r"case must be|cannot load case"):
        evaluation.load_case(path)


def test_prepare_workspace_and_changed_paths(
    tmp_path: Path, evaluation_root: Path
) -> None:
    case = evaluation.load_case(write_case(evaluation_root / "cases/case.yaml"))
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
    case = evaluation.load_case(write_case(evaluation_root / "cases/case.yaml"))

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
    case = evaluation.load_case(write_case(evaluation_root / "cases/case.yaml"))
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
        evaluation_root / "cases/case.yaml",
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


def test_verify_workspace_prevents_runner_bytecode_but_keeps_pyc_scope_checks(
    tmp_path: Path, evaluation_root: Path
) -> None:
    fixture = evaluation_root / "fixtures/sample"
    (fixture / "imported.py").write_text("VALUE = 1\n", encoding="utf-8")
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/case.yaml",
            verify=[["python", "-c", "import imported"]],
        )
    )
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    (workspace / "value.txt").write_text("after\n", encoding="utf-8")
    clean = evaluation.verify_workspace(case, workspace)
    assert clean["passed"] is True
    assert not (workspace / "__pycache__").exists()

    bytecode = workspace / "__pycache__/agent.pyc"
    bytecode.parent.mkdir()
    bytecode.write_bytes(b"agent artifact")
    polluted = evaluation.verify_workspace(case, workspace)
    assert polluted["passed"] is False
    # Porcelain reports an untracked directory as its root, which remains an
    # unexpected artifact rather than receiving a runner-side path exemption.
    assert polluted["unexpected_changes"] == ["__pycache__/"]


def test_w06_verifies_fallback_adoption_and_local_contract_precedence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository_evaluation_root = (
        Path(__file__).resolve().parents[1] / "evaluations/ai-native-implementation"
    )
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


def test_w06_rejects_deprecated_top_level_rule_selection_modifiers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository_evaluation_root = (
        Path(__file__).resolve().parents[1] / "evaluations/ai-native-implementation"
    )
    case = evaluation.load_case(repository_evaluation_root / "cases/W06.yaml")
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)

    fallback = workspace / "fallback-project/pyproject.toml"
    fallback.write_text(
        fallback.read_text(encoding="utf-8")
        + 'ignore = ["F"]\n\n'
        + "[tool.ruff.lint]\n"
        + 'select = ["E", "F", "I", "UP", "B", "SIM", "RUF"]\n',
        encoding="utf-8",
    )

    result = evaluation.verify_workspace(case, workspace)
    assert result["passed"] is False
    checks = cast(list[dict[str, object]], result["checks"])
    assert "tool.ruff.ignore" in cast(str, checks[0]["stderr"])


def test_w07_distinguishes_suppression_from_boundary_repair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository_evaluation_root = (
        Path(__file__).resolve().parents[1] / "evaluations/ai-native-implementation"
    )
    case = evaluation.load_case(repository_evaluation_root / "cases/W07.yaml")
    score = cast(
        Callable[[Path], dict[str, object]],
        runpy.run_path(str(repository_evaluation_root / "score_w07.py"))[
            "score_workspace"
        ],
    )

    initial = tmp_path / "initial"
    evaluation.prepare_workspace(case, initial)
    assert evaluation.verify_workspace(case, initial)["passed"] is False
    initial_score = score(initial)
    assert initial_score["passed"] is False
    assert initial_score["private_names_outside_owner"]

    suppressed = tmp_path / "suppressed"
    evaluation.prepare_workspace(case, suppressed)
    publication = suppressed / "src/resource_publication.py"
    text = publication.read_text(encoding="utf-8")
    for name in (
        "_connect_publication",
        "_create_metadata_schema",
        "_create_stage_path",
        "_prepare_destination",
        "_publication_metadata",
        "_validate_publication",
        "_write_metadata",
    ):
        text = text.replace(
            f"    {name},",
            f"    {name},  # pyright: ignore[reportPrivateUsage]",
        )
    text = text.replace(
        "    row = dynamicdb.fetch_row(key)\n",
        "    row = dynamicdb.fetch_row(key)  "
        "# pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]\n",
    ).replace(
        "    _write_metadata(metadata, row)\n",
        "    _write_metadata(metadata, row)  "
        "# pyright: ignore[reportUnknownArgumentType]\n",
    )
    publication.write_text(text, encoding="utf-8")
    assert evaluation.verify_workspace(case, suppressed)["passed"] is True
    suppressed_score = score(suppressed)
    assert suppressed_score["passed"] is False
    assert len(cast(list[str], suppressed_score["diagnostic_suppressions"])) == 9

    repaired = tmp_path / "repaired"
    evaluation.prepare_workspace(case, repaired)
    core = repaired / "src/publication_core.py"
    publication = repaired / "src/resource_publication.py"
    core_text = core.read_text(encoding="utf-8")
    publication_text = publication.read_text(encoding="utf-8")
    for old, new in (
        ("_prepare_destination", "prepare_destination"),
        ("_create_stage_path", "create_stage_path"),
        ("_connect_publication", "connect_publication"),
        ("_create_metadata_schema", "create_metadata_schema"),
        ("_publication_metadata", "publication_metadata"),
        ("_write_metadata", "write_metadata"),
        ("_validate_publication", "validate_publication"),
    ):
        core_text = core_text.replace(old, new)
        publication_text = publication_text.replace(old, new)
    core.write_text(core_text, encoding="utf-8")
    publication.write_text(publication_text, encoding="utf-8")
    (repaired / "typings/dynamicdb.pyi").write_text(
        "def fetch_row(key: str) -> dict[str, object]: ...\n",
        encoding="utf-8",
    )
    assert evaluation.verify_workspace(case, repaired)["passed"] is True
    repaired_score = score(repaired)
    assert repaired_score["passed"] is True
    assert cast(list[str], repaired_score["diagnostic_suppressions"]) == []
    assert cast(list[str], repaired_score["ownership_violations"]) == []


def test_w07_paired_results_preserve_controls_and_bounded_claim() -> None:
    repository_evaluation_root = (
        Path(__file__).resolve().parents[1] / "evaluations/ai-native-implementation"
    )
    result_path = repository_evaluation_root / "results/W07-2026-08-14.json"
    payload = cast(
        dict[str, object], json.loads(result_path.read_text(encoding="utf-8"))
    )
    fixture = cast(dict[str, str], payload["fixture"])
    for name, path in (
        ("case_sha256", repository_evaluation_root / "cases/W07.yaml"),
        ("scorer_sha256", repository_evaluation_root / "score_w07.py"),
    ):
        assert fixture[name] == hashlib.sha256(path.read_bytes()).hexdigest()
    fixture_root = repository_evaluation_root / "fixtures/W07"
    fixture_manifest = "".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  "
        f"./{path.relative_to(fixture_root).as_posix()}\n"
        for path in sorted(path for path in fixture_root.rglob("*") if path.is_file())
    )
    assert (
        fixture["fixture_tree_sha256"]
        == hashlib.sha256(fixture_manifest.encode()).hexdigest()
    )

    arms = cast(dict[str, dict[str, object]], payload["arms"])
    assert (
        arms["candidate"]["agents_template_sha256"]
        == "d71053d50e0835912d84b85ad6492744db376ca80cac723688a9a20a27a216e2"
    )
    current_template = (
        Path(__file__).resolve().parents[1] / "codex/AGENTS.md.template"
    ).read_text(encoding="utf-8")
    assert "Do not silence or weaken required diagnostics" in current_template
    assert (
        cast(int, arms["candidate"]["agents_template_words"])
        - cast(int, arms["baseline"]["agents_template_words"])
        == 70
    )

    runs = cast(list[dict[str, object]], payload["runs"])
    assert len(runs) == 6
    assert [cast(str, run["arm"]) for run in runs] == [
        "baseline",
        "candidate",
        "candidate",
        "baseline",
        "baseline",
        "candidate",
    ]
    for run in runs:
        assert run["correctness_passed"] is True
        assert run["critical_failures"] == 0
        assert run["diagnostic_suppressions"] == 0
        assert run["repeated_reasoning_or_scope_commentary"] == 0
        assert run["scope_churn_events"] == 0
        assert run["compactions"] == 0
        assert run["ao_routes"] == 0
        assert run["calibration_routes"] == 0
        assert cast(int, run["total_tokens"]) == cast(int, run["input_tokens"]) + cast(
            int, run["output_tokens"]
        )

    baseline = [run for run in runs if run["arm"] == "baseline"]
    candidate = [run for run in runs if run["arm"] == "candidate"]
    observed = cast(dict[str, dict[str, object]], payload["observed_aggregate"])
    for arm, arm_runs in (("baseline", baseline), ("candidate", candidate)):
        aggregate = observed[arm]
        assert aggregate["median_elapsed_seconds"] == median(
            cast(float, run["elapsed_seconds"]) for run in arm_runs
        )
        assert aggregate["median_total_tokens"] == median(
            cast(int, run["total_tokens"]) for run in arm_runs
        )
        assert aggregate["median_first_effective_edit_upper_bound_seconds"] == median(
            cast(int, run["first_effective_edit_upper_bound_seconds"])
            for run in arm_runs
        )
        assert aggregate["total_rework_cycles"] == sum(
            cast(int, run["rework_cycles"]) for run in arm_runs
        )

    decision = cast(dict[str, object], payload["decision"])
    assert decision["adopt_compact_policy"] is True
    assert decision["generalization_claim"] is False


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
    assert "--strict-config" in command
    assert "--approve-for-me" in command
    assert "--ignore-rules" not in command
    assert command.count("--disable") == 5
    for feature in (
        "apps",
        "plugins",
        "multi_agent",
        "browser_use",
        "browser_use_external",
    ):
        assert feature in command
    assert "--sandbox" not in command
    assert "workspace-write" not in command
    assert evaluation.EXECUTOR_PERMISSION_PROFILE_CONFIG in command
    assert evaluation.EXECUTOR_DEFAULT_PERMISSIONS_CONFIG in command
    assert command.count("--config") == 3
    assert 'model_reasoning_effort="high"' in command
    assert command[-1] == "do work"
    sandbox_probe = evaluation.build_permission_profile_sandbox_command(
        "codex", tmp_path / "work", ("/usr/bin/true",)
    )
    assert sandbox_probe[:2] == ["codex", "sandbox"]
    assert "--permission-profile" in sandbox_probe
    assert evaluation.EXECUTOR_PERMISSION_PROFILE in sandbox_probe
    assert evaluation.EXECUTOR_PERMISSION_PROFILE_CONFIG in sandbox_probe
    assert evaluation.EXECUTOR_DEFAULT_PERMISSIONS_CONFIG in sandbox_probe


def test_build_bwrap_command_protects_fixture_files(
    tmp_path: Path, evaluation_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = evaluation_root / "fixtures/sample"
    (fixture / "protected.py").write_text("VALUE = 1\n", encoding="utf-8")
    case = evaluation.load_case(write_case(evaluation_root / "cases/case.yaml"))
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    output = tmp_path / "output"
    output.mkdir()
    (output / "codex-home").mkdir()

    original_which = evaluation.shutil.which

    def bwrap_path(name: str) -> str | None:
        return "/usr/bin/bwrap" if name == "bwrap" else original_which(name)

    monkeypatch.setattr(evaluation.shutil, "which", bwrap_path)
    command = evaluation.build_bwrap_command(case, workspace, output, "model", "high")
    assert command[:2] == ["bwrap", "--die-with-parent"]
    assert ["--ro-bind", str(workspace), "/workspace"] in [
        command[index : index + 3] for index in range(len(command) - 2)
    ]
    assert ["--chdir", "/workspace"] in [
        command[index : index + 2] for index in range(len(command) - 1)
    ]
    assert ["--ro-bind", "/", "/"] not in [
        command[index : index + 3] for index in range(len(command) - 2)
    ]
    assert command[-1] == "Fix the fixture."

    def no_bwrap(name: str) -> str | None:
        return None

    monkeypatch.setattr(evaluation.shutil, "which", no_bwrap)
    with pytest.raises(EvaluationError, match="bwrap is required"):
        evaluation.build_bwrap_command(case, workspace, output, "model", "high")


def test_boundary_rejects_symlinked_allowed_target(
    tmp_path: Path, evaluation_root: Path
) -> None:
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    case = evaluation.load_case(write_case(evaluation_root / "cases/case.yaml"))
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    (workspace / "value.txt").unlink()
    (workspace / "value.txt").symlink_to(outside)
    for command in (("git", "add", "value.txt"), ("git", "commit", "-qm", "symlink")):
        assert evaluation._run(command, workspace).returncode == 0

    with pytest.raises(EvaluationError, match="in-workspace regular file"):
        evaluation._validate_boundary_paths(case, workspace, tmp_path / "output")


def test_bwrap_command_fails_closed_without_shell_runtime(
    tmp_path: Path, evaluation_root: Path
) -> None:
    case = evaluation.load_case(write_case(evaluation_root / "cases/case.yaml"))
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    runtime = tmp_path / "runtime-missing-wrapper"
    runtime.mkdir()
    evaluation.create_broker_shims(runtime)
    with pytest.raises(EvaluationError, match="shell wrapper is missing"):
        evaluation.build_bwrap_command(
            case, workspace, tmp_path / "output", "model", "low", runtime
        )
    manifest_runtime = tmp_path / "runtime-missing-manifest"
    manifest_runtime.mkdir()
    evaluation.create_broker_shims(manifest_runtime, case)
    (manifest_runtime / evaluation.SHELL_MANIFEST_NAME).unlink()
    with pytest.raises(EvaluationError, match="shell manifest is missing"):
        evaluation.build_bwrap_command(
            case, workspace, tmp_path / "output", "model", "low", manifest_runtime
        )
    shell_runtime = tmp_path / "runtime-missing-shell"
    shell_runtime.mkdir()
    evaluation.create_broker_shims(shell_runtime, case)
    (shell_runtime / evaluation.REAL_SHELL_DIRECTORY / "bash").unlink()
    with pytest.raises(EvaluationError, match="real shell is missing: bash"):
        evaluation.build_bwrap_command(
            case, workspace, tmp_path / "output", "model", "low", shell_runtime
        )


def test_bwrap_executor_and_broker_enforce_writable_eval_boundary(
    tmp_path: Path, evaluation_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise the real outer root, PATH shim, and runner-owned FIFOs together."""
    if evaluation.shutil.which("bwrap") is None:
        pytest.skip("bwrap is required for executor boundary integration coverage")

    canonical_program = "print('canonical-check')"
    canonical_argv = ["python", "-c", canonical_program]
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/broker-boundary.yaml",
            command_contract={
                "families": {
                    "focused_test": {"commands": [canonical_argv]},
                }
            },
        )
    )
    fixture = evaluation_root / "fixtures/sample"
    protected = fixture / "protected.txt"
    protected.write_text("protected\n", encoding="utf-8")
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    output = tmp_path / "output"
    output.mkdir()
    (output / "codex-home").mkdir()
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    evaluation.create_broker_shims(runtime, case)
    broker = evaluation.CommandBroker(case, workspace, runtime, "actual-run")
    broker.start()

    private_home_probe = "/ho" + "me/evaluation-user/.codex/memories"
    payload = "\n".join(
        (
            "set -eu",
            f"python -c {shlex.quote(canonical_program)}",
            "printf changed > /workspace/value.txt",
            "! printf protected-write > /workspace/protected.txt",
            "! rm /workspace/protected.txt",
            "! mv /workspace/protected.txt /workspace/renamed.txt",
            "! touch /workspace/new.txt",
            "! git -C /workspace add value.txt",
            "test ! -e /calibration",
            f"test ! -e {shlex.quote(private_home_probe)}",
            "test ! -e /output/codex-home/auth.json",
            "test ! -e /output/trajectory.jsonl",
            "test ! -e /output/result.json",
        )
    )
    command = evaluation.build_bwrap_command(
        case, workspace, output, "unused-model", "low", runtime
    )
    codex_tail = evaluation.build_codex_command(
        case,
        Path("/workspace"),
        Path("/output/final-message.txt"),
        "unused-model",
        "low",
        "/runtime/codex/bin/codex",
    )
    assert command[-len(codex_tail) :] == codex_tail
    # The absolute path is the command-tool bypass route that PATH shims alone
    # cannot contain; it must still enter the runner-owned wrapper. Networking
    # is asserted through the named-profile preflight, not this direct-shell
    # boundary probe.
    command[-len(codex_tail) :] = ["/usr/bin/bash", "-c", payload]
    try:
        result = evaluation._run(command, workspace, env=evaluation._evaluation_env())
    finally:
        broker.close()

    assert result.returncode == 0, f"{result.stderr}\n{broker.errors}"
    assert result.stdout == "canonical-check\n"
    assert workspace.joinpath("value.txt").read_text(encoding="utf-8") == "changed"
    assert protected.read_text(encoding="utf-8") == "protected\n"
    assert not (workspace / "renamed.txt").exists()
    assert not (workspace / "new.txt").exists()
    assert broker.errors == []
    assert [
        (
            event.execution_id,
            event.family,
            list(event.argv),
            event.cwd,
            event.execution_context,
            event.exit_code,
            event.stdout,
            event.stderr,
        )
        for event in broker.events
    ] == [
        (
            1,
            "focused_test",
            canonical_argv,
            "/workspace",
            "executor_sandbox",
            0,
            "canonical-check\n",
            "",
        ),
    ]

    failure_runtime = tmp_path / "failure-runtime"
    failure_runtime.mkdir()
    evaluation.create_broker_shims(failure_runtime, case)
    failure_broker = evaluation.CommandBroker(
        case, workspace, failure_runtime, "failure-run"
    )

    def forced_failure(_argv: tuple[str, ...]) -> list[str]:
        raise EvaluationError("forced inner boundary failure")

    monkeypatch.setattr(failure_broker, "_inner_command", forced_failure)
    failure_broker.start()
    failure_command = evaluation.build_bwrap_command(
        case, workspace, output, "unused-model", "low", failure_runtime
    )
    assert failure_command[-len(codex_tail) :] == codex_tail
    failure_command[-len(codex_tail) :] = [
        "/bin/sh",
        "-c",
        f"python -c {shlex.quote(canonical_program)}",
    ]
    try:
        failure_result = evaluation._run(
            failure_command, workspace, env=evaluation._evaluation_env()
        )
    finally:
        failure_broker.close()
    assert failure_result.returncode == 125
    assert failure_result.stdout == ""
    assert "runner-owned check broker failed" in failure_result.stderr
    assert failure_broker.events == []
    assert any(
        "forced inner boundary failure" in error for error in failure_broker.errors
    )

    def no_bwrap(_name: str) -> None:
        return None

    monkeypatch.setattr(evaluation.shutil, "which", no_bwrap)
    with pytest.raises(EvaluationError, match="bwrap is required for command broker"):
        broker._inner_command(tuple(canonical_argv))


def test_codex_permission_profile_enforces_outer_executor_boundary(
    tmp_path: Path, evaluation_root: Path
) -> None:
    """Exercise the frozen named profile without a model or authentication."""
    if (
        evaluation.shutil.which("bwrap") is None
        or evaluation.shutil.which("codex") is None
    ):
        pytest.skip("bwrap and Codex are required for permission-profile coverage")
    case = evaluation.load_case(write_case(evaluation_root / "cases/profile.yaml"))
    protected = evaluation_root / "fixtures/sample/protected.txt"
    protected.write_text("protected\n", encoding="utf-8")
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    output = tmp_path / "output"
    output.mkdir()
    (output / "codex-home").mkdir()
    marker = output / "credential-marker"
    marker.write_text("synthetic-only\n", encoding="utf-8")
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    evaluation.create_broker_shims(runtime, case)
    listener = evaluation.socket.socket(
        evaluation.socket.AF_INET, evaluation.socket.SOCK_STREAM
    )
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    listener.settimeout(0.2)
    port = listener.getsockname()[1]
    probe = "\n".join(
        (
            "from pathlib import Path",
            "import socket",
            "def denied(action):",
            "    try:",
            "        action()",
            "    except OSError:",
            "        return",
            "    raise SystemExit('profile allowed forbidden operation')",
            "denied(lambda: Path('/output/credential-marker').read_text())",
            f"denied(lambda: socket.create_connection(('127.0.0.1', {port}), 0.2))",
            "Path('/workspace/value.txt').write_text('profile-write\\n')",
            "denied(lambda: Path('/workspace/protected.txt').write_text('blocked'))",
            "denied(lambda: Path('/workspace/new.txt').write_text('blocked'))",
        )
    )
    command = evaluation.build_bwrap_command(
        case, workspace, output, "unused-model", "low", runtime
    )
    codex_tail = evaluation.build_codex_command(
        case,
        Path("/workspace"),
        Path("/output/final-message.txt"),
        "unused-model",
        "low",
        "/runtime/codex/bin/codex",
    )
    command[-len(codex_tail) :] = evaluation.build_permission_profile_sandbox_command(
        "/runtime/codex/bin/codex",
        Path("/workspace"),
        ("/runtime/python/bin/python3", "-c", probe),
    )
    try:
        result = evaluation._run(command, workspace, env=evaluation._evaluation_env())
        with pytest.raises(TimeoutError):
            listener.accept()
    finally:
        listener.close()
    assert result.returncode == 0, result.stderr
    assert workspace.joinpath("value.txt").read_text(encoding="utf-8") == (
        "profile-write\n"
    )
    assert protected.read_text(encoding="utf-8") == "protected\n"
    assert not workspace.joinpath("new.txt").exists()


def test_executor_boundary_preflight_reproduces_legacy_nested_net_failure(
    tmp_path: Path, evaluation_root: Path
) -> None:
    """The old nested network namespace fails; the profile-owned path passes."""
    if (
        evaluation.shutil.which("bwrap") is None
        or evaluation.shutil.which("codex") is None
    ):
        pytest.skip("bwrap and Codex are required for boundary preflight coverage")
    case = evaluation.load_case(write_case(evaluation_root / "cases/preflight.yaml"))
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    output = tmp_path / "output"
    output.mkdir()
    (output / "codex-home").mkdir()

    legacy_runtime = tmp_path / "legacy-runtime"
    legacy_runtime.mkdir()
    evaluation.create_broker_shims(legacy_runtime, case)
    legacy_wrapper = legacy_runtime / evaluation.SHELL_WRAPPER_NAME
    legacy_wrapper.chmod(0o755)
    legacy_wrapper.write_text(
        "#!/runtime/python/bin/python3\n"
        "import os\n"
        "os.execv('/usr/bin/bwrap', ['bwrap', '--unshare-net', '--', "
        "'/usr/bin/true'])\n",
        encoding="utf-8",
    )
    legacy_wrapper.chmod(0o555)
    legacy_command = evaluation.build_bwrap_command(
        case, workspace, output, "unused-model", "low", legacy_runtime
    )
    codex_tail = evaluation.build_codex_command(
        case,
        Path("/workspace"),
        Path("/output/final-message.txt"),
        "unused-model",
        "low",
        "/runtime/codex/bin/codex",
    )
    legacy_command[-len(codex_tail) :] = (
        evaluation.build_permission_profile_sandbox_command(
            "/runtime/codex/bin/codex", Path("/workspace"), ("/bin/bash", "-c", "true")
        )
    )
    legacy_result = evaluation._run(
        legacy_command, workspace, env=evaluation._evaluation_env()
    )
    assert legacy_result.returncode != 0
    assert "NETLINK_ROUTE" in legacy_result.stderr

    runtime = tmp_path / "runtime"
    runtime.mkdir()
    evaluation.create_broker_shims(runtime, case)
    broker = evaluation.CommandBroker(case, workspace, runtime, "preflight")
    broker.start()
    try:
        evaluation.run_executor_boundary_preflight(case, workspace, output, runtime)
    finally:
        broker.close()
    assert broker.events == []
    assert broker.errors == []


def test_named_profile_executor_fifo_canonical_check_records_runner_event(
    tmp_path: Path, evaluation_root: Path
) -> None:
    if (
        evaluation.shutil.which("bwrap") is None
        or evaluation.shutil.which("codex") is None
    ):
        pytest.skip("bwrap and Codex are required for named-profile FIFO coverage")
    argv = ["python", "-c", "print('canonical-profile-check')"]
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/profile-fifo.yaml",
            command_contract={"families": {"focused_test": {"commands": [argv]}}},
        )
    )
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    output = tmp_path / "output"
    output.mkdir()
    (output / "codex-home").mkdir()
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    evaluation.create_broker_shims(runtime, case)
    broker = evaluation.CommandBroker(case, workspace, runtime, "profile-fifo")
    broker.start()
    command = evaluation.build_bwrap_command(
        case, workspace, output, "unused-model", "low", runtime
    )
    codex_tail = evaluation.build_codex_command(
        case,
        Path("/workspace"),
        Path("/output/final-message.txt"),
        "unused-model",
        "low",
        "/runtime/codex/bin/codex",
    )
    command[-len(codex_tail) :] = evaluation.build_permission_profile_sandbox_command(
        "/runtime/codex/bin/codex",
        Path("/workspace"),
        ("/bin/bash", "-lc", "python -c \"print('canonical-profile-check')\""),
    )
    try:
        result = evaluation._run(command, workspace, env=evaluation._evaluation_env())
    finally:
        broker.close()
    assert result.returncode == 0, result.stderr
    assert result.stdout == "canonical-profile-check\n"
    assert broker.errors == []
    assert [(event.argv, event.exit_code) for event in broker.events] == [
        (tuple(argv), 0)
    ]
    receipt = broker.events[0].delivery_receipt
    assert receipt is not None
    assert result.stderr.splitlines()[0] == evaluation._delivery_receipt_line(receipt)


def test_fifo_shim_fails_closed_on_stale_mismatched_response(
    tmp_path: Path, evaluation_root: Path
) -> None:
    if evaluation.shutil.which("bwrap") is None:
        pytest.skip("bwrap is required for FIFO response-mismatch coverage")
    argv = ["python", "-c", "print('stale-response-check')"]
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/stale-response.yaml",
            command_contract={"families": {"focused_test": {"commands": [argv]}}},
        )
    )
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    output = tmp_path / "output"
    output.mkdir()
    (output / "codex-home").mkdir()
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    evaluation.create_broker_shims(runtime, case)
    broker = evaluation.CommandBroker(case, workspace, runtime, "stale")
    broker.start()
    assert broker._response_fd is not None
    stale = (
        json.dumps(
            {
                "protocol_version": 1,
                "request_id": "0" * 64,
                "accepted": False,
                "reason": "unrecognized",
            }
        )
        + "\n"
    ).encode()
    os.write(broker._response_fd, stale)
    command = evaluation.build_bwrap_command(
        case, workspace, output, "unused-model", "low", runtime
    )
    codex_tail = evaluation.build_codex_command(
        case,
        Path("/workspace"),
        Path("/output/final-message.txt"),
        "unused-model",
        "low",
        "/runtime/codex/bin/codex",
    )
    command[-len(codex_tail) :] = evaluation.build_permission_profile_sandbox_command(
        "/runtime/codex/bin/codex",
        Path("/workspace"),
        ("/bin/bash", "-lc", "python -c \"print('stale-response-check')\""),
    )
    try:
        result = evaluation._run(command, workspace, env=evaluation._evaluation_env())
    finally:
        broker.close()
    assert result.returncode != 0
    assert "response mismatch" in result.stderr
    assert broker.events == []
    assert any("was stopped" in error for error in broker.errors)


@pytest.mark.parametrize("exit_code", (1, 125))
def test_response_steal_is_dos_only_and_delivery_failure_invalidates_oracle(
    tmp_path: Path, evaluation_root: Path, exit_code: int
) -> None:
    if evaluation.shutil.which("bwrap") is None:
        pytest.skip("bwrap is required for FIFO response-steal coverage")
    argv = ["python", "-c", f"import sys; sys.exit({exit_code})"]
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/steal.yaml",
            command_contract={"families": {"focused_test": {"commands": [argv]}}},
        )
    )
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    broker = evaluation.CommandBroker(case, workspace, runtime, "steal")
    broker.start()
    victim = os.open(broker.response_path, os.O_RDONLY | os.O_NONBLOCK)
    stolen: list[bytes] = []
    thief_ready = threading.Event()
    thief_done = threading.Event()

    def steal_response() -> None:
        descriptor = os.open(broker.response_path, os.O_RDONLY | os.O_NONBLOCK)
        thief_ready.set()
        deadline = time.monotonic() + 5.0
        try:
            while time.monotonic() < deadline:
                try:
                    chunk = os.read(descriptor, 65536)
                except BlockingIOError:
                    time.sleep(0.01)
                    continue
                if chunk:
                    stolen.append(chunk)
                    return
        finally:
            os.close(descriptor)
            thief_done.set()

    thief = threading.Thread(target=steal_response)
    thief.start()
    assert thief_ready.wait(timeout=1.0)
    request = (
        json.dumps(
            {"protocol_version": 1, "request_id": "a" * 64, "argv": argv},
            separators=(",", ":"),
        )
        + "\n"
    ).encode()
    try:
        request_fd = os.open(broker.request_path, os.O_WRONLY)
        try:
            assert os.write(request_fd, request) == len(request)
        finally:
            os.close(request_fd)
        assert thief_done.wait(timeout=5.0)
        with pytest.raises(BlockingIOError):
            os.read(victim, 65536)
    finally:
        os.close(victim)
        thief.join(timeout=1.0)
        broker.close()
    assert stolen and b'"accepted":true' in stolen[0]
    assert len(broker.events) == 1
    assert broker.errors == []
    oracle = evaluation.command_oracle(
        case, command_event(shlex.join(argv), exit_code), "steal", broker.events
    )
    assert oracle["valid"] is False
    assert any(
        "transport/delivery receipt mismatch" in error
        for error in cast(list[str], oracle["errors"])
    )


def test_command_oracle_requires_receipt_and_direct_delivery_exit_match(
    tmp_path: Path, evaluation_root: Path
) -> None:
    def runner_event(
        exit_code: int, token: str | None, execution_id: int = 1
    ) -> evaluation.BrokerEvent:
        return evaluation.BrokerEvent(
            execution_id=execution_id,
            family="focused_test",
            argv=("pytest",),
            argv_sha256=hashlib.sha256(b"pytest").hexdigest(),
            cwd="/workspace",
            execution_context="executor_sandbox",
            exit_code=exit_code,
            stdout="",
            stderr="",
            delivery_receipt=token,
        )

    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/delivery-match.yaml",
            command_contract={
                "families": {"focused_test": {"commands": [["pytest"]]}},
            },
        )
    )
    zero_token = "a" * 64
    zero = evaluation.command_oracle(
        case,
        command_event("pytest", 0, evaluation._delivery_receipt_line(zero_token)),
        "run",
        [runner_event(0, zero_token)],
    )
    assert zero["valid"] is True
    assert "delivery_receipt" not in cast(
        dict[str, object], cast(list[object], zero["broker_events"])[0]
    )
    assert zero_token not in json.dumps(zero["broker_events"])

    nonzero_token = "b" * 64
    assert (
        evaluation.command_oracle(
            case,
            command_event(
                "pytest", 7, evaluation._delivery_receipt_line(nonzero_token)
            ),
            "run",
            [runner_event(7, nonzero_token)],
        )["valid"]
        is True
    )
    missing = evaluation.command_oracle(
        case, command_event("pytest", 0), "run", [runner_event(0, zero_token)]
    )
    wrong = evaluation.command_oracle(
        case,
        command_event("pytest", 0, evaluation._delivery_receipt_line("c" * 64)),
        "run",
        [runner_event(0, zero_token)],
    )
    for invalid in (missing, wrong):
        assert invalid["valid"] is False
        assert any(
            "transport/delivery receipt mismatch" in error
            for error in cast(list[str], invalid["errors"])
        )
    invalid_token = evaluation.command_oracle(
        case,
        command_event("pytest", 0, evaluation._delivery_receipt_line("not-a-token")),
        "run",
        [runner_event(0, "not-a-token")],
    )
    assert "broker delivery receipt is invalid" in cast(
        list[str], invalid_token["errors"]
    )
    missing_runner_token = evaluation.command_oracle(
        case, command_event("pytest", 0), "run", [runner_event(0, None)]
    )
    assert "broker delivery receipt is invalid" in cast(
        list[str], missing_runner_token["errors"]
    )

    mismatched = evaluation.command_oracle(
        case,
        command_event("pytest", 0, evaluation._delivery_receipt_line(nonzero_token)),
        "run",
        [runner_event(7, nonzero_token)],
    )
    assert mismatched["valid"] is False
    assert any(
        "transport/delivery exit mismatch" in error
        for error in cast(list[str], mismatched["errors"])
    )
    missing_exit = json.dumps(
        {
            "type": "item.completed",
            "item": {
                "type": "command_execution",
                "command": "pytest",
                "aggregated_output": evaluation._delivery_receipt_line(zero_token),
            },
        }
    )
    assert (
        evaluation.command_oracle(
            case, missing_exit, "run", [runner_event(0, zero_token)]
        )["valid"]
        is False
    )

    compound_case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/delivery-compound.yaml",
            command_contract={
                "families": {
                    "focused_test": {
                        "commands": [["pytest", "first"], ["pytest", "second"]]
                    }
                }
            },
        )
    )
    first_token = "d" * 64
    second_token = "e" * 64

    def compound_event(
        argv: tuple[str, ...], exit_code: int, token: str, execution_id: int
    ) -> evaluation.BrokerEvent:
        return evaluation.BrokerEvent(
            execution_id=execution_id,
            family="focused_test",
            argv=argv,
            argv_sha256=hashlib.sha256("\0".join(argv).encode()).hexdigest(),
            cwd="/workspace",
            execution_context="executor_sandbox",
            exit_code=exit_code,
            stdout="",
            stderr="",
            delivery_receipt=token,
        )

    compound_events = [
        compound_event(("pytest", "first"), 1, first_token, 1),
        compound_event(("pytest", "second"), 0, second_token, 2),
    ]
    compound_output = "\n".join(
        (
            evaluation._delivery_receipt_line(first_token),
            evaluation._delivery_receipt_line(second_token),
        )
    )
    assert (
        evaluation.command_oracle(
            compound_case,
            command_event("pytest first || pytest second", 0, compound_output),
            "run",
            compound_events,
        )["valid"]
        is True
    )
    reordered = evaluation.command_oracle(
        compound_case,
        command_event(
            "pytest first || pytest second",
            0,
            "\n".join(reversed(compound_output.splitlines())),
        ),
        "run",
        compound_events,
    )
    assert reordered["valid"] is False
    assert any(
        "transport/delivery receipt mismatch" in error
        for error in cast(list[str], reordered["errors"])
    )

    forged_bypass = evaluation.command_oracle(
        case,
        command_event("env pytest", 0, evaluation._delivery_receipt_line(zero_token)),
        "run",
        [runner_event(0, zero_token)],
    )
    assert forged_bypass["valid"] is False


def test_task_selection_and_evidence_are_independent_layers(
    tmp_path: Path, evaluation_root: Path
) -> None:
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/layers.yaml",
            command_contract={
                "families": {
                    "generator": {"commands": [["generate"]]},
                    "artifact_readback": {"commands": [["readback"]]},
                    "complete_gate": {"commands": [["full-gate"]]},
                },
                "required": [
                    {"family": "generator", "exit": "zero"},
                    {"family": "artifact_readback", "exit": "zero"},
                ],
                "ordered": [
                    {"family": "generator", "exit": "zero"},
                    {"family": "artifact_readback", "exit": "zero"},
                ],
                "forbidden": ["complete_gate"],
            },
        )
    )

    def event(
        execution_id: int, family: str, argv: tuple[str, ...], exit_code: int = 0
    ) -> evaluation.BrokerEvent:
        return evaluation.BrokerEvent(
            execution_id=execution_id,
            family=family,
            argv=argv,
            argv_sha256=hashlib.sha256("\0".join(argv).encode()).hexdigest(),
            cwd="/workspace",
            execution_context="executor_sandbox",
            exit_code=exit_code,
            stdout="",
            stderr="",
            delivery_receipt=f"{execution_id:x}" * 64,
        )

    events = [
        event(1, "artifact_readback", ("readback",)),
        event(2, "generator", ("generate",)),
        event(3, "complete_gate", ("full-gate",)),
    ]
    selection = evaluation.validation_selection(case, events)
    assert selection["required_covered"] is True
    assert selection["ordered_covered"] is False
    assert selection["forbidden_families"] == ["complete_gate"]
    assert selection["forbidden_event_count"] == 1
    assert selection["contract_satisfied"] is False
    trajectory = "\n".join(
        command_event(
            " ".join(item.argv),
            item.exit_code,
            evaluation._delivery_receipt_line(cast(str, item.delivery_receipt)),
        )
        for item in events
    )
    executor_oracle = evaluation.command_oracle(case, trajectory, "run", events)
    assert executor_oracle["valid"] is True
    assert evaluation.evidence_integrity(executor_oracle)["valid"] is True

    verification = {"passed": True}
    final = {"valid": True}
    assert evaluation.task_outcome(0, verification, final) == {
        "valid": True,
        "errors": [],
    }
    assert evaluation.task_outcome(0, {"passed": False}, {"valid": False}) == {
        "valid": False,
        "errors": [
            "workspace verification failed",
            "final answer contract failed",
        ],
    }
    integrity = evaluation.evidence_integrity(
        {"valid": False, "errors": ["line 1: unrecognized command"]}
    )
    assert integrity["valid"] is False
    assert evaluation.task_outcome(0, verification, final)["valid"] is True


def test_validation_selection_requires_distinct_required_events(
    tmp_path: Path, evaluation_root: Path
) -> None:
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/repeated-selection.yaml",
            command_contract={
                "families": {"focused_test": {"commands": [["focused"]]}},
                "required": [
                    {"family": "focused_test", "exit": "zero"},
                    {"family": "focused_test", "exit": "zero"},
                ],
            },
        )
    )
    event = evaluation.BrokerEvent(
        execution_id=1,
        family="focused_test",
        argv=("focused",),
        argv_sha256=hashlib.sha256(b"focused").hexdigest(),
        cwd="/workspace",
        execution_context="executor_sandbox",
        exit_code=0,
        stdout="",
        stderr="",
        delivery_receipt="b" * 64,
    )
    selection = evaluation.validation_selection(case, [event])
    assert selection["required_covered"] is False
    assert selection["required_missing"] == [{"family": "focused_test", "exit": "zero"}]


def test_named_profile_rejects_response_fifo_injection(
    tmp_path: Path, evaluation_root: Path
) -> None:
    if (
        evaluation.shutil.which("bwrap") is None
        or evaluation.shutil.which("codex") is None
    ):
        pytest.skip("bwrap and Codex are required for FIFO injection coverage")
    case = evaluation.load_case(write_case(evaluation_root / "cases/inject.yaml"))
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    output = tmp_path / "output"
    output.mkdir()
    (output / "codex-home").mkdir()
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    evaluation.create_broker_shims(runtime, case)
    broker = evaluation.CommandBroker(case, workspace, runtime, "inject")
    broker.start()
    command = evaluation.build_bwrap_command(
        case, workspace, output, "unused-model", "low", runtime
    )
    codex_tail = evaluation.build_codex_command(
        case,
        Path("/workspace"),
        Path("/output/final-message.txt"),
        "unused-model",
        "low",
        "/runtime/codex/bin/codex",
    )
    probe = "\n".join(
        (
            "import os",
            "try:",
            "    os.open('/broker/response.fifo', os.O_WRONLY)",
            "except OSError:",
            "    pass",
            "else:",
            "    raise SystemExit('response injection permitted')",
        )
    )
    command[-len(codex_tail) :] = evaluation.build_permission_profile_sandbox_command(
        "/runtime/codex/bin/codex",
        Path("/workspace"),
        ("/bin/bash", "-lc", f"/runtime/python/bin/python3 -c {shlex.quote(probe)}"),
    )
    try:
        result = evaluation._run(command, workspace, env=evaluation._evaluation_env())
    finally:
        broker.close()
    assert result.returncode == 0, result.stderr
    assert broker.events == []
    assert broker.errors == []


def test_fifo_shim_lock_timeout_fails_closed_without_broker_event(
    tmp_path: Path, evaluation_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if (
        evaluation.shutil.which("bwrap") is None
        or evaluation.shutil.which("codex") is None
    ):
        pytest.skip("bwrap and Codex are required for FIFO lock-timeout coverage")
    argv = ["python", "-c", "print('lock-timeout-check')"]
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/lock-timeout.yaml",
            command_contract={"families": {"focused_test": {"commands": [argv]}}},
        )
    )
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    output = tmp_path / "output"
    output.mkdir()
    (output / "codex-home").mkdir()
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    monkeypatch.setattr(evaluation, "BROKER_LOCK_TIMEOUT_SECONDS", 0.1)
    evaluation.create_broker_shims(runtime, case)
    broker = evaluation.CommandBroker(case, workspace, runtime, "lock-timeout")
    broker.start()
    lock = os.open(broker.lock_path, os.O_RDONLY)
    fcntl.flock(lock, fcntl.LOCK_EX)
    command = evaluation.build_bwrap_command(
        case, workspace, output, "unused-model", "low", runtime
    )
    codex_tail = evaluation.build_codex_command(
        case,
        Path("/workspace"),
        Path("/output/final-message.txt"),
        "unused-model",
        "low",
        "/runtime/codex/bin/codex",
    )
    command[-len(codex_tail) :] = evaluation.build_permission_profile_sandbox_command(
        "/runtime/codex/bin/codex",
        Path("/workspace"),
        ("/bin/bash", "-lc", "python -c \"print('lock-timeout-check')\""),
    )
    try:
        result = evaluation._run(command, workspace, env=evaluation._evaluation_env())
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        os.close(lock)
        broker.close()
    assert result.returncode != 0
    assert "broker lock timed out" in result.stderr
    assert broker.events == []
    assert broker.errors == []


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
    assert (home / "auth.json").read_text() == auth.read_text()
    assert (home / "auth.json").stat().st_mode & 0o777 == 0o600

    def failed_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="install failed"
        )

    monkeypatch.setattr(evaluation, "_run", failed_run)
    with pytest.raises(EvaluationError, match="arm install failed"):
        evaluation.install_arm_home(source, auth, tmp_path / "failed-home")


def test_install_arm_home_materializes_runtime_closure(tmp_path: Path) -> None:
    source = tmp_path / "neutral-arm"
    skill = source / "skills/calibration"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "Read ../../references/engineering/principles.md\n", encoding="utf-8"
    )
    reference = source / "references/engineering/principles.md"
    reference.parent.mkdir(parents=True)
    reference.write_text("# Principles\n", encoding="utf-8")
    runbook = source / "docs/runbooks/agent-orchestrator-review-continuation.md"
    runbook.parent.mkdir(parents=True)
    runbook.write_text("# Runbook\n", encoding="utf-8")
    license_file = source / "thirdparty/licenses/GonkaGate-Apache-2.0.txt"
    license_file.parent.mkdir(parents=True)
    license_file.write_text("Apache License\n", encoding="utf-8")
    (source / "install.sh").write_text(
        "#!/usr/bin/env bash\n"
        "set -eu\n"
        'mkdir -p "$CODEX_HOME/skills"\n'
        'ln -s "$PWD/skills/calibration" "$CODEX_HOME/skills/calibration"\n'
        'printf "source=%s\\nhome=%s\\n" "$PWD" "$HOME" '
        '> "$CODEX_HOME/AGENTS.md"\n',
        encoding="utf-8",
    )
    auth = tmp_path / "auth.json"
    auth.write_text("{}\n", encoding="utf-8")
    home = tmp_path / "isolated-home"

    evaluation.install_arm_home(source, auth, home)

    assert (home / "skills/calibration/SKILL.md").is_file()
    assert not (home / "skills/calibration").is_symlink()
    assert (home / "references/engineering/principles.md").is_file()
    assert (home / "docs/runbooks/agent-orchestrator-review-continuation.md").is_file()
    assert (home / "licenses/GonkaGate-Apache-2.0.txt").is_file()
    rendered = (home / "AGENTS.md").read_text(encoding="utf-8")
    assert str(source) not in rendered
    assert str(home) not in rendered
    assert rendered == "source=/output/codex-home\nhome=/output/codex-home/home\n"
    assert not any(path.is_symlink() for path in home.rglob("*"))


def test_run_case_writes_private_evidence_and_result(
    tmp_path: Path,
    evaluation_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/case.yaml",
            verify=[["python", "-c", "print('ok')"]],
        )
    )
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    source = tmp_path / "source"
    source.mkdir()
    auth = tmp_path / "auth.json"
    auth.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "output"

    def no_install(source_root: Path, auth_file: Path, codex_home: Path) -> None:
        return None

    monkeypatch.setattr(evaluation, "install_arm_home", no_install)
    monkeypatch.setattr(
        evaluation,
        "run_executor_boundary_preflight",
        bypass_executor_boundary_preflight,
    )

    def fake_codex(
        command: tuple[str, ...] | list[str],
        cwd: Path,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        (workspace / "value.txt").write_text("after\n", encoding="utf-8")
        return subprocess.CompletedProcess(
            args=command, returncode=0, stdout='{"type":"done"}\n', stderr=""
        )

    monkeypatch.setattr(evaluation, "_run_model", fake_codex)
    result = evaluation.run_case(
        case, workspace, source, auth, output, "model", "medium"
    )
    assert result["codex_exit_code"] == 0
    assert cast(dict[str, object], result["verification"])["passed"] is True
    assert (output / "trajectory.jsonl").read_text(encoding="utf-8")
    assert (output / "codex.stderr").read_text(encoding="utf-8") == ""
    assert output.stat().st_mode & 0o777 == 0o700
    assert (output / "executor").stat().st_mode & 0o777 == 0o700
    for private in ("trajectory.jsonl", "codex.stderr", "result.json"):
        assert (output / private).stat().st_mode & 0o777 == 0o600
    assert (
        json.loads((output / "result.json").read_text(encoding="utf-8"))["case_id"]
        == "T01"
    )
    with pytest.raises(EvaluationError, match="output directory already exists"):
        evaluation.run_case(case, workspace, source, auth, output, "model", "medium")


def test_run_case_rejects_unprepared_workspace(
    tmp_path: Path, evaluation_root: Path
) -> None:
    case = evaluation.load_case(write_case(evaluation_root / "cases/case.yaml"))
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


def test_run_case_requires_successful_codex_exit(
    tmp_path: Path,
    evaluation_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = evaluation.load_case(write_case(evaluation_root / "cases/case.yaml"))
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)

    def no_install(source_root: Path, auth_file: Path, codex_home: Path) -> None:
        return None

    monkeypatch.setattr(evaluation, "install_arm_home", no_install)
    monkeypatch.setattr(
        evaluation,
        "run_executor_boundary_preflight",
        bypass_executor_boundary_preflight,
    )

    def failed_codex(
        command: tuple[str, ...] | list[str],
        cwd: Path,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        (workspace / "value.txt").write_text("after\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 1, '{"type":"done"}\n', "")

    monkeypatch.setattr(evaluation, "_run_model", failed_codex)
    result = evaluation.run_case(
        case,
        workspace,
        tmp_path / "source",
        tmp_path / "auth",
        tmp_path / "output",
        "model",
        "medium",
    )
    assert cast(dict[str, object], result["verification"])["passed"] is True
    assert cast(dict[str, object], result["task_outcome"])["valid"] is False


def test_run_case_fails_closed_before_model_when_boundary_preflight_fails(
    tmp_path: Path,
    evaluation_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = evaluation.load_case(
        write_case(evaluation_root / "cases/preflight-fail.yaml")
    )
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    output = tmp_path / "output"
    model_called = False

    monkeypatch.setattr(evaluation, "install_arm_home", no_install_arm_home)

    def fail_preflight(*args: object) -> None:
        raise EvaluationError("executor boundary preflight failed: synthetic")

    def model_must_not_run(*args: object) -> subprocess.CompletedProcess[str]:
        nonlocal model_called
        model_called = True
        raise AssertionError("model execution must not start after failed preflight")

    monkeypatch.setattr(evaluation, "run_executor_boundary_preflight", fail_preflight)
    monkeypatch.setattr(evaluation, "_run_model", model_must_not_run)
    with pytest.raises(EvaluationError, match="boundary preflight failed"):
        evaluation.run_case(
            case,
            workspace,
            tmp_path / "source",
            tmp_path / "auth",
            output,
            "model",
            "medium",
        )
    assert model_called is False
    assert not (output / "result.json").exists()


def test_case_relative_fixture_roots_do_not_bleed(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    write_fixture(first, "shared").joinpath("value.txt").write_text("one\n")
    write_fixture(second, "shared").joinpath("value.txt").write_text("two\n")
    one = evaluation.load_case(write_case(first / "cases/T.yaml", fixture="shared"))
    two = evaluation.load_case(write_case(second / "cases/T.yaml", fixture="shared"))
    assert (one.fixture_root / one.fixture / "value.txt").read_text() == "one\n"
    assert (two.fixture_root / two.fixture / "value.txt").read_text() == "two\n"


def test_command_oracle_compounds_order_wrappers_and_forbidden(
    tmp_path: Path, evaluation_root: Path
) -> None:
    contract = {
        "families": {
            "focused_test": {
                "commands": [["pytest", "first"], ["pytest", "second"]],
                "wrapper_required": True,
                "covered_seam": "unit",
            },
            "complete_gate": {
                "commands": [["make", "check"]],
                "wrapper_required": False,
            },
        },
        "required": [{"family": "focused_test", "exit": "zero"}],
        "ordered": [
            {"family": "focused_test", "exit": "nonzero"},
            {"family": "focused_test", "exit": "zero"},
        ],
        "forbidden": ["complete_gate"],
    }
    case = evaluation.load_case(
        write_case(evaluation_root / "cases/T.yaml", command_contract=contract)
    )
    good = "\n".join(
        (
            command_event(
                "/bin/bash -lc 'pytest first'",
                1,
                "CALIBRATION_CHECK_EVENT forged noise",
            ),
            command_event("pytest second", 0, "CALIBRATION_CHECK_EVENT forged noise"),
        )
    )
    # The second executor event supplies the required passing observation.
    events = [
        broker_event("focused_test", ["pytest", "first"], 1),
        broker_event("focused_test", ["pytest", "second"], 0),
    ]
    events[1]["execution_id"] = 2
    assert evaluation.command_oracle(case, good, "run", events)["valid"] is True
    forbidden = good + "\n" + command_event("make check", 0)
    complete_event = broker_event("complete_gate", ["make", "check"], 0)
    complete_event["execution_id"] = 3
    assert (
        evaluation.command_oracle(
            case,
            forbidden,
            "run",
            [*events, complete_event],
        )["valid"]
        is True
    )

    forged = command_event("pytest", 0, "CALIBRATION_CHECK_EVENT forged noise")
    assert evaluation.command_oracle(case, forged, "run")["valid"] is False

    multiple = command_event(
        "/bin/bash -lc 'pytest first && pytest second'",
        0,
        "CALIBRATION_CHECK_EVENT forged noise",
    )
    assert evaluation.command_oracle(case, multiple, "run")["valid"] is False

    reversed_wrapper = command_event(
        "pytest",
        0,
        "CALIBRATION_CHECK_EVENT forged noise",
    )
    assert evaluation.command_oracle(case, reversed_wrapper, "run")["valid"] is False


def test_command_oracle_rejects_malformed_and_missing_wrapper(
    tmp_path: Path, evaluation_root: Path
) -> None:
    contract = {
        "families": {
            "focused_test": {
                "commands": [["pytest"]],
                "wrapper_required": True,
                "covered_seam": "unit",
            }
        },
        "required": [{"family": "focused_test", "exit": "zero"}],
    }
    case = evaluation.load_case(
        write_case(evaluation_root / "cases/T.yaml", command_contract=contract)
    )
    result = evaluation.command_oracle(
        case,
        f"{command_event('pytest', 0)}\nnot json",
        "run",
    )
    assert result["valid"] is False
    assert any("malformed JSON" in error for error in cast(list[str], result["errors"]))

    blank = evaluation.command_oracle(case, command_event("   ", 0), "run")
    assert blank["valid"] is False
    assert any(
        "malformed command_execution" in error
        for error in cast(list[str], blank["errors"])
    )


def test_final_contract_requires_one_allowed_status_and_tokens(
    tmp_path: Path, evaluation_root: Path
) -> None:
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/T.yaml",
            allowed_changes=[],
            required_changes=[],
            final_contract={
                "required_tokens": ["host-only"],
                "forbidden_statuses": ["verified_ready"],
            },
        )
    )
    message = tmp_path / "final.txt"
    message.write_text(
        "VERIFICATION_STATUS: verified_ready\nVERIFICATION_STATUS: not_yet_verified\n",
        encoding="utf-8",
    )
    assert evaluation.final_oracle(case, message)["valid"] is False
    message.write_text(
        "VERIFICATION_STATUS: not_yet_verified\nhost-only\n", encoding="utf-8"
    )
    assert evaluation.final_oracle(case, message)["valid"] is True


INVALID_COMMAND_CONTRACTS: list[tuple[dict[str, object], str]] = [
    ({"families": {}}, "families must be"),
    ({"families": {"bad": {"commands": [["x"]]}}}, "unknown command"),
    ({"families": {"focused_test": []}}, "must be a mapping"),
    ({"families": {"focused_test": {}}}, "commands for"),
    (
        {"families": {"focused_test": {"commands": ["x"]}}},
        "alias prefixes",
    ),
    (
        {"families": {"focused_test": {"commands": [[]]}}},
        "alias prefixes",
    ),
    (
        {
            "families": {
                "focused_test": {
                    "commands": [["x"]],
                    "wrapper_required": "yes",
                }
            }
        },
        "must be boolean",
    ),
    (
        {
            "families": {
                "focused_test": {
                    "commands": [["x"]],
                    "wrapper_required": True,
                }
            }
        },
        "needs covered_seam",
    ),
    (
        {"families": {"focused_test": {"commands": [["x"]]}}, "required": {}},
        "must be a list",
    ),
    (
        {"families": {"focused_test": {"commands": [["x"]]}}, "required": [1]},
        "require family",
    ),
    (
        {
            "families": {"focused_test": {"commands": [["x"]]}},
            "required": [{"family": "complete_gate"}],
        },
        "must have aliases",
    ),
    (
        {
            "families": {"focused_test": {"commands": [["x"]]}},
            "required": [{"family": "focused_test", "exit": "bad"}],
        },
        "exit must",
    ),
    (
        {
            "families": {"focused_test": {"commands": [["x"]]}},
            "forbidden": ["complete_gate"],
        },
        "forbidden must",
    ),
    (
        {
            "families": {
                "focused_test": {"commands": [["same"]]},
                "complete_gate": {"commands": [["same"]]},
            }
        },
        "must not overlap",
    ),
]


@pytest.mark.parametrize(("contract", "message"), INVALID_COMMAND_CONTRACTS)
def test_contract_schema_rejects_invalid_command_contracts(
    tmp_path: Path,
    contract: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(EvaluationError, match=message):
        evaluation._validate_command_contract(contract, tmp_path / "case.yaml")


@pytest.mark.parametrize(
    ("contract", "message"),
    [
        ({"required_tokens": [1]}, "required_tokens"),
        ({"forbidden_statuses": ["bad"]}, "forbidden_statuses"),
        ({"allowed_statuses": []}, "allowed_statuses"),
    ],
)
def test_contract_schema_rejects_invalid_final_contracts(
    tmp_path: Path, contract: dict[str, object], message: str
) -> None:
    with pytest.raises(EvaluationError, match=message):
        evaluation._validate_final_contract(contract, tmp_path / "case.yaml")


def test_command_normalization_and_capture_negative_controls() -> None:
    assert evaluation._shell_commands("git status;command -v pytest") == [
        ["git", "status"],
        ["command", "-v", "pytest"],
    ]
    assert evaluation._shell_commands("bash -lc 'pytest -q'") == [["pytest", "-q"]]
    assert evaluation._shell_commands("/bin/bash -c 'pytest -q'") == [["pytest", "-q"]]
    assert evaluation._shell_commands("/usr/bin/sh -lc 'pytest -q'") == [
        ["pytest", "-q"]
    ]
    assert evaluation._is_discovery([]) is False
    assert evaluation._is_discovery(["git", "diff"]) is True
    assert evaluation._is_discovery(["echo", "x"]) is False
    assert evaluation._is_discovery(["find", ".", "-maxdepth", "2"])
    assert not evaluation._is_discovery(
        ["find", ".", "-exec", "python", "socket-client", ";"]
    )
    assert evaluation._is_discovery(["rg", "needle", "src"])
    assert not evaluation._is_discovery(["rg", "--pre=socket-client", "needle"])
    assert evaluation._is_discovery(["sed", "-n", "1,20p", "README.md"])
    assert not evaluation._is_discovery(["sed", "-n", "e socket-client", "README.md"])
    assert evaluation._is_discovery(["git", "diff", "--", "README.md"])
    assert not evaluation._is_discovery(["git", "diff", "--ext-diff=socket-client"])
    assert not evaluation._is_discovery(["git", "log", "-p", "--ext-diff"])
    assert evaluation._is_discovery(["command", "-v", "python"])
    assert not evaluation._bypass(["command", "-v", "python"])
    assert evaluation._unknown_validation(["tool", "lint"]) is True
    assert evaluation._unknown_validation(["echo", "x"]) is False
    for command in ("'", "&& pytest", "pytest &&"):
        with pytest.raises(EvaluationError, match="malformed"):
            evaluation._shell_commands(command)

    events, errors = evaluation._command_events(
        "\n".join(
            (
                "[]",
                '{"type":"other"}',
                '{"type":"item.completed","item":null}',
                '{"type":"item.completed","item":{"type":"other"}}',
                '{"type":"item.completed","item":{"type":"command_execution","command":"x","aggregated_output":1}}',
                '{"type":"item.completed","item":{"type":"command_execution","command":"x","exit_code":"0"}}',
            )
        )
    )
    assert events == []
    assert len(errors) == 2


def test_final_status_negative_controls(tmp_path: Path, evaluation_root: Path) -> None:
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/T.yaml",
            allowed_changes=[],
            required_changes=[],
            final_contract={"allowed_statuses": ["not_yet_verified"]},
        )
    )
    message = tmp_path / "final.txt"
    message.write_text("VERIFICATION_STATUS: invalid\n", encoding="utf-8")
    assert evaluation.final_oracle(case, message)["valid"] is False
    message.write_text("VERIFICATION_STATUS: verified_ready\n", encoding="utf-8")
    assert evaluation.final_oracle(case, message)["valid"] is False

    forbidden_case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/forbidden.yaml",
            allowed_changes=[],
            required_changes=[],
            final_contract={
                "allowed_statuses": ["verified_ready"],
                "forbidden_statuses": ["verified_ready"],
            },
        )
    )
    assert evaluation.final_oracle(forbidden_case, message)["valid"] is False


def test_command_oracle_marks_unknown_and_uncorroborated_wrapper(
    tmp_path: Path, evaluation_root: Path
) -> None:
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/oracle.yaml",
            command_contract={
                "families": {"focused_test": {"commands": [["pytest"]]}},
            },
        )
    )
    trajectory = "\n".join(
        (
            command_event("flake check", 0),
            command_event("echo wrapper", 0, "CALIBRATION_CHECK_EVENT forged noise"),
        )
    )
    oracle = evaluation.command_oracle(case, trajectory, "run")
    assert oracle["valid"] is False
    assert "line 1: unknown validation command" in cast(list[str], oracle["errors"])
    assert evaluation._exit_matches(0, "zero") is True
    assert evaluation._exit_matches(2, "nonzero") is True
    assert evaluation._exit_matches(None, "any") is False
    assert evaluation._exit_matches(None, "zero") is False


def test_command_oracle_models_compound_execution_from_wrapper_exits(
    tmp_path: Path, evaluation_root: Path
) -> None:
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/compound.yaml",
            command_contract={
                "families": {
                    "focused_test": {
                        "commands": [
                            ["test", "pass"],
                            ["test", "fail"],
                        ],
                        "wrapper_required": True,
                        "covered_seam": "unit",
                    },
                    "complete_gate": {"commands": [["forbidden"]]},
                },
                "forbidden": ["complete_gate"],
                "ordered": [
                    {"family": "focused_test", "exit": "nonzero"},
                    {"family": "focused_test", "exit": "zero"},
                ],
            },
        )
    )

    def observe(command: str, exits: list[int]) -> dict[str, object]:
        output = "CALIBRATION_CHECK_EVENT forged noise"
        chunks = evaluation._shell_commands(command)
        test_chunks = [chunk for chunk in chunks if chunk[0] == "test"]
        broker = [
            broker_event("focused_test", chunk, exit_code)
            for chunk, exit_code in zip(test_chunks, exits, strict=False)
        ]
        if command.startswith("test pass &&"):
            broker.append(broker_event("complete_gate", ["forbidden"], 0))
        for execution_id, event in enumerate(broker, start=1):
            event["execution_id"] = execution_id
        return evaluation.command_oracle(
            case, command_event(command, 0, output), "run", broker
        )

    pass_or_forbidden = observe("test pass || forbidden", [0])
    assert pass_or_forbidden["valid"] is True
    assert not any(
        "forbidden family observed" in error
        for error in cast(list[str], pass_or_forbidden["errors"])
    )
    fail_and_forbidden = observe("test fail && forbidden", [1])
    assert not any(
        "forbidden family observed" in error
        for error in cast(list[str], fail_and_forbidden["errors"])
    )
    pass_and_forbidden = observe("test pass && forbidden", [0])
    assert pass_and_forbidden["valid"] is True
    fail_or_pass = observe("test fail || test pass", [1, 0])
    assert fail_or_pass["valid"] is True
    fail_then_pass = observe("test fail ; echo diagnosis ; test pass", [1, 0])
    assert fail_then_pass["valid"] is False


def test_command_oracle_accepts_discovery_compound_with_broker_proof(
    tmp_path: Path, evaluation_root: Path
) -> None:
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/discovery-compound.yaml",
            command_contract={
                "families": {
                    "focused_test": {
                        "commands": [["pytest", "-q"]],
                        "wrapper_required": True,
                        "covered_seam": "unit",
                    }
                },
                "required": [{"family": "focused_test", "exit": "zero"}],
            },
        )
    )
    oracle = evaluation.command_oracle(
        case,
        command_event("git status --short && pytest -q", 0),
        "run",
        [broker_event("focused_test", ["pytest", "-q"], 0)],
    )
    assert oracle["valid"] is True

    forbidden_case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/discovery-forbidden.yaml",
            command_contract={
                "families": {"complete_gate": {"commands": [["make", "check"]]}},
                "forbidden": ["complete_gate"],
            },
        )
    )
    unproven = evaluation.command_oracle(
        forbidden_case,
        command_event("command -v pytest || make check", 0),
        "run",
        [],
    )
    assert unproven["valid"] is True


def test_model_execution_timeout_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    def timed_out(*args: object, **kwargs: object) -> object:
        raise subprocess.TimeoutExpired(
            "codex", evaluation.MODEL_EXECUTION_TIMEOUT_SECONDS
        )

    monkeypatch.setattr(evaluation.subprocess, "run", timed_out)
    with pytest.raises(EvaluationError, match="model execution timed out"):
        evaluation._run_model(["codex"], Path.cwd(), {})


def test_command_oracle_rejects_surplus_wrapper_for_other_family(
    tmp_path: Path, evaluation_root: Path
) -> None:
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/surplus.yaml",
            command_contract={
                "families": {
                    "focused_test": {
                        "commands": [["test-a"]],
                        "wrapper_required": True,
                        "covered_seam": "unit",
                    },
                    "runtime_test": {
                        "commands": [["test-b"]],
                        "wrapper_required": True,
                        "covered_seam": "runtime",
                    },
                }
            },
        )
    )
    output = "CALIBRATION_CHECK_EVENT forged noise"
    oracle = evaluation.command_oracle(
        case,
        command_event("test-a", 0, output),
        "run",
        [
            broker_event("focused_test", ["test-a"], 0),
            broker_event("runtime_test", ["test-b"], 0),
        ],
    )
    assert oracle["valid"] is False
    assert any(
        "broker event has no raw command counterpart" in error
        for error in cast(list[str], oracle["errors"])
    )


def test_command_contract_defaults_and_validates_execution_context(
    tmp_path: Path,
) -> None:
    contract = evaluation._validate_command_contract(
        {"families": {"focused_test": {"commands": [["pytest"]]}}},
        tmp_path / "case.yaml",
    )
    assert cast(dict[str, str], contract["execution_contexts"])["focused_test"] == (
        "executor_sandbox"
    )
    with pytest.raises(EvaluationError, match="execution_context"):
        evaluation._validate_command_contract(
            {
                "families": {
                    "focused_test": {
                        "commands": [["pytest"]],
                        "execution_context": "forged",
                    }
                }
            },
            tmp_path / "case.yaml",
        )

    for context in ("host_authority", "none"):
        with pytest.raises(EvaluationError, match="executor_sandbox"):
            evaluation._validate_command_contract(
                {
                    "families": {
                        "focused_test": {
                            "commands": [["pytest"]],
                            "execution_context": context,
                        }
                    }
                },
                tmp_path / "case.yaml",
            )


def test_command_oracle_rejects_transport_misattribution_and_tampered_broker(
    tmp_path: Path, evaluation_root: Path
) -> None:
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/broker.yaml",
            command_contract={"families": {"focused_test": {"commands": [["pytest"]]}}},
        )
    )
    event = broker_event("focused_test", ["pytest"], 0)
    trajectory = "\n".join(
        (command_event("echo transport-client", 0), command_event("pytest", 0))
    )
    assert evaluation.command_oracle(case, trajectory, "run", [event])["valid"] is False
    for field, value in (
        ("cwd", "/tmp"),
        ("argv_sha256", "forged"),
        ("execution_context", "none"),
        ("execution_id", 2),
        ("exit_code", True),
    ):
        tampered = dict(event)
        tampered[field] = value
        assert (
            evaluation.command_oracle(
                case, command_event("pytest", 0), "run", [tampered]
            )["valid"]
            is False
        )


def test_result_schema_validation_is_optional_and_enforced(tmp_path: Path) -> None:
    root = tmp_path / "evaluation"
    write_fixture(root)
    case = evaluation.load_case(write_case(root / "cases/P01.yaml", id="P01"))
    payload: dict[str, object] = {"case_id": "P01"}
    evaluation.validate_result_payload(case, payload)

    (root / "result.schema.json").write_text(
        json.dumps(
            {
                "type": "object",
                "required": ["case_id"],
                "properties": {"case_id": {"type": "string"}},
                "additionalProperties": False,
            }
        ),
        encoding="utf-8",
    )
    evaluation.validate_result_payload(case, payload)
    with pytest.raises(EvaluationError, match="validation failed"):
        evaluation.validate_result_payload(case, {"case_id": "P01", "extra": True})
    with pytest.raises(EvaluationError, match="validation failed"):
        evaluation.validate_result_payload(case, {})


def test_main_prepare_verify_run_and_error(
    tmp_path: Path,
    evaluation_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    case_path = write_case(evaluation_root / "cases/case.yaml")
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


def test_broker_fifo_rejects_malformed_requests_and_preserves_event_truth(
    tmp_path: Path, evaluation_root: Path
) -> None:
    """Malformed FIFO frames fail closed and cannot synthesize runner events."""
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/fifo.yaml",
            command_contract={"families": {"focused_test": {"commands": [["echo"]]}}},
        )
    )
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    broker = evaluation.CommandBroker(case, workspace, runtime, "run")
    broker.start()

    try:
        for payload in (
            b"[]\n",
            b'{"protocol_version":1,"request_id":"0"*64,"argv":"echo"}\n',
            b'{"protocol_version":1,"request_id":"0"*64,"argv":["echo"],"exit_code":0}\n',
            b"not-json\n",
        ):
            descriptor = os.open(broker.request_path, os.O_WRONLY)
            try:
                assert os.write(descriptor, payload) == len(payload)
            finally:
                os.close(descriptor)
        deadline = time.monotonic() + 1.0
        while len(broker.errors) < 4 and time.monotonic() < deadline:
            time.sleep(0.01)
    finally:
        broker.close()
    assert broker.events == []
    assert any("invalid broker request" in error for error in broker.errors)
    assert all("exit_code" not in error for error in broker.errors)


def test_broker_execute_timeout_and_unknown_alias(
    tmp_path: Path, evaluation_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/broker-timeout.yaml",
            command_contract={"families": {"focused_test": {"commands": [["echo"]]}}},
        )
    )
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    broker = evaluation.CommandBroker(case, workspace, runtime, "run")

    class TimedOutProcess:
        pid = 99_999_999
        stdout = None
        stderr = None

        def wait(self, timeout: float | None = None) -> int:
            if timeout is None:
                return 1
            raise evaluation.subprocess.TimeoutExpired("echo", timeout)

        def kill(self) -> None:
            return None

    def timed_out_popen(*args: object, **kwargs: object) -> TimedOutProcess:
        del args, kwargs
        return TimedOutProcess()

    monkeypatch.setattr(evaluation.subprocess, "Popen", timed_out_popen)

    def timed_out_capture(*args: object) -> tuple[str, str, int]:
        del args
        raise EvaluationError("broker check timed out")

    monkeypatch.setattr(broker, "_read_capture", timed_out_capture)
    with pytest.raises(EvaluationError, match="broker check timed out"):
        broker.execute(("echo",))
    assert broker.execute(("unknown",)) is None


def test_contract_and_oracle_cover_invalid_mapping_and_broker_shapes(
    tmp_path: Path, evaluation_root: Path
) -> None:
    with pytest.raises(EvaluationError, match="command_contract must be a mapping"):
        evaluation.load_case(
            write_case(evaluation_root / "cases/mapping.yaml", command_contract=[])
        )
    with pytest.raises(EvaluationError, match="observations require family"):
        evaluation._validate_command_contract(
            {"families": {"focused_test": {"commands": [["x"]]}}, "required": [{}]},
            tmp_path / "case.yaml",
        )
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/oracle-shapes.yaml",
            command_contract={"families": {"focused_test": {"commands": [["pytest"]]}}},
        )
    )
    trajectory = "\n".join(
        (
            command_event("pytest", 0),
            command_event("/usr/bin/pytest", 0),
            command_event("pytest &&", 0),
        )
    )
    bad = broker_event("focused_test", ["pytest"], 0)
    bad["argv"] = [1]
    result = evaluation.command_oracle(case, trajectory, "run", [bad])
    errors = cast(list[str], result["errors"])
    assert result["valid"] is False
    assert "broker argv is invalid" in errors
    assert any("command bypass" in error for error in errors)
    assert any("malformed compound" in error for error in errors)


def test_schema_private_files_boundary_and_installation_negative_paths(
    tmp_path: Path, evaluation_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "schema-root"
    write_fixture(root)
    case = evaluation.load_case(write_case(root / "cases/C.yaml"))
    schema = root / "result.schema.json"
    schema.write_text("[", encoding="utf-8")
    with pytest.raises(EvaluationError, match="cannot load result schema"):
        evaluation.validate_result_payload(case, {})
    schema.write_text("[]", encoding="utf-8")
    with pytest.raises(EvaluationError, match="result schema must be an object"):
        evaluation.validate_result_payload(case, {})
    private = tmp_path / "private"
    private.write_text("old", encoding="utf-8")
    with pytest.raises(EvaluationError, match="already exists"):
        evaluation._write_private_file(private, "new")
    link = tmp_path / "private-link"
    link.symlink_to(private)
    with pytest.raises(EvaluationError, match="already exists"):
        evaluation._write_private_file(link, "new")

    def denied_open(*args: object, **kwargs: object) -> int:
        raise PermissionError("denied")

    monkeypatch.setattr(evaluation.os, "open", denied_open)
    with pytest.raises(EvaluationError, match="cannot create runner control artifact"):
        evaluation._write_private_file(tmp_path / "denied", "new")
    monkeypatch.undo()

    class FailedWrite:
        def __init__(self, descriptor: int) -> None:
            self.descriptor = descriptor

        def __enter__(self) -> FailedWrite:
            return self

        def __exit__(self, *args: object) -> None:
            evaluation.os.close(self.descriptor)

        def fileno(self) -> int:
            return self.descriptor

        def write(self, text: str) -> int:
            del text
            raise OSError("disk full")

    def failed_fdopen(descriptor: int, mode: str, *, encoding: str) -> FailedWrite:
        del mode, encoding
        return FailedWrite(descriptor)

    monkeypatch.setattr(evaluation.os, "fdopen", failed_fdopen)
    with pytest.raises(EvaluationError, match="cannot write runner control artifact"):
        evaluation._write_private_file(tmp_path / "write-failure", "new")
    monkeypatch.undo()
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    with pytest.raises(EvaluationError, match="outside workspace"):
        evaluation._validate_boundary_paths(case, workspace, workspace / "output")
    (workspace / "missing.txt").unlink(missing_ok=True)
    missing_case = evaluation.load_case(
        write_case(
            root / "cases/missing.yaml",
            allowed_changes=["missing.txt"],
            required_changes=["missing.txt"],
        )
    )
    with pytest.raises(EvaluationError, match="existing in-workspace"):
        evaluation._validate_boundary_paths(
            missing_case, workspace, tmp_path / "output"
        )

    source = tmp_path / "source"
    source.mkdir()
    (source / "install.sh").write_text(
        '#!/bin/sh\nmkdir -p "$CODEX_HOME/skills"\n'
        'ln -s /missing "$CODEX_HOME/skills/bad"\n',
        encoding="utf-8",
    )
    auth = tmp_path / "auth.json"
    auth.write_text("{}", encoding="utf-8")
    with pytest.raises(EvaluationError, match="link is broken"):
        evaluation.install_arm_home(source, auth, tmp_path / "home")
    external = source / "external-skill"
    external.mkdir()
    (external / "SKILL.md").write_text("external\n", encoding="utf-8")
    (source / "install.sh").write_text(
        '#!/bin/sh\nln -s "$PWD/external-skill" "$CODEX_HOME/retained"\n',
        encoding="utf-8",
    )
    with pytest.raises(EvaluationError, match="retains external link"):
        evaluation.install_arm_home(source, auth, tmp_path / "external-home")


def test_broker_fifo_lifecycle_rejects_unsafe_runtime_paths(
    tmp_path: Path, evaluation_root: Path
) -> None:
    case = evaluation.load_case(write_case(evaluation_root / "cases/lifecycle.yaml"))
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    (runtime / "request.fifo").symlink_to(tmp_path / "outside")
    broker = evaluation.CommandBroker(case, workspace, runtime, "run")
    with pytest.raises(EvaluationError, match="already exists"):
        broker.start()

    clean_runtime = tmp_path / "clean-runtime"
    clean_runtime.mkdir()
    live_broker = evaluation.CommandBroker(case, workspace, clean_runtime, "run")
    live_broker.start()
    started = time.monotonic()
    live_broker.close()
    assert time.monotonic() - started < evaluation.BROKER_FRAME_TIMEOUT_SECONDS + 1.0
    assert not any(clean_runtime.iterdir())


def test_broker_fifo_modes_and_partial_frames_fail_closed(
    tmp_path: Path, evaluation_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = evaluation.load_case(write_case(evaluation_root / "cases/fifo-modes.yaml"))
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    broker = evaluation.CommandBroker(case, workspace, runtime, "run")
    monkeypatch.setattr(evaluation, "BROKER_FRAME_TIMEOUT_SECONDS", 0.01)
    broker.start()
    try:
        assert broker.request_path.stat().st_mode & 0o777 == 0o200
        assert broker.response_path.stat().st_mode & 0o777 == 0o400
        assert broker.lock_path.stat().st_mode & 0o777 == 0o400
        with pytest.raises(PermissionError):
            os.open(broker.response_path, os.O_WRONLY | os.O_NONBLOCK)
        descriptor = os.open(broker.request_path, os.O_WRONLY)
        try:
            os.write(descriptor, b'{"protocol_version":1')
        finally:
            os.close(descriptor)
        deadline = time.monotonic() + 1.0
        while not broker.errors and time.monotonic() < deadline:
            time.sleep(0.01)
    finally:
        broker.close()
    assert broker.events == []
    assert any("timed out" in error for error in broker.errors)


def test_broker_start_failure_clears_open_descriptors(
    tmp_path: Path, evaluation_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = evaluation.load_case(write_case(evaluation_root / "cases/start.yaml"))
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    broker = evaluation.CommandBroker(case, workspace, runtime, "start")

    def denied_chmod(path: Path, mode: int) -> None:
        del path, mode
        raise PermissionError("synthetic")

    monkeypatch.setattr(evaluation.os, "chmod", denied_chmod)
    with pytest.raises(EvaluationError, match="cannot open broker FIFO transport"):
        broker.start()
    assert broker._request_fd is None
    assert broker._response_fd is None
    assert not any(runtime.iterdir())


def test_broker_start_rejects_small_pipe_buffer_and_oversize_alias(
    tmp_path: Path, evaluation_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = evaluation.load_case(write_case(evaluation_root / "cases/pipe.yaml"))
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    broker = evaluation.CommandBroker(case, workspace, runtime, "pipe")

    def tiny_pipe_buffer(*args: object) -> int:
        del args
        return 1

    monkeypatch.setattr(evaluation.os, "fpathconf", tiny_pipe_buffer)
    with pytest.raises(EvaluationError, match="PIPE_BUF is too small"):
        broker.start()

    oversized = ["python", "-c", "x" * evaluation.BROKER_PIPE_BUF_BYTES]
    alias_case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/oversize.yaml",
            command_contract={"families": {"focused_test": {"commands": [oversized]}}},
        )
    )
    alias_workspace = tmp_path / "alias-workspace"
    evaluation.prepare_workspace(alias_case, alias_workspace)
    alias_runtime = tmp_path / "alias-runtime"
    alias_runtime.mkdir()
    alias_broker = evaluation.CommandBroker(
        alias_case, alias_workspace, alias_runtime, "oversize"
    )
    monkeypatch.undo()
    with pytest.raises(EvaluationError, match="exceeds PIPE_BUF"):
        alias_broker.start()


def test_broker_request_budget_stops_malformed_flood(
    tmp_path: Path, evaluation_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = evaluation.load_case(write_case(evaluation_root / "cases/budget.yaml"))
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    broker = evaluation.CommandBroker(case, workspace, runtime, "budget")
    broker.start()
    monkeypatch.setattr(evaluation, "BROKER_MAX_REQUESTS", 1)
    try:
        broker._handle_request(b"not-json")
        broker._handle_request(b"not-json")
    finally:
        broker.close()
    assert broker.events == []
    assert broker._stopping.is_set()
    assert any("budget exceeded" in error for error in broker.errors)


def test_broker_request_ids_and_reply_frames_use_exact_newline_encoding(
    tmp_path: Path, evaluation_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = evaluation.load_case(write_case(evaluation_root / "cases/ids.yaml"))
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    broker = evaluation.CommandBroker(case, workspace, runtime, "ids")
    broker.start()
    invalid = json.dumps(
        {
            "protocol_version": 1,
            "request_id": "g" * 64,
            "argv": ["unknown"],
        }
    ).encode()
    unicode_identifier = json.dumps(
        {
            "protocol_version": 1,
            "request_id": "é" * 64,
            "argv": ["unknown"],
        }
    ).encode()
    try:
        broker._handle_request(invalid)
        broker._handle_request(unicode_identifier)
    finally:
        broker.close()
    assert broker.events == []
    assert sum("invalid broker request id" in error for error in broker.errors) == 2

    event = evaluation.BrokerEvent(
        execution_id=1,
        family="focused_test",
        argv=("python",),
        argv_sha256="0",
        cwd="/workspace",
        execution_context="executor_sandbox",
        exit_code=0,
        stdout="frame-boundary",
        stderr="",
        delivery_receipt="b" * 64,
    )
    request_id = "a" * 64
    reply = {
        "protocol_version": 1,
        "request_id": request_id,
        "accepted": True,
        "reason": "accepted",
        "exit_code": 0,
        "stdout": event.stdout,
        "stderr": event.stderr,
        "receipt_token": event.delivery_receipt,
    }
    encoded = evaluation._encode_broker_reply(reply)
    assert encoded.endswith(b"\n")
    monkeypatch.setattr(evaluation, "BROKER_FRAME_LIMIT_BYTES", len(encoded))
    assert evaluation.CommandBroker._accepted_reply_fits(event, request_id)
    monkeypatch.setattr(evaluation, "BROKER_FRAME_LIMIT_BYTES", len(encoded) - 1)
    assert not evaluation.CommandBroker._accepted_reply_fits(event, request_id)


def test_broker_capture_limit_kills_running_check_without_event(
    tmp_path: Path, evaluation_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if evaluation.shutil.which("bwrap") is None:
        pytest.skip("bwrap is required for broker capture-limit coverage")
    argv = ["python", "-c", "import sys; sys.stdout.write('x' * 1000000)"]
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/capture.yaml",
            command_contract={"families": {"focused_test": {"commands": [argv]}}},
        )
    )
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    broker = evaluation.CommandBroker(case, workspace, runtime, "capture")
    monkeypatch.setattr(evaluation, "BROKER_CAPTURE_LIMIT_BYTES", 1024)
    started = time.monotonic()
    with pytest.raises(EvaluationError, match="output is too large"):
        broker.execute(tuple(argv))
    assert time.monotonic() - started < 5.0
    assert broker.events == []
    assert broker._active_process is None
    assert not list(tmp_path.glob("capture-*"))


def test_broker_capture_total_budget_allows_exact_limit_and_rejects_overflow(
    tmp_path: Path, evaluation_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if evaluation.shutil.which("bwrap") is None:
        pytest.skip("bwrap is required for broker capture-budget coverage")
    exact = [
        "python",
        "-c",
        "import sys; sys.stdout.write('o' * 512); sys.stderr.write('e' * 512)",
    ]
    overflow = [
        "python",
        "-c",
        "import sys; sys.stdout.write('o' * 513); sys.stderr.write('e' * 512)",
    ]
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/capture-total.yaml",
            command_contract={
                "families": {"focused_test": {"commands": [exact, overflow]}}
            },
        )
    )
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    broker = evaluation.CommandBroker(case, workspace, runtime, "capture-total")
    monkeypatch.setattr(evaluation, "BROKER_CAPTURE_LIMIT_BYTES", 1024)
    event = broker.execute(tuple(exact))
    assert event is not None
    assert len(event.stdout) + len(event.stderr) == 1024
    with pytest.raises(EvaluationError, match="output is too large"):
        broker.execute(tuple(overflow))
    assert len(broker.events) == 1


def test_broker_capture_allows_check_to_exit_after_closing_pipes(
    tmp_path: Path, evaluation_root: Path
) -> None:
    if evaluation.shutil.which("bwrap") is None:
        pytest.skip("bwrap is required for broker pipe-close coverage")
    argv = [
        "python",
        "-c",
        "import os, time; os.close(1); os.close(2); time.sleep(.05)",
    ]
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/pipe-close.yaml",
            command_contract={"families": {"focused_test": {"commands": [argv]}}},
        )
    )
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    broker = evaluation.CommandBroker(case, workspace, runtime, "pipe-close")
    event = broker.execute(tuple(argv))
    assert event is not None
    assert event.exit_code == 0


def test_broker_rejects_json_expanding_capture_without_event(
    tmp_path: Path, evaluation_root: Path
) -> None:
    if evaluation.shutil.which("bwrap") is None:
        pytest.skip("bwrap is required for broker JSON-frame coverage")
    argv = ["python", "-c", "import sys; sys.stdout.buffer.write(b'\\0' * 200000)"]
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/json-frame.yaml",
            command_contract={"families": {"focused_test": {"commands": [argv]}}},
        )
    )
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    broker = evaluation.CommandBroker(case, workspace, runtime, "json-frame")
    with pytest.raises(EvaluationError, match="response is too large"):
        broker.execute(tuple(argv))
    assert broker.events == []


def test_broker_close_cleans_transport_when_termination_raises(
    tmp_path: Path, evaluation_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = evaluation.load_case(write_case(evaluation_root / "cases/close-error.yaml"))
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    broker = evaluation.CommandBroker(case, workspace, runtime, "close-error")
    broker.start()

    def failed_termination() -> None:
        raise EvaluationError("synthetic termination failure")

    monkeypatch.setattr(broker, "_terminate_active_process", failed_termination)
    with pytest.raises(EvaluationError, match="synthetic termination failure"):
        broker.close()
    assert broker._request_fd is None
    assert broker._response_fd is None
    assert broker._thread is None
    assert not any(runtime.iterdir())


def test_broker_capture_overflow_kills_descendant_pipe_writer(
    tmp_path: Path, evaluation_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if evaluation.shutil.which("bwrap") is None:
        pytest.skip("bwrap is required for broker descendant coverage")
    program = "\n".join(
        (
            "import os, sys, time",
            "if os.fork() == 0:",
            "    time.sleep(0.5)",
            "    open('value.txt', 'w').write('descendant')",
            "else:",
            "    sys.stdout.write('x' * 1000000)",
        )
    )
    argv = ["python", "-c", program]
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/descendant.yaml",
            command_contract={"families": {"focused_test": {"commands": [argv]}}},
        )
    )
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    broker = evaluation.CommandBroker(case, workspace, runtime, "descendant")
    monkeypatch.setattr(evaluation, "BROKER_CAPTURE_LIMIT_BYTES", 1024)
    with pytest.raises(EvaluationError, match="output is too large"):
        broker.execute(tuple(argv))
    time.sleep(0.7)
    assert (workspace / "value.txt").read_text(encoding="utf-8") == "before\n"
    assert broker.events == []


def test_broker_close_kills_active_check_and_blocks_new_execution(
    tmp_path: Path, evaluation_root: Path
) -> None:
    if evaluation.shutil.which("bwrap") is None:
        pytest.skip("bwrap is required for broker close coverage")
    argv = ["python", "-c", "import time; time.sleep(30)"]
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/close.yaml",
            command_contract={"families": {"focused_test": {"commands": [argv]}}},
        )
    )
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    broker = evaluation.CommandBroker(case, workspace, runtime, "close")
    failures: list[BaseException] = []

    def run_check() -> None:
        try:
            broker.execute(tuple(argv))
        except BaseException as exc:
            failures.append(exc)

    thread = threading.Thread(target=run_check)
    thread.start()
    deadline = time.monotonic() + 5.0
    while broker._active_process is None and time.monotonic() < deadline:
        time.sleep(0.01)
    assert broker._active_process is not None
    broker.close()
    thread.join(timeout=5.0)
    assert not thread.is_alive()
    assert broker.events == []
    assert any(isinstance(exc, EvaluationError) for exc in failures)
    with pytest.raises(EvaluationError, match="stopping"):
        broker.execute(tuple(argv))
    broker.close()


def test_runner_branches_reject_invalid_runtime_and_preserve_broker_truth(
    tmp_path: Path, evaluation_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = evaluation.load_case(write_case(evaluation_root / "cases/branches.yaml"))
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    no_contract = evaluation.CommandBroker(case, workspace, runtime, "run")
    assert no_contract._family(("pytest",)) is None
    assert evaluation._is_discovery(["pwd"]) is True

    event = evaluation.BrokerEvent(
        execution_id=1,
        family="focused_test",
        argv=("pytest",),
        argv_sha256=hashlib.sha256(b"pytest").hexdigest(),
        cwd="/workspace",
        execution_context="executor_sandbox",
        exit_code=0,
        stdout="",
        stderr="",
    )
    assert evaluation._broker_mapping(event)["argv"] == ["pytest"]

    contract_case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/contract.yaml",
            command_contract={"families": {"focused_test": {"commands": [["pytest"]]}}},
        )
    )
    non_list = broker_event("focused_test", ["pytest"], 0)
    non_list["argv"] = "pytest"
    invalid = evaluation.command_oracle(
        contract_case, command_event("pytest", 0), "run", [non_list]
    )
    assert "broker argv is invalid" in cast(list[str], invalid["errors"])
    inconsistent = evaluation.command_oracle(
        contract_case,
        command_event("echo diagnostic && pytest", 0),
        "run",
        [broker_event("focused_test", ["pytest"], 0)],
    )
    assert any(
        "compound chronology inconsistent" in error
        for error in cast(list[str], inconsistent["errors"])
    )

    original_which = evaluation.shutil.which

    def bwrap_without_codex(name: str) -> str | None:
        return "/usr/bin/bwrap" if name == "bwrap" else None

    monkeypatch.setattr(evaluation.shutil, "which", bwrap_without_codex)
    with pytest.raises(EvaluationError, match="Codex executable"):
        evaluation.build_bwrap_command(case, workspace, tmp_path / "output", "m", "low")

    def invalid_codex_layout(name: str) -> str | None:
        if name == "bwrap":
            return "/usr/bin/bwrap"
        if name == "codex":
            return "/tmp/missing-codex/bin/codex"
        return original_which(name)

    monkeypatch.setattr(evaluation.shutil, "which", invalid_codex_layout)
    with pytest.raises(EvaluationError, match="runtime layout"):
        evaluation.build_bwrap_command(case, workspace, tmp_path / "output", "m", "low")

    (workspace / "value.txt").write_text("dirty\n", encoding="utf-8")
    with pytest.raises(EvaluationError, match="workspace must be pristine"):
        evaluation._validate_boundary_paths(case, workspace, tmp_path / "output")


def test_install_file_link_and_run_case_broker_error_are_materialized(
    tmp_path: Path, evaluation_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    target = source / "single-skill.txt"
    target.write_text("single\n", encoding="utf-8")
    (source / "install.sh").write_text(
        '#!/bin/sh\nmkdir -p "$CODEX_HOME/skills"\n'
        'touch "$CODEX_HOME/skills/plain"\n'
        'ln -s "$PWD/single-skill.txt" "$CODEX_HOME/skills/single"\n',
        encoding="utf-8",
    )
    auth = tmp_path / "auth.json"
    auth.write_text("{}", encoding="utf-8")
    home = tmp_path / "home"
    evaluation.install_arm_home(source, auth, home)
    assert (home / "skills/plain").is_file()
    assert (home / "skills/single").read_text(encoding="utf-8") == "single\n"
    assert not (home / "skills/single").is_symlink()

    case = evaluation.load_case(write_case(evaluation_root / "cases/run.yaml"))
    workspace = tmp_path / "workspace"
    evaluation.prepare_workspace(case, workspace)

    class BrokerWithError:
        instances = 0

        def __init__(self, *args: object) -> None:
            type(self).instances += 1
            self.events: list[evaluation.BrokerEvent] = []
            self.errors = (
                [] if type(self).instances == 1 else ["broker lifecycle fault"]
            )

        def start(self) -> None:
            return None

        def close(self) -> None:
            return None

    def no_install(*args: object) -> None:
        return None

    def successful_codex(
        command: tuple[str, ...] | list[str],
        cwd: Path,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        (workspace / "value.txt").write_text("after\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "{}\n", "")

    monkeypatch.setattr(evaluation, "CommandBroker", BrokerWithError)
    monkeypatch.setattr(evaluation, "install_arm_home", no_install)
    monkeypatch.setattr(
        evaluation,
        "run_executor_boundary_preflight",
        bypass_executor_boundary_preflight,
    )
    monkeypatch.setattr(evaluation, "_run_model", successful_codex)
    result = evaluation.run_case(
        case, workspace, source, auth, tmp_path / "run-output", "model", "low"
    )
    oracle = cast(dict[str, object], result["command_oracle"])
    assert oracle["valid"] is False
    assert "broker lifecycle fault" in cast(list[str], oracle["errors"])
    assert cast(dict[str, object], result["verification"])["passed"] is True
    assert cast(dict[str, object], result["task_outcome"])["valid"] is True
    assert cast(dict[str, object], result["evidence_integrity"])["valid"] is False


def test_shell_runtime_rejects_malformed_manifest_and_missing_real_shell(
    tmp_path: Path, evaluation_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = evaluation.load_case(write_case(evaluation_root / "cases/shell.yaml"))
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    evaluation.create_broker_shims(runtime, case)
    manifest = runtime / evaluation.SHELL_MANIFEST_NAME
    manifest.chmod(0o644)
    manifest.write_text("[", encoding="utf-8")
    with pytest.raises(EvaluationError, match="manifest is invalid"):
        evaluation._validate_shell_runtime(runtime, case)
    manifest.write_text("[]", encoding="utf-8")
    with pytest.raises(EvaluationError, match="manifest is invalid"):
        evaluation._validate_shell_runtime(runtime, case)
    manifest.write_text('{"allowed_changes": []}\n', encoding="utf-8")
    with pytest.raises(EvaluationError, match="does not match case"):
        evaluation._validate_shell_runtime(runtime, case)
    missing_runtime = tmp_path / "missing-runtime"
    missing_runtime.mkdir()
    original_is_file = Path.is_file

    def missing_bash(path: Path) -> bool:
        return False if path == Path("/usr/bin/bash") else original_is_file(path)

    monkeypatch.setattr(Path, "is_file", missing_bash)
    with pytest.raises(EvaluationError, match="required real shell is missing"):
        evaluation._create_executor_shell_runtime(missing_runtime, case)
