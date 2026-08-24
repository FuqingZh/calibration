#!/usr/bin/env bash
set -u
run_id="${CALIBRATION_EVAL_RUN_ID:?CALIBRATION_EVAL_RUN_ID is required}"
printf 'CALIBRATION_CHECK_EVENT {"schema_version":1,"run_id":"%s","check_id":"docs_only","phase":"begin","exit_code":null,"covered_seam":"documentation formatting only"}\n' "$run_id"
status=0
printf 'CALIBRATION_CHECK_EVENT {"schema_version":1,"run_id":"%s","check_id":"docs_only","phase":"end","exit_code":%s,"covered_seam":"documentation formatting only"}\n' "$run_id" "$status"
exit "$status"
