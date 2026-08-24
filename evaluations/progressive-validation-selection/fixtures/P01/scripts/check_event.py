"""Emit evaluation check events for this fixture's agent-run commands."""

import json
import os
import sys


def emit(check_id: str, phase: str, exit_code: int | None, covered_seam: str) -> None:
    event = {
        "schema_version": 1,
        "run_id": os.environ.get("CALIBRATION_EVAL_RUN_ID", ""),
        "check_id": check_id,
        "phase": phase,
        "exit_code": exit_code,
        "covered_seam": covered_seam,
    }
    print("CALIBRATION_CHECK_EVENT " + json.dumps(event, sort_keys=True), flush=True)


def run(check_id: str, covered_seam: str, check) -> None:
    emit(check_id, "begin", None, covered_seam)
    try:
        check()
    except BaseException as error:
        emit(check_id, "end", 1, covered_seam)
        print(error, file=sys.stderr)
        raise SystemExit(1) from error
    emit(check_id, "end", 0, covered_seam)
