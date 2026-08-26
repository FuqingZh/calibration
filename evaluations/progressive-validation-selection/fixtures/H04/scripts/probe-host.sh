#!/usr/bin/env bash
set -u
run_id="${CALIBRATION_EVAL_RUN_ID:?CALIBRATION_EVAL_RUN_ID is required}"
printf 'CALIBRATION_CHECK_EVENT {"schema_version":1,"run_id":"%s","check_id":"host_probe","phase":"begin","exit_code":null,"covered_seam":"host deployment endpoint"}\n' "$run_id"
status=75
printf 'CALIBRATION_CHECK_EVENT {"schema_version":1,"run_id":"%s","check_id":"host_probe","phase":"end","exit_code":%s,"covered_seam":"host deployment endpoint"}\n' "$run_id" "$status"
exit "$status"
