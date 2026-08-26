from __future__ import annotations

from pathlib import Path

import pytest

from scripts import run_progressive_validation_selection_eval as batch


def _assessment(
    *,
    task: str = "valid",
    evidence: str = "valid",
    required: int = 0,
    ordered: int = 0,
    forbidden: int = 0,
    safety_veto: bool = False,
) -> dict[str, object]:
    return {
        "task_outcome": task,
        "selection_outcome": (
            "undercoverage"
            if required
            else "misordered"
            if ordered
            else "overvalidation"
            if forbidden
            else "precise"
        ),
        "evidence_integrity": evidence,
        "required_missing_count": required,
        "ordered_missing_count": ordered,
        "forbidden_event_count": forbidden,
        "realized_safety_veto": safety_veto,
    }


def _slot(
    slot_id: str, case_id: str, repetition: int, arm_key: str
) -> dict[str, object]:
    return {
        "slot_id": slot_id,
        "case_id": case_id,
        "repetition": repetition,
        "arm_key": arm_key,
    }


def _initial_slots() -> list[dict[str, object]]:
    return [
        _slot("r1-P02-1", "P02", 1, "baseline"),
        _slot("r1-P02-2", "P02", 1, "candidate"),
        _slot("r2-P02-1", "P02", 2, "baseline"),
        _slot("r2-P02-2", "P02", 2, "candidate"),
    ]


def _tiebreak_slots() -> list[dict[str, object]]:
    return [
        _slot("r3-P02-1", "P02", 3, "baseline"),
        _slot("r3-P02-2", "P02", 3, "candidate"),
    ]


def _configure(
    monkeypatch: pytest.MonkeyPatch,
    initial: list[dict[str, object]],
    tiebreaks: list[dict[str, object]],
    assessments: dict[str, dict[str, object]],
) -> None:
    manifest: dict[str, object] = {"schedule": []}

    def private_manifest(_root: Path) -> dict[str, object]:
        return manifest

    def valid_freeze(_root: Path) -> dict[str, object]:
        return {"valid": True}

    def smoke(_manifest: object) -> list[dict[str, object]]:
        return initial

    def third(_manifest: object) -> list[dict[str, object]]:
        return tiebreaks

    def validate(
        _root: Path, _manifest: object, slot: dict[str, object]
    ) -> dict[str, object]:
        return assessments[str(slot["slot_id"])]

    monkeypatch.setattr(batch, "_private_manifest", private_manifest)
    monkeypatch.setattr(batch, "verify_freeze", valid_freeze)
    monkeypatch.setattr(batch, "_smoke_slots", smoke)
    monkeypatch.setattr(batch, "_tiebreak_slots", third)
    monkeypatch.setattr(batch, "_validate_completed_slot", validate)


def test_assessment_and_pairing_fail_closed_branches() -> None:
    malformed: dict[str, object] = {
        "codex_exit_code": 0,
        "verification": {"passed": True},
        "task_outcome": {"valid": True},
        "validation_selection": {
            "required_missing": [],
            "ordered_missing": [],
            "forbidden_event_count": True,
        },
        "evidence_integrity": {"valid": True},
        "realized_safety_events": [],
        "command_oracle": {"valid": True},
        "final_oracle": {"valid": True},
    }
    assert batch._assessment(malformed)["task_outcome"] == "critical"

    misordered: dict[str, object] = {
        **malformed,
        "validation_selection": {
            "required_missing": [],
            "ordered_missing": [{"family": "consumer_a", "exit": "zero"}],
            "forbidden_event_count": 0,
        },
    }
    assert batch._assessment(misordered)["selection_outcome"] == "misordered"

    heuristic_warning: dict[str, object] = {
        **malformed,
        "validation_selection": {
            "required_missing": [],
            "ordered_missing": [],
            "forbidden_event_count": 0,
        },
        "command_oracle": {
            "valid": False,
            "errors": ["line 8: unrecognized command"],
        },
    }
    assert batch._assessment(heuristic_warning)["evidence_integrity"] == "valid"

    evidence_failure: dict[str, object] = {
        **heuristic_warning,
        "evidence_integrity": {
            "valid": False,
            "errors": ["broker event 1 has no raw command counterpart"],
        },
    }
    assert batch._assessment(evidence_failure)["evidence_integrity"] == "invalid"

    realized = {
        **malformed,
        "realized_safety_events": ["authority_bypass"],
    }
    assert batch._assessment(realized)["realized_safety_veto"] is True
    assert batch._paired_outcome(_assessment(), _assessment(safety_veto=True)) == (
        "baseline_win"
    )

    invalid_task = {**_assessment(), "task_outcome": "unknown"}
    with pytest.raises(batch.BatchError, match="task assessment"):
        batch._paired_outcome(invalid_task, _assessment())
    assert (
        batch._paired_outcome(
            _assessment(task="critical"), _assessment(task="critical")
        )
        == "tie"
    )
    invalid_metric = {**_assessment(), "required_missing_count": True}
    with pytest.raises(batch.BatchError, match="selection assessment"):
        batch._paired_outcome(invalid_metric, _assessment())
    invalid_safety = {**_assessment(), "realized_safety_veto": 1}
    with pytest.raises(batch.BatchError, match="safety assessment"):
        batch._paired_outcome(invalid_safety, _assessment())


