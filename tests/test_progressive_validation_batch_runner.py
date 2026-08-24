from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import cast

import pytest

from scripts import run_progressive_validation_selection_eval as batch


@pytest.fixture(autouse=True)
def _permit_canary_for_slot_contract_tests(  # pyright: ignore[reportUnusedFunction]
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise slot invariants independently of the separately tested canary gate."""

    def permit(_root: Path) -> None:
        return None

    monkeypatch.setattr(batch, "_require_verified_canary", permit)


def _private_manifest(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    root = tmp_path / "progressive-validation-selection"
    root.mkdir(parents=True)
    manifest: dict[str, object] = {
        "requested_model": "frozen-model",
        "requested_reasoning_effort": "medium",
        "arm_map": {
            "baseline": {"archive": "sources/baseline.tar"},
            "candidate": {"archive": "sources/candidate.tar"},
        },
        "live_canary_case_id": "C01",
        "canary_source": {
            "commit": "c" * 40,
            "archive": "sources/canary.tar",
            "archive_sha256": "d" * 64,
            "git_tree_oid": "tree",
        },
        "schedule": batch._schedule(batch.load_batch_config()),
    }
    canonical = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    (root / "manifest.json").write_text(canonical, encoding="utf-8")
    (root / "manifest.sha256").write_text(
        json.dumps(
            {"sha256": hashlib.sha256(canonical.encode()).hexdigest()},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return root, manifest


def _result(
    case_id: str,
    *,
    model: str = "frozen-model",
    effort: str = "medium",
    oracle_errors: list[str] | None = None,
    codex_exit_code: int = 0,
    final_valid: bool = True,
) -> dict[str, object]:
    errors = oracle_errors or []
    oracle_valid = not errors
    return {
        "case_id": case_id,
        "model": model,
        "reasoning_effort": effort,
        "codex_exit_code": codex_exit_code,
        "elapsed_seconds": 1.0,
        "verification": {
            "passed": codex_exit_code == 0 and oracle_valid and final_valid,
            "checks": [{"exit_code": 0}],
            "unexpected_changes": [],
            "missing_required_changes": [],
        },
        "command_oracle": {"valid": oracle_valid, "errors": errors},
        "final_oracle": {"valid": final_valid},
    }


def _valid_freeze(_private_root: Path) -> dict[str, object]:
    return {"valid": True}


def test_config_is_strict_and_schedule_counterbalances_all_slots() -> None:
    config = batch.load_batch_config()
    schedule = batch._schedule(config)
    assert len(schedule) == 14 * 2 * 3
    assert sum(slot["phase"] == "smoke" for slot in schedule) == 14 * 2
    assert schedule == batch._schedule(config)
    for repetition in range(1, 4):
        first_arms = [
            slot["arm_key"]
            for slot in schedule
            if slot["repetition"] == repetition
            and cast(str, slot["slot_id"]).endswith("-1")
        ]
        assert first_arms.count("baseline") == 7
        assert first_arms.count("candidate") == 7
    for case_id in cast(list[str], config["case_ids"]):
        for repetition in range(1, 4):
            pair = [
                slot
                for slot in schedule
                if slot["case_id"] == case_id and slot["repetition"] == repetition
            ]
            assert [slot["arm_key"] for slot in pair] in (
                ["baseline", "candidate"],
                ["candidate", "baseline"],
            )
        first_count = sum(
            slot["arm_key"] == "baseline"
            for slot in schedule
            if slot["case_id"] == case_id and cast(str, slot["slot_id"]).endswith("-1")
        )
        assert first_count in {1, 2}


def test_unpack_real_git_archive_with_directories(tmp_path: Path) -> None:
    archive = tmp_path / "source.tar"
    with archive.open("wb") as output:
        result = subprocess.run(
            ["git", "archive", "--format=tar", "HEAD"],
            cwd=batch.REPOSITORY_ROOT,
            stdout=output,
            check=False,
        )
    assert result.returncode == 0
    source = tmp_path / "source"
    batch.unpack_source_archive(archive, source)
    assert (source / "README.md").is_file()


def test_freeze_requires_clean_exact_commits_and_archives(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    commit_a = "a" * 40
    commit_b = "b" * 40

    def fake_git(args: list[str], *, cwd: Path = batch.REPOSITORY_ROOT) -> str:
        if args == ["status", "--porcelain"]:
            return ""
        assert args[:2] == ["rev-parse", "--verify"]
        if args[2] == "HEAD^{commit}":
            return "c" * 40
        return args[2].replace("^{commit}", "").replace("^{tree}", "tree")

    def fake_archive(commit: str, descriptor: int, _name: str) -> str:
        archive = os.open(
            _name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=descriptor
        )
        try:
            os.write(archive, commit.encode())
        finally:
            os.close(archive)
        return hashlib.sha256(commit.encode()).hexdigest()

    monkeypatch.setattr(batch, "_git", fake_git)
    monkeypatch.setattr(batch, "_archive_commit_at", fake_archive)
    monkeypatch.setattr(batch, "_codex_version", lambda: "codex 1.2.3")
    manifest = batch.freeze_batch(
        tmp_path, commit_a, commit_b, model="test-model", reasoning_effort="high"
    )
    assert manifest["status"] == "frozen"
    assert len(cast(list[object], manifest["schedule"])) == 84
    saved = json.loads(
        (tmp_path / "progressive-validation-selection/manifest.json").read_text()
    )
    assert saved["arm_map"]["baseline"]["commit"] == commit_a
    assert saved["requested_model"] == "test-model"
    assert saved["turn_budget"] == 1
    with pytest.raises(batch.BatchError, match="private frozen run root"):
        batch.freeze_batch(
            tmp_path, commit_a, commit_b, model="test-model", reasoning_effort="high"
        )


def test_freeze_rejects_dirty_non_commit_and_repository_private_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def dirty_git(args: list[str], *, cwd: Path = batch.REPOSITORY_ROOT) -> str:
        del args, cwd
        return " M file\n"

    monkeypatch.setattr(batch, "_git", dirty_git)
    with pytest.raises(batch.BatchError, match="dirty"):
        batch.freeze_batch(
            tmp_path, "a" * 40, "b" * 40, model="m", reasoning_effort="medium"
        )
    with pytest.raises(batch.BatchError, match="outside"):
        batch.freeze_batch(
            batch.REPOSITORY_ROOT / "private",
            "a" * 40,
            "b" * 40,
            model="m",
            reasoning_effort="medium",
        )
    with pytest.raises(batch.BatchError, match="absolute"):
        batch.freeze_batch(
            Path("private"), "a" * 40, "b" * 40, model="m", reasoning_effort="medium"
        )


def test_public_projection_hashes_raw_commands_and_removes_private_fields(
    tmp_path: Path,
) -> None:
    private = tmp_path / "private.json"
    public = tmp_path / "public.json"
    private.write_text(
        json.dumps(
            {
                "case_id": "P01",
                "model": "test-model",
                "reasoning_effort": "medium",
                "elapsed_seconds": 1.0,
                "codex_exit_code": 0,
                "arm": "candidate",
                "commit": "a" * 40,
                "codex_home": "/secret/home",
                "verification": {
                    "passed": True,
                    "changed_paths": ["README.md", "prefix:/srv/private"],
                    "unexpected_changes": [],
                    "missing_required_changes": [],
                    "checks": [
                        {"command": ["make", "secret"], "stdout": "/srv/private"}
                    ],
                },
                "command_oracle": {
                    "valid": True,
                    "observations": [
                        {
                            "raw_command": "make docs",
                            "argv": ["make", "docs"],
                            "family": "docs_check",
                            "exit_code": 0,
                        }
                    ],
                    "errors": ["prefix:/srv/private"],
                },
                "executor_log": "/private/output/trajectory.jsonl",
                "final_oracle": {"valid": True},
            }
        )
    )
    projection = batch.project_public(private, public)
    encoded = public.read_text().lower()
    assert projection["valid"] is True
    assert "raw_command" not in encoded and "candidate" not in encoded
    assert "make docs" not in encoded and "command_sha256" in encoded
    assert "/private/output" not in encoded
    with pytest.raises(batch.BatchError, match="overwrite"):
        batch.project_public(private, public)


def test_summary_never_offsets_critical_failure_with_efficiency(tmp_path: Path) -> None:
    valid = tmp_path / "valid.json"
    failed = tmp_path / "failed.json"
    valid.write_text('{"valid": true, "elapsed_seconds": 0.1}')
    failed.write_text('{"valid": false, "elapsed_seconds": 0.01}')
    summary = batch.summarize_public([valid, failed])
    assert summary["decision"] == "reject"
    assert batch.summarize_public([])["decision"] == "not_yet_verified"


def test_manifest_slot_derives_every_execution_field_and_is_exclusive(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root, manifest = _private_manifest(tmp_path)
    first = cast(list[dict[str, object]], manifest["schedule"])[0]
    slot_id = cast(str, first["slot_id"])
    captured: dict[str, object] = {}

    def verified(_private_root: Path) -> dict[str, object]:
        return {"valid": True}

    def fake_run(
        archive: Path,
        source_dir: Path,
        case_path: Path,
        workspace: Path,
        auth_file: Path,
        output_dir: Path,
        model: str,
        effort: str,
    ) -> dict[str, object]:
        captured.update(
            archive=archive,
            source_dir=source_dir,
            case_path=case_path,
            workspace=workspace,
            auth_file=auth_file,
            model=model,
            effort=effort,
        )
        output_dir.mkdir(parents=True)
        payload = _result(cast(str, first["case_id"]))
        (output_dir / "result.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return payload

    monkeypatch.setattr(batch, "verify_freeze", verified)
    monkeypatch.setattr(batch, "run_archived_slot", fake_run)
    completed = batch.run_manifest_slot(tmp_path, tmp_path / "auth.json", slot_id)
    arm = cast(str, first["arm_key"])
    assert captured["archive"] == root / f"sources/{arm}.tar"
    assert cast(Path, captured["case_path"]).name == f"{first['case_id']}.yaml"
    assert captured["model"] == "frozen-model"
    assert captured["effort"] == "medium"
    assert completed["classification"] == "valid"
    with pytest.raises(batch.BatchError, match="refusing to reuse"):
        batch.run_manifest_slot(tmp_path, tmp_path / "auth.json", slot_id)


def test_comparison_slot_requires_verified_live_canary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _root, manifest = _private_manifest(tmp_path)
    first = cast(list[dict[str, object]], manifest["schedule"])[0]
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)

    def missing_canary(_root: Path) -> None:
        raise batch.BatchError("live canary is not completed")

    monkeypatch.setattr(batch, "_require_verified_canary", missing_canary)
    with pytest.raises(batch.BatchError, match="live canary is not completed"):
        batch.run_manifest_slot(
            tmp_path, tmp_path / "auth.json", cast(str, first["slot_id"])
        )


def test_live_canary_is_independent_append_only_evidence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root, _manifest = _private_manifest(tmp_path)
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)

    def fake_canary_run(*args: object) -> dict[str, object]:
        assert cast(Path, args[2]).name == "C01.yaml"
        output = cast(Path, args[5])
        output.mkdir(parents=True)
        result: dict[str, object] = {
            "case_id": "C01",
            "model": "frozen-model",
            "reasoning_effort": "medium",
            "codex_exit_code": 0,
            "verification": {
                "passed": True,
                "unexpected_changes": [],
                "missing_required_changes": [],
            },
            "command_oracle": {
                "valid": True,
                "broker_events": [{"execution_id": 1}],
            },
            "final_oracle": {"valid": True},
        }
        (output / "result.json").write_text(json.dumps(result), encoding="utf-8")
        return result

    monkeypatch.setattr(batch, "run_archived_slot", fake_canary_run)
    assert batch.canary_status(tmp_path)["state"] == "not_yet_verified"
    completed = batch.run_canary(tmp_path, tmp_path / "auth.json")
    assert completed["verified"] is True
    assert batch.canary_status(tmp_path) == {"state": "verified"}
    assert not (root / "slots").exists()
    with pytest.raises(batch.BatchError, match="refusing to reuse private live canary"):
        batch.run_canary(tmp_path, tmp_path / "auth.json")


def test_live_canary_refuses_preexisting_symlink_without_external_write(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root, _manifest = _private_manifest(tmp_path)
    external = tmp_path / "external-canary"
    external.mkdir()
    (root / "canary").symlink_to(external, target_is_directory=True)
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)

    with pytest.raises(
        batch.BatchError, match="cannot safely open private live canary"
    ):
        batch.run_canary(tmp_path, tmp_path / "auth.json")
    assert list(external.iterdir()) == []


@pytest.mark.parametrize("record_name", ["started.json", "failed.json"])
def test_live_canary_started_or_failed_ledger_cannot_be_reused(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, record_name: str
) -> None:
    root, _manifest = _private_manifest(tmp_path)
    canary = root / "canary"
    canary.mkdir()
    record: dict[str, object] = (
        {
            "case_id": "C01",
            "requested_model": "frozen-model",
            "requested_reasoning_effort": "medium",
            "canary_source_sha256": "d" * 64,
        }
        if record_name == "started.json"
        else {
            "case_id": "C01",
            "error_type": "BatchError",
            "error": "boundary preflight failed",
        }
    )
    (canary / record_name).write_text(json.dumps(record), encoding="utf-8")
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)

    expected = "not completed" if record_name == "started.json" else "is invalid"
    with pytest.raises(batch.BatchError, match=expected):
        batch.canary_status(tmp_path)
    with pytest.raises(batch.BatchError, match="refusing to reuse private live canary"):
        batch.run_canary(tmp_path, tmp_path / "auth.json")


def test_invalid_live_canary_is_retained_and_blocks_reuse(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _root, _manifest = _private_manifest(tmp_path)
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)

    def invalid_canary_run(*args: object) -> dict[str, object]:
        output = cast(Path, args[5])
        output.mkdir(parents=True)
        result: dict[str, object] = {
            "case_id": "C01",
            "model": "frozen-model",
            "reasoning_effort": "medium",
            "codex_exit_code": 0,
            "verification": {
                "passed": True,
                "unexpected_changes": [],
                "missing_required_changes": [],
            },
            "command_oracle": {"valid": True, "broker_events": []},
            "final_oracle": {"valid": True},
        }
        (output / "result.json").write_text(json.dumps(result), encoding="utf-8")
        return result

    monkeypatch.setattr(batch, "run_archived_slot", invalid_canary_run)
    with pytest.raises(batch.BatchError, match="live canary is invalid"):
        batch.run_canary(tmp_path, tmp_path / "auth.json")
    with pytest.raises(batch.BatchError, match="live canary is invalid"):
        batch.canary_status(tmp_path)
    with pytest.raises(batch.BatchError, match="refusing to reuse private live canary"):
        batch.run_canary(tmp_path, tmp_path / "auth.json")


def test_manifest_slot_requires_frozen_order_and_records_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root, manifest = _private_manifest(tmp_path)
    smoke = [
        slot
        for slot in cast(list[dict[str, object]], manifest["schedule"])
        if slot["repetition"] == 1
    ]
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)
    with pytest.raises(batch.BatchError, match="incomplete"):
        batch.run_manifest_slot(
            tmp_path, tmp_path / "auth.json", cast(str, smoke[1]["slot_id"])
        )

    def fail_run(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise batch.BatchError("synthetic boundary failure")

    monkeypatch.setattr(batch, "run_archived_slot", fail_run)
    first_id = cast(str, smoke[0]["slot_id"])
    with pytest.raises(batch.BatchError, match="synthetic boundary"):
        batch.run_manifest_slot(tmp_path, tmp_path / "auth.json", first_id)
    failure = json.loads((root / "slots" / first_id / "failed.json").read_text())
    assert failure["error_type"] == "BatchError"
    with pytest.raises(batch.BatchError, match="refusing to reuse"):
        batch.run_manifest_slot(tmp_path, tmp_path / "auth.json", first_id)


def test_manifest_slot_refuses_symlinked_slots_root_without_external_write(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root, manifest = _private_manifest(tmp_path)
    first = cast(list[dict[str, object]], manifest["schedule"])[0]
    external = tmp_path / "external-slots"
    external.mkdir()
    (root / "slots").symlink_to(external, target_is_directory=True)
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)

    def must_not_run(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise AssertionError("unsafe slots root reached the runner")

    monkeypatch.setattr(batch, "run_archived_slot", must_not_run)
    with pytest.raises(
        batch.BatchError, match="cannot safely open private slot ledger"
    ):
        batch.run_manifest_slot(
            tmp_path, tmp_path / "auth.json", cast(str, first["slot_id"])
        )
    assert list(external.iterdir()) == []


def test_runner_preflight_failure_is_recorded_as_invalid_and_cannot_reuse_slot(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The controller trusts the runner exception, never model stderr text."""
    root, manifest = _private_manifest(tmp_path)
    first = cast(list[dict[str, object]], manifest["schedule"])[0]
    slot_id = cast(str, first["slot_id"])
    runner_invoked = False

    def preflight_failure(*_args: object, **_kwargs: object) -> dict[str, object]:
        nonlocal runner_invoked
        runner_invoked = True
        raise batch.BatchError("runner execution boundary preflight failed")

    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)
    monkeypatch.setattr(batch, "run_archived_slot", preflight_failure)
    with pytest.raises(batch.BatchError, match="boundary preflight failed"):
        batch.run_manifest_slot(tmp_path, tmp_path / "auth.json", slot_id)

    slot_root = root / "slots" / slot_id
    assert runner_invoked is True
    assert not (slot_root / "output/result.json").exists()
    failure = json.loads((slot_root / "failed.json").read_text(encoding="utf-8"))
    assert failure["error_type"] == "BatchError"
    assert batch.smoke_status(tmp_path)["state"] == "invalid"
    with pytest.raises(batch.BatchError, match="refusing to reuse"):
        batch.run_manifest_slot(tmp_path, tmp_path / "auth.json", slot_id)


