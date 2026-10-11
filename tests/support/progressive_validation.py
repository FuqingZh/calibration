"""Synthetic batch records with explicit minimal smoke and canary shapes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast


def batch_result(
    case_id: str = "P01",
    *,
    model: str = "frozen-model",
    effort: str = "medium",
    oracle_errors: list[str] | None = None,
    codex_exit_code: int = 0,
    final_valid: bool = True,
    required_missing: int = 0,
    ordered_missing: int = 0,
    forbidden_events: int = 0,
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
            "passed": True,
            "checks": [{"exit_code": 0}],
            "unexpected_changes": [],
            "missing_required_changes": [],
        },
        "task_outcome": {
            "valid": codex_exit_code == 0 and final_valid,
            "errors": [],
        },
        "validation_selection": {
            "enabled": True,
            "contract_satisfied": not (
                required_missing or ordered_missing or forbidden_events
            ),
            "required_covered": required_missing == 0,
            "ordered_covered": ordered_missing == 0,
            "required_missing": [
                {"family": "focused_test", "exit": "zero"}
                for _ in range(required_missing)
            ],
            "ordered_missing": [
                {"family": "focused_test", "exit": "zero"}
                for _ in range(ordered_missing)
            ],
            "forbidden_families": ["complete_gate"] if forbidden_events else [],
            "forbidden_event_count": forbidden_events,
            "observations": [],
        },
        "evidence_integrity": {"valid": oracle_valid, "errors": errors},
        "realized_safety_events": [],
        "command_oracle": {"valid": oracle_valid, "errors": errors},
        "final_oracle": {"valid": final_valid},
    }


def projection_result(case_id: str = "P01") -> dict[str, object]:
    """Retain the projection fixture's existing serialized field order."""
    result = batch_result(case_id)
    result["command_oracle"] = {"valid": True, "errors": []}
    leading = ("case_id", "model", "reasoning_effort", "elapsed_seconds")
    return {**{key: result.pop(key) for key in leading}, **result}


def smoke_result(case_id: str, *, model: str = "frozen-model") -> dict[str, object]:
    """Keep recovery inputs minimal: no elapsed time or final oracle."""
    result = batch_result(case_id, model=model)
    result.pop("elapsed_seconds")
    result.pop("final_oracle")
    result["verification"] = {"passed": True}
    result["command_oracle"] = {"valid": True, "errors": []}
    return result


def canary_result() -> dict[str, object]:
    """Include broker evidence while retaining the canary's minimal verification."""
    result = batch_result("C01")
    result.pop("elapsed_seconds")
    cast(dict[str, object], result["verification"]).pop("checks")
    result["command_oracle"] = {"valid": True, "broker_events": [{}]}
    return result


def write_manifest(root: Path, manifest: dict[str, object]) -> None:
    """Write canonical manifest bytes and their digest for synthetic batches."""
    manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
    (root / "manifest.json").write_bytes(manifest_bytes)
    digest = {"sha256": hashlib.sha256(manifest_bytes).hexdigest()}
    (root / "manifest.sha256").write_text(
        json.dumps(digest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_completed_slot(
    root: Path,
    manifest: dict[str, object],
    slot: dict[str, object],
    result: dict[str, object],
    *,
    classification: str,
) -> tuple[Path, dict[str, object]]:
    """Persist synthetic slot records; each test supplies its classification policy."""
    slot_id = cast(str, slot["slot_id"])
    started = {
        "slot_id": slot_id,
        "case_id": slot["case_id"],
        "arm_key": slot["arm_key"],
    }
    slot_root = root / "slots" / slot_id
    output = slot_root / "output"
    output.mkdir(parents=True)
    result_path = output / "result.json"
    result_path.write_text(json.dumps(result), encoding="utf-8")
    (slot_root / "started.json").write_text(json.dumps(started), encoding="utf-8")
    completed = {
        **started,
        "requested_model": manifest["requested_model"],
        "requested_reasoning_effort": manifest["requested_reasoning_effort"],
        "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
        "classification": classification,
    }
    (slot_root / "completed.json").write_text(json.dumps(completed), encoding="utf-8")
    return slot_root, completed
