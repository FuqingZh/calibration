from __future__ import annotations

import os
from pathlib import Path
from typing import cast

import pytest

from scripts import run_progressive_validation_selection_eval as batch


def _root(tmp_path: Path, name: str) -> Path:
    root = tmp_path / name
    root.mkdir()
    return root


def _manifest() -> dict[str, object]:
    return {
        "requested_model": "frozen-model",
        "requested_reasoning_effort": "medium",
        "arm_map": {
            "baseline": {"archive": "sources/baseline.tar"},
            "candidate": {"archive": "sources/candidate.tar"},
        },
        "schedule": batch._schedule(batch.load_batch_config()),
        "case_ids": ["P01", "P02", "P03", "P04", "P05", "P10"],
        "initial_repetitions": 2,
    }


def test_slot_directory_recovery_fails_closed_at_unsafe_boundaries(
    tmp_path: Path,
) -> None:
    with pytest.raises(batch.BatchError, match="cannot safely open missing root"):
        batch._open_directory(tmp_path / "missing", "missing root")

    root = _root(tmp_path, "run")
    assert batch._open_slot_directory(root, "slot-1") is None
    slots_root = root / "slots"
    slots_root.mkdir()
    assert batch._open_slot_directory(root, "slot-1") is None

    slots_root.rmdir()
    target = tmp_path / "slots-target"
    target.mkdir()
    slots_root.symlink_to(target, target_is_directory=True)
    with pytest.raises(
        batch.BatchError, match="cannot safely open private slot ledger"
    ):
        batch._open_slot_directory(root, "slot-1")


def test_slot_ledger_listing_rethrows_an_unsafe_slots_directory(tmp_path: Path) -> None:
    root = _root(tmp_path, "run")
    (root / "slots").write_text("not a directory", encoding="utf-8")

    with pytest.raises(
        batch.BatchError, match="cannot safely open private slot ledger"
    ):
        batch._slot_ledger_entry_names(root)


def test_completed_smoke_prefix_rejects_extra_or_invalid_slot_ids(
    tmp_path: Path,
) -> None:
    root = _root(tmp_path, "extra-slot")
    (root / "slots/unexpected").mkdir(parents=True)
    with pytest.raises(
        batch.BatchError, match="private slot ledger is not safely resumable"
    ):
        batch._completed_smoke_prefix(root, {}, [{"slot_id": "slot-1"}])

    for slot_id in (None, "", 1):
        root = _root(tmp_path, f"invalid-{slot_id!r}")
        with pytest.raises(batch.BatchError, match="frozen smoke slot is invalid"):
            batch._completed_smoke_prefix(root, {}, [{"slot_id": slot_id}])


def test_slot_ledger_leaf_and_json_readers_fail_closed(tmp_path: Path) -> None:
    root = _root(tmp_path, "run")
    slot_root = root / "slots/slot-1"
    slot_root.mkdir(parents=True)
    descriptor = batch._open_slot_directory(root, "slot-1")
    assert descriptor is not None
    try:
        with pytest.raises(batch.BatchError, match="private slot JSON path is empty"):
            batch._slot_json_with_sha256(descriptor, "slot-1")

        target = tmp_path / "leaf-target.json"
        target.write_text("{}", encoding="utf-8")
        (slot_root / "started.json").symlink_to(target)
        with pytest.raises(
            batch.BatchError, match="cannot safely read frozen slot ledger"
        ):
            batch._slot_regular_file_exists(descriptor, "started.json", "slot-1")

        (slot_root / "output").mkdir()
        with pytest.raises(
            batch.BatchError, match="frozen slot ledger leaf is not regular"
        ):
            batch._slot_regular_file_exists(descriptor, "output", "slot-1")
        with pytest.raises(batch.BatchError, match="frozen slot result is not regular"):
            batch._slot_json_with_sha256(descriptor, "slot-1", "output")

        invalid = slot_root / "invalid.json"
        invalid.write_text("not json", encoding="utf-8")
        with pytest.raises(batch.BatchError, match="frozen slot JSON is invalid"):
            batch._slot_json_with_sha256(descriptor, "slot-1", "invalid.json")

        array = slot_root / "array.json"
        array.write_text("[]", encoding="utf-8")
        with pytest.raises(batch.BatchError, match="frozen slot JSON object required"):
            batch._slot_json_with_sha256(descriptor, "slot-1", "array.json")
    finally:
        os.close(descriptor)


def test_completed_slot_rejects_missing_completed_ledger(tmp_path: Path) -> None:
    root = _root(tmp_path, "run")
    slot = {"slot_id": "slot-1", "case_id": "P01", "arm_key": "baseline"}
    slot_root = root / "slots/slot-1"
    slot_root.mkdir(parents=True)
    (slot_root / "started.json").write_text(
        '{"slot_id":"slot-1","case_id":"P01","arm_key":"baseline"}',
        encoding="utf-8",
    )

    with pytest.raises(batch.BatchError, match="frozen slot is incomplete: slot-1"):
        batch._validate_completed_slot(root, _manifest(), slot)


def test_manifest_slot_fails_closed_when_result_slot_cannot_be_reopened(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    manifest = _manifest()
    first = batch._smoke_slots(manifest)[0]
    slot_id = cast(str, first["slot_id"])

    def valid_freeze(_private_root: Path) -> dict[str, object]:
        return {"valid": True}

    def private_manifest(_private_root: Path) -> dict[str, object]:
        return manifest

    def missing_slot_directory(_root: Path, _slot: str) -> None:
        return None

    def successful_run(
        _archive: Path,
        _source_dir: Path,
        _case_path: Path,
        _workspace: Path,
        _auth_file: Path,
        _output_dir: Path,
        _model: str,
        _reasoning_effort: str,
    ) -> dict[str, object]:
        return {}

    monkeypatch.setattr(batch, "verify_freeze", valid_freeze)
    monkeypatch.setattr(batch, "_private_manifest", private_manifest)

    def permit_canary(_root: Path) -> None:
        return None

    monkeypatch.setattr(batch, "_require_verified_canary", permit_canary)
    (tmp_path / "progressive-validation-selection").mkdir()
    monkeypatch.setattr(batch, "_open_slot_directory", missing_slot_directory)
    monkeypatch.setattr(batch, "run_archived_slot", successful_run)

    with pytest.raises(
        batch.BatchError, match=f"single-run result is missing or unsafe: {slot_id}"
    ):
        batch.run_manifest_slot(tmp_path, tmp_path / "auth.json", slot_id)
