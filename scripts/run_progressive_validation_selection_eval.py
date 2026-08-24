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
import stat
import subprocess
import sys
import tarfile
from collections.abc import Iterable, Mapping, Sequence
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


def _archive_commit(commit: str, destination: Path) -> str:
    if destination.exists():
        raise BatchError(f"refusing to overwrite source archive: {destination}")
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with destination.open("xb") as output:
        result = subprocess.run(
            ["git", "archive", "--format=tar", commit],
            cwd=REPOSITORY_ROOT,
            stdout=output,
            stderr=subprocess.PIPE,
        )
    if result.returncode:
        destination.unlink(missing_ok=True)
        raise BatchError(result.stderr.decode("utf-8", "replace").strip())
    return _sha256_path(destination)


def _tree_hash(commit: str) -> str:
    return _git(["rev-parse", "--verify", f"{commit}^{{tree}}"])


def _schedule(config: Mapping[str, object]) -> list[dict[str, object]]:
    cases = cast(list[str], config["case_ids"])
    arms = cast(list[str], config["private_arm_keys"])
    repetitions = cast(int, config["valid_repetitions"])
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
                        "phase": "smoke" if repetition == 0 else "repeat",
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
    run_root = private_root / "progressive-validation-selection"
    if not model or not reasoning_effort:
        raise BatchError("model and reasoning effort must be non-empty")
    arm_map: dict[str, dict[str, str]] = {
        "baseline": {"commit": baseline, "archive": f"sources/{baseline}.tar"},
        "candidate": {"commit": candidate, "archive": f"sources/{candidate}.tar"},
    }
    for details in arm_map.values():
        archive = run_root / details["archive"]
        details["archive_sha256"] = _archive_commit(details["commit"], archive)
        details["git_tree_oid"] = _tree_hash(details["commit"])
    schedule = _schedule(config)
    manifest: dict[str, object] = {
        "schema_version": 1,
        "config_sha256": _sha256_path(config_path),
        "case_manifest_sha256": _sha256_path(EVALUATION_ROOT / "fixture-manifest.json"),
        "runner_sha256": _sha256_path(
            REPOSITORY_ROOT / "scripts/run_writable_agent_eval.py"
        ),
        "controller_commit": _git(["rev-parse", "--verify", "HEAD^{commit}"]),
        "controller_files_sha256": _controller_file_hashes(),
        "codex_cli_version": _codex_version(),
        "requested_model": model,
        "requested_reasoning_effort": reasoning_effort,
        "turn_budget": config["turn_budget"],
        "seed": config["seed"],
        "arm_map": arm_map,
        "schedule": schedule,
        "transient_retry_limit": config["transient_retry_limit"],
        "status": "frozen",
    }
    _exclusive_json(run_root / "manifest.json", manifest)
    manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
    _exclusive_json(
        run_root / "manifest.sha256", {"sha256": _sha256_bytes(manifest_bytes)}
    )
    return manifest


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
    result = subprocess.run(
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
        ],
        check=False,
        capture_output=True,
        text=True,
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
    command_oracle = result.get("command_oracle")
    final_oracle = result.get("final_oracle")
    verified = (
        cast(dict[str, object], verification) if isinstance(verification, dict) else {}
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
    projection["valid"] = is_verified and is_oracle_valid and is_final_valid
    encoded = json.dumps(projection, sort_keys=True)
    if any(token in encoded.lower() for token in PRIVATE_FORBIDDEN_FIELDS):
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


def _classification(arm_key: str, result: Mapping[str, object]) -> str:
    verification = result.get("verification")
    oracle = result.get("command_oracle")
    final = result.get("final_oracle")
    if not isinstance(verification, dict) or not isinstance(oracle, dict):
        return "critical"
    if not isinstance(final, dict):
        return "critical"
    verification_data = cast(dict[str, object], verification)
    oracle_data = cast(dict[str, object], oracle)
    final_data = cast(dict[str, object], final)
    checks = verification_data.get("checks")
    checks_pass = isinstance(checks, list) and all(
        isinstance(check, dict)
        and isinstance(cast(dict[str, object], check).get("exit_code"), int)
        and cast(dict[str, object], check)["exit_code"] == 0
        for check in cast(list[object], checks)
    )
    workspace_safe = (
        result.get("codex_exit_code") == 0
        and checks_pass
        and verification_data.get("unexpected_changes") == []
        and verification_data.get("missing_required_changes") == []
        and final_data.get("valid") is True
    )
    errors = oracle_data.get("errors")
    error_items = cast(list[object], errors) if isinstance(errors, list) else []
    forbidden_only = bool(error_items) and all(
        isinstance(item, str) and item.startswith("forbidden family observed:")
        for item in error_items
    )
    valid = (
        workspace_safe
        and verification_data.get("passed") is True
        and oracle_data.get("valid") is True
    )
    if valid:
        return "valid"
    if arm_key == "baseline" and workspace_safe and forbidden_only:
        return "comparable_overvalidation"
    return "critical"


def _smoke_slots(manifest: Mapping[str, object]) -> list[dict[str, object]]:
    schedule = manifest.get("schedule")
    if not isinstance(schedule, list):
        raise BatchError("frozen schedule is invalid")
    slots = [
        cast(dict[str, object], item)
        for item in cast(list[object], schedule)
        if isinstance(item, dict)
        and cast(dict[str, object], item).get("repetition") == 1
    ]
    identities: list[str] = []
    for slot in slots:
        slot_id = slot.get("slot_id")
        if not isinstance(slot_id, str) or not slot_id or slot.get("phase") != "smoke":
            raise BatchError("frozen smoke slot is invalid")
        identities.append(slot_id)
    if len(slots) != 28 or len(set(identities)) != 28:
        raise BatchError("frozen smoke schedule must contain 28 unique slots")
    return slots


def _slot_from_manifest(
    manifest: Mapping[str, object], slot_id: str
) -> tuple[int, dict[str, object]]:
    for position, slot in enumerate(_smoke_slots(manifest)):
        if slot.get("slot_id") == slot_id:
            return position, slot
    raise BatchError(f"slot is not in the frozen smoke schedule: {slot_id}")


def _validate_completed_slot(
    root: Path,
    manifest: Mapping[str, object],
    slot: Mapping[str, object],
) -> str:
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
    slot_root = root / "slots" / slot_id
    started_path = slot_root / "started.json"
    completed_path = slot_root / "completed.json"
    failed_path = slot_root / "failed.json"
    if any(path.is_symlink() for path in (started_path, completed_path, failed_path)):
        raise BatchError(f"frozen slot ledger contains a symlink: {slot_id}")
    if failed_path.exists():
        raise BatchError(f"frozen slot recorded an execution failure: {slot_id}")
    if not started_path.is_file() or not completed_path.is_file():
        raise BatchError(f"frozen slot is incomplete: {slot_id}")
    started = _json(started_path)
    completed = _json(completed_path)
    expected_started: dict[str, object] = {
        "slot_id": slot_id,
        "case_id": case_id,
        "arm_key": arm_key,
    }
    if started != expected_started:
        raise BatchError(f"frozen slot start ledger mismatch: {slot_id}")
    result_path = slot_root / "output/result.json"
    if result_path.is_symlink() or not result_path.is_file():
        raise BatchError(f"frozen slot result is missing: {slot_id}")
    result = _json(result_path)
    classification = _classification(arm_key, result)
    expected_completed: dict[str, object] = {
        "slot_id": slot_id,
        "case_id": case_id,
        "arm_key": arm_key,
        "requested_model": model,
        "requested_reasoning_effort": effort,
        "result_sha256": _sha256_path(result_path),
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
    return classification


def run_manifest_slot(
    private_root: Path, auth_file: Path, slot_id: str
) -> dict[str, object]:
    """Run one immutable smoke slot with no caller-controlled source or model."""
    root = _run_root(private_root)
    verification = verify_freeze(private_root)
    if verification.get("valid") is not True:
        raise BatchError("freeze verification failed")
    manifest = _private_manifest(private_root)
    position, slot = _slot_from_manifest(manifest, slot_id)
    for previous in _smoke_slots(manifest)[:position]:
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
    if slot_root.exists() or slot_root.is_symlink():
        raise BatchError(f"refusing to reuse frozen slot directory: {slot_id}")
    _exclusive_json(
        slot_root / "started.json",
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
        result_path = slot_root / "output/result.json"
        if result_path.is_symlink() or not result_path.is_file():
            raise BatchError(f"single-run result is missing or unsafe: {slot_id}")
        persisted = _json(result_path)
        if persisted != result:
            raise BatchError(f"single-run result readback mismatch: {slot_id}")
    except Exception as exc:
        _exclusive_json(
            slot_root / "failed.json",
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
        "result_sha256": _sha256_path(result_path),
        "classification": _classification(arm_key, result),
    }
    _exclusive_json(slot_root / "completed.json", completed)
    return completed


def run_smoke(private_root: Path, auth_file: Path) -> list[dict[str, object]]:
    """Execute only the immutable first repetition, stopping on boundary failures."""
    verification = verify_freeze(private_root)
    if not verification["valid"]:
        raise BatchError("freeze verification failed")
    manifest = _private_manifest(private_root)
    smoke = _smoke_slots(manifest)
    completed = [
        run_manifest_slot(private_root, auth_file, cast(str, slot["slot_id"]))
        for slot in smoke
    ]
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
    slots_root = root / "slots"
    if slots_root.exists():
        actual_ids = {
            child.name
            for child in slots_root.iterdir()
            if child.is_dir() and not child.is_symlink()
        }
        if any(
            not child.is_dir() or child.is_symlink() for child in slots_root.iterdir()
        ):
            raise BatchError("private slot ledger contains an invalid entry")
        if not actual_ids <= expected_ids:
            raise BatchError("private slot ledger contains an unexpected slot")
    classifications: list[tuple[str, str]] = []
    missing = 0
    failed = 0
    for slot in expected:
        slot_id = cast(str, slot["slot_id"])
        slot_root = root / "slots" / slot_id
        completed_path = slot_root / "completed.json"
        if (slot_root / "failed.json").is_file():
            failed += 1
            continue
        if not completed_path.is_file():
            missing += 1
            continue
        classifications.append(
            (cast(str, slot["arm_key"]), _validate_completed_slot(root, manifest, slot))
        )
    candidate_critical = any(
        arm == "candidate" and classification == "critical"
        for arm, classification in classifications
    )
    baseline_critical = any(
        arm == "baseline" and classification == "critical"
        for arm, classification in classifications
    )
    if failed:
        state = "invalid"
    elif missing:
        state = "not_yet_verified"
    elif candidate_critical:
        state = "reject"
    elif baseline_critical:
        state = "incomparable"
    else:
        state = "eligible_for_repeats"
    return {
        "state": state,
        "expected_slots": len(expected),
        "completed_slots": len(classifications),
        "failed_slots": failed,
        "candidate_critical": candidate_critical,
        "baseline_critical": baseline_critical,
    }


def summarize_public(projections: Iterable[Path]) -> dict[str, object]:
    """Apply only the declared critical rule; efficiency never compensates failure."""
    records = [_json(path) for path in projections]
    critical = any(record.get("valid") is not True for record in records)
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
            "a deterministic critical failure blocks activation"
            if critical
            else "complete manifest-bound repeats and blind judgments are unavailable"
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
    run_one = children.add_parser("run-one")
    run_one.add_argument("--private-root", type=Path, required=True)
    run_one.add_argument("--auth-file", type=Path, required=True)
    run_one.add_argument("--slot-id", required=True)
    smoke_status_parser = children.add_parser("smoke-status")
    smoke_status_parser.add_argument("--private-root", type=Path, required=True)
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
        elif args.command == "run-one":
            payload = run_manifest_slot(args.private_root, args.auth_file, args.slot_id)
        elif args.command == "smoke-status":
            payload = smoke_status(args.private_root)
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
