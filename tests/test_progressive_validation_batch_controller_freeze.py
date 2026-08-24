from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

import pytest

from scripts import run_progressive_validation_selection_eval as batch


def _freeze(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    controller_root = tmp_path / "controller"
    controller = (
        controller_root / "scripts/run_progressive_validation_selection_eval.py"
    )
    runner = controller_root / "scripts/run_writable_agent_eval.py"
    controller.parent.mkdir(parents=True)
    controller.write_text("frozen controller\n")
    runner.write_text("frozen runner\n")
    monkeypatch.setattr(batch, "REPOSITORY_ROOT", controller_root)
    monkeypatch.setattr(
        batch,
        "CONTROLLER_FILES",
        (Path("scripts/run_progressive_validation_selection_eval.py"),),
    )

    def fake_git(args: list[str], *, cwd: Path = controller_root) -> str:
        del cwd
        if args == ["status", "--porcelain"]:
            return ""
        value = args[-1]
        if value == "HEAD^{commit}":
            return "c" * 40
        return value.replace("^{commit}", "").replace("^{tree}", "tree")

    def archive(commit: str, path: Path) -> str:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(commit.encode())
        return hashlib.sha256(commit.encode()).hexdigest()

    monkeypatch.setattr(batch, "_git", fake_git)
    monkeypatch.setattr(batch, "_archive_commit", archive)
    monkeypatch.setattr(batch, "_codex_version", lambda: "codex test")
    private = tmp_path / "private"
    batch.freeze_batch(
        private, "a" * 40, "b" * 40, model="test", reasoning_effort="medium"
    )
    return private


def test_verify_freeze_accepts_unchanged_clean_controller(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    private = _freeze(monkeypatch, tmp_path)
    assert batch.verify_freeze(private)["valid"] is True


def test_verify_freeze_rejects_controller_byte_change_without_head_change(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    private = _freeze(monkeypatch, tmp_path)
    (
        batch.REPOSITORY_ROOT / "scripts/run_progressive_validation_selection_eval.py"
    ).write_text("changed byte\n")
    result = batch.verify_freeze(private)
    assert result["valid"] is False
    assert cast(dict[str, bool], result["checks"])["controller_files"] is False


def test_verify_freeze_rejects_unrelated_dirty_controller_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    private = _freeze(monkeypatch, tmp_path)
    original_git = batch._git

    def dirty_git(args: list[str], *, cwd: Path = batch.REPOSITORY_ROOT) -> str:
        if args == ["status", "--porcelain"]:
            return " M unrelated.txt\n"
        return original_git(args, cwd=cwd)

    monkeypatch.setattr(batch, "_git", dirty_git)
    result = batch.verify_freeze(private)
    assert result["valid"] is False
    assert cast(dict[str, bool], result["checks"])["controller_clean"] is False


@pytest.mark.parametrize("field", ["requested_model", "schedule", "arm_map"])
def test_private_manifest_replacement_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, field: str
) -> None:
    private = _freeze(monkeypatch, tmp_path)
    manifest_path = private / "progressive-validation-selection/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest[field] = "replacement"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises(batch.BatchError, match="hash"):
        batch.verify_freeze(private)


def test_private_manifest_leaf_symlink_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    private = _freeze(monkeypatch, tmp_path)
    root = private / "progressive-validation-selection"
    manifest = root / "manifest.json"
    replacement = root / "replacement.json"
    manifest.rename(replacement)
    manifest.symlink_to(replacement.name)
    with pytest.raises(batch.BatchError, match="control file"):
        batch.verify_freeze(private)


def test_private_manifest_parent_symlink_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    private = _freeze(monkeypatch, tmp_path)
    root = private / "progressive-validation-selection"
    replacement = private / "replacement"
    root.rename(replacement)
    root.symlink_to(replacement.name, target_is_directory=True)
    with pytest.raises(batch.BatchError, match="control file"):
        batch.verify_freeze(private)


def test_malformed_private_manifest_is_a_batch_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    private = _freeze(monkeypatch, tmp_path)
    (private / "progressive-validation-selection/manifest.json").write_bytes(
        b"{ malformed"
    )
    with pytest.raises(batch.BatchError, match="valid JSON"):
        batch.verify_freeze(private)
