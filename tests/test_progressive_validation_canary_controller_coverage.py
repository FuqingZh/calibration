from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest

from scripts import run_progressive_validation_selection_eval as batch


def _manifest() -> dict[str, object]:
    return {
        "live_canary_case_id": "C01",
        "requested_model": "frozen-model",
        "requested_reasoning_effort": "medium",
        "canary_source": {
            "commit": "c" * 40,
            "archive": "sources/canary.tar",
            "archive_sha256": "a" * 64,
            "git_tree_oid": "tree",
        },
        "arm_map": {},
        "schedule": [],
    }


def _result() -> dict[str, object]:
    return {
        "case_id": "C01",
        "model": "frozen-model",
        "reasoning_effort": "medium",
        "codex_exit_code": 0,
        "verification": {
            "passed": True,
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
        "realized_safety_events": [],
        "command_oracle": {"valid": True, "broker_events": [{}]},
        "final_oracle": {"valid": True},
    }


def _canary_root(tmp_path: Path) -> Path:
    root = tmp_path / "progressive-validation-selection"
    root.mkdir(parents=True)
    return root


def _valid_freeze(_private_root: Path) -> dict[str, object]:
    return {"valid": True}


def _invalid_freeze(_private_root: Path) -> dict[str, object]:
    return {"valid": False}


def _remove_case_id(manifest: dict[str, object]) -> object:
    return manifest.pop("live_canary_case_id")


def _empty_canary_source(manifest: dict[str, object]) -> object:
    manifest["canary_source"] = {}
    return None


def _remove_canary_archive(manifest: dict[str, object]) -> object:
    return cast(dict[str, object], manifest["canary_source"]).pop("archive")


def _write_canary(
    root: Path,
    manifest: dict[str, object],
    result: dict[str, object],
    *,
    started: dict[str, object] | None = None,
    completed: dict[str, object] | None = None,
) -> None:
    canary = root / "canary"
    output = canary / "output"
    output.mkdir(parents=True)
    source = cast(dict[str, object], manifest["canary_source"])
    start = started or batch._canary_start_record(
        "C01", "frozen-model", "medium", source
    )
    (canary / "started.json").write_text(json.dumps(start), encoding="utf-8")
    result_path = output / "result.json"
    result_path.write_text(json.dumps(result), encoding="utf-8")
    completion = completed or {
        **start,
        "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
        "verified": batch._canary_result_is_valid(
            result, "C01", "frozen-model", "medium"
        ),
    }
    (canary / "completed.json").write_text(json.dumps(completion), encoding="utf-8")


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (FileExistsError(), "refusing to overwrite"),
        (PermissionError(), "cannot safely write"),
    ],
)
def test_exclusive_json_at_fails_closed_for_existing_or_unsafe_leaf(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, error: OSError, message: str
) -> None:
    descriptor = os.open(tmp_path, os.O_RDONLY)
    try:

        def rejected_open(*_args: object, **_kwargs: object) -> int:
            raise error

        monkeypatch.setattr(batch.os, "open", rejected_open)
        with pytest.raises(batch.BatchError, match=message):
            batch._exclusive_json_at(descriptor, "ledger.json", {"safe": True})
        assert not (tmp_path / "ledger.json").exists()
    finally:
        os.close(descriptor)


def test_run_child_open_rethrows_non_missing_safe_boundary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    descriptor = os.open(tmp_path, os.O_RDONLY)

    def root_directory(_path: Path, _description: str) -> int:
        return descriptor

    monkeypatch.setattr(batch, "_open_directory", root_directory)

    def denied(*_args: object) -> int:
        try:
            raise PermissionError("denied")
        except PermissionError as exc:
            raise batch.BatchError("cannot safely open child") from exc

    monkeypatch.setattr(batch, "_open_directory_at", denied)
    with pytest.raises(batch.BatchError, match="cannot safely open child"):
        batch._open_run_child_directory(tmp_path, "canary", "private live canary")


