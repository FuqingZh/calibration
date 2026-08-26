from __future__ import annotations

import hashlib
import json
import os
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

    def archive(commit: str, descriptor: int, _name: str) -> str:
        archive = os.open(
            _name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=descriptor
        )
        try:
            os.write(archive, commit.encode())
        finally:
            os.close(archive)
        return hashlib.sha256(commit.encode()).hexdigest()

    monkeypatch.setattr(batch, "_git", fake_git)
    monkeypatch.setattr(batch, "_archive_commit_at", archive)
    monkeypatch.setattr(batch, "_codex_version", lambda: "codex test")
    private = tmp_path / "private"
    private.mkdir()
    batch.freeze_batch(
        private, "a" * 40, "b" * 40, model="test", reasoning_effort="medium"
    )
    return private


def test_verify_freeze_accepts_unchanged_clean_controller(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    private = _freeze(monkeypatch, tmp_path)
    assert batch.verify_freeze(private)["valid"] is True


def test_freeze_records_distinct_current_controller_canary_source(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    private = _freeze(monkeypatch, tmp_path)
    manifest = json.loads(
        (private / "progressive-validation-selection/manifest.json").read_text()
    )
    source = cast(dict[str, object], manifest["canary_source"])
    assert manifest["live_canary_case_id"] == "C01"
    assert source["commit"] == "c" * 40
    assert source["archive"] == f"sources/canary-{'c' * 40}.tar"
    assert source["archive_sha256"] == hashlib.sha256(("c" * 40).encode()).hexdigest()
    assert batch.verify_freeze(private)["valid"] is True


@pytest.mark.parametrize("preexisting", ["directory", "symlink"])
def test_freeze_rejects_preexisting_run_root_before_archiving(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, preexisting: str
) -> None:
    private = tmp_path / "private"
    private.mkdir()
    run_root = private / "progressive-validation-selection"
    external = tmp_path / "external"
    external.mkdir()
    if preexisting == "directory":
        run_root.mkdir()
    else:
        run_root.symlink_to(external, target_is_directory=True)

    def git(args: list[str], *, cwd: Path = batch.REPOSITORY_ROOT) -> str:
        del cwd
        if args == ["status", "--porcelain"]:
            return ""
        value = args[-1]
        if value == "HEAD^{commit}":
            return "c" * 40
        return value.replace("^{commit}", "").replace("^{tree}", "tree")

    def must_not_archive(_commit: str, _descriptor: int, _name: str) -> str:
        raise AssertionError("unsafe frozen root reached archive creation")

    monkeypatch.setattr(batch, "_git", git)
    monkeypatch.setattr(batch, "_archive_commit_at", must_not_archive)
    with pytest.raises(batch.BatchError, match="private frozen run root"):
        batch.freeze_batch(
            private, "a" * 40, "b" * 40, model="test", reasoning_effort="medium"
        )
    assert list(external.iterdir()) == []


@pytest.mark.parametrize("replacement", ["symlink", "file"])
def test_freeze_rejects_unsafe_sources_before_archiving(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, replacement: str
) -> None:
    private = tmp_path / "private"
    external = tmp_path / "external"
    external.mkdir()
    original_mkdir = os.mkdir

    def injected_mkdir(
        name: str | bytes, mode: int = 0o777, *, dir_fd: int | None = None
    ) -> None:
        if name == "sources":
            assert dir_fd is not None
            if replacement == "symlink":
                os.symlink(external, "sources", dir_fd=dir_fd)
            else:
                leaf = os.open(
                    "sources", os.O_WRONLY | os.O_CREAT | os.O_EXCL, dir_fd=dir_fd
                )
                os.close(leaf)
            raise FileExistsError
        original_mkdir(name, mode, dir_fd=dir_fd)

    def git(args: list[str], *, cwd: Path = batch.REPOSITORY_ROOT) -> str:
        del cwd
        if args == ["status", "--porcelain"]:
            return ""
        value = args[-1]
        if value == "HEAD^{commit}":
            return "c" * 40
        return value.replace("^{commit}", "").replace("^{tree}", "tree")

    def must_not_archive(_commit: str, _descriptor: int, _name: str) -> str:
        raise AssertionError("unsafe sources reached archive creation")

    monkeypatch.setattr(batch.os, "mkdir", injected_mkdir)
    monkeypatch.setattr(batch, "_git", git)
    monkeypatch.setattr(batch, "_archive_commit_at", must_not_archive)
    with pytest.raises(batch.BatchError, match="private frozen sources"):
        batch.freeze_batch(
            private, "a" * 40, "b" * 40, model="test", reasoning_effort="medium"
        )
    assert list(external.iterdir()) == []


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
