"""Case and schema contracts for the writable evaluation runner."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from scripts import run_writable_agent_eval as evaluation
from scripts.run_writable_agent_eval import EvaluationError
from tests.support.writable_eval import (
    evaluation_root as evaluation_root,
)
from tests.support.writable_eval import (
    write_case,
    write_fixture,
)

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


def test_case_relative_fixture_roots_do_not_bleed(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    write_fixture(first, "shared").joinpath("value.txt").write_text("one\n")
    write_fixture(second, "shared").joinpath("value.txt").write_text("two\n")
    one = evaluation.load_case(write_case(first / "cases/T.yaml", fixture="shared"))
    two = evaluation.load_case(write_case(second / "cases/T.yaml", fixture="shared"))
    assert (one.fixture_root / one.fixture / "value.txt").read_text() == "one\n"
    assert (two.fixture_root / two.fixture / "value.txt").read_text() == "two\n"


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
