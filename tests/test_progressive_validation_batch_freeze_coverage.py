from __future__ import annotations

import io
import json
import os
import tarfile
from collections.abc import Iterator, Sequence
from pathlib import Path
from subprocess import CompletedProcess

import pytest

from scripts import run_progressive_validation_selection_eval as batch


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def _write_private_manifest(root: Path, manifest: dict[str, object]) -> None:
    _write_json(root / "manifest.json", manifest)
    canonical = json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
    _write_json(root / "manifest.sha256", {"sha256": batch._sha256_bytes(canonical)})


def test_json_and_config_fail_closed_for_invalid_documents(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="utf-8")
    with pytest.raises(batch.BatchError, match="cannot read JSON"):
        batch._json(malformed)

    array = tmp_path / "array.json"
    _write_json(array, [])
    with pytest.raises(batch.BatchError, match="JSON object required"):
        batch._json(array)

    invalid_config = tmp_path / "invalid-config.json"
    _write_json(invalid_config, {})
    with pytest.raises(batch.BatchError, match="invalid batch configuration"):
        batch.load_batch_config(invalid_config)


def test_private_control_files_require_regular_json_objects_and_real_roots(
    tmp_path: Path,
) -> None:
    root = tmp_path / "progressive-validation-selection"
    root.mkdir()
    (root / "manifest.json").mkdir()
    with pytest.raises(batch.BatchError, match="regular file"):
        batch._private_json_file(tmp_path, "manifest.json")

    (root / "manifest.json").rmdir()
    _write_json(root / "manifest.json", [])
    with pytest.raises(batch.BatchError, match="JSON object"):
        batch._private_json_file(tmp_path, "manifest.json")

    linked = tmp_path.parent / f"{tmp_path.name}-linked"
    linked.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(batch.BatchError, match="must not traverse a symlink"):
        batch._private_root(linked)


def test_git_and_commit_boundaries_preserve_exact_source_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def rejected(*_args: object, **_kwargs: object) -> CompletedProcess[str]:
        return CompletedProcess(["git"], 1, "", "repository unavailable")

    monkeypatch.setattr(batch.subprocess, "run", rejected)
    with pytest.raises(batch.BatchError, match="repository unavailable"):
        batch._git(["status"])

    def non_exact(_args: Sequence[str], *, cwd: Path = batch.REPOSITORY_ROOT) -> str:
        del cwd
        return "b" * 40

    monkeypatch.setattr(batch, "_git", non_exact)
    with pytest.raises(batch.BatchError, match="exact commit hashes"):
        batch._exact_commit("a" * 40)


