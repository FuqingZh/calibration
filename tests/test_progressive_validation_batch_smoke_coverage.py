from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

import pytest

from scripts import run_progressive_validation_selection_eval as batch


@pytest.fixture(autouse=True)
def _permit_canary_for_smoke_recovery_tests(  # pyright: ignore[reportUnusedFunction]
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise smoke-ledger recovery independently of the separate canary gate."""

    def permit(_root: Path) -> None:
        return None

    monkeypatch.setattr(batch, "_require_verified_canary", permit)


def _manifest_root(
    tmp_path: Path, name: str = "private"
) -> tuple[Path, dict[str, object]]:
    private_root = tmp_path / name
    root = private_root / "progressive-validation-selection"
    root.mkdir(parents=True)
    manifest: dict[str, object] = {
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
    _write_manifest(root, manifest)
    return private_root, manifest


def _write_manifest(root: Path, manifest: dict[str, object]) -> None:
    manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
    (root / "manifest.json").write_bytes(manifest_bytes)
    digest = {"sha256": hashlib.sha256(manifest_bytes).hexdigest()}
    (root / "manifest.sha256").write_text(
        json.dumps(digest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _result(case_id: str, *, model: str = "frozen-model") -> dict[str, object]:
    return {
        "case_id": case_id,
        "model": model,
        "reasoning_effort": "medium",
        "codex_exit_code": 0,
        "verification": {"passed": True},
        "command_oracle": {"valid": True, "errors": []},
    }


def _valid_freeze(_private_root: Path) -> dict[str, object]:
    return {"valid": True}


def _invalid_freeze(_private_root: Path) -> dict[str, object]:
    return {"valid": False}


def _write_completed_slot(
    root: Path,
    manifest: dict[str, object],
    slot: dict[str, object],
    result: dict[str, object],
) -> None:
    slot_id = cast(str, slot["slot_id"])
    case_id = cast(str, slot["case_id"])
    arm_key = cast(str, slot["arm_key"])
    slot_root = root / "slots" / slot_id
    output = slot_root / "output"
    output.mkdir(parents=True)
    result_path = output / "result.json"
    result_path.write_text(json.dumps(result), encoding="utf-8")
    started = {"slot_id": slot_id, "case_id": case_id, "arm_key": arm_key}
    (slot_root / "started.json").write_text(json.dumps(started), encoding="utf-8")
    completed = {
        **started,
        "requested_model": manifest["requested_model"],
        "requested_reasoning_effort": manifest["requested_reasoning_effort"],
        "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
        "classification": batch._classification(arm_key, result),
    }
    (slot_root / "completed.json").write_text(json.dumps(completed), encoding="utf-8")


def test_completed_slot_rejects_result_identity_tampering(tmp_path: Path) -> None:
    _private_root, manifest = _manifest_root(tmp_path)
    root = tmp_path / "private/progressive-validation-selection"
    first = cast(list[dict[str, object]], manifest["schedule"])[0]
    _write_completed_slot(
        root, manifest, first, _result(cast(str, first["case_id"]), model="other-model")
    )

    with pytest.raises(batch.BatchError, match="result identity mismatch"):
        batch._validate_completed_slot(root, manifest, first)


def test_completed_slot_rejects_tampered_completion_ledger(tmp_path: Path) -> None:
    _private_root, manifest = _manifest_root(tmp_path)
    root = tmp_path / "private/progressive-validation-selection"
    first = cast(list[dict[str, object]], manifest["schedule"])[0]
    _write_completed_slot(root, manifest, first, _result(cast(str, first["case_id"])))
    completed_path = root / "slots" / cast(str, first["slot_id"]) / "completed.json"
    completed = json.loads(completed_path.read_text(encoding="utf-8"))
    completed["classification"] = "tampered-classification"
    completed_path.write_text(json.dumps(completed), encoding="utf-8")

    with pytest.raises(batch.BatchError, match="completion ledger mismatch"):
        batch._validate_completed_slot(root, manifest, first)


def test_completed_slot_rejects_output_directory_symlink_to_external_result(
    tmp_path: Path,
) -> None:
    _private_root, manifest = _manifest_root(tmp_path)
    root = tmp_path / "private/progressive-validation-selection"
    first = batch._smoke_slots(manifest)[0]
    _write_completed_slot(root, manifest, first, _result(cast(str, first["case_id"])))
    slot_root = root / "slots" / cast(str, first["slot_id"])
    output = slot_root / "output"
    external_output = tmp_path / "external-output"
    output.rename(external_output)
    output.symlink_to(external_output, target_is_directory=True)

    with pytest.raises(batch.BatchError, match="cannot safely open"):
        batch._validate_completed_slot(root, manifest, first)
    with pytest.raises(batch.BatchError, match="cannot safely open"):
        batch._completed_smoke_prefix(root, manifest, batch._smoke_slots(manifest))


def test_completed_slot_rejects_slot_parent_symlink_before_recovery(
    tmp_path: Path,
) -> None:
    _private_root, manifest = _manifest_root(tmp_path)
    root = tmp_path / "private/progressive-validation-selection"
    first = batch._smoke_slots(manifest)[0]
    _write_completed_slot(root, manifest, first, _result(cast(str, first["case_id"])))
    slot_root = root / "slots" / cast(str, first["slot_id"])
    external_slot = tmp_path / "external-slot"
    slot_root.rename(external_slot)
    slot_root.symlink_to(external_slot, target_is_directory=True)

    with pytest.raises(batch.BatchError, match="cannot safely open"):
        batch._validate_completed_slot(root, manifest, first)
    with pytest.raises(batch.BatchError, match="cannot safely open"):
        batch._completed_smoke_prefix(root, manifest, batch._smoke_slots(manifest))


def test_completed_slot_rejects_result_leaf_symlink_before_recovery(
    tmp_path: Path,
) -> None:
    _private_root, manifest = _manifest_root(tmp_path)
    root = tmp_path / "private/progressive-validation-selection"
    first = batch._smoke_slots(manifest)[0]
    _write_completed_slot(root, manifest, first, _result(cast(str, first["case_id"])))
    result = root / "slots" / cast(str, first["slot_id"]) / "output/result.json"
    external_result = tmp_path / "external-result.json"
    result.rename(external_result)
    result.symlink_to(external_result)

    with pytest.raises(batch.BatchError, match="cannot safely read frozen slot result"):
        batch._validate_completed_slot(root, manifest, first)
    with pytest.raises(batch.BatchError, match="cannot safely read frozen slot result"):
        batch._completed_smoke_prefix(root, manifest, batch._smoke_slots(manifest))


def test_run_manifest_slot_fail_closes_invalid_boundaries(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    private_root, manifest = _manifest_root(tmp_path, "invalid-freeze")
    slot = cast(list[dict[str, object]], manifest["schedule"])[0]
    monkeypatch.setattr(batch, "verify_freeze", _invalid_freeze)
    with pytest.raises(batch.BatchError, match="freeze verification failed"):
        batch.run_manifest_slot(
            private_root, tmp_path / "auth.json", cast(str, slot["slot_id"])
        )

    private_root, manifest = _manifest_root(tmp_path, "invalid-slot")
    slot = cast(list[dict[str, object]], manifest["schedule"])[0]
    slot["case_id"] = ""
    _write_manifest(
        private_root / "progressive-validation-selection",
        manifest,
    )
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)
    with pytest.raises(batch.BatchError, match="frozen slot is invalid"):
        batch.run_manifest_slot(
            private_root, tmp_path / "auth.json", cast(str, slot["slot_id"])
        )

    private_root, manifest = _manifest_root(tmp_path, "invalid-arm")
    slot = cast(list[dict[str, object]], manifest["schedule"])[0]
    manifest["arm_map"] = {}
    _write_manifest(
        private_root / "progressive-validation-selection",
        manifest,
    )
    with pytest.raises(batch.BatchError, match="frozen arm map is invalid"):
        batch.run_manifest_slot(
            private_root, tmp_path / "auth.json", cast(str, slot["slot_id"])
        )

    private_root, manifest = _manifest_root(tmp_path, "invalid-execution-fields")
    slot = cast(list[dict[str, object]], manifest["schedule"])[0]
    arm_map = cast(dict[str, dict[str, object]], manifest["arm_map"])
    arm_map[cast(str, slot["arm_key"])]["archive"] = None
    _write_manifest(
        private_root / "progressive-validation-selection",
        manifest,
    )
    with pytest.raises(batch.BatchError, match="execution fields are invalid"):
        batch.run_manifest_slot(
            private_root, tmp_path / "auth.json", cast(str, slot["slot_id"])
        )


def test_run_manifest_slot_records_missing_and_unexpected_execution_failures(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)

    missing_private, missing_manifest = _manifest_root(tmp_path, "missing-result")
    missing_slot = cast(list[dict[str, object]], missing_manifest["schedule"])[0]

    def return_without_persisting(
        _archive: Path,
        _source: Path,
        _case: Path,
        _workspace: Path,
        _auth: Path,
        _output: Path,
        _model: str,
        _effort: str,
    ) -> dict[str, object]:
        return _result(cast(str, missing_slot["case_id"]))

    monkeypatch.setattr(batch, "run_archived_slot", return_without_persisting)
    with pytest.raises(batch.BatchError, match="result is missing or unsafe"):
        batch.run_manifest_slot(
            missing_private, tmp_path / "auth.json", cast(str, missing_slot["slot_id"])
        )
    missing_failure = json.loads(
        (
            missing_private
            / "progressive-validation-selection/slots"
            / cast(str, missing_slot["slot_id"])
            / "failed.json"
        ).read_text(encoding="utf-8")
    )
    assert missing_failure["error_type"] == "BatchError"

    error_private, error_manifest = _manifest_root(tmp_path, "unexpected-error")
    error_slot = cast(list[dict[str, object]], error_manifest["schedule"])[0]

    def fail_run(*_args: object) -> dict[str, object]:
        raise OSError("executor unavailable")

    monkeypatch.setattr(batch, "run_archived_slot", fail_run)
    with pytest.raises(batch.BatchError, match="frozen slot execution failed") as error:
        batch.run_manifest_slot(
            error_private, tmp_path / "auth.json", cast(str, error_slot["slot_id"])
        )
    assert isinstance(error.value.__cause__, OSError)


def test_run_manifest_slot_rejects_changed_result_between_run_and_readback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    private_root, manifest = _manifest_root(tmp_path)
    slot = cast(list[dict[str, object]], manifest["schedule"])[0]
    result = _result(cast(str, slot["case_id"]))
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)

    def write_different_result(*args: object) -> dict[str, object]:
        output_dir = cast(Path, args[5])
        output_dir.mkdir(parents=True)
        persisted = {**result, "model": "changed-after-run"}
        (output_dir / "result.json").write_text(json.dumps(persisted), encoding="utf-8")
        return result

    monkeypatch.setattr(batch, "run_archived_slot", write_different_result)
    with pytest.raises(batch.BatchError, match="result readback mismatch"):
        batch.run_manifest_slot(
            private_root, tmp_path / "auth.json", cast(str, slot["slot_id"])
        )


def test_run_smoke_requires_freeze_then_invokes_each_frozen_slot(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    private_root, manifest = _manifest_root(tmp_path)
    monkeypatch.setattr(batch, "verify_freeze", _invalid_freeze)
    with pytest.raises(batch.BatchError, match="freeze verification failed"):
        batch.run_smoke(private_root, tmp_path / "auth.json")

    calls: list[str] = []

    def run_one(_root: Path, auth_file: Path, slot_id: str) -> dict[str, object]:
        assert auth_file == tmp_path / "auth.json"
        calls.append(slot_id)
        return {"slot_id": slot_id}

    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)
    monkeypatch.setattr(batch, "run_manifest_slot", run_one)
    completed = batch.run_smoke(private_root, tmp_path / "auth.json")
    expected = [
        cast(str, slot["slot_id"])
        for slot in cast(list[dict[str, object]], manifest["schedule"])
        if slot["phase"] == "smoke"
    ]
    assert calls == expected
    assert completed == [{"slot_id": slot_id} for slot_id in expected]


def test_run_smoke_requires_verified_live_canary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    private_root, _manifest = _manifest_root(tmp_path)
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)

    def missing_canary(_root: Path) -> None:
        raise batch.BatchError("live canary is not completed")

    monkeypatch.setattr(batch, "_require_verified_canary", missing_canary)
    with pytest.raises(batch.BatchError, match="live canary is not completed"):
        batch.run_smoke(private_root, tmp_path / "auth.json")


def test_run_smoke_resumes_only_after_a_validated_completed_prefix(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    private_root, manifest = _manifest_root(tmp_path)
    root = private_root / "progressive-validation-selection"
    smoke = batch._smoke_slots(manifest)
    first = smoke[0]
    _write_completed_slot(root, manifest, first, _result(cast(str, first["case_id"])))
    calls: list[str] = []

    def run_one(_root: Path, _auth: Path, slot_id: str) -> dict[str, object]:
        calls.append(slot_id)
        return {"slot_id": slot_id}

    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)
    monkeypatch.setattr(batch, "run_manifest_slot", run_one)
    completed = batch.run_smoke(private_root, tmp_path / "auth.json")

    assert calls == [cast(str, slot["slot_id"]) for slot in smoke[1:]]
    assert completed[0]["slot_id"] == first["slot_id"]
    assert completed[1:] == [{"slot_id": slot_id} for slot_id in calls]


@pytest.mark.parametrize("ledger_name", ["started.json", "failed.json"])
def test_run_smoke_refuses_interrupted_or_failed_slot_recovery(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, ledger_name: str
) -> None:
    private_root, manifest = _manifest_root(tmp_path)
    root = private_root / "progressive-validation-selection"
    first = batch._smoke_slots(manifest)[0]
    slot_root = root / "slots" / cast(str, first["slot_id"])
    slot_root.mkdir(parents=True)
    (slot_root / ledger_name).write_text("{}", encoding="utf-8")
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)

    with pytest.raises(batch.BatchError, match="not safely resumable"):
        batch.run_smoke(private_root, tmp_path / "auth.json")


def test_run_smoke_refuses_noncontiguous_or_tampered_completed_ledgers(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    private_root, manifest = _manifest_root(tmp_path)
    root = private_root / "progressive-validation-selection"
    smoke = batch._smoke_slots(manifest)
    _write_completed_slot(
        root, manifest, smoke[1], _result(cast(str, smoke[1]["case_id"]))
    )
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)
    with pytest.raises(batch.BatchError, match="contiguous completed prefix"):
        batch.run_smoke(private_root, tmp_path / "auth.json")

    private_root, manifest = _manifest_root(tmp_path, "tampered")
    root = private_root / "progressive-validation-selection"
    first = batch._smoke_slots(manifest)[0]
    _write_completed_slot(root, manifest, first, _result(cast(str, first["case_id"])))
    completed_path = root / "slots" / cast(str, first["slot_id"]) / "completed.json"
    completed = json.loads(completed_path.read_text(encoding="utf-8"))
    completed["classification"] = "tampered"
    completed_path.write_text(json.dumps(completed), encoding="utf-8")
    with pytest.raises(batch.BatchError, match="completion ledger mismatch"):
        batch.run_smoke(private_root, tmp_path / "auth.json")


def test_smoke_status_rejects_invalid_freeze_and_ledger_entries(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    private_root, _manifest = _manifest_root(tmp_path, "bad-freeze")
    monkeypatch.setattr(batch, "verify_freeze", _invalid_freeze)
    with pytest.raises(batch.BatchError, match="freeze verification failed"):
        batch.smoke_status(private_root)

    private_root, _manifest = _manifest_root(tmp_path, "unsafe-ledger")
    slots = private_root / "progressive-validation-selection/slots"
    slots.mkdir()
    (slots / "not-a-slot-directory").write_text("unsafe", encoding="utf-8")
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)
    with pytest.raises(batch.BatchError, match="cannot safely open"):
        batch.smoke_status(private_root)


@pytest.mark.parametrize(
    "ledger_name", ["started.json", "completed.json", "failed.json"]
)
def test_smoke_status_rejects_ledger_leaf_symlinks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, ledger_name: str
) -> None:
    private_root, manifest = _manifest_root(tmp_path)
    root = private_root / "progressive-validation-selection"
    first = batch._smoke_slots(manifest)[0]
    slot_root = root / "slots" / cast(str, first["slot_id"])
    slot_root.mkdir(parents=True)
    external = tmp_path / f"external-{ledger_name}"
    external.write_text("{}", encoding="utf-8")
    (slot_root / ledger_name).symlink_to(external)
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)

    with pytest.raises(batch.BatchError, match="cannot safely read frozen slot ledger"):
        batch.smoke_status(private_root)


@pytest.mark.parametrize("target", ["slots", "slot"])
def test_smoke_status_rejects_slots_and_slot_parent_symlinks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, target: str
) -> None:
    private_root, manifest = _manifest_root(tmp_path)
    root = private_root / "progressive-validation-selection"
    external = tmp_path / f"external-{target}"
    external.mkdir()
    if target == "slots":
        (root / "slots").symlink_to(external, target_is_directory=True)
    else:
        slots = root / "slots"
        slots.mkdir()
        (slots / cast(str, batch._smoke_slots(manifest)[0]["slot_id"])).symlink_to(
            external, target_is_directory=True
        )
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)

    with pytest.raises(batch.BatchError, match="cannot safely open"):
        batch.smoke_status(private_root)


def test_smoke_status_rejects_malformed_failure_ledger(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    private_root, manifest = _manifest_root(tmp_path)
    root = private_root / "progressive-validation-selection"
    first = batch._smoke_slots(manifest)[0]
    slot_root = root / "slots" / cast(str, first["slot_id"])
    slot_root.mkdir(parents=True)
    (slot_root / "failed.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)

    with pytest.raises(batch.BatchError, match="failure ledger mismatch"):
        batch.smoke_status(private_root)
