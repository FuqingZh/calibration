from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

import pytest

from scripts import run_progressive_validation_selection_eval as batch


def _result(case_id: str = "P01") -> dict[str, object]:
    return {
        "case_id": case_id,
        "model": "frozen-model",
        "reasoning_effort": "medium",
        "elapsed_seconds": 1.0,
        "codex_exit_code": 0,
        "verification": {
            "passed": True,
            "checks": [{"exit_code": 0}],
            "unexpected_changes": [],
            "missing_required_changes": [],
        },
        "task_outcome": {"valid": True, "errors": []},
        "validation_selection": {
            "enabled": True,
            "contract_satisfied": True,
            "required_covered": True,
            "ordered_covered": True,
            "required_missing": [],
            "ordered_missing": [],
            "forbidden_families": [],
            "forbidden_event_count": 0,
            "observations": [],
        },
        "evidence_integrity": {"valid": True, "errors": []},
        "command_oracle": {"valid": True, "errors": []},
        "final_oracle": {"valid": True},
    }


def _smoke_manifest() -> dict[str, object]:
    schedule = batch._schedule(batch.load_batch_config())
    return {
        "requested_model": "frozen-model",
        "requested_reasoning_effort": "medium",
        "case_ids": ["P02", "P03", "P05"],
        "initial_repetitions": 2,
        "schedule": schedule,
    }


def _write_completed_slot(
    root: Path, manifest: dict[str, object], slot: dict[str, object]
) -> tuple[Path, dict[str, object]]:
    slot_id = cast(str, slot["slot_id"])
    case_id = cast(str, slot["case_id"])
    arm_key = cast(str, slot["arm_key"])
    slot_root = root / "slots" / slot_id
    output = slot_root / "output"
    output.mkdir(parents=True)
    result = _result(case_id)
    result_path = output / "result.json"
    result_path.write_text(json.dumps(result), encoding="utf-8")
    started = {"slot_id": slot_id, "case_id": case_id, "arm_key": arm_key}
    (slot_root / "started.json").write_text(json.dumps(started), encoding="utf-8")
    completed = {
        **started,
        "requested_model": manifest["requested_model"],
        "requested_reasoning_effort": manifest["requested_reasoning_effort"],
        "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
        "classification": "precise",
    }
    (slot_root / "completed.json").write_text(json.dumps(completed), encoding="utf-8")
    return slot_root, completed


def test_project_public_filters_observations_hashes_errors_and_rejects_leaks(
    tmp_path: Path,
) -> None:
    private = tmp_path / "private.json"
    public = tmp_path / "public.json"
    payload = _result()
    payload["verification"] = {
        "passed": True,
        "changed_paths": ["README.md", "/private/path", 3],
        "unexpected_changes": "not-a-list",
        "missing_required_changes": ["relative.md"],
    }
    payload["command_oracle"] = {
        "enabled": True,
        "valid": False,
        "errors": ["private error", 4],
        "observations": [
            {"raw_command": "pytest tests", "family": "focused_test", "exit_code": 0},
            {"raw_command": "unknown", "family": "unlisted", "exit_code": 0},
            {"raw_command": "wrong-exit", "family": "focused_test", "exit_code": "0"},
            "not-an-observation",
        ],
    }
    payload["task_outcome"] = {"valid": False, "errors": ["final answer failed"]}
    payload["evidence_integrity"] = {
        "valid": False,
        "errors": ["private error"],
    }
    payload["final_oracle"] = {
        "enabled": True,
        "valid": False,
        "status": "internal_state",
        "errors": "not-a-list",
    }
    private.write_text(json.dumps(payload), encoding="utf-8")

    projection = batch.project_public(private, public)

    assert projection["valid"] is False
    assert projection["verification"] == {
        "passed": True,
        "changed_path_count": 1,
        "unexpected_change_count": 0,
        "missing_required_change_count": 1,
    }
    assert projection["command_oracle"] == {
        "enabled": True,
        "valid": False,
        "observations": [
            {
                "family": "focused_test",
                "exit_code": 0,
                "command_sha256": hashlib.sha256(b"pytest tests").hexdigest(),
            }
        ],
        "errors": [hashlib.sha256(b"private error").hexdigest(), "[invalid]"],
    }
    assert projection["final_oracle"] == {
        "enabled": True,
        "valid": False,
        "status": None,
        "errors": [],
    }

    leaking = _result()
    leaking["model"] = "arm"
    private.write_text(json.dumps(leaking), encoding="utf-8")
    with pytest.raises(batch.BatchError, match="private control field"):
        batch.project_public(private, tmp_path / "leaking.json")


def test_project_public_fails_closed_when_projection_breaks_public_schema(
    tmp_path: Path,
) -> None:
    private = tmp_path / "private.json"
    payload = _result("not-a-public-case")
    private.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(batch.BatchError, match="public projection fails schema"):
        batch.project_public(private, tmp_path / "public.json")