def test_git_archive_and_codex_success_paths_preserve_reported_identity(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    archive_root = tmp_path / "archives"
    archive_root.mkdir()
    descriptor = os.open(archive_root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        digest = batch._archive_commit_at("HEAD", descriptor, "source.tar")
    finally:
        os.close(descriptor)
    archive = archive_root / "source.tar"
    assert archive.is_file()
    assert digest == batch._sha256_path(archive)

    def git_success(*_args: object, **_kwargs: object) -> CompletedProcess[str]:
        return CompletedProcess(["git"], 0, "  exact-value\n", "")

    monkeypatch.setattr(batch.subprocess, "run", git_success)
    assert batch._git(["rev-parse", "HEAD"]) == "exact-value"

    def codex_success(*_args: object, **_kwargs: object) -> CompletedProcess[str]:
        return CompletedProcess(["codex"], 0, "codex 1.2.3\n", "")

    monkeypatch.setattr(batch.subprocess, "run", codex_success)
    assert batch._codex_version() == "codex 1.2.3"


def test_private_ledger_and_archives_are_exclusive_and_clean_up_failed_exports(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ledger = tmp_path / "ledger.json"
    batch._exclusive_json(ledger, {"state": "frozen"})
    assert json.loads(ledger.read_text(encoding="utf-8")) == {"state": "frozen"}
    with pytest.raises(batch.BatchError, match="refusing to overwrite"):
        batch._exclusive_json(ledger, {})

    archive_root = tmp_path / "archives"
    archive_root.mkdir()
    descriptor = os.open(archive_root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        (archive_root / "existing.tar").write_bytes(b"archive")
        with pytest.raises(
            batch.BatchError, match="refusing to overwrite source archive"
        ):
            batch._archive_commit_at("a" * 40, descriptor, "existing.tar")

        failed = archive_root / "failed.tar"

        def archive_failure(
            *_args: object, **_kwargs: object
        ) -> CompletedProcess[bytes]:
            return CompletedProcess(["git", "archive"], 1, b"", b"bad archive")

        monkeypatch.setattr(batch.subprocess, "run", archive_failure)
        with pytest.raises(batch.BatchError, match="bad archive"):
            batch._archive_commit_at("a" * 40, descriptor, "failed.tar")
        assert not failed.exists()
    finally:
        os.close(descriptor)


def test_freeze_rejects_equal_revisions_and_empty_execution_controls(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    commit = "a" * 40

    def freeze_git(args: Sequence[str], *, cwd: Path = batch.REPOSITORY_ROOT) -> str:
        del cwd
        return "" if args[0] == "status" else commit

    monkeypatch.setattr(batch, "_git", freeze_git)
    with pytest.raises(batch.BatchError, match="commits must differ"):
        batch.freeze_batch(
            tmp_path, commit, commit, model="model", reasoning_effort="low"
        )

    values = iter(("", commit, "b" * 40))

    def empty_controls_git(
        _args: Sequence[str], *, cwd: Path = batch.REPOSITORY_ROOT
    ) -> str:
        del cwd
        return next(values)

    monkeypatch.setattr(batch, "_git", empty_controls_git)
    with pytest.raises(batch.BatchError, match="non-empty"):
        batch.freeze_batch(tmp_path, commit, "b" * 40, model="", reasoning_effort="low")


def test_codex_version_and_freeze_readback_reject_malformed_private_manifests(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def codex_missing(*_args: object, **_kwargs: object) -> CompletedProcess[str]:
        return CompletedProcess(["codex"], 1, "", "missing")

    monkeypatch.setattr(batch.subprocess, "run", codex_missing)
    with pytest.raises(batch.BatchError, match="cannot freeze Codex CLI version"):
        batch._codex_version()

    root = tmp_path / "progressive-validation-selection"
    root.mkdir()
    malformed_manifest: dict[str, object] = {"arm_map": []}
    _write_json(root / "manifest.json", malformed_manifest)
    with pytest.raises(batch.BatchError, match="cannot safely read private control"):
        batch.verify_freeze(tmp_path)
    _write_private_manifest(root, malformed_manifest)
    _write_json(root / "manifest.sha256", {"sha256": "wrong"})
    with pytest.raises(batch.BatchError, match="manifest hash does not match"):
        batch.verify_freeze(tmp_path)
    _write_private_manifest(root, malformed_manifest)
    monkeypatch.setattr(batch, "_fixture_manifest_is_exact", lambda: True)
    monkeypatch.setattr(batch, "_codex_version", lambda: "codex test")

    def hash_path(_path: Path) -> str:
        return "hash"

    def head_git(_args: Sequence[str], *, cwd: Path = batch.REPOSITORY_ROOT) -> str:
        del cwd
        return "head"

    monkeypatch.setattr(batch, "_sha256_path", hash_path)
    monkeypatch.setattr(batch, "_git", head_git)
    with pytest.raises(batch.BatchError, match="private arm map is invalid"):
        batch.verify_freeze(tmp_path)

    _write_private_manifest(root, {"arm_map": {"baseline": []}})
    with pytest.raises(batch.BatchError, match="private arm map entry is invalid"):
        batch.verify_freeze(tmp_path)

    _write_private_manifest(root, {"arm_map": {"baseline": {}}})
    with pytest.raises(batch.BatchError, match="private arm archive is invalid"):
        batch.verify_freeze(tmp_path)


def test_verify_freeze_recomputes_archives_and_tree_identity(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = tmp_path / "progressive-validation-selection"
    archive = root / "sources/base.tar"
    archive.parent.mkdir(parents=True)
    archive.write_bytes(b"archive")
    canary_archive = root / "sources/canary-head.tar"
    canary_archive.write_bytes(b"canary")
    _write_private_manifest(
        root,
        {
            "config_sha256": "hash",
            "case_manifest_sha256": "hash",
            "runner_sha256": "hash",
            "codex_cli_version": "codex test",
            "controller_commit": "head",
            "controller_files_sha256": {"runner": "hash"},
            "arm_map": {
                "baseline": {
                    "archive": "sources/base.tar",
                    "archive_sha256": "hash",
                    "commit": "a" * 40,
                    "git_tree_oid": "tree",
                }
            },
            "canary_source": {
                "archive": "sources/canary-head.tar",
                "archive_sha256": "hash",
                "commit": "c" * 40,
                "git_tree_oid": "tree",
            },
        },
    )

    def hash_path(_path: Path) -> str:
        return "hash"

    def git(args: Sequence[str], *, cwd: Path = batch.REPOSITORY_ROOT) -> str:
        del cwd
        if args[0] == "status":
            return ""
        return "tree" if args[2].endswith("^{tree}") else "head"

    monkeypatch.setattr(batch, "_fixture_manifest_is_exact", lambda: True)
    monkeypatch.setattr(batch, "_codex_version", lambda: "codex test")
    monkeypatch.setattr(batch, "_sha256_path", hash_path)
    monkeypatch.setattr(batch, "_controller_file_hashes", lambda: {"runner": "hash"})
    monkeypatch.setattr(batch, "_git", git)
    assert batch.verify_freeze(tmp_path) == {
        "valid": True,
        "checks": {
            "config": True,
            "fixture_manifest": True,
            "runner": True,
            "fixture_bytes": True,
            "codex_cli_version": True,
            "controller_commit": True,
            "controller_files": True,
            "controller_clean": True,
            "archive:base.tar": True,
            "tree:base.tar": True,
            "archive:canary-head.tar": True,
            "tree:canary-head.tar": True,
        },
    }


def _tar_with_member(path: Path, member: tarfile.TarInfo, content: bytes = b"") -> None:
    with tarfile.open(path, "w") as archive:
        archive.addfile(member, io.BytesIO(content) if member.isfile() else None)


def test_unpack_rejects_existing_or_unsafe_archives_and_symlink_traversal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    archive = tmp_path / "source.tar"
    member = tarfile.TarInfo("file.txt")
    member.size = 1
    _tar_with_member(archive, member, b"x")
    destination = tmp_path / "already-there"
    destination.mkdir()
    with pytest.raises(batch.BatchError, match="existing directory"):
        batch.unpack_source_archive(archive, destination)

    unsafe = tmp_path / "unsafe.tar"
    link = tarfile.TarInfo("link")
    link.type = tarfile.SYMTYPE
    _tar_with_member(unsafe, link)
    with pytest.raises(batch.BatchError, match="unsafe member"):
        batch.unpack_source_archive(unsafe, tmp_path / "unsafe-output")

    source = tmp_path / "source"
    nested = tarfile.TarInfo("nested/file.txt")
    nested.size = 1
    members = [nested]

    class Archive:
        calls = 0

        def __enter__(self) -> Archive:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def getmembers(self) -> list[tarfile.TarInfo]:
            self.calls += 1
            if self.calls == 2:
                (source / "nested").symlink_to(tmp_path)
            return members

        def extractfile(self, _member: tarfile.TarInfo) -> io.BytesIO:
            return io.BytesIO(b"x")

    def symlink_archive(*_args: object, **_kwargs: object) -> Archive:
        return Archive()

    monkeypatch.setattr(batch.tarfile, "open", symlink_archive)
    with pytest.raises(batch.BatchError, match="traverse a symlink"):
        batch.unpack_source_archive(archive, source)


def test_unpack_rejects_unreadable_regular_member(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    member = tarfile.TarInfo("file.txt")
    member.size = 1

    class Archive:
        def __enter__(self) -> Archive:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def getmembers(self) -> list[tarfile.TarInfo]:
            return [member]

        def extractfile(self, _member: tarfile.TarInfo) -> None:
            return None

    def unreadable_archive(*_args: object, **_kwargs: object) -> Archive:
        return Archive()

    monkeypatch.setattr(batch.tarfile, "open", unreadable_archive)
    with pytest.raises(batch.BatchError, match="could not be read"):
        batch.unpack_source_archive(tmp_path / "source.tar", tmp_path / "output")


def test_fixture_manifest_and_redaction_fail_closed_for_tampering(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = tmp_path / "evaluation"
    root.mkdir()
    fixture = root / "fixtures"
    fixture.mkdir()
    source = fixture / "case.txt"
    source.write_text("fixture", encoding="utf-8")
    digest = batch._sha256_path(source)
    manifest = root / "fixture-manifest.json"
    _write_json(
        manifest, {"files": {"fixtures/case.txt": digest}, "root_tree_sha256": "bad"}
    )
    monkeypatch.setattr(batch, "EVALUATION_ROOT", root)
    assert not batch._fixture_manifest_is_exact()
    _write_json(
        manifest, {"files": {"fixtures/case.txt": 2}, "root_tree_sha256": "bad"}
    )
    assert not batch._fixture_manifest_is_exact()
    _write_json(manifest, {"files": [], "root_tree_sha256": "bad"})
    assert not batch._fixture_manifest_is_exact()
    _write_json(
        manifest,
        {"files": {"fixtures/case.txt": "wrong"}, "root_tree_sha256": "bad"},
    )
    assert not batch._fixture_manifest_is_exact()
    _write_json(manifest, {"files": {}, "root_tree_sha256": "bad"})
    assert not batch._fixture_manifest_is_exact()

    raw: dict[str, object] = {
        "raw_command": "make test",
        "auth": "secret",
        "nested": ["relative.txt", "/private/result", {"cwd": "hidden"}],
    }
    redacted = batch._redact(raw)
    assert redacted == {
        "command_sha256": batch._sha256_bytes(b"make test"),
        "nested": ["relative.txt", "[redacted-absolute-path]", {}],
    }
    assert batch._path_count(["relative.txt", "/private", 1]) == 1
    assert batch._path_count("relative.txt") == 0


def test_fixture_manifest_rejects_filesystem_change_between_inventory_readbacks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = tmp_path / "evaluation"
    fixtures = root / "fixtures"
    fixtures.mkdir(parents=True)
    source = fixtures / "case.txt"
    extra = fixtures / "extra.txt"
    source.write_text("fixture", encoding="utf-8")
    extra.write_text("late fixture", encoding="utf-8")
    digest = batch._sha256_path(source)
    _write_json(
        root / "fixture-manifest.json",
        {"files": {"fixtures/case.txt": digest}, "root_tree_sha256": "unused"},
    )
    calls = 0

    def changing_rglob(_path: Path, _pattern: str) -> Iterator[Path]:
        nonlocal calls
        calls += 1
        return iter([source] if calls == 1 else [source, extra])

    monkeypatch.setattr(batch, "EVALUATION_ROOT", root)
    monkeypatch.setattr(Path, "rglob", changing_rglob)
    assert not batch._fixture_manifest_is_exact()
    assert calls == 2


def test_run_slot_delegates_only_from_unpacked_source_and_rejects_bad_runner_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    with pytest.raises(batch.BatchError, match="unpacked private directory"):
        batch.run_slot(
            tmp_path / "case.yaml",
            tmp_path / "workspace",
            tmp_path / "nope",
            tmp_path / "auth",
            tmp_path / "output",
            "m",
            "low",
        )

    source = tmp_path / "source"
    source.mkdir()
    replies: list[CompletedProcess[str]] = [
        CompletedProcess(["runner", "prepare"], 1, "", ""),
    ]

    def runner_reply(*_args: object, **_kwargs: object) -> CompletedProcess[str]:
        return replies.pop(0)

    monkeypatch.setattr(batch.subprocess, "run", runner_reply)
    with pytest.raises(batch.BatchError, match="preparation failed"):
        batch.run_slot(
            tmp_path / "case.yaml",
            tmp_path / "workspace",
            source,
            tmp_path / "auth",
            tmp_path / "output",
            "m",
            "low",
        )

    replies.extend(
        [
            CompletedProcess(["runner", "prepare"], 0, "", ""),
            CompletedProcess(["runner", "run"], 0, "not-json", ""),
        ]
    )
    with pytest.raises(batch.BatchError, match="did not emit JSON"):
        batch.run_slot(
            tmp_path / "case.yaml",
            tmp_path / "workspace",
            source,
            tmp_path / "auth",
            tmp_path / "output",
            "m",
            "low",
        )

    replies.extend(
        [
            CompletedProcess(["runner", "prepare"], 0, "", ""),
            CompletedProcess(["runner", "run"], 0, "[]", ""),
        ]
    )
    with pytest.raises(batch.BatchError, match="payload must be an object"):
        batch.run_slot(
            tmp_path / "case.yaml",
            tmp_path / "workspace",
            source,
            tmp_path / "auth",
            tmp_path / "output",
            "m",
            "low",
        )

    replies.extend(
        [
            CompletedProcess(["runner", "prepare"], 0, "", ""),
            CompletedProcess(["runner", "run"], 1, "", ""),
        ]
    )
    with pytest.raises(batch.BatchError, match="execution failed"):
        batch.run_slot(
            tmp_path / "case.yaml",
            tmp_path / "workspace",
            source,
            tmp_path / "auth",
            tmp_path / "output",
            "m",
            "low",
        )

    replies.extend(
        [
            CompletedProcess(["runner", "prepare"], 0, "", ""),
            CompletedProcess(["runner", "run"], 0, '{"case_id": "P01"}', ""),
        ]
    )
    assert batch.run_slot(
        tmp_path / "case.yaml",
        tmp_path / "workspace",
        source,
        tmp_path / "auth",
        tmp_path / "output",
        "m",
        "low",
    ) == {"case_id": "P01"}

    calls: list[tuple[Path, Path]] = []

    def unpack(archive: Path, source_dir: Path) -> None:
        calls.append((archive, source_dir))

    def completed(
        _case_path: Path,
        _workspace: Path,
        _source_root: Path,
        _auth_file: Path,
        _output_dir: Path,
        _model: str,
        _reasoning_effort: str,
    ) -> dict[str, object]:
        return {"case_id": "P01"}

    monkeypatch.setattr(batch, "unpack_source_archive", unpack)
    monkeypatch.setattr(batch, "run_slot", completed)
    assert batch.run_archived_slot(
        tmp_path / "archive.tar",
        source,
        tmp_path / "case.yaml",
        tmp_path / "workspace",
        tmp_path / "auth",
        tmp_path / "output",
        "m",
        "low",
    ) == {"case_id": "P01"}
    assert calls == [(tmp_path / "archive.tar", source)]