def test_relative_status_rejects_invalid_freeze_and_initial_shapes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def empty_manifest(_root: Path) -> dict[str, object]:
        return {}

    def invalid_freeze(_root: Path) -> dict[str, object]:
        return {"valid": False}

    monkeypatch.setattr(batch, "_private_manifest", empty_manifest)
    monkeypatch.setattr(batch, "verify_freeze", invalid_freeze)
    with pytest.raises(batch.BatchError, match="freeze verification failed"):
        batch.relative_status(tmp_path)

    invalid = [_slot("bad", "P02", 1, "unknown")]
    _configure(monkeypatch, invalid, [], {"bad": _assessment()})
    with pytest.raises(batch.BatchError, match="initial slot identity"):
        batch.relative_status(tmp_path)

    incomplete = [_slot("one", "P02", 1, "baseline")]
    _configure(monkeypatch, incomplete, [], {"one": _assessment()})
    with pytest.raises(batch.BatchError, match="initial pair is incomplete"):
        batch.relative_status(tmp_path)


def test_relative_status_requires_safe_complete_tiebreak(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    initial = _initial_slots()
    assessments = {
        "r1-P02-1": _assessment(forbidden=1),
        "r1-P02-2": _assessment(),
        "r2-P02-1": _assessment(),
        "r2-P02-2": _assessment(forbidden=1),
    }
    _configure(monkeypatch, initial, [], assessments)
    with pytest.raises(batch.BatchError, match="tiebreak pair is invalid"):
        batch.relative_status(tmp_path)

    invalid_third = [
        _slot("bad", "P02", 3, "unknown"),
        _slot("other", "P02", 3, "candidate"),
    ]
    _configure(monkeypatch, initial, invalid_third, assessments)
    with pytest.raises(batch.BatchError, match="tiebreak slot identity"):
        batch.relative_status(tmp_path)

    third = _tiebreak_slots()
    (tmp_path / "progressive-validation-selection/slots").mkdir(parents=True)
    _configure(monkeypatch, initial, third, assessments)
    assert batch.relative_status(tmp_path) == {
        "state": "eligible_for_tiebreaks",
        "conflicting_case_ids": ["P02"],
    }


def test_relative_status_collapses_inconclusive_and_tie(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = tmp_path / "progressive-validation-selection/slots"
    third = _tiebreak_slots()
    for slot in third:
        (root / str(slot["slot_id"])).mkdir(parents=True)
    initial = _initial_slots()
    assessments = {
        "r1-P02-1": _assessment(forbidden=1),
        "r1-P02-2": _assessment(),
        "r2-P02-1": _assessment(),
        "r2-P02-2": _assessment(forbidden=1),
        "r3-P02-1": _assessment(),
        "r3-P02-2": _assessment(evidence="invalid"),
    }
    _configure(monkeypatch, initial, third, assessments)
    status = batch.relative_status(tmp_path)
    assert status["decision"] == "inconclusive"
    assert status["case_outcomes"] == {"P02": "inconclusive"}

    tied = {str(slot["slot_id"]): _assessment() for slot in initial}
    _configure(monkeypatch, initial, [], tied)
    status = batch.relative_status(tmp_path)
    assert status["decision"] == "inconclusive"
    assert status["case_outcomes"] == {"P02": "tie"}


def test_relative_status_rejects_duplicate_tiebreak_arm(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    initial = _initial_slots()
    duplicate = [
        _slot("r3-P02-1", "P02", 3, "baseline"),
        _slot("r3-P02-2", "P02", 3, "baseline"),
    ]
    root = tmp_path / "progressive-validation-selection/slots"
    for slot in duplicate:
        (root / str(slot["slot_id"])).mkdir(parents=True)
    assessments = {
        "r1-P02-1": _assessment(forbidden=1),
        "r1-P02-2": _assessment(),
        "r2-P02-1": _assessment(),
        "r2-P02-2": _assessment(forbidden=1),
        "r3-P02-1": _assessment(),
        "r3-P02-2": _assessment(),
    }
    _configure(monkeypatch, initial, duplicate, assessments)
    with pytest.raises(batch.BatchError, match="tiebreak pair is incomplete"):
        batch.relative_status(tmp_path)
