from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

import pytest
import yaml

from scripts.run_writable_agent_eval import (
    BrokerEvent,
    command_oracle,
    final_oracle,
    load_case,
    prepare_workspace,
    validation_selection,
    verify_workspace,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVALUATION_ROOT = REPOSITORY_ROOT / "evaluations/progressive-validation-selection"
CASES = sorted((EVALUATION_ROOT / "cases").glob("*.yaml"))
CASE_IDS = {f"P{number:02}" for number in range(1, 11)} | {
    f"H{number:02}" for number in range(1, 5)
}
LIVE_CANARY_CASE_ID = "C01"


def _event(command: str, output: str, exit_code: int) -> str:
    return json.dumps(
        {
            "type": "item.completed",
            "item": {
                "type": "command_execution",
                "command": command,
                "aggregated_output": output,
                "exit_code": exit_code,
            },
        }
    )


def _broker_event(
    family: str, argv: list[str], exit_code: int, *, context: str = "executor_sandbox"
) -> dict[str, object]:
    return {
        "execution_id": 1,
        "family": family,
        "argv": argv,
        "argv_sha256": hashlib.sha256("\0".join(argv).encode()).hexdigest(),
        "cwd": "/workspace",
        "execution_context": context,
        "exit_code": exit_code,
    }


def _runner_event(
    family: str, argv: list[str], exit_code: int, *, execution_id: int = 1
) -> BrokerEvent:
    return BrokerEvent(
        execution_id=execution_id,
        family=family,
        argv=tuple(argv),
        argv_sha256=hashlib.sha256("\0".join(argv).encode()).hexdigest(),
        cwd="/workspace",
        execution_context="executor_sandbox",
        exit_code=exit_code,
        stdout="",
        stderr="",
        delivery_receipt="a" * 64,
    )


def _text(*lines: str) -> str:
    return "\n".join(lines) + "\n"


def _solve(case_id: str, workspace: Path) -> None:
    replacements = {
        "P01": {
            "README.md": _text(
                "# Release notes",
                "",
                "This introduces the reviewed release-notes process.",
                "",
                "Read the [release guide](docs/release-guide.md) "
                "before preparing a release.",
            )
        },
        "P02": {
            "content/release-channel.txt": "stable\n",
            "docs/generated-release.md": (
                "# Release channel\\n\\nCurrent channel: stable\\n"
            ),
        },
        "P03": {
            "AGENTS.md": _text(
                "# Repository Instructions",
                "",
                "Review conclusions must record the affected seam "
                "and validation evidence.",
            )
        },
        "P04": {
            "src/slug.py": _text(
                "def normalize_slug(value: str) -> str:",
                "    return value.strip().lower().replace(' ', '-')",
            )
        },
        "P05": {
            "schema/profile.schema.json": json.dumps(
                {
                    "type": "object",
                    "required": ["id", "email", "display_name"],
                    "properties": {
                        "id": {"type": "string"},
                        "email": {"type": "string"},
                        "display_name": {"type": "string"},
                    },
                },
                indent=2,
            )
            + "\n",
            "consumers/summary.py": _text(
                "def summarize(profile: dict[str, str]) -> str:",
                "    return profile['display_name']",
            ),
            "consumers/export.py": _text(
                "def export_row(profile: dict[str, str]) -> list[str]:",
                "    return [profile['id'], profile['display_name'], profile['email']]",
            ),
        },
        "P06": {
            "src/greeting.py": _text(
                "def format_greeting(name: str) -> str:", "    return f'Hello, {name}!'"
            ),
            "README.md": _text(
                "# Greeting utility",
                "",
                "`format_greeting(name)` returns `Hello, Ada!` for Ada.",
            ),
        },
        "P07": {
            "src/conversion.py": _text(
                "def to_milliseconds(seconds: int) -> int:", "    return seconds * 1000"
            )
        },
        "P09": {
            "src/parser.py": _text(
                "def parse_record(text: str) -> tuple[str, str]:",
                "    left, right = text.split(':')",
                "    return left.strip(), right.strip()",
            )
        },
        "P10": {
            "validation/selector.py": _text(
                "def select_for(change_area: str) -> str:", "    return 'complete_gate'"
            ),
            "dependency.lock": "gate-selector==2.0\nharness-contract==2.0\n",
            "scripts/harness.py": _text(
                "def canonical_gate_steps() -> tuple[str, ...]:",
                "    return ('complete_gate', 'dependency.lock')",
            ),
        },
        "H01": {
            "README.md": _text(
                "# Greeting utility",
                "",
                "Run this example to print the greeting:",
                "",
                "```sh",
                "printf 'hello, calibration\\n'",
                "```",
            )
        },
        "H02": {
            "src/normalize.py": _text(
                "def normalize(value: str) -> str:",
                "    return ' '.join(value.split())",
            )
        },
        "H03": {
            "src/generate-summary.py": _text(
                "from pathlib import Path",
                "",
                "Path('generated').mkdir(exist_ok=True)",
                "Path('generated/release-summary.txt').write_text("
                "'release-status: published\\n')",
            ),
            "generated/release-summary.txt": "release-status: published\n",
        },
    }
    for relative, text in replacements.get(case_id, {}).items():
        (workspace / relative).write_text(text, encoding="utf-8")


def _manifest_entries() -> dict[str, str]:
    paths = [
        path
        for path in EVALUATION_ROOT.rglob("*")
        if path.is_file()
        and path.name != "fixture-manifest.json"
        and "results" not in path.relative_to(EVALUATION_ROOT).parts
        and (
            "fixtures" in path.relative_to(EVALUATION_ROOT).parts
            or path.relative_to(EVALUATION_ROOT).parts[0] == "cases"
            or path.name
            in {
                "rubric.yaml",
                "judge-prompt.md",
                "result.schema.json",
                "batch-config.json",
                "batch.schema.json",
            }
        )
    ]
    return {
        path.relative_to(EVALUATION_ROOT).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(paths)
    }


def test_freezes_fourteen_comparison_cases_and_one_independent_live_canary() -> None:
    assert {path.stem for path in CASES} == CASE_IDS | {LIVE_CANARY_CASE_ID}
    assert {load_case(path).case_id for path in CASES} == CASE_IDS | {
        LIVE_CANARY_CASE_ID
    }
    config = json.loads((EVALUATION_ROOT / "batch-config.json").read_text())
    assert config["case_ids"] == ["P02", "P03", "P05"]
    assert config["live_canary_case_id"] == LIVE_CANARY_CASE_ID
    for path in CASES:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        contract = raw["command_contract"]
        assert all(contract[key] for key in ("required", "ordered")), path
        assert "forbidden" in contract, path
        normalized = load_case(path).command_contract
        assert normalized is not None
        assert normalized["required"] and normalized["ordered_required"], path


def test_prompts_and_fixtures_do_not_leak_oracle_metadata() -> None:
    forbidden = ("expected", "forbidden", "rubric", "arm")
    for path in CASES:
        prompt = yaml.safe_load(path.read_text(encoding="utf-8"))["prompt"].lower()
        assert not any(token in prompt for token in forbidden), path
    for path in (EVALUATION_ROOT / "fixtures").rglob("*"):
        if path.is_file() and path.suffix in {".md", ".py", ".txt"}:
            text = path.read_text(encoding="utf-8").lower()
            assert not any(
                token in text
                for token in ("expected event", "forbidden family", "rubric")
            ), path


def test_alias_paths_exist_or_name_an_intentional_executable() -> None:
    executables = {"bash", "sh", "python", "python3", "make"}
    for path in CASES:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        fixture = EVALUATION_ROOT / "fixtures" / raw["fixture"]
        for config in raw["command_contract"]["families"].values():
            for command in config["commands"]:
                assert command[0] in executables, (path, command)
                for part in command[1:]:
                    if part.startswith(("scripts/", "tests/")) and part.endswith(
                        (".py", ".sh")
                    ):
                        assert (fixture / part).is_file(), (path, part)


@pytest.mark.parametrize("case_path", CASES, ids=lambda path: path.stem)
def test_initial_and_solved_fixture_verification(
    case_path: Path, tmp_path: Path
) -> None:
    case = load_case(case_path)
    workspace = tmp_path / case.case_id
    prepare_workspace(case, workspace)
    initial = verify_workspace(case, workspace)
    assert bool(initial["passed"]) is (case.case_id in {"P08", "H04", "C01"})
    _solve(case.case_id, workspace)
    solved = verify_workspace(case, workspace)
    assert solved["passed"], solved


def test_manifest_hashes_freeze_the_final_lexical_tree() -> None:
    manifest = json.loads((EVALUATION_ROOT / "fixture-manifest.json").read_text())
    entries = _manifest_entries()
    assert manifest["files"] == entries
    canonical = "".join(f"{path}\0{digest}\n" for path, digest in entries.items())
    assert (
        manifest["root_tree_sha256"] == hashlib.sha256(canonical.encode()).hexdigest()
    )


def test_broker_evidence_is_runner_owned_and_execution_context_is_bounded() -> None:
    p09 = load_case(EVALUATION_ROOT / "cases/P09.yaml")
    argv = ["python", "-m", "unittest", "-q"]
    trajectory = _event("python -m unittest -q", "", 0)
    result = command_oracle(
        p09, trajectory, "run", [_broker_event("complete_gate", argv, 0)]
    )
    assert result["valid"] is True
    selection = validation_selection(p09, [_runner_event("complete_gate", argv, 0)])
    assert selection["forbidden_families"] == ["complete_gate"]
    mismatch = command_oracle(
        p09, trajectory, "run", [_broker_event("focused_test", argv, 0)]
    )
    assert "raw/broker mismatch for complete_gate at line 1" in cast(
        list[str], mismatch["errors"]
    )
    extra = command_oracle(p09, "", "run", [_broker_event("complete_gate", argv, 0)])
    assert "broker event has no raw command counterpart" in cast(
        list[str], extra["errors"]
    )
    for case_id in ("P08", "H04"):
        case = load_case(EVALUATION_ROOT / f"cases/{case_id}.yaml")
        contexts = cast(
            dict[str, str],
            cast(dict[str, object], case.command_contract)["execution_contexts"],
        )
        assert contexts["host_probe"] == "executor_sandbox"


def test_live_canary_requires_one_real_shell_check_no_changes_and_ready_status(
    tmp_path: Path,
) -> None:
    case = load_case(EVALUATION_ROOT / "cases/C01.yaml")
    assert not case.allowed_changes
    assert not case.required_changes
    assert case.command_contract is not None
    aliases = cast(dict[str, list[list[str]]], case.command_contract["aliases"])
    assert aliases == {"contract_check": [["bash", "scripts/check-live-canary.sh"]]}
    trajectory = _event("bash scripts/check-live-canary.sh", "live canary passed", 0)
    oracle = command_oracle(
        case,
        trajectory,
        "live-canary",
        [_broker_event("contract_check", aliases["contract_check"][0], 0)],
    )
    assert oracle["valid"], oracle
    final_message = tmp_path / "final-message.txt"
    final_message.write_text("VERIFICATION_STATUS: verified_ready\n", encoding="utf-8")
    assert final_oracle(case, final_message) == {
        "enabled": True,
        "valid": True,
        "status": "verified_ready",
        "errors": [],
    }


def test_result_schema_matches_rubric_codes_and_runner_result_shape() -> None:
    schema = json.loads((EVALUATION_ROOT / "result.schema.json").read_text())
    rubric = yaml.safe_load((EVALUATION_ROOT / "rubric.yaml").read_text())
    critical_codes = schema["$defs"]["blind_judgment"]["properties"][
        "critical_failures"
    ]["items"]["enum"]
    assert set(critical_codes) == set(rubric["critical_failures"])
    broker = schema["$defs"]["broker_event"]
    assert set(broker["required"]) == {
        "execution_id",
        "family",
        "argv",
        "argv_sha256",
        "cwd",
        "execution_context",
        "exit_code",
    }
    assert broker["additionalProperties"] is False
    assert broker["properties"]["execution_context"] == {"const": "executor_sandbox"}
    observation = schema["$defs"]["command_observation"]
    assert set(observation["required"]) == {
        "line",
        "sequence",
        "raw_command",
        "argv",
        "family",
        "exit_code",
    }
    assert observation["properties"]["raw_command"] == {
        "type": "string",
        "minLength": 1,
    }
    result_required = set(schema["required"])
    assert result_required == {
        "case_id",
        "model",
        "reasoning_effort",
        "codex_exit_code",
        "elapsed_seconds",
        "verification",
        "task_outcome",
        "validation_selection",
        "evidence_integrity",
        "command_oracle",
        "final_oracle",
    }
    selection = schema["$defs"]["validation_selection"]
    assert selection["additionalProperties"] is False
    assert {
        "required_missing",
        "ordered_missing",
        "forbidden_families",
        "forbidden_event_count",
    } <= set(selection["required"])


def test_oracle_negative_controls_cover_wrapper_compound_completion_and_order() -> None:
    case = load_case(EVALUATION_ROOT / "cases/P09.yaml")
    forged = _event(
        "python scripts/check.py focused_test", "CALIBRATION_CHECK_EVENT {}", 1
    )
    assert not command_oracle(case, forged, "run")["valid"]
    unwrapped = _event("python -m unittest -q", "", 0)
    unwrapped_errors = cast(list[str], command_oracle(case, unwrapped, "run")["errors"])
    assert "missing runner-owned broker evidence" in unwrapped_errors
    compound = _event(
        "python scripts/check.py focused_test && "
        "python scripts/check.py unrelated_suite",
        "",
        0,
    )
    compound_errors = cast(list[str], command_oracle(case, compound, "run")["errors"])
    assert "cannot determine compound branch at line 1" in compound_errors
    missing_completion = _event(
        "python scripts/check.py focused_test",
        "CALIBRATION_CHECK_EVENT "
        '{"schema_version": 1, "run_id": "run", "check_id": "focused_test", '
        '"phase": "begin", "exit_code": null, '
        '"covered_seam": "parser-empty-field"}',
        0,
    )
    assert not command_oracle(case, missing_completion, "run")["valid"]
    reversed_order = "\n".join(
        [
            _event("python scripts/check.py focused_test", "", 0),
            _event("python scripts/check.py focused_test", "", 1),
        ]
    )
    assert not command_oracle(case, reversed_order, "run")["valid"]
    reversed_selection = validation_selection(
        case,
        [
            _runner_event(
                "focused_test", ["python", "scripts/check.py", "focused_test"], 0
            ),
            _runner_event(
                "focused_test",
                ["python", "scripts/check.py", "focused_test"],
                1,
                execution_id=2,
            ),
        ],
    )
    assert reversed_selection["ordered_covered"] is False
