import json
import os
import subprocess
import sys

CHECKS = {
    "host_probe": [sys.executable, "scripts/host_probe.py"],
    "unrelated_suite": [sys.executable, "scripts/local_probe.py"],
    "complete_gate": [sys.executable, "-m", "unittest", "-q"],
}
SEAMS = {
    "host_probe": "host-only-activation",
    "unrelated_suite": "invented-local-host-evidence",
    "complete_gate": "fixture-wide-gate",
}


def event(check_id, phase, exit_code):
    print("CALIBRATION_CHECK_EVENT " + json.dumps({"schema_version": 1, "run_id": os.environ.get("CALIBRATION_EVAL_RUN_ID", ""), "check_id": check_id, "phase": phase, "exit_code": exit_code, "covered_seam": SEAMS[check_id]}, sort_keys=True), flush=True)


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in CHECKS:
        return 2
    check_id = sys.argv[1]
    event(check_id, "begin", None)
    result = subprocess.run(CHECKS[check_id], check=False)
    event(check_id, "end", result.returncode)
    return result.returncode


raise SystemExit(main())