@pytest.mark.parametrize(
    "schema",
    [{"$defs": []}, {"$defs": {"public_projection": []}}],
)
def test_project_public_requires_a_public_projection_schema(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, schema: dict[str, object]
) -> None:
    private = tmp_path / "private.json"
    payload = _result()
    private.write_text(json.dumps(payload), encoding="utf-8")
    original_json = batch._json

    def schema_json(path: Path) -> dict[str, object]:
        return schema if path == batch.SCHEMA_PATH else original_json(path)

    monkeypatch.setattr(batch, "_json", schema_json)
    with pytest.raises(batch.BatchError, match="public projection"):
        batch.project_public(private, tmp_path / "public.json")


def test_classification_and_smoke_slot_boundaries_are_fail_closed() -> None:
    assert (
        batch._classification("baseline", {"verification": {}, "command_oracle": {}})
        == "critical"
    )
    assert batch._classification("baseline", {}) == "critical"
    unsafe = _result()
    unsafe["verification"] = {"checks": [{"exit_code": "0"}]}
    assert batch._classification("baseline", unsafe) == "critical"

    with pytest.raises(batch.BatchError, match="frozen schedule is invalid"):
        batch._smoke_slots({"schedule": "not-a-list"})
    with pytest.raises(batch.BatchError, match="initial schedule metadata"):
        batch._smoke_slots({"schedule": [], "case_ids": [], "initial_repetitions": 0})
    with pytest.raises(batch.BatchError, match="frozen smoke slot is invalid"):
        batch._smoke_slots(
            {
                "case_ids": ["P01"],
                "initial_repetitions": 1,
                "schedule": [{"repetition": 1, "slot_id": "", "phase": "smoke"}],
            }
        )
    with pytest.raises(batch.BatchError, match="12 unique slots"):
        batch._smoke_slots(
            {
                "case_ids": ["P02", "P03", "P05"],
                "initial_repetitions": 2,
                "schedule": [
                    {"repetition": 1, "slot_id": "duplicate", "phase": "smoke"}
                ]
                * 12,
            }
        )

    manifest = _smoke_manifest()
    smoke_slots = batch._smoke_slots(manifest)
    assert len(smoke_slots) == 12
    first_slot = smoke_slots[0]
    position, selected = batch._slot_from_manifest(
        manifest, cast(str, first_slot["slot_id"])
    )
    assert position == 0 and selected == first_slot
    with pytest.raises(batch.BatchError, match="not in the frozen smoke schedule"):
        batch._slot_from_manifest(manifest, "missing-slot")
    with pytest.raises(batch.BatchError, match="tiebreak schedule metadata"):
        batch._tiebreak_slots({"schedule": "invalid", "case_ids": []})
    with pytest.raises(batch.BatchError, match="6 unique slots"):
        batch._tiebreak_slots({"schedule": [], "case_ids": manifest["case_ids"]})


def test_completed_slot_rejects_invalid_ledger_identity_hash_and_symlink(
    tmp_path: Path,
) -> None:
    manifest = _smoke_manifest()
    slot = batch._smoke_slots(manifest)[0]
    root = tmp_path / "batch"
    slot_root, completed = _write_completed_slot(root, manifest, slot)
    assert batch._validate_completed_slot(root, manifest, slot) == batch._assessment(
        _result(cast(str, slot["case_id"]))
    )

    invalid_manifest = {**manifest, "requested_reasoning_effort": ""}
    with pytest.raises(batch.BatchError, match="execution fields are invalid"):
        batch._validate_completed_slot(root, invalid_manifest, slot)

    started_path = slot_root / "started.json"
    started_path.write_text("{}", encoding="utf-8")
    with pytest.raises(batch.BatchError, match="start ledger mismatch"):
        batch._validate_completed_slot(root, manifest, slot)
    started_path.write_text(
        json.dumps(
            {
                "slot_id": slot["slot_id"],
                "case_id": slot["case_id"],
                "arm_key": slot["arm_key"],
            }
        ),
        encoding="utf-8",
    )

    completed["result_sha256"] = "tampered"
    (slot_root / "completed.json").write_text(json.dumps(completed), encoding="utf-8")
    with pytest.raises(batch.BatchError, match="completion ledger mismatch"):
        batch._validate_completed_slot(root, manifest, slot)
    completed["result_sha256"] = hashlib.sha256(
        (slot_root / "output/result.json").read_bytes()
    ).hexdigest()

    result_path = slot_root / "output/result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["model"] = "other-model"
    result_path.write_text(json.dumps(result), encoding="utf-8")
    completed["result_sha256"] = hashlib.sha256(result_path.read_bytes()).hexdigest()
    (slot_root / "completed.json").write_text(json.dumps(completed), encoding="utf-8")
    with pytest.raises(batch.BatchError, match="result identity mismatch"):
        batch._validate_completed_slot(root, manifest, slot)

    failed_path = slot_root / "failed.json"
    failed_path.write_text("{}", encoding="utf-8")
    with pytest.raises(batch.BatchError, match="recorded an execution failure"):
        batch._validate_completed_slot(root, manifest, slot)
    failed_path.unlink()

    result_path.unlink()
    with pytest.raises(batch.BatchError, match="cannot safely read frozen slot result"):
        batch._validate_completed_slot(root, manifest, slot)

    started_path.unlink()
    started_path.symlink_to("elsewhere.json")
    with pytest.raises(batch.BatchError, match="cannot safely read frozen slot ledger"):
        batch._validate_completed_slot(root, manifest, slot)
