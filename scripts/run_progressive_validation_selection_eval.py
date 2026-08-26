#!/usr/bin/env python3
"""Control-plane runner for the frozen progressive-validation comparison.

This program deliberately does not judge model output.  It freezes the two
source revisions, executes manifest-bound smoke slots through the existing
single-run executor, maintains an append-only private ledger, and derives a
redacted public projection from private artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
from collections.abc import Iterable, Mapping, Sequence
from contextlib import suppress
from pathlib import Path
from typing import Any, Protocol, cast

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVALUATION_ROOT = REPOSITORY_ROOT / "evaluations/progressive-validation-selection"
CONFIG_PATH = EVALUATION_ROOT / "batch-config.json"
SCHEMA_PATH = EVALUATION_ROOT / "batch.schema.json"
CONTROLLER_FILES = (Path("scripts/run_progressive_validation_selection_eval.py"),)
PRIVATE_FORBIDDEN_FIELDS = frozenset(
    {
        "raw_command",
        "argv",
        "trajectory",
        "auth",
        "codex_home",
        "commit",
        "arm",
        "cwd",
    }
)
ABSOLUTE_PATH_PATTERN = re.compile(r"(?:^|[^A-Za-z0-9_.-])/")
PUBLIC_FAMILIES = frozenset(
    {
        "focused_test",
        "docs_check",
        "runtime_test",
        "repository_check",
        "complete_gate",
        "generator",
        "artifact_readback",
        "docs_only",
        "structural_check",
        "behavior_sample",
        "unrelated_suite",
        "schema_contract",
        "consumer_a",
        "consumer_b",
        "example_check",
        "host_probe",
        "diff_inspection",
        "contract_check",
        "consumer_check",
        "host_check",
    }
)
PUBLIC_FINAL_STATUSES = frozenset(
    {"verified_ready", "conditionally_ready", "not_yet_verified"}
)
SLOT_EXECUTION_TIMEOUT_SECONDS = 960.0


class BatchError(RuntimeError):
    """Raised when a frozen batch boundary cannot be proven."""


class _PayloadValidator(Protocol):
    def validate(self, instance: object) -> None: ...


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _controller_file_hashes() -> dict[str, str]:
    """Hash the controller source that interprets a frozen batch manifest."""
    return {
        relative.as_posix(): _sha256_path(REPOSITORY_ROOT / relative)
        for relative in CONTROLLER_FILES
    }


def _json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BatchError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BatchError(f"JSON object required: {path}")
    return cast(dict[str, object], value)


def _private_json_file(private_root: Path, filename: str) -> dict[str, object]:
    """Read the private manifest through no-follow directory descriptors.

    This prevents symlink substitution at every named component. It cannot
    protect against a same-owner rename/delete race after each descriptor is
    opened; private-run ownership and O_EXCL artifacts remain required.
    """
    path = _private_root(private_root) / "progressive-validation-selection" / filename
    flags = os.O_RDONLY
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open("/", flags | directory)
    try:
        for part in path.parts[1:-1]:
            next_descriptor = os.open(
                part, flags | directory | nofollow, dir_fd=descriptor
            )
            os.close(descriptor)
            descriptor = next_descriptor
        leaf = os.open(path.name, flags | nofollow, dir_fd=descriptor)
        try:
            if not stat.S_ISREG(os.fstat(leaf).st_mode):
                raise BatchError("private control file must be a regular file")
            chunks: list[bytes] = []
            while chunk := os.read(leaf, 65536):
                chunks.append(chunk)
            raw = b"".join(chunks)
        finally:
            os.close(leaf)
    except OSError as exc:
        raise BatchError(f"cannot safely read private control file: {exc}") from exc
    finally:
        os.close(descriptor)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise BatchError(f"private control file is not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise BatchError("private control file must be a JSON object")
    return cast(dict[str, object], value)


def _private_manifest(private_root: Path) -> dict[str, object]:
    manifest = _private_json_file(private_root, "manifest.json")
    digest = _private_json_file(private_root, "manifest.sha256").get("sha256")
    canonical = json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
    if not isinstance(digest, str) or digest != _sha256_bytes(canonical):
        raise BatchError("private manifest hash does not match")
    return manifest


def _open_directory(path: Path, description: str) -> int:
    """Open one trusted directory without accepting a symlink leaf."""
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        return os.open(path, flags)
    except OSError as exc:
        raise BatchError(f"cannot safely open {description}: {exc}") from exc


def _open_directory_at(descriptor: int, name: str, description: str) -> int:
    """Open a descendant directory without following a replacement symlink."""
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        return os.open(name, flags, dir_fd=descriptor)
    except OSError as exc:
        raise BatchError(f"cannot safely open {description}: {exc}") from exc


def _open_slot_directory(root: Path, slot_id: str) -> int | None:
    """Open a ledger slot through no-follow directory descriptors.

    A missing ``slots`` directory or slot is normal before execution.  Every
    other failure is an unsafe private-ledger boundary rather than a reason to
    inspect a path through a possible symlink.
    """
    root_descriptor = _open_directory(root, "private run root")
    try:
        try:
            slots_descriptor = _open_directory_at(
                root_descriptor, "slots", "private slot ledger"
            )
        except BatchError as exc:
            if isinstance(exc.__cause__, FileNotFoundError):
                return None
            raise
        try:
            try:
                return _open_directory_at(
                    slots_descriptor, slot_id, f"frozen slot directory: {slot_id}"
                )
            except BatchError as exc:
                if isinstance(exc.__cause__, FileNotFoundError):
                    return None
                raise
        finally:
            os.close(slots_descriptor)
    finally:
        os.close(root_descriptor)


def _slot_ledger_entry_names(root: Path) -> list[str]:
    """List only real slot directories below the private ledger root."""
    root_descriptor = _open_directory(root, "private run root")
    try:
        try:
            slots_descriptor = _open_directory_at(
                root_descriptor, "slots", "private slot ledger"
            )
        except BatchError as exc:
            if isinstance(exc.__cause__, FileNotFoundError):
                return []
            raise
        try:
            names = os.listdir(slots_descriptor)
            for name in names:
                child = _open_directory_at(
                    slots_descriptor, name, "private slot ledger entry"
                )
                os.close(child)
            return names
        finally:
            os.close(slots_descriptor)
    finally:
        os.close(root_descriptor)


def _slot_regular_file_exists(descriptor: int, name: str, slot_id: str) -> bool:
    """Check a direct ledger leaf without following a symlink."""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        leaf = os.open(name, flags, dir_fd=descriptor)
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise BatchError(f"cannot safely read frozen slot ledger: {slot_id}") from exc
    try:
        if not stat.S_ISREG(os.fstat(leaf).st_mode):
            raise BatchError(f"frozen slot ledger leaf is not regular: {slot_id}")
        return True
    finally:
        os.close(leaf)


def _slot_json_with_sha256(
    descriptor: int, slot_id: str, *parts: str
) -> tuple[dict[str, object], str]:
    """Read a private slot JSON file and its exact bytes through safe descriptors."""
    if not parts:
        raise BatchError("private slot JSON path is empty")
    current = os.dup(descriptor)
    try:
        for part in parts[:-1]:
            next_descriptor = _open_directory_at(
                current, part, f"frozen slot directory: {slot_id}"
            )
            os.close(current)
            current = next_descriptor
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            leaf = os.open(parts[-1], flags, dir_fd=current)
        except OSError as exc:
            raise BatchError(
                f"cannot safely read frozen slot result: {slot_id}"
            ) from exc
        try:
            if not stat.S_ISREG(os.fstat(leaf).st_mode):
                raise BatchError(f"frozen slot result is not regular: {slot_id}")
            chunks: list[bytes] = []
            while chunk := os.read(leaf, 65536):
                chunks.append(chunk)
            raw = b"".join(chunks)
        finally:
            os.close(leaf)
    finally:
        os.close(current)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise BatchError(f"frozen slot JSON is invalid: {slot_id}") from exc
    if not isinstance(value, dict):
        raise BatchError(f"frozen slot JSON object required: {slot_id}")
    return cast(dict[str, object], value), _sha256_bytes(raw)


def _slot_json(descriptor: int, slot_id: str, *parts: str) -> dict[str, object]:
    """Read one private slot JSON object through no-follow ancestor descriptors."""
    value, _digest = _slot_json_with_sha256(descriptor, slot_id, *parts)
    return value


def _validate_started_ledger(
    descriptor: int, slot_id: str, case_id: str, arm_key: str
) -> None:
    """Validate the immutable start identity before accepting later evidence."""
    started = _slot_json(descriptor, slot_id, "started.json")
    expected: dict[str, object] = {
        "slot_id": slot_id,
        "case_id": case_id,
        "arm_key": arm_key,
    }
    if started != expected:
        raise BatchError(f"frozen slot start ledger mismatch: {slot_id}")


def _validate_failed_ledger(descriptor: int, slot_id: str) -> None:
    """Reject malformed failure records rather than downgrading them to absence."""
    failed = _slot_json(descriptor, slot_id, "failed.json")
    if (
        failed.get("slot_id") != slot_id
        or not isinstance(failed.get("error_type"), str)
        or not failed["error_type"]
        or not isinstance(failed.get("error"), str)
    ):
        raise BatchError(f"frozen slot failure ledger mismatch: {slot_id}")


def load_batch_config(config_path: Path = CONFIG_PATH) -> dict[str, object]:
    """Load and strictly validate the public, path-free batch configuration."""
    config = _json(config_path)
    schema = _json(SCHEMA_PATH)
    try:
        Draft202012Validator.check_schema(cast(dict[str, Any], schema))
        validator = cast(
            _PayloadValidator, Draft202012Validator(cast(dict[str, Any], schema))
        )
        validator.validate(config)
    except (SchemaError, ValidationError) as exc:
        raise BatchError(f"invalid batch configuration: {exc.message}") from exc
    return config


def _private_root(path: Path) -> Path:
    if not path.is_absolute():
        raise BatchError("private root must be absolute and outside the repository")
    ancestor = Path("/")
    for component in path.parts[1:]:
        ancestor /= component
        if ancestor.is_symlink():
            raise BatchError("private root must not traverse a symlink")
    resolved = path.resolve()
    root = REPOSITORY_ROOT.resolve()
    if resolved == root or root in resolved.parents:
        raise BatchError("private root must be absolute and outside the repository")
    return resolved


def _git(args: Sequence[str], *, cwd: Path = REPOSITORY_ROOT) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, check=False, capture_output=True, text=True
    )
    if result.returncode:
        raise BatchError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _exact_commit(value: str) -> str:
    resolved = _git(["rev-parse", "--verify", f"{value}^{{commit}}"])
    if resolved != value:
        raise BatchError("source revisions must be supplied as exact commit hashes")
    return resolved


def _exclusive_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError as exc:
        raise BatchError(f"refusing to overwrite private artifact: {path}") from exc
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _exclusive_json_at(
    descriptor: int, name: str, payload: Mapping[str, object]
) -> None:
    """Write one append-only private JSON leaf below an open directory."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        leaf = os.open(name, flags, 0o600, dir_fd=descriptor)
    except FileExistsError as exc:
        raise BatchError(f"refusing to overwrite private artifact: {name}") from exc
    except OSError as exc:
        raise BatchError(f"cannot safely write private artifact: {name}") from exc
    with os.fdopen(leaf, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _create_slot_directory(root: Path, slot_id: str) -> int:
    """Create one new slot below real private-ledger directories only."""
    root_descriptor = _open_directory(root, "private run root")
    try:
        with suppress(FileExistsError):
            os.mkdir("slots", 0o700, dir_fd=root_descriptor)
        slots_descriptor = _open_directory_at(
            root_descriptor, "slots", "private slot ledger"
        )
        try:
            try:
                os.mkdir(slot_id, 0o700, dir_fd=slots_descriptor)
            except FileExistsError as exc:
                existing = _open_directory_at(
                    slots_descriptor, slot_id, f"frozen slot directory: {slot_id}"
                )
                os.close(existing)
                raise BatchError(
                    f"refusing to reuse frozen slot directory: {slot_id}"
                ) from exc
            return _open_directory_at(
                slots_descriptor, slot_id, f"frozen slot directory: {slot_id}"
            )
        finally:
            os.close(slots_descriptor)
    finally:
        os.close(root_descriptor)


def _open_run_child_directory(root: Path, name: str, description: str) -> int | None:
    """Open one optional run-root child through a no-follow descriptor chain."""
    root_descriptor = _open_directory(root, "private run root")
    try:
        try:
            return _open_directory_at(root_descriptor, name, description)
        except BatchError as exc:
            if isinstance(exc.__cause__, FileNotFoundError):
                return None
            raise
    finally:
        os.close(root_descriptor)


def _create_run_child_directory(root: Path, name: str, description: str) -> int:
    """Create one exclusive run-root child without following a replacement link."""
    root_descriptor = _open_directory(root, "private run root")
    try:
        try:
            os.mkdir(name, 0o700, dir_fd=root_descriptor)
        except FileExistsError as exc:
            existing = _open_directory_at(root_descriptor, name, description)
            os.close(existing)
            raise BatchError(f"refusing to reuse {description}") from exc
        return _open_directory_at(root_descriptor, name, description)
    finally:
        os.close(root_descriptor)


def _sha256_descriptor(descriptor: int) -> str:
    """Hash the exact bytes of one already-open private artifact."""
    os.lseek(descriptor, 0, os.SEEK_SET)
    digest = hashlib.sha256()
    while chunk := os.read(descriptor, 65536):
        digest.update(chunk)
    return digest.hexdigest()


def _archive_commit_at(commit: str, descriptor: int, name: str) -> str:
    """Archive one commit to an exclusive no-follow file below an open directory."""
    flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        archive = os.open(name, flags, 0o600, dir_fd=descriptor)
    except FileExistsError as exc:
        raise BatchError(f"refusing to overwrite source archive: {name}") from exc
    except OSError as exc:
        raise BatchError(f"cannot safely create source archive: {name}") from exc
    try:
        with os.fdopen(archive, "wb", closefd=False) as output:
            result = subprocess.run(
                ["git", "archive", "--format=tar", commit],
                cwd=REPOSITORY_ROOT,
                stdout=output,
                stderr=subprocess.PIPE,
            )
        if result.returncode:
            os.unlink(name, dir_fd=descriptor)
            raise BatchError(result.stderr.decode("utf-8", "replace").strip())
        return _sha256_descriptor(archive)
    finally:
        os.close(archive)


def _create_frozen_run_root(private_root: Path) -> tuple[Path, int, int]:
    """Create the immutable run and source roots without following prior paths."""
    private_root = _private_root(private_root)
    descriptor = os.open("/", os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        for component in private_root.parts[1:]:
            with suppress(FileExistsError):
                os.mkdir(component, 0o700, dir_fd=descriptor)
            next_descriptor = _open_directory_at(descriptor, component, "private root")
            os.close(descriptor)
            descriptor = next_descriptor
        private_descriptor = descriptor
    except Exception:
        os.close(descriptor)
        raise
    run_name = "progressive-validation-selection"
    try:
        try:
            os.mkdir(run_name, 0o700, dir_fd=private_descriptor)
        except FileExistsError as exc:
            existing = _open_directory_at(
                private_descriptor, run_name, "private frozen run root"
            )
            os.close(existing)
            raise BatchError("refusing to reuse private frozen run root") from exc
        run_descriptor = _open_directory_at(
            private_descriptor, run_name, "private frozen run root"
        )
    finally:
        os.close(private_descriptor)
    try:
        try:
            os.mkdir("sources", 0o700, dir_fd=run_descriptor)
        except FileExistsError as exc:
            existing = _open_directory_at(
                run_descriptor, "sources", "private frozen sources"
            )
            os.close(existing)
            raise BatchError("refusing to reuse private frozen sources") from exc
        sources_descriptor = _open_directory_at(
            run_descriptor, "sources", "private frozen sources"
        )
        return private_root / run_name, run_descriptor, sources_descriptor
    except Exception:
        os.close(run_descriptor)
        raise


def _tree_hash(commit: str) -> str:
    return _git(["rev-parse", "--verify", f"{commit}^{{tree}}"])


def _schedule(config: Mapping[str, object]) -> list[dict[str, object]]:
    cases = cast(list[str], config["case_ids"])
    arms = cast(list[str], config["private_arm_keys"])
    repetitions = cast(int, config["valid_repetitions"])
    initial_repetitions = cast(int, config["smoke_repetitions"])
    rng = random.Random(cast(int, config["seed"]))
    slots: list[dict[str, object]] = []
    assignment_order = cases.copy()
    rng.shuffle(assignment_order)
    baseline_majority = set(assignment_order[: len(assignment_order) // 2])
    for repetition in range(repetitions):
        case_order = cases.copy()
        rng.shuffle(case_order)
        baseline_first = (
            baseline_majority
            if repetition in {0, 2}
            else set(cases) - baseline_majority
        )
        for case_id in case_order:
            order = arms if case_id in baseline_first else list(reversed(arms))
            for position, arm_key in enumerate(order):
                slots.append(
                    {
                        "slot_id": f"r{repetition + 1}-{case_id}-{position + 1}",
                        "case_id": case_id,
                        "repetition": repetition + 1,
                        "phase": (
                            "smoke" if repetition < initial_repetitions else "tiebreak"
                        ),
                        "arm_key": arm_key,
                        "paired_slot": f"r{repetition + 1}-{case_id}",
                    }
                )
    return slots


def freeze_batch(
    private_root: Path,
    baseline_commit: str,
    candidate_commit: str,
    *,
    model: str,
    reasoning_effort: str,
    config_path: Path = CONFIG_PATH,
) -> dict[str, object]:
    """Freeze two clean exact commits into hashes and an append-only ledger."""
    config = load_batch_config(config_path)
    private_root = _private_root(private_root)
    if _git(["status", "--porcelain"]):
        raise BatchError("refusing to freeze a dirty source repository")
    baseline = _exact_commit(baseline_commit)
    candidate = _exact_commit(candidate_commit)
    if baseline == candidate:
        raise BatchError("baseline and candidate commits must differ")
    if not model or not reasoning_effort:
        raise BatchError("model and reasoning effort must be non-empty")
    _, run_descriptor, sources_descriptor = _create_frozen_run_root(private_root)
    arm_map: dict[str, dict[str, str]] = {
        "baseline": {"commit": baseline, "archive": f"sources/{baseline}.tar"},
        "candidate": {"commit": candidate, "archive": f"sources/{candidate}.tar"},
    }
    try:
        for details in arm_map.values():
            archive_name = Path(details["archive"]).name
            details["archive_sha256"] = _archive_commit_at(
                details["commit"], sources_descriptor, archive_name
            )
            details["git_tree_oid"] = _tree_hash(details["commit"])
        controller_commit = _git(["rev-parse", "--verify", "HEAD^{commit}"])
        canary_case_id = config.get("live_canary_case_id")
        if not isinstance(canary_case_id, str) or not canary_case_id:
            raise BatchError("live canary case is invalid")
        canary_source: dict[str, str] = {
            "commit": controller_commit,
            "archive": f"sources/canary-{controller_commit}.tar",
        }
        canary_source["archive_sha256"] = _archive_commit_at(
            controller_commit, sources_descriptor, Path(canary_source["archive"]).name
        )
        canary_source["git_tree_oid"] = _tree_hash(controller_commit)
        schedule = _schedule(config)
        manifest: dict[str, object] = {
            "schema_version": 1,
            "config_sha256": _sha256_path(config_path),
            "case_manifest_sha256": _sha256_path(
                EVALUATION_ROOT / "fixture-manifest.json"
            ),
            "runner_sha256": _sha256_path(
                REPOSITORY_ROOT / "scripts/run_writable_agent_eval.py"
            ),
            "controller_commit": controller_commit,
            "controller_files_sha256": _controller_file_hashes(),
            "codex_cli_version": _codex_version(),
            "requested_model": model,
            "requested_reasoning_effort": reasoning_effort,
            "turn_budget": config["turn_budget"],
            "seed": config["seed"],
            "case_ids": config["case_ids"],
            "initial_repetitions": config["smoke_repetitions"],
            "valid_repetitions": config["valid_repetitions"],
            "arm_map": arm_map,
            "live_canary_case_id": canary_case_id,
            "canary_source": canary_source,
            "schedule": schedule,
            "transient_retry_limit": config["transient_retry_limit"],
            "status": "frozen",
        }
        _exclusive_json_at(run_descriptor, "manifest.json", manifest)
        manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
        _exclusive_json_at(
            run_descriptor, "manifest.sha256", {"sha256": _sha256_bytes(manifest_bytes)}
        )
        return manifest
    finally:
        os.close(sources_descriptor)
        os.close(run_descriptor)


def _codex_version() -> str:
    result = subprocess.run(
        ["codex", "--version"], check=False, capture_output=True, text=True
    )
    if result.returncode or not result.stdout.strip():
        raise BatchError("cannot freeze Codex CLI version")
    return result.stdout.strip()


def verify_freeze(private_root: Path) -> dict[str, object]:
    """Recompute all frozen hashes without executing a model."""
    root = _private_root(private_root) / "progressive-validation-selection"
    manifest = _private_manifest(private_root)
    clean = not bool(_git(["status", "--porcelain"]))
    checks: dict[str, bool] = {
        "config": manifest.get("config_sha256") == _sha256_path(CONFIG_PATH),
        "fixture_manifest": manifest.get("case_manifest_sha256")
        == _sha256_path(EVALUATION_ROOT / "fixture-manifest.json"),
        "runner": manifest.get("runner_sha256")
        == _sha256_path(REPOSITORY_ROOT / "scripts/run_writable_agent_eval.py"),
        "fixture_bytes": _fixture_manifest_is_exact(),
        "codex_cli_version": manifest.get("codex_cli_version") == _codex_version(),
        "controller_commit": manifest.get("controller_commit")
        == _git(["rev-parse", "--verify", "HEAD^{commit}"]),
        "controller_files": manifest.get("controller_files_sha256")
        == _controller_file_hashes(),
        "controller_clean": clean,
    }
    arm_map = manifest.get("arm_map")
    if not isinstance(arm_map, dict):
        raise BatchError("private arm map is invalid")
    typed_arm_map = cast(dict[str, object], arm_map)
    for raw_details in typed_arm_map.values():
        if not isinstance(raw_details, dict):
            raise BatchError("private arm map entry is invalid")
        details = cast(dict[str, object], raw_details)
        archive_name = details.get("archive")
        if not isinstance(archive_name, str):
            raise BatchError("private arm archive is invalid")
        archive = root / archive_name
        checks[f"archive:{archive.name}"] = archive.is_file() and details.get(
            "archive_sha256"
        ) == _sha256_path(archive)
        commit = details.get("commit")
        checks[f"tree:{archive.name}"] = isinstance(commit, str) and details.get(
            "git_tree_oid"
        ) == _tree_hash(commit)
    canary_source = manifest.get("canary_source")
    if not isinstance(canary_source, dict):
        raise BatchError("private canary source is invalid")
    canary_details = cast(dict[str, object], canary_source)
    canary_archive_name = canary_details.get("archive")
    canary_commit = canary_details.get("commit")
    if not isinstance(canary_archive_name, str) or not isinstance(canary_commit, str):
        raise BatchError("private canary source is invalid")
    canary_archive = root / canary_archive_name
    checks[f"archive:{canary_archive.name}"] = (
        canary_archive.is_file()
        and canary_details.get("archive_sha256") == _sha256_path(canary_archive)
    )
    checks[f"tree:{canary_archive.name}"] = canary_details.get(
        "git_tree_oid"
    ) == _tree_hash(canary_commit)
    return {"valid": all(checks.values()), "checks": checks}


def unpack_source_archive(archive: Path, source_dir: Path) -> None:
    """Safely materialize a frozen Git archive before it reaches a single run."""
    if source_dir.exists():
        raise BatchError("refusing to unpack source over an existing directory")
    with tarfile.open(archive, "r") as contents:
        for member in contents.getmembers():
            member_path = Path(member.name)
            if (
                member_path.is_absolute()
                or ".." in member_path.parts
                or not (member.isdir() or member.isreg())
            ):
                raise BatchError("source archive contains an unsafe member")
        source_dir.mkdir(mode=0o700, parents=True)
        for member in contents.getmembers():
            destination = source_dir / member.name
            for ancestor in (destination.parent, *destination.parent.parents):
                if ancestor == source_dir.parent:
                    break
                if ancestor.exists() and ancestor.is_symlink():
                    raise BatchError("source archive would traverse a symlink parent")
            if member.isdir():
                destination.mkdir(mode=0o700, exist_ok=True)
                destination.chmod(member.mode & 0o777)
                continue
            destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            content = contents.extractfile(member)
            if content is None:
                raise BatchError("source archive member could not be read")
            with content, destination.open("xb") as output:
                shutil.copyfileobj(content, output)
            destination.chmod(member.mode & 0o777)
            destination.chmod(member.mode & 0o777)


def _fixture_manifest_is_exact() -> bool:
    manifest = _json(EVALUATION_ROOT / "fixture-manifest.json")
    files = manifest.get("files")
    root_hash = manifest.get("root_tree_sha256")
    if not isinstance(files, dict) or not isinstance(root_hash, str):
        return False
    entries: dict[str, str] = {}
    for relative, digest in cast(dict[object, object], files).items():
        if not isinstance(relative, str) or not isinstance(digest, str):
            return False
        candidate = EVALUATION_ROOT / relative
        if not candidate.is_file() or _sha256_path(candidate) != digest:
            return False
        entries[relative] = digest
    actual = {
        candidate.relative_to(EVALUATION_ROOT).as_posix()
        for candidate in EVALUATION_ROOT.rglob("*")
        if candidate.is_file()
        and candidate.name != "fixture-manifest.json"
        and "results" not in candidate.relative_to(EVALUATION_ROOT).parts
        and (
            "fixtures" in candidate.relative_to(EVALUATION_ROOT).parts
            or candidate.relative_to(EVALUATION_ROOT).parts[0] == "cases"
            or candidate.name
            in {
                "rubric.yaml",
                "judge-prompt.md",
                "result.schema.json",
                "batch-config.json",
                "batch.schema.json",
            }
        )
    }
    if set(entries) != actual:
        return False
    actual = {
        path.relative_to(EVALUATION_ROOT).as_posix()
        for path in EVALUATION_ROOT.rglob("*")
        if path.is_file()
        and path.name != "fixture-manifest.json"
        and "results" not in path.relative_to(EVALUATION_ROOT).parts
        and (
            "fixtures" in path.relative_to(EVALUATION_ROOT).parts
            or path.relative_to(EVALUATION_ROOT).parts[0] == "cases"
            or path.name
            in {
                "rubric.yaml",
                "judge-prompt.md",
                "result.schema.json",
                "batch-config.json",
                "batch.schema.json",
            }
        )
    }
    if set(entries) != actual:
        return False
    canonical = "".join(
        f"{path}\0{digest}\n" for path, digest in sorted(entries.items())
    )
    return _sha256_bytes(canonical.encode()) == root_hash


def run_slot(
    case_path: Path,
    workspace: Path,
    source_root: Path,
    auth_file: Path,
    output_dir: Path,
    model: str,
    reasoning_effort: str,
) -> dict[str, object]:
    """Execute exactly one future batch slot through the frozen single-run runner.

    Scheduling, eligibility, and judge collection intentionally remain outside
    this narrow adapter.  The delegated runner owns isolated execution and its
    result path is exclusive, so an invalid run remains at its original path.
    """
    if not source_root.is_dir():
        raise BatchError("single-run source root must be an unpacked private directory")
    runner = REPOSITORY_ROOT / "scripts/run_writable_agent_eval.py"
    prepare = subprocess.run(
        [
            sys.executable,
            str(runner),
            "prepare",
            "--case",
            str(case_path),
            "--workspace",
            str(workspace),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if prepare.returncode:
        raise BatchError("single-run preparation failed")
    result = _run_slot_process(
        [
            sys.executable,
            str(runner),
            "run",
            "--case",
            str(case_path),
            "--workspace",
            str(workspace),
            "--source-root",
            str(source_root),
            "--auth-file",
            str(auth_file),
            "--output-dir",
            str(output_dir),
            "--model",
            model,
            "--reasoning-effort",
            reasoning_effort,
        ]
    )
    if result.returncode:
        raise BatchError(
            "single-run execution failed; original private artifacts are retained"
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise BatchError("single-run did not emit JSON") from exc
    if not isinstance(payload, dict):
        raise BatchError("single-run JSON payload must be an object")
    return cast(dict[str, object], payload)


def _run_slot_process(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run the delegated slot under one deadline and reap its process group."""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=SLOT_EXECUTION_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as exc:
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        raise BatchError(
            "single-run execution timed out; original private artifacts are retained"
        ) from exc
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def run_archived_slot(
    archive: Path,
    source_dir: Path,
    case_path: Path,
    workspace: Path,
    auth_file: Path,
    output_dir: Path,
    model: str,
    reasoning_effort: str,
) -> dict[str, object]:
    """Safely unpack one frozen archive, then delegate to the single-run CLI."""
    unpack_source_archive(archive, source_dir)
    return run_slot(
        case_path,
        workspace,
        source_dir,
        auth_file,
        output_dir,
        model,
        reasoning_effort,
    )


def _redact(value: object) -> object:
    if isinstance(value, list):
        return [_redact(item) for item in cast(list[object], value)]
    if isinstance(value, str) and ABSOLUTE_PATH_PATTERN.search(value):
        return "[redacted-absolute-path]"
    if not isinstance(value, dict):
        return value
    result: dict[str, object] = {}
    for key, item in cast(dict[str, object], value).items():
        lowered = key.lower()
        if any(token in lowered for token in PRIVATE_FORBIDDEN_FIELDS):
            if key == "raw_command" and isinstance(item, str):
                result["command_sha256"] = _sha256_bytes(item.encode())
            continue
        result[key] = _redact(item)
    return result


def _contains_private_projection_key(value: object) -> bool:
    if isinstance(value, list):
        return any(
            _contains_private_projection_key(item) for item in cast(list[object], value)
        )
    if not isinstance(value, dict):
        return False
    mapping = cast(dict[str, object], value)
    return any(
        key.lower() in PRIVATE_FORBIDDEN_FIELDS
        or _contains_private_projection_key(item)
        for key, item in mapping.items()
    )


def _path_count(value: object) -> int:
    if not isinstance(value, list):
        return 0
    paths = cast(list[object], value)
    return sum(
        isinstance(item, str)
        and not Path(item).is_absolute()
        and not ABSOLUTE_PATH_PATTERN.search(item)
        for item in paths
    )


def _safe_errors(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [
        _sha256_bytes(item.encode()) if isinstance(item, str) else "[invalid]"
        for item in cast(list[object], value)
    ]


def project_public(private_result: Path, public_path: Path) -> dict[str, object]:
    """Create one schema-validated public projection with no arm or path leaks."""
    result = _json(private_result)
    verification = result.get("verification")
    task_outcome = result.get("task_outcome")
    validation_selection = result.get("validation_selection")
    evidence_integrity = result.get("evidence_integrity")
    realized_safety_events = result.get("realized_safety_events")
    command_oracle = result.get("command_oracle")
    final_oracle = result.get("final_oracle")
    verified = (
        cast(dict[str, object], verification) if isinstance(verification, dict) else {}
    )
    task = (
        cast(dict[str, object], task_outcome) if isinstance(task_outcome, dict) else {}
    )
    selection = (
        cast(dict[str, object], validation_selection)
        if isinstance(validation_selection, dict)
        else {}
    )
    integrity = (
        cast(dict[str, object], evidence_integrity)
        if isinstance(evidence_integrity, dict)
        else {}
    )
    oracle = (
        cast(dict[str, object], command_oracle)
        if isinstance(command_oracle, dict)
        else {}
    )
    final = (
        cast(dict[str, object], final_oracle) if isinstance(final_oracle, dict) else {}
    )
    is_verified = verified.get("passed") is True
    is_oracle_valid = oracle.get("valid") is True
    is_final_valid = final.get("valid") is True
    raw_required_missing = selection.get("required_missing")
    raw_ordered_missing = selection.get("ordered_missing")
    observations: list[dict[str, object]] = []
    raw_observations = oracle.get("observations")
    if isinstance(raw_observations, list):
        for raw in cast(list[object], raw_observations):
            if isinstance(raw, dict):
                item = cast(dict[str, object], raw)
                raw_command = item.get("raw_command")
                family = item.get("family")
                exit_code = item.get("exit_code")
                if (
                    isinstance(raw_command, str)
                    and isinstance(family, str)
                    and family in PUBLIC_FAMILIES
                    and isinstance(exit_code, (int, type(None)))
                ):
                    observations.append(
                        {
                            "family": family,
                            "exit_code": exit_code,
                            "command_sha256": _sha256_bytes(raw_command.encode()),
                        }
                    )
    projection: dict[str, object] = {
        "case_id": result.get("case_id"),
        "requested_model": result.get("model"),
        "reasoning_effort": result.get("reasoning_effort"),
        "elapsed_seconds": result.get("elapsed_seconds"),
        "codex_exit_code": result.get("codex_exit_code"),
        "verification": {
            "passed": is_verified,
            "changed_path_count": _path_count(verified.get("changed_paths")),
            "unexpected_change_count": _path_count(verified.get("unexpected_changes")),
            "missing_required_change_count": _path_count(
                verified.get("missing_required_changes")
            ),
        },
        "task_outcome": {
            "valid": task.get("valid") is True,
            "errors": _safe_errors(task.get("errors")),
        },
        "validation_selection": {
            "enabled": selection.get("enabled") is True,
            "contract_satisfied": selection.get("contract_satisfied") is True,
            "required_covered": selection.get("required_covered") is True,
            "ordered_covered": selection.get("ordered_covered") is True,
            "required_missing_count": len(cast(list[object], raw_required_missing))
            if isinstance(raw_required_missing, list)
            else 0,
            "ordered_missing_count": len(cast(list[object], raw_ordered_missing))
            if isinstance(raw_ordered_missing, list)
            else 0,
            "forbidden_families": selection.get("forbidden_families")
            if isinstance(selection.get("forbidden_families"), list)
            else [],
            "forbidden_event_count": selection.get("forbidden_event_count")
            if isinstance(selection.get("forbidden_event_count"), int)
            and not isinstance(selection.get("forbidden_event_count"), bool)
            else 0,
        },
        "evidence_integrity": {
            "valid": integrity.get("valid") is True,
            "errors": _safe_errors(integrity.get("errors")),
        },
        "realized_safety_veto": bool(cast(list[object], realized_safety_events))
        if isinstance(realized_safety_events, list)
        else True,
        "command_oracle": {
            "enabled": oracle.get("enabled") is True,
            "valid": is_oracle_valid,
            "observations": observations,
            "errors": _safe_errors(oracle.get("errors")),
        },
        "final_oracle": {
            "enabled": final.get("enabled") is True,
            "valid": is_final_valid,
            "status": final.get("status")
            if final.get("status") in PUBLIC_FINAL_STATUSES
            else None,
            "errors": _safe_errors(final.get("errors")),
        },
    }
    projection["valid"] = (
        task.get("valid") is True
        and selection.get("contract_satisfied") is True
        and integrity.get("valid") is True
        and projection["realized_safety_veto"] is False
    )
    if _contains_private_projection_key(projection):
        raise BatchError("public projection still contains a private control field")
    schema = _json(SCHEMA_PATH)
    definitions = schema.get("$defs")
    if not isinstance(definitions, dict):
        raise BatchError("batch schema lacks public projection definition")
    typed_definitions = cast(dict[str, object], definitions)
    public_schema = typed_definitions.get("public_projection")
    if not isinstance(public_schema, dict):
        raise BatchError("batch schema public projection is invalid")
    try:
        projection_schema = {**schema, **cast(dict[str, object], public_schema)}
        validator = cast(
            _PayloadValidator,
            Draft202012Validator(cast(dict[str, Any], projection_schema)),
        )
        validator.validate(projection)
    except ValidationError as exc:
        raise BatchError(f"public projection fails schema: {exc.message}") from exc
    _exclusive_json(public_path, projection)
    return projection


def _run_root(private_root: Path) -> Path:
    return _private_root(private_root) / "progressive-validation-selection"


def _assessment(result: Mapping[str, object]) -> dict[str, object]:
    """Read the three frozen outcome layers without collapsing their meaning."""
    task = result.get("task_outcome")
    selection = result.get("validation_selection")
    integrity = result.get("evidence_integrity")
    verification = result.get("verification")
    final = result.get("final_oracle")
    oracle = result.get("command_oracle")
    realized_safety_events = result.get("realized_safety_events")
    if not all(
        isinstance(item, dict)
        for item in (task, selection, integrity, verification, final, oracle)
    ):
        return {
            "task_outcome": "critical",
            "selection_outcome": "undercoverage",
            "evidence_integrity": "invalid",
            "required_missing_count": 1,
            "ordered_missing_count": 1,
            "forbidden_event_count": 0,
            "realized_safety_veto": True,
        }
    task_data = cast(dict[str, object], task)
    selection_data = cast(dict[str, object], selection)
    integrity_data = cast(dict[str, object], integrity)
    verification_data = cast(dict[str, object], verification)
    final_data = cast(dict[str, object], final)
    required_missing = selection_data.get("required_missing")
    ordered_missing = selection_data.get("ordered_missing")
    forbidden_count = selection_data.get("forbidden_event_count")
    if (
        not isinstance(required_missing, list)
        or not isinstance(ordered_missing, list)
        or not isinstance(forbidden_count, int)
        or isinstance(forbidden_count, bool)
        or forbidden_count < 0
        or not isinstance(realized_safety_events, list)
        or not all(
            isinstance(item, str) and item
            for item in cast(list[object], realized_safety_events)
        )
    ):
        return {
            "task_outcome": "critical",
            "selection_outcome": "undercoverage",
            "evidence_integrity": "invalid",
            "required_missing_count": 1,
            "ordered_missing_count": 1,
            "forbidden_event_count": 0,
            "realized_safety_veto": True,
        }
    if required_missing:
        selection_outcome = "undercoverage"
    elif ordered_missing:
        selection_outcome = "misordered"
    elif forbidden_count:
        selection_outcome = "overvalidation"
    else:
        selection_outcome = "precise"
    return {
        "task_outcome": (
            "valid"
            if task_data.get("valid") is True
            and result.get("codex_exit_code") == 0
            and verification_data.get("passed") is True
            and final_data.get("valid") is True
            else "critical"
        ),
        "selection_outcome": selection_outcome,
        "evidence_integrity": (
            "valid" if integrity_data.get("valid") is True else "invalid"
        ),
        "required_missing_count": len(cast(list[object], required_missing)),
        "ordered_missing_count": len(cast(list[object], ordered_missing)),
        "forbidden_event_count": forbidden_count,
        "realized_safety_veto": bool(cast(list[object], realized_safety_events)),
    }


def _classification(arm_key: str, result: Mapping[str, object]) -> str:
    """Retain a compact ledger label while preserving layered result fields."""
    del arm_key
    assessment = _assessment(result)
    if assessment["task_outcome"] == "critical":
        return "critical"
    if assessment["evidence_integrity"] == "invalid":
        return "evidence_invalid"
    return cast(str, assessment["selection_outcome"])


def _canary_fields(
    manifest: Mapping[str, object],
) -> tuple[str, str, str, dict[str, object]]:
    """Return frozen canary identity and source details without live defaults."""
    case_id = manifest.get("live_canary_case_id")
    model = manifest.get("requested_model")
    effort = manifest.get("requested_reasoning_effort")
    source = manifest.get("canary_source")
    if (
        not isinstance(case_id, str)
        or not case_id
        or not isinstance(model, str)
        or not model
        or not isinstance(effort, str)
        or not effort
        or not isinstance(source, dict)
    ):
        raise BatchError("frozen live canary fields are invalid")
    details = cast(dict[str, object], source)
    if not all(
        isinstance(details.get(field), str) and details[field]
        for field in ("commit", "archive", "archive_sha256", "git_tree_oid")
    ):
        raise BatchError("frozen live canary source is invalid")
    return case_id, model, effort, details


def _canary_start_record(
    case_id: str, model: str, effort: str, source: Mapping[str, object]
) -> dict[str, object]:
    return {
        "case_id": case_id,
        "requested_model": model,
        "requested_reasoning_effort": effort,
        "canary_source_sha256": source["archive_sha256"],
    }


def _canary_result_is_valid(
    result: Mapping[str, object], case_id: str, model: str, effort: str
) -> bool:
    verification = result.get("verification")
    task = result.get("task_outcome")
    selection = result.get("validation_selection")
    integrity = result.get("evidence_integrity")
    oracle = result.get("command_oracle")
    final = result.get("final_oracle")
    if not all(
        isinstance(item, dict)
        for item in (verification, task, selection, integrity, oracle, final)
    ):
        return False
    verification_data = cast(dict[str, object], verification)
    task_data = cast(dict[str, object], task)
    selection_data = cast(dict[str, object], selection)
    integrity_data = cast(dict[str, object], integrity)
    oracle_data = cast(dict[str, object], oracle)
    final_data = cast(dict[str, object], final)
    broker_events = oracle_data.get("broker_events")
    return (
        result.get("case_id") == case_id
        and result.get("model") == model
        and result.get("reasoning_effort") == effort
        and result.get("codex_exit_code") == 0
        and verification_data.get("passed") is True
        and verification_data.get("unexpected_changes") == []
        and verification_data.get("missing_required_changes") == []
        and task_data.get("valid") is True
        and selection_data.get("contract_satisfied") is True
        and integrity_data.get("valid") is True
        and oracle_data.get("valid") is True
        and isinstance(broker_events, list)
        and len(cast(list[object], broker_events)) > 0
        and final_data.get("valid") is True
    )


def _validate_canary_completion(root: Path, manifest: Mapping[str, object]) -> None:
    """Validate the independent canary ledger before comparison evidence exists."""
    case_id, model, effort, source = _canary_fields(manifest)
    descriptor = _open_run_child_directory(root, "canary", "private live canary")
    if descriptor is None:
        raise BatchError("live canary is not completed")
    try:
        if _slot_regular_file_exists(descriptor, "failed.json", "canary"):
            failed = _slot_json(descriptor, "canary", "failed.json")
            if (
                failed.get("case_id") != case_id
                or not isinstance(failed.get("error_type"), str)
                or not failed["error_type"]
                or not isinstance(failed.get("error"), str)
            ):
                raise BatchError("live canary failure ledger is invalid")
            raise BatchError("live canary is invalid")
        if not all(
            _slot_regular_file_exists(descriptor, name, "canary")
            for name in ("started.json", "completed.json")
        ):
            raise BatchError("live canary is not completed")
        started = _slot_json(descriptor, "canary", "started.json")
        if started != _canary_start_record(case_id, model, effort, source):
            raise BatchError("live canary start ledger mismatch")
        result, digest = _slot_json_with_sha256(
            descriptor, "canary", "output", "result.json"
        )
        completed = _slot_json(descriptor, "canary", "completed.json")
    finally:
        os.close(descriptor)
    expected_completed: dict[str, object] = {
        **_canary_start_record(case_id, model, effort, source),
        "result_sha256": digest,
        "verified": _canary_result_is_valid(result, case_id, model, effort),
    }
    if completed != expected_completed:
        raise BatchError("live canary completion ledger mismatch")
    if completed["verified"] is not True:
        raise BatchError("live canary is invalid")


def canary_status(private_root: Path) -> dict[str, object]:
    """Report whether the independent live canary permits comparison execution."""
    root = _run_root(private_root)
    manifest = _private_manifest(private_root)
    verification = verify_freeze(private_root)
    if verification.get("valid") is not True:
        raise BatchError("freeze verification failed")
    descriptor = _open_run_child_directory(root, "canary", "private live canary")
    if descriptor is None:
        return {"state": "not_yet_verified"}
    os.close(descriptor)
    _validate_canary_completion(root, manifest)
    return {"state": "verified"}


def _require_verified_canary(private_root: Path) -> None:
    if canary_status(private_root).get("state") != "verified":
        raise BatchError("live canary is not completed")


def run_canary(private_root: Path, auth_file: Path) -> dict[str, object]:
    """Run the one frozen live canary outside the comparison-slot schedule."""
    root = _run_root(private_root)
    verification = verify_freeze(private_root)
    if verification.get("valid") is not True:
        raise BatchError("freeze verification failed")
    manifest = _private_manifest(private_root)
    case_id, model, effort, source = _canary_fields(manifest)
    canary_root = root / "canary"
    descriptor = _create_run_child_directory(root, "canary", "private live canary")
    started = _canary_start_record(case_id, model, effort, source)
    try:
        _exclusive_json_at(descriptor, "started.json", started)
        try:
            result = run_archived_slot(
                root / cast(str, source["archive"]),
                canary_root / "source",
                EVALUATION_ROOT / "cases" / f"{case_id}.yaml",
                canary_root / "workspace",
                auth_file,
                canary_root / "output",
                model,
                effort,
            )
            persisted, digest = _slot_json_with_sha256(
                descriptor, "canary", "output", "result.json"
            )
            if persisted != result:
                raise BatchError("live canary result readback mismatch")
        except Exception as exc:
            _exclusive_json_at(
                descriptor,
                "failed.json",
                {
                    "case_id": case_id,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
            if isinstance(exc, BatchError):
                raise
            raise BatchError("live canary execution failed") from exc
        completed: dict[str, object] = {
            **started,
            "result_sha256": digest,
            "verified": _canary_result_is_valid(result, case_id, model, effort),
        }
        _exclusive_json_at(descriptor, "completed.json", completed)
        if completed["verified"] is not True:
            raise BatchError("live canary is invalid")
        return completed
    finally:
        os.close(descriptor)


def _smoke_slots(manifest: Mapping[str, object]) -> list[dict[str, object]]:
    schedule = manifest.get("schedule")
    if not isinstance(schedule, list):
        raise BatchError("frozen schedule is invalid")
    raw_case_ids = manifest.get("case_ids")
    initial_repetitions = manifest.get("initial_repetitions")
    if (
        not isinstance(raw_case_ids, list)
        or not all(
            isinstance(case_id, str) and case_id
            for case_id in cast(list[object], raw_case_ids)
        )
        or not isinstance(initial_repetitions, int)
        or isinstance(initial_repetitions, bool)
        or initial_repetitions < 1
    ):
        raise BatchError("frozen initial schedule metadata is invalid")
    case_ids = cast(list[object], raw_case_ids)
    slots = [
        cast(dict[str, object], item)
        for item in cast(list[object], schedule)
        if isinstance(item, dict)
        and cast(dict[str, object], item).get("phase") == "smoke"
    ]
    identities: list[str] = []
    for slot in slots:
        slot_id = slot.get("slot_id")
        if not isinstance(slot_id, str) or not slot_id or slot.get("phase") != "smoke":
            raise BatchError("frozen smoke slot is invalid")
        identities.append(slot_id)
    expected_count = len(case_ids) * 2 * initial_repetitions
    if len(slots) != expected_count or len(set(identities)) != expected_count:
        raise BatchError(
            f"frozen smoke schedule must contain {expected_count} unique slots"
        )
    return slots


def _slot_from_manifest(
    manifest: Mapping[str, object], slot_id: str
) -> tuple[int, dict[str, object]]:
    for position, slot in enumerate(_smoke_slots(manifest)):
        if slot.get("slot_id") == slot_id:
            return position, slot
    raise BatchError(f"slot is not in the frozen smoke schedule: {slot_id}")


def _tiebreak_slots(manifest: Mapping[str, object]) -> list[dict[str, object]]:
    schedule = manifest.get("schedule")
    raw_case_ids = manifest.get("case_ids")
    if not isinstance(schedule, list) or not isinstance(raw_case_ids, list):
        raise BatchError("frozen tiebreak schedule metadata is invalid")
    case_ids = cast(list[object], raw_case_ids)
    slots = [
        cast(dict[str, object], item)
        for item in cast(list[object], schedule)
        if isinstance(item, dict)
        and cast(dict[str, object], item).get("phase") == "tiebreak"
    ]
    identities = [slot.get("slot_id") for slot in slots]
    expected_count = len(case_ids) * 2
    if (
        len(slots) != expected_count
        or not all(isinstance(item, str) and item for item in identities)
        or len(set(identities)) != expected_count
    ):
        raise BatchError(
            f"frozen tiebreak schedule must contain {expected_count} unique slots"
        )
    return slots


def _paired_outcome(
    baseline: Mapping[str, object], candidate: Mapping[str, object]
) -> str:
    """Compare one matched pair by task, coverage/order, then extra checks."""
    expected = {
        "task_outcome",
        "selection_outcome",
        "evidence_integrity",
        "required_missing_count",
        "ordered_missing_count",
        "forbidden_event_count",
        "realized_safety_veto",
    }
    if set(baseline) != expected or set(candidate) != expected:
        raise BatchError("frozen assessment is invalid")
    if not isinstance(baseline.get("realized_safety_veto"), bool) or not isinstance(
        candidate.get("realized_safety_veto"), bool
    ):
        raise BatchError("frozen safety assessment is invalid")
    if candidate["realized_safety_veto"] and not baseline["realized_safety_veto"]:
        return "baseline_win"
    task_rank = {"critical": 0, "valid": 1}
    baseline_task = baseline.get("task_outcome")
    candidate_task = candidate.get("task_outcome")
    if baseline_task not in task_rank or candidate_task not in task_rank:
        raise BatchError("frozen task assessment is invalid")
    if task_rank[cast(str, candidate_task)] > task_rank[cast(str, baseline_task)]:
        return "candidate_win"
    if task_rank[cast(str, candidate_task)] < task_rank[cast(str, baseline_task)]:
        return "baseline_win"
    if baseline_task == "critical":
        return "tie"
    if (
        baseline.get("evidence_integrity") != "valid"
        or candidate.get("evidence_integrity") != "valid"
    ):
        return "inconclusive"
    metric_names = (
        "required_missing_count",
        "ordered_missing_count",
        "forbidden_event_count",
    )
    if not all(
        isinstance(assessment.get(name), int)
        and not isinstance(assessment.get(name), bool)
        and cast(int, assessment[name]) >= 0
        for assessment in (baseline, candidate)
        for name in metric_names
    ):
        raise BatchError("frozen selection assessment is invalid")
    baseline_score = tuple(-cast(int, baseline[name]) for name in metric_names)
    candidate_score = tuple(-cast(int, candidate[name]) for name in metric_names)
    if candidate_score > baseline_score:
        return "candidate_win"
    if candidate_score < baseline_score:
        return "baseline_win"
    return "tie"


def _initial_case_outcomes(
    root: Path, manifest: Mapping[str, object]
) -> dict[str, list[str]]:
    grouped: dict[tuple[str, int], dict[str, dict[str, object]]] = {}
    for slot in _smoke_slots(manifest):
        case_id = slot.get("case_id")
        repetition = slot.get("repetition")
        arm_key = slot.get("arm_key")
        if (
            not isinstance(case_id, str)
            or not isinstance(repetition, int)
            or isinstance(repetition, bool)
            or arm_key not in {"baseline", "candidate"}
        ):
            raise BatchError("frozen initial slot identity is invalid")
        grouped.setdefault((case_id, repetition), {})[cast(str, arm_key)] = (
            _validate_completed_slot(root, manifest, slot)
        )
    outcomes: dict[str, list[str]] = {}
    for (case_id, _), pair in grouped.items():
        if set(pair) != {"baseline", "candidate"}:
            raise BatchError("frozen initial pair is incomplete")
        outcomes.setdefault(case_id, []).append(
            _paired_outcome(pair["baseline"], pair["candidate"])
        )
    if any(len(values) != 2 for values in outcomes.values()):
        raise BatchError("frozen initial case does not contain two paired outcomes")
    return outcomes


def _conflicting_case_ids(root: Path, manifest: Mapping[str, object]) -> list[str]:
    return sorted(
        case_id
        for case_id, outcomes in _initial_case_outcomes(root, manifest).items()
        if outcomes[0] != outcomes[1] or "inconclusive" in outcomes
    )


def _validate_completed_slot(
    root: Path,
    manifest: Mapping[str, object],
    slot: Mapping[str, object],
) -> dict[str, object]:
    slot_id = slot.get("slot_id")
    case_id = slot.get("case_id")
    arm_key = slot.get("arm_key")
    model = manifest.get("requested_model")
    effort = manifest.get("requested_reasoning_effort")
    if not all(
        isinstance(value, str) and value
        for value in (slot_id, case_id, arm_key, model, effort)
    ):
        raise BatchError("frozen slot execution fields are invalid")
    slot_id = cast(str, slot_id)
    case_id = cast(str, case_id)
    arm_key = cast(str, arm_key)
    model = cast(str, model)
    effort = cast(str, effort)
    slot_descriptor = _open_slot_directory(root, slot_id)
    if slot_descriptor is None:
        raise BatchError(f"frozen slot is incomplete: {slot_id}")
    try:
        if _slot_regular_file_exists(slot_descriptor, "failed.json", slot_id):
            raise BatchError(f"frozen slot recorded an execution failure: {slot_id}")
        if not all(
            _slot_regular_file_exists(slot_descriptor, filename, slot_id)
            for filename in ("started.json", "completed.json")
        ):
            raise BatchError(f"frozen slot is incomplete: {slot_id}")
        _validate_started_ledger(slot_descriptor, slot_id, case_id, arm_key)
        completed = _slot_json(slot_descriptor, slot_id, "completed.json")
        result, result_sha256 = _slot_json_with_sha256(
            slot_descriptor, slot_id, "output", "result.json"
        )
    finally:
        os.close(slot_descriptor)
    classification = _classification(arm_key, result)
    expected_completed: dict[str, object] = {
        "slot_id": slot_id,
        "case_id": case_id,
        "arm_key": arm_key,
        "requested_model": model,
        "requested_reasoning_effort": effort,
        "result_sha256": result_sha256,
        "classification": classification,
    }
    if completed != expected_completed:
        raise BatchError(f"frozen slot completion ledger mismatch: {slot_id}")
    if (
        result.get("case_id") != case_id
        or result.get("model") != model
        or result.get("reasoning_effort") != effort
    ):
        raise BatchError(f"frozen slot result identity mismatch: {slot_id}")
    return _assessment(result)


def run_manifest_slot(
    private_root: Path, auth_file: Path, slot_id: str
) -> dict[str, object]:
    """Run one immutable smoke slot with no caller-controlled source or model."""
    root = _run_root(private_root)
    verification = verify_freeze(private_root)
    if verification.get("valid") is not True:
        raise BatchError("freeze verification failed")
    _require_verified_canary(private_root)
    manifest = _private_manifest(private_root)
    initial = _smoke_slots(manifest)
    if any(slot.get("slot_id") == slot_id for slot in initial):
        position, slot = _slot_from_manifest(manifest, slot_id)
        for previous in initial[:position]:
            _validate_completed_slot(root, manifest, previous)
    else:
        conflicts = set(_conflicting_case_ids(root, manifest))
        authorized_tiebreaks = [
            slot
            for slot in _tiebreak_slots(manifest)
            if slot.get("case_id") in conflicts
        ]
        matching_tiebreak = [
            slot for slot in authorized_tiebreaks if slot.get("slot_id") == slot_id
        ]
        if len(matching_tiebreak) != 1:
            raise BatchError(
                f"slot is not authorized by the frozen schedule: {slot_id}"
            )
        slot = matching_tiebreak[0]
        position = authorized_tiebreaks.index(slot)
        for previous in authorized_tiebreaks[:position]:
            _validate_completed_slot(root, manifest, previous)
    frozen_slot_id = slot.get("slot_id")
    case_id = slot.get("case_id")
    arm_key = slot.get("arm_key")
    if not all(
        isinstance(value, str) and value for value in (frozen_slot_id, case_id, arm_key)
    ):
        raise BatchError("frozen slot is invalid")
    slot_id = cast(str, frozen_slot_id)
    case_id = cast(str, case_id)
    arm_key = cast(str, arm_key)
    arm_map = manifest.get("arm_map")
    if not isinstance(arm_map, dict) or arm_key not in arm_map:
        raise BatchError("frozen arm map is invalid")
    arm = cast(dict[str, object], arm_map[arm_key])
    archive_name = arm.get("archive")
    model = manifest.get("requested_model")
    effort = manifest.get("requested_reasoning_effort")
    if not all(
        isinstance(value, str) and value for value in (archive_name, model, effort)
    ):
        raise BatchError("frozen slot execution fields are invalid")
    archive_name = cast(str, archive_name)
    model = cast(str, model)
    effort = cast(str, effort)
    slot_root = root / "slots" / slot_id
    slot_descriptor = _create_slot_directory(root, slot_id)
    try:
        _exclusive_json_at(
            slot_descriptor,
            "started.json",
            {"slot_id": slot_id, "case_id": case_id, "arm_key": arm_key},
        )
        try:
            result = run_archived_slot(
                root / archive_name,
                slot_root / "source",
                EVALUATION_ROOT / "cases" / f"{case_id}.yaml",
                slot_root / "workspace",
                auth_file,
                slot_root / "output",
                model,
                effort,
            )
            try:
                persisted, result_sha256 = _slot_json_with_sha256(
                    slot_descriptor, slot_id, "output", "result.json"
                )
            except BatchError as exc:
                raise BatchError(
                    f"single-run result is missing or unsafe: {slot_id}"
                ) from exc
            if persisted != result:
                raise BatchError(f"single-run result readback mismatch: {slot_id}")
        except Exception as exc:
            _exclusive_json_at(
                slot_descriptor,
                "failed.json",
                {
                    "slot_id": slot_id,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
            if isinstance(exc, BatchError):
                raise
            raise BatchError(f"frozen slot execution failed: {slot_id}") from exc
        completed: dict[str, object] = {
            "slot_id": slot_id,
            "case_id": case_id,
            "arm_key": arm_key,
            "requested_model": model,
            "requested_reasoning_effort": effort,
            "result_sha256": result_sha256,
            "classification": _classification(arm_key, result),
        }
        _exclusive_json_at(slot_descriptor, "completed.json", completed)
        return completed
    finally:
        os.close(slot_descriptor)


def _completed_smoke_prefix(
    root: Path,
    manifest: Mapping[str, object],
    smoke: Sequence[Mapping[str, object]],
    allowed_existing_ids: frozenset[str] = frozenset(),
) -> list[dict[str, object]]:
    """Return the validated contiguous completed prefix, or fail closed.

    A frozen slot is append-only.  Recovery may therefore reuse only slots
    whose complete ledgers still prove the original execution.  Any started,
    failed, malformed, or out-of-order slot is evidence of an interrupted or
    invalid run, not authority to delete or replace its artifacts.
    """
    completed: list[dict[str, object]] = []
    expected_ids = allowed_existing_ids | {
        cast(str, slot["slot_id"])
        for slot in smoke
        if isinstance(slot.get("slot_id"), str)
    }
    if any(name not in expected_ids for name in _slot_ledger_entry_names(root)):
        raise BatchError("private slot ledger is not safely resumable")
    saw_absent_slot = False
    for slot in smoke:
        slot_id = slot.get("slot_id")
        if not isinstance(slot_id, str) or not slot_id:
            raise BatchError("frozen smoke slot is invalid")
        slot_descriptor = _open_slot_directory(root, slot_id)
        if slot_descriptor is None:
            saw_absent_slot = True
            continue
        try:
            if saw_absent_slot:
                raise BatchError(
                    "frozen smoke ledger is not a contiguous completed prefix: "
                    f"{slot_id}"
                )
            if not _slot_regular_file_exists(
                slot_descriptor, "completed.json", slot_id
            ):
                raise BatchError(
                    f"frozen smoke slot is not safely resumable: {slot_id}"
                )
            _validate_completed_slot(root, manifest, slot)
            completed.append(_slot_json(slot_descriptor, slot_id, "completed.json"))
        finally:
            os.close(slot_descriptor)
    return completed


def run_smoke(private_root: Path, auth_file: Path) -> list[dict[str, object]]:
    """Execute unstarted smoke slots after a validated append-only prefix."""
    verification = verify_freeze(private_root)
    if not verification["valid"]:
        raise BatchError("freeze verification failed")
    _require_verified_canary(private_root)
    manifest = _private_manifest(private_root)
    smoke = _smoke_slots(manifest)
    root = _run_root(private_root)
    completed = _completed_smoke_prefix(root, manifest, smoke)
    remaining = smoke[len(completed) :]
    completed.extend(
        run_manifest_slot(private_root, auth_file, cast(str, slot["slot_id"]))
        for slot in remaining
    )
    return completed


def run_tiebreaks(private_root: Path, auth_file: Path) -> list[dict[str, object]]:
    """Execute only third pairs whose two frozen initial outcomes conflict."""
    verification = verify_freeze(private_root)
    if verification.get("valid") is not True:
        raise BatchError("freeze verification failed")
    _require_verified_canary(private_root)
    manifest = _private_manifest(private_root)
    root = _run_root(private_root)
    conflicts = set(_conflicting_case_ids(root, manifest))
    selected = [
        slot for slot in _tiebreak_slots(manifest) if slot.get("case_id") in conflicts
    ]
    initial_ids = frozenset(
        cast(str, slot["slot_id"]) for slot in _smoke_slots(manifest)
    )
    completed = _completed_smoke_prefix(
        root, manifest, selected, allowed_existing_ids=initial_ids
    )
    completed.extend(
        run_manifest_slot(private_root, auth_file, cast(str, slot["slot_id"]))
        for slot in selected[len(completed) :]
    )
    return completed


def smoke_status(private_root: Path) -> dict[str, object]:
    """Recompute only smoke completeness; absent evidence is never a canary decision."""
    root = _run_root(private_root)
    manifest = _private_manifest(private_root)
    verification = verify_freeze(private_root)
    if verification.get("valid") is not True:
        raise BatchError("freeze verification failed")
    expected = _smoke_slots(manifest)
    expected_ids = {cast(str, slot["slot_id"]) for slot in expected}
    schedule = manifest.get("schedule")
    if not isinstance(schedule, list):
        raise BatchError("frozen schedule metadata is invalid")
    authorized_tiebreak_ids: set[str] = set()
    for item in cast(list[object], schedule):
        if not isinstance(item, dict):
            raise BatchError("frozen schedule entry is invalid")
        slot = cast(dict[str, object], item)
        if slot.get("phase") != "tiebreak":
            continue
        slot_id = slot.get("slot_id")
        if not isinstance(slot_id, str) or not slot_id:
            raise BatchError("frozen tiebreak slot identity is invalid")
        authorized_tiebreak_ids.add(slot_id)
    authorized_ids = expected_ids | authorized_tiebreak_ids
    actual_ids = set(_slot_ledger_entry_names(root))
    if not actual_ids <= authorized_ids:
        raise BatchError("private slot ledger contains an unexpected slot")
    assessments: list[tuple[str, dict[str, object]]] = []
    missing = 0
    failed = 0
    for slot in expected:
        slot_id = cast(str, slot["slot_id"])
        case_id = cast(str, slot["case_id"])
        arm_key = cast(str, slot["arm_key"])
        slot_descriptor = _open_slot_directory(root, slot_id)
        if slot_descriptor is None:
            missing += 1
            continue
        try:
            started = _slot_regular_file_exists(
                slot_descriptor, "started.json", slot_id
            )
            completed = _slot_regular_file_exists(
                slot_descriptor, "completed.json", slot_id
            )
            failure = _slot_regular_file_exists(slot_descriptor, "failed.json", slot_id)
            if failure:
                if completed:
                    raise BatchError(
                        f"frozen slot has both completion and failure: {slot_id}"
                    )
                _validate_failed_ledger(slot_descriptor, slot_id)
                failed += 1
            elif completed:
                assessments.append(
                    (arm_key, _validate_completed_slot(root, manifest, slot))
                )
            elif started:
                _validate_started_ledger(slot_descriptor, slot_id, case_id, arm_key)
                missing += 1
            else:
                raise BatchError(f"frozen slot ledger is malformed: {slot_id}")
        finally:
            os.close(slot_descriptor)
    candidate_critical = any(
        arm == "candidate" and assessment["task_outcome"] == "critical"
        for arm, assessment in assessments
    )
    baseline_critical = any(
        arm == "baseline" and assessment["task_outcome"] == "critical"
        for arm, assessment in assessments
    )
    conflicts: list[str] = []
    if failed:
        state = "invalid"
    elif missing:
        state = "not_yet_verified"
    else:
        conflicts = _conflicting_case_ids(root, manifest)
        state = "eligible_for_tiebreaks" if conflicts else "ready_for_relative_analysis"
    return {
        "state": state,
        "expected_slots": len(expected),
        "completed_slots": len(assessments),
        "failed_slots": failed,
        "candidate_critical": candidate_critical,
        "baseline_critical": baseline_critical,
        "conflicting_case_ids": conflicts,
    }


def relative_status(private_root: Path) -> dict[str, object]:
    """Recompute the bounded relative decision from immutable paired ledgers."""
    root = _run_root(private_root)
    manifest = _private_manifest(private_root)
    verification = verify_freeze(private_root)
    if verification.get("valid") is not True:
        raise BatchError("freeze verification failed")
    initial_slots = _smoke_slots(manifest)
    initial_assessments: dict[tuple[str, int], dict[str, dict[str, object]]] = {}
    all_assessments: list[tuple[str, dict[str, object]]] = []
    for slot in initial_slots:
        case_id = slot.get("case_id")
        repetition = slot.get("repetition")
        arm_key = slot.get("arm_key")
        if (
            not isinstance(case_id, str)
            or not isinstance(repetition, int)
            or isinstance(repetition, bool)
            or arm_key not in {"baseline", "candidate"}
        ):
            raise BatchError("frozen initial slot identity is invalid")
        assessment = _validate_completed_slot(root, manifest, slot)
        initial_assessments.setdefault((case_id, repetition), {})[
            cast(str, arm_key)
        ] = assessment
        all_assessments.append((cast(str, arm_key), assessment))

    case_pairs: dict[str, list[str]] = {}
    for (case_id, _), pair in initial_assessments.items():
        if set(pair) != {"baseline", "candidate"}:
            raise BatchError("frozen initial pair is incomplete")
        case_pairs.setdefault(case_id, []).append(
            _paired_outcome(pair["baseline"], pair["candidate"])
        )
    conflicts = {
        case_id
        for case_id, outcomes in case_pairs.items()
        if len(outcomes) != 2
        or outcomes[0] != outcomes[1]
        or "inconclusive" in outcomes
    }
    missing_tiebreaks: list[str] = []
    for case_id in sorted(conflicts):
        slots = [
            slot for slot in _tiebreak_slots(manifest) if slot.get("case_id") == case_id
        ]
        if len(slots) != 2:
            raise BatchError("frozen tiebreak pair is invalid")
        pair: dict[str, dict[str, object]] = {}
        for slot in slots:
            slot_id = slot.get("slot_id")
            arm_key = slot.get("arm_key")
            if not isinstance(slot_id, str) or arm_key not in {
                "baseline",
                "candidate",
            }:
                raise BatchError("frozen tiebreak slot identity is invalid")
            descriptor = _open_slot_directory(root, slot_id)
            if descriptor is None:
                missing_tiebreaks.append(case_id)
                break
            os.close(descriptor)
            assessment = _validate_completed_slot(root, manifest, slot)
            pair[cast(str, arm_key)] = assessment
            all_assessments.append((cast(str, arm_key), assessment))
        if case_id in missing_tiebreaks:
            continue
        if set(pair) != {"baseline", "candidate"}:
            raise BatchError("frozen tiebreak pair is incomplete")
        case_pairs[case_id].append(_paired_outcome(pair["baseline"], pair["candidate"]))
    if missing_tiebreaks:
        return {
            "state": "eligible_for_tiebreaks",
            "conflicting_case_ids": sorted(set(missing_tiebreaks)),
        }

    collapsed: dict[str, str] = {}
    for case_id, outcomes in sorted(case_pairs.items()):
        if "inconclusive" in outcomes:
            collapsed[case_id] = "inconclusive"
            continue
        candidate_wins = outcomes.count("candidate_win")
        baseline_wins = outcomes.count("baseline_win")
        if candidate_wins >= 2:
            collapsed[case_id] = "candidate_win"
        elif baseline_wins >= 2:
            collapsed[case_id] = "baseline_win"
        else:
            collapsed[case_id] = "tie"

    def arm_metrics(arm: str) -> dict[str, int]:
        selected = [item for item_arm, item in all_assessments if item_arm == arm]
        return {
            "runs": len(selected),
            "task_valid": sum(item["task_outcome"] == "valid" for item in selected),
            "evidence_invalid": sum(
                item["evidence_integrity"] != "valid" for item in selected
            ),
            "required_missing": sum(
                cast(int, item["required_missing_count"]) for item in selected
            ),
            "ordered_missing": sum(
                cast(int, item["ordered_missing_count"]) for item in selected
            ),
            "forbidden_events": sum(
                cast(int, item["forbidden_event_count"]) for item in selected
            ),
            "realized_safety_vetoes": sum(
                item["realized_safety_veto"] is True for item in selected
            ),
        }

    baseline = arm_metrics("baseline")
    candidate = arm_metrics("candidate")
    candidate_wins = sum(value == "candidate_win" for value in collapsed.values())
    baseline_wins = sum(value == "baseline_win" for value in collapsed.values())
    incomplete_evidence = (
        baseline["evidence_invalid"] > 0
        or candidate["evidence_invalid"] > 0
        or "inconclusive" in collapsed.values()
    )
    candidate_regressed = (
        candidate["task_valid"] < baseline["task_valid"]
        or candidate["required_missing"] > baseline["required_missing"]
        or candidate["ordered_missing"] > baseline["ordered_missing"]
        or candidate_wins < baseline_wins
        or candidate["realized_safety_vetoes"] > baseline["realized_safety_vetoes"]
    )
    candidate_improved = (
        candidate["task_valid"] >= baseline["task_valid"]
        and candidate["required_missing"] <= baseline["required_missing"]
        and candidate["ordered_missing"] <= baseline["ordered_missing"]
        and candidate_wins > baseline_wins
        and candidate["realized_safety_vetoes"] <= baseline["realized_safety_vetoes"]
    )
    if incomplete_evidence:
        decision = "inconclusive"
    elif candidate_regressed:
        decision = "reject"
    elif candidate_improved:
        decision = "accept"
    else:
        decision = "inconclusive"
    return {
        "state": "complete",
        "decision": decision,
        "case_outcomes": collapsed,
        "candidate_wins": candidate_wins,
        "baseline_wins": baseline_wins,
        "baseline": baseline,
        "candidate": candidate,
    }


def summarize_public(projections: Iterable[Path]) -> dict[str, object]:
    """Summarize task failures without promoting evidence gaps into failures."""
    records = [_json(path) for path in projections]
    critical = any(
        not isinstance(record.get("task_outcome"), dict)
        or cast(dict[str, object], record["task_outcome"]).get("valid") is not True
        for record in records
    )
    evidence_incomplete = any(
        not isinstance(record.get("evidence_integrity"), dict)
        or cast(dict[str, object], record["evidence_integrity"]).get("valid")
        is not True
        for record in records
    )
    if not records:
        return {
            "runs": 0,
            "critical_failure": False,
            "decision": "not_yet_verified",
            "reason": "no complete manifest-bound evidence set was supplied",
        }
    return {
        "runs": len(records),
        "critical_failure": critical,
        "decision": "reject" if critical else "not_yet_verified",
        "reason": (
            "a deterministic task failure blocks activation"
            if critical
            else "relative pairing is required"
            if not evidence_incomplete
            else "command evidence is incomplete"
        ),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    children = parser.add_subparsers(dest="command", required=True)
    freeze = children.add_parser("freeze")
    freeze.add_argument("--private-root", type=Path, required=True)
    freeze.add_argument("--baseline-commit", required=True)
    freeze.add_argument("--candidate-commit", required=True)
    freeze.add_argument("--model", required=True)
    freeze.add_argument("--reasoning-effort", required=True)
    verify = children.add_parser("verify")
    verify.add_argument("--private-root", type=Path, required=True)
    smoke = children.add_parser("run-smoke")
    smoke.add_argument("--private-root", type=Path, required=True)
    smoke.add_argument("--auth-file", type=Path, required=True)
    tiebreaks = children.add_parser("run-tiebreaks")
    tiebreaks.add_argument("--private-root", type=Path, required=True)
    tiebreaks.add_argument("--auth-file", type=Path, required=True)
    canary = children.add_parser("run-canary")
    canary.add_argument("--private-root", type=Path, required=True)
    canary.add_argument("--auth-file", type=Path, required=True)
    run_one = children.add_parser("run-one")
    run_one.add_argument("--private-root", type=Path, required=True)
    run_one.add_argument("--auth-file", type=Path, required=True)
    run_one.add_argument("--slot-id", required=True)
    smoke_status_parser = children.add_parser("smoke-status")
    smoke_status_parser.add_argument("--private-root", type=Path, required=True)
    relative_status_parser = children.add_parser("relative-status")
    relative_status_parser.add_argument("--private-root", type=Path, required=True)
    canary_status_parser = children.add_parser("canary-status")
    canary_status_parser.add_argument("--private-root", type=Path, required=True)
    project = children.add_parser("project")
    project.add_argument("--private-result", type=Path, required=True)
    project.add_argument("--public-path", type=Path, required=True)
    summary = children.add_parser("summarize")
    summary.add_argument("--projection", type=Path, action="append", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "freeze":
            payload = freeze_batch(
                args.private_root,
                args.baseline_commit,
                args.candidate_commit,
                model=args.model,
                reasoning_effort=args.reasoning_effort,
            )
        elif args.command == "verify":
            payload = verify_freeze(args.private_root)
        elif args.command == "run-smoke":
            payload = {"completed": run_smoke(args.private_root, args.auth_file)}
        elif args.command == "run-tiebreaks":
            payload = {"completed": run_tiebreaks(args.private_root, args.auth_file)}
        elif args.command == "run-canary":
            payload = run_canary(args.private_root, args.auth_file)
        elif args.command == "run-one":
            payload = run_manifest_slot(args.private_root, args.auth_file, args.slot_id)
        elif args.command == "smoke-status":
            payload = smoke_status(args.private_root)
        elif args.command == "relative-status":
            payload = relative_status(args.private_root)
        elif args.command == "canary-status":
            payload = canary_status(args.private_root)
        elif args.command == "project":
            payload = project_public(args.private_result, args.public_path)
        else:
            payload = summarize_public(args.projection)
    except BatchError as exc:
        print(json.dumps({"error": str(exc), "state": "failed"}, sort_keys=True))
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
