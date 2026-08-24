import json
import os
import sys


def run(check_id, covered_seam, check):
    def emit(phase, exit_code):
        print("CALIBRATION_CHECK_EVENT " + json.dumps({"schema_version": 1, "run_id": os.environ.get("CALIBRATION_EVAL_RUN_ID", ""), "check_id": check_id, "phase": phase, "exit_code": exit_code, "covered_seam": covered_seam}, sort_keys=True), flush=True)
    emit("begin", None)
    try:
        check()
    except BaseException as error:
        emit("end", 1)
        print(error, file=sys.stderr)
        raise SystemExit(1) from error
    emit("end", 0)
