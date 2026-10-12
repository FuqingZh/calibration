"""Command evidence, validation selection, and final-result classification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

import pytest

from scripts import run_writable_agent_eval as evaluation
from scripts.run_writable_agent_eval import EvaluationError
from tests.support.writable_eval import (
    broker_event,
    command_event,
    write_case,
)
from tests.support.writable_eval import (
    evaluation_root as evaluation_root,
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
    newline_events = [
        event(1, "generator", ("generate",)),
        event(2, "artifact_readback", ("readback",)),
    ]
    newline_output = "\n".join(
        evaluation._delivery_receipt_line(cast(str, item.delivery_receipt))
        for item in newline_events
    )
    newline_oracle = evaluation.command_oracle(
        case,
        command_event("generate\nreadback", 0, newline_output),
        "run",
        newline_events,
    )
    assert newline_oracle["valid"] is True

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
        {
            "valid": False,
            "errors": [
                "line 8: unknown validation command",
                "line 10: malformed compound command",
                "line 13: unrecognized command",
            ],
        }
    )
    assert integrity == {
        "valid": False,
        "errors": ["line 8: unknown validation command"],
    }
    unlisted_forbidden = evaluation.command_oracle(
        case,
        command_event("python3 scripts/complete_gate.py", 0),
        "run",
        [],
    )
    assert evaluation.evidence_integrity(unlisted_forbidden)["valid"] is False
    discovery = evaluation.command_oracle(
        case,
        command_event("sed -n 1,20p scripts/complete_gate.py", 0),
        "run",
        [],
    )
    assert evaluation.evidence_integrity(discovery)["valid"] is True
    assert evaluation.evidence_integrity(
        {
            "valid": False,
            "errors": ["line 13: transport/delivery receipt mismatch"],
        }
    ) == {
        "valid": False,
        "errors": ["line 13: transport/delivery receipt mismatch"],
    }
    assert evaluation.evidence_integrity(
        {
            "valid": False,
            "errors": [
                "line 10: malformed compound command",
                "broker event 1 has no raw command counterpart",
            ],
        }
    ) == {
        "valid": False,
        "errors": ["broker event 1 has no raw command counterpart"],
    }
    assert evaluation.evidence_integrity(
        {"valid": False, "errors": ["unrecognized command"]}
    ) == {"valid": False, "errors": ["unrecognized command"]}
    assert evaluation.evidence_integrity(
        {"valid": False, "errors": ["line bad: unrecognized command"]}
    ) == {"valid": False, "errors": ["line bad: unrecognized command"]}
    assert evaluation.evidence_integrity({"valid": False, "errors": [1]}) == {
        "valid": False,
        "errors": ["command evidence errors are malformed"],
    }
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


def test_c01_final_contract_rejects_any_additional_response_line(
    tmp_path: Path, evaluation_root: Path
) -> None:
    case = evaluation.load_case(
        write_case(
            evaluation_root / "cases/C01.yaml",
            id="C01",
            allowed_changes=[],
            required_changes=[],
            final_contract={
                "required_tokens": ["VERIFICATION_STATUS: verified_ready"],
                "allowed_statuses": ["verified_ready"],
                "forbidden_statuses": [],
            },
        )
    )
    message = tmp_path / "final.txt"
    message.write_text(
        "VERIFICATION_STATUS: verified_ready\nextra detail\n", encoding="utf-8"
    )
    assert evaluation.final_oracle(case, message)["valid"] is False


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
    assert evaluation._shell_commands("pytest -q\nruff check") == [
        ["pytest", "-q"],
        ["ruff", "check"],
    ]
    assert evaluation._shell_commands("pytest -q\n\nruff check") == [
        ["pytest", "-q"],
        ["ruff", "check"],
    ]
    assert evaluation._shell_commands("\npytest -q") == [["pytest", "-q"]]
    assert evaluation._shell_commands("printf 'a\nb'\npytest -q") == [
        ["printf", "a\nb"],
        ["pytest", "-q"],
    ]
    assert evaluation._is_discovery([]) is False
    assert evaluation._is_discovery(["git", "diff"]) is True
    assert evaluation._is_discovery(["echo", "x"]) is False
    assert evaluation._is_discovery(["find", ".", "-maxdepth", "2"])
    assert not evaluation._is_discovery(["find", ".", "-delete"])
    safe_find = (
        '/bin/bash -lc "find consumers -maxdepth 2 -type f -print '
        "-exec sed -n '1,240p' {} \\;\""
    )
    safe_find_chunks = evaluation._shell_commands(safe_find)
    assert len(safe_find_chunks) == 1
    assert evaluation._is_discovery(safe_find_chunks[0]) is True
    assert not evaluation._is_discovery(
        [
            "find",
            ".",
            "-exec",
            "sed",
            "-i",
            "1d",
            "{}",
            evaluation.FIND_EXEC_TERMINATOR,
        ]
    )
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
    assert evaluation._unknown_validation(["python3", "-m", "pytest"]) is True
    assert evaluation._unknown_validation(["python3", "-c", "print('check')"]) is False
    assert evaluation._unknown_validation(["pdm", "run", "ruff"]) is True
    assert evaluation._unknown_validation(["pdm", "run"]) is False
    assert evaluation._unknown_validation(["make", "check"]) is True
    assert (
        evaluation._unknown_validation(["sed", "-n", "1p", "complete_gate.py"]) is False
    )
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