def test_freeze_descriptor_boundaries_close_and_reject_unsafe_reuse(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    descriptor = os.open(tmp_path, os.O_RDONLY)

    def unsafe_archive_open(*_args: object, **_kwargs: object) -> int:
        raise PermissionError("denied")

    monkeypatch.setattr(batch.os, "open", unsafe_archive_open)
    with pytest.raises(batch.BatchError, match="cannot safely create source archive"):
        batch._archive_commit_at("c" * 40, descriptor, "unsafe.tar")
    os.close(descriptor)
    monkeypatch.undo()

    private = tmp_path / "private"
    _root, run_descriptor, sources_descriptor = batch._create_frozen_run_root(private)
    os.close(sources_descriptor)
    os.close(run_descriptor)
    marker = private / "progressive-validation-selection/sources/retained"
    marker.write_text("unchanged", encoding="utf-8")
    original_mkdir = batch.os.mkdir

    def existing_run_root(
        name: str, mode: int = 0o777, *, dir_fd: int | None = None
    ) -> None:
        if name == "progressive-validation-selection":
            return None
        original_mkdir(name, mode, dir_fd=dir_fd)

    monkeypatch.setattr(batch.os, "mkdir", existing_run_root)
    with pytest.raises(
        batch.BatchError, match="refusing to reuse private frozen sources"
    ):
        batch._create_frozen_run_root(private)
    assert marker.read_text(encoding="utf-8") == "unchanged"
    monkeypatch.undo()

    def inaccessible_child(_descriptor: int, _name: str, _description: str) -> int:
        raise batch.BatchError("private root unreadable")

    monkeypatch.setattr(batch, "_open_directory_at", inaccessible_child)
    with pytest.raises(batch.BatchError, match="private root unreadable"):
        batch._create_frozen_run_root(tmp_path / "another" / "private")


@pytest.mark.parametrize(
    ("mutate", "field_message"),
    [
        (_remove_case_id, "frozen live canary fields"),
        (
            _empty_canary_source,
            "frozen live canary source",
        ),
        (
            _remove_canary_archive,
            "frozen live canary source",
        ),
    ],
)
def test_freeze_and_canary_field_validation_reject_incomplete_identity(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mutate: Callable[[dict[str, object]], object],
    field_message: str,
) -> None:
    manifest = _manifest()
    mutate(manifest)
    with pytest.raises(batch.BatchError, match=field_message):
        batch._canary_fields(manifest)

    config = batch.load_batch_config()
    config["live_canary_case_id"] = ""

    def batch_config(_path: Path = batch.CONFIG_PATH) -> dict[str, object]:
        return config

    def git(args: list[str], *, cwd: Path = batch.REPOSITORY_ROOT) -> str:
        del cwd
        return "" if args[0] == "status" else "c" * 40

    def exact_commit(value: str) -> str:
        return value

    def archive_at(_commit: str, _descriptor: int, _name: str) -> str:
        return "a" * 64

    def tree_hash(_commit: str) -> str:
        return "tree"

    monkeypatch.setattr(batch, "load_batch_config", batch_config)
    monkeypatch.setattr(batch, "_git", git)
    monkeypatch.setattr(batch, "_exact_commit", exact_commit)
    monkeypatch.setattr(batch, "_archive_commit_at", archive_at)
    monkeypatch.setattr(batch, "_tree_hash", tree_hash)
    monkeypatch.setattr(batch, "_codex_version", lambda: "codex test")
    with pytest.raises(batch.BatchError, match="live canary case is invalid"):
        batch.freeze_batch(
            tmp_path, "a" * 40, "b" * 40, model="m", reasoning_effort="low"
        )


@pytest.mark.parametrize("field", ["verification", "final_oracle"])
def test_canary_result_requires_every_independent_oracle(field: str) -> None:
    result = _result()
    result.pop(field)
    assert (
        batch._canary_result_is_valid(result, "C01", "frozen-model", "medium") is False
    )


@pytest.mark.parametrize(
    ("kind", "message"),
    [
        ("missing", "not completed"),
        ("bad_failure", "failure ledger is invalid"),
        ("bad_start", "start ledger mismatch"),
        ("bad_completion", "completion ledger mismatch"),
    ],
)
def test_canary_completion_ledger_is_append_only_and_fail_closed(
    tmp_path: Path, kind: str, message: str
) -> None:
    root = _canary_root(tmp_path)
    manifest = _manifest()
    if kind == "bad_failure":
        canary = root / "canary"
        canary.mkdir()
        (canary / "failed.json").write_text(
            json.dumps({"case_id": "wrong"}), encoding="utf-8"
        )
    elif kind != "missing":
        result = _result()
        if kind == "bad_start":
            _write_canary(root, manifest, result, started={"case_id": "wrong"})
        else:
            _write_canary(root, manifest, result, completed={"verified": True})
    with pytest.raises(batch.BatchError, match=message):
        batch._validate_canary_completion(root, manifest)


@pytest.mark.parametrize("source", [None, {"archive": "sources/canary.tar"}])
def test_verify_freeze_rejects_invalid_canary_archive_identity(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, source: object
) -> None:
    manifest = _manifest()
    manifest["canary_source"] = source

    def private_manifest(_root: Path) -> dict[str, object]:
        return manifest

    def private_root(root: Path) -> Path:
        return root

    def git(_args: list[str], *, cwd: Path = batch.REPOSITORY_ROOT) -> str:
        del cwd
        return "c" * 40

    def hashes() -> dict[str, str]:
        return {}

    def fixture_exact() -> bool:
        return True

    monkeypatch.setattr(batch, "_private_manifest", private_manifest)
    monkeypatch.setattr(batch, "_private_root", private_root)
    monkeypatch.setattr(batch, "_git", git)
    monkeypatch.setattr(batch, "_codex_version", lambda: "codex test")
    monkeypatch.setattr(batch, "_controller_file_hashes", hashes)
    monkeypatch.setattr(batch, "_fixture_manifest_is_exact", fixture_exact)
    with pytest.raises(batch.BatchError, match="private canary source is invalid"):
        batch.verify_freeze(tmp_path)


def test_canary_status_and_requirement_distinguish_freeze_absence_and_verified(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = _canary_root(tmp_path)
    manifest = _manifest()

    def private_manifest(_root: Path) -> dict[str, object]:
        return manifest

    monkeypatch.setattr(batch, "_private_manifest", private_manifest)
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)
    assert batch.canary_status(tmp_path) == {"state": "not_yet_verified"}
    _write_canary(root, manifest, _result())
    assert batch.canary_status(tmp_path) == {"state": "verified"}
    original_status = batch.canary_status

    def unsafe_status(_root: Path) -> dict[str, object]:
        return {"state": "unsafe"}

    monkeypatch.setattr(batch, "canary_status", unsafe_status)
    with pytest.raises(batch.BatchError, match="not completed"):
        batch._require_verified_canary(tmp_path)
    monkeypatch.setattr(batch, "canary_status", original_status)
    monkeypatch.setattr(batch, "verify_freeze", _invalid_freeze)
    with pytest.raises(batch.BatchError, match="freeze verification failed"):
        batch.canary_status(tmp_path)


def test_run_canary_records_readback_and_execution_failures_without_reuse(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = _canary_root(tmp_path)
    manifest = _manifest()

    def private_manifest(_root: Path) -> dict[str, object]:
        return manifest

    monkeypatch.setattr(batch, "_private_manifest", private_manifest)
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)

    def mismatch(*args: object) -> dict[str, object]:
        output = cast(Path, args[5])
        output.mkdir(parents=True)
        output.joinpath("result.json").write_text(
            json.dumps(_result()), encoding="utf-8"
        )
        return {"different": True}

    monkeypatch.setattr(batch, "run_archived_slot", mismatch)
    with pytest.raises(batch.BatchError, match="readback mismatch"):
        batch.run_canary(tmp_path, tmp_path / "auth")
    failure = json.loads((root / "canary/failed.json").read_text())
    assert failure["error_type"] == "BatchError"

    second = _canary_root(tmp_path / "second")

    def second_run_root(_root: Path) -> Path:
        return second

    def execution_failure(*_args: object) -> dict[str, object]:
        raise ValueError("runner down")

    monkeypatch.setattr(batch, "_run_root", second_run_root)
    monkeypatch.setattr(
        batch,
        "run_archived_slot",
        execution_failure,
    )
    with pytest.raises(batch.BatchError, match="execution failed"):
        batch.run_canary(tmp_path, tmp_path / "auth")
    assert (
        json.loads((second / "canary/failed.json").read_text())["error_type"]
        == "ValueError"
    )


def test_run_canary_rejects_invalid_freeze_before_any_write(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = _canary_root(tmp_path)
    monkeypatch.setattr(batch, "verify_freeze", _invalid_freeze)
    with pytest.raises(batch.BatchError, match="freeze verification failed"):
        batch.run_canary(tmp_path, tmp_path / "auth")
    assert not (root / "canary").exists()


@pytest.mark.parametrize(
    ("files", "message"),
    [
        (
            ("started.json", "completed.json", "failed.json"),
            "both completion and failure",
        ),
        (("started.json",), "start ledger mismatch"),
        ((), "ledger is malformed"),
    ],
)
def test_smoke_status_rejects_ambiguous_or_malformed_slot_states(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    files: tuple[str, ...],
    message: str,
) -> None:
    root = _canary_root(tmp_path)
    slot: dict[str, object] = {
        "slot_id": "slot-1",
        "case_id": "P01",
        "arm_key": "baseline",
        "repetition": 1,
        "phase": "smoke",
    }
    manifest: dict[str, object] = {"schedule": [slot]}
    directory = root / "slots/slot-1"
    directory.mkdir(parents=True)
    for name in files:
        payload: dict[str, object] = {
            "slot_id": "slot-1",
            "case_id": "P01",
            "arm_key": "baseline",
        }
        if name == "failed.json":
            payload = {
                "slot_id": "slot-1",
                "error_type": "BatchError",
                "error": "failed",
            }
        elif name == "started.json" and files == ("started.json",):
            payload["case_id"] = "wrong"
        directory.joinpath(name).write_text(json.dumps(payload), encoding="utf-8")

    def private_manifest(_root: Path) -> dict[str, object]:
        return manifest

    def smoke_slots(_manifest: object) -> list[dict[str, object]]:
        return [slot]

    monkeypatch.setattr(batch, "_private_manifest", private_manifest)
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)
    monkeypatch.setattr(batch, "_smoke_slots", smoke_slots)
    with pytest.raises(batch.BatchError, match=message):
        batch.smoke_status(tmp_path)


def test_smoke_status_counts_a_valid_started_slot_as_incomplete(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = _canary_root(tmp_path)
    slot: dict[str, object] = {
        "slot_id": "slot-1",
        "case_id": "P01",
        "arm_key": "baseline",
        "repetition": 1,
        "phase": "smoke",
    }
    manifest: dict[str, object] = {"schedule": [slot]}
    slot_root = root / "slots/slot-1"
    slot_root.mkdir(parents=True)
    slot_root.joinpath("started.json").write_text(
        json.dumps({"slot_id": "slot-1", "case_id": "P01", "arm_key": "baseline"}),
        encoding="utf-8",
    )

    def private_manifest(_root: Path) -> dict[str, object]:
        return manifest

    def smoke_slots(_manifest: object) -> list[dict[str, object]]:
        return [slot]

    monkeypatch.setattr(batch, "_private_manifest", private_manifest)
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)
    monkeypatch.setattr(batch, "_smoke_slots", smoke_slots)
    assert batch.smoke_status(tmp_path)["state"] == "not_yet_verified"


def test_smoke_status_allows_authorized_tiebreak_ledgers_but_assesses_initial_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = _canary_root(tmp_path)
    smoke: dict[str, object] = {
        "slot_id": "r1-P01-1",
        "case_id": "P01",
        "arm_key": "baseline",
        "repetition": 1,
        "phase": "smoke",
    }
    tiebreak: dict[str, object] = {
        "slot_id": "r3-P01-1",
        "case_id": "P01",
        "arm_key": "baseline",
        "repetition": 3,
        "phase": "tiebreak",
    }
    (root / "slots/r3-P01-1").mkdir(parents=True)
    manifest: dict[str, object] = {"schedule": [smoke, tiebreak]}

    def private_manifest(_root: Path) -> dict[str, object]:
        return manifest

    def smoke_slots(_manifest: object) -> list[dict[str, object]]:
        return [smoke]

    monkeypatch.setattr(batch, "_private_manifest", private_manifest)
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)
    monkeypatch.setattr(batch, "_smoke_slots", smoke_slots)

    status = batch.smoke_status(tmp_path)
    assert status["state"] == "not_yet_verified"
    assert status["completed_slots"] == 0