def test_result_classification_never_hides_non_selection_failure() -> None:
    forbidden = ["forbidden family observed: complete_gate"]
    assert (
        batch._classification("baseline", _result("P01", oracle_errors=forbidden))
        == "comparable_overvalidation"
    )
    assert (
        batch._classification("candidate", _result("P01", oracle_errors=forbidden))
        == "critical"
    )
    assert (
        batch._classification(
            "baseline",
            _result("P01", oracle_errors=forbidden, codex_exit_code=1),
        )
        == "critical"
    )
    assert (
        batch._classification(
            "baseline", _result("P01", oracle_errors=forbidden, final_valid=False)
        )
        == "critical"
    )


SMOKE_STATUS_CASES: list[tuple[frozenset[str], str]] = [
    (frozenset(), "eligible_for_repeats"),
    (frozenset({"baseline"}), "incomparable"),
    (frozenset({"candidate"}), "reject"),
    # Both arms completed a real deterministic semantic failure.  This is not
    # a runner-boundary failure and remains candidate rejection.
    (frozenset({"baseline", "candidate"}), "reject"),
]


@pytest.mark.parametrize(
    ("critical_arms", "expected_state"),
    SMOKE_STATUS_CASES,
)
def test_smoke_status_recomputes_complete_ledger(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    critical_arms: frozenset[str],
    expected_state: str,
) -> None:
    root, manifest = _private_manifest(tmp_path)
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)
    smoke = [
        slot
        for slot in cast(list[dict[str, object]], manifest["schedule"])
        if slot["repetition"] == 1
    ]
    for slot in smoke:
        slot_id = cast(str, slot["slot_id"])
        case_id = cast(str, slot["case_id"])
        arm_key = cast(str, slot["arm_key"])
        slot_root = root / "slots" / slot_id
        output = slot_root / "output"
        output.mkdir(parents=True)
        payload = _result(
            case_id,
            oracle_errors=(
                ["missing required docs_check (zero)"]
                if arm_key in critical_arms
                else None
            ),
        )
        result_path = output / "result.json"
        result_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        started = {"slot_id": slot_id, "case_id": case_id, "arm_key": arm_key}
        (slot_root / "started.json").write_text(json.dumps(started), encoding="utf-8")
        completed = {
            **started,
            "requested_model": "frozen-model",
            "requested_reasoning_effort": "medium",
            "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
            "classification": batch._classification(arm_key, payload),
        }
        (slot_root / "completed.json").write_text(
            json.dumps(completed), encoding="utf-8"
        )
    status = batch.smoke_status(tmp_path)
    assert status["state"] == expected_state
    assert status["completed_slots"] == 28


def test_smoke_status_is_fail_closed_for_missing_failed_and_tampered_ledgers(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root, manifest = _private_manifest(tmp_path)
    monkeypatch.setattr(batch, "verify_freeze", _valid_freeze)
    assert batch.smoke_status(tmp_path)["state"] == "not_yet_verified"
    first = cast(list[dict[str, object]], manifest["schedule"])[0]
    slot_root = root / "slots" / cast(str, first["slot_id"])
    slot_root.mkdir(parents=True)
    (slot_root / "failed.json").write_text(
        json.dumps(
            {
                "slot_id": first["slot_id"],
                "error_type": "BatchError",
                "error": "synthetic boundary failure",
            }
        ),
        encoding="utf-8",
    )
    status = batch.smoke_status(tmp_path)
    assert status["state"] == "invalid"
    assert status["failed_slots"] == 1
    extra = root / "slots/not-frozen"
    extra.mkdir()
    with pytest.raises(batch.BatchError, match="unexpected slot"):
        batch.smoke_status(tmp_path)