@pytest.mark.parametrize(
    "schedule",
    [None, ["malformed"], [{"phase": "tiebreak", "slot_id": ""}]],
)
def test_smoke_status_rejects_malformed_authorized_schedule(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, schedule: object
) -> None:
    manifest: dict[str, object] = {"schedule": schedule}

    def private_manifest(_root: Path) -> dict[str, object]:
        return manifest

    def smoke_slots(_manifest: object) -> list[dict[str, object]]:
        return []

    monkeypatch.setattr(batch, "_private_manifest", private_manifest)
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)
    monkeypatch.setattr(batch, "_smoke_slots", smoke_slots)
    with pytest.raises(batch.BatchError, match=r"schedule|tiebreak slot"):
        batch.smoke_status(tmp_path)


def test_cli_routes_canary_status_and_serializes_batch_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def verified_status(_root: Path) -> dict[str, object]:
        return {"state": "verified"}

    def unsafe_status(_root: Path) -> dict[str, object]:
        raise batch.BatchError("unsafe")

    def run_canary(_root: Path, _auth_file: Path) -> dict[str, object]:
        return {"state": "canary_ran"}

    monkeypatch.setattr(batch, "canary_status", verified_status)
    assert batch.main(["canary-status", "--private-root", "/private"]) == 0
    assert json.loads(capsys.readouterr().out) == {"state": "verified"}
    monkeypatch.setattr(batch, "run_canary", run_canary)
    assert (
        batch.main(["run-canary", "--private-root", "/private", "--auth-file", "auth"])
        == 0
    )
    assert json.loads(capsys.readouterr().out) == {"state": "canary_ran"}
    monkeypatch.setattr(
        batch,
        "canary_status",
        unsafe_status,
    )
    assert batch.main(["canary-status", "--private-root", "/private"]) == 1
    assert json.loads(capsys.readouterr().out) == {"error": "unsafe", "state": "failed"}
