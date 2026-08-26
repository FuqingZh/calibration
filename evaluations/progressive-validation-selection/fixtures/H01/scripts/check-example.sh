#!/usr/bin/env bash
set -u
run_id="${CALIBRATION_EVAL_RUN_ID:?CALIBRATION_EVAL_RUN_ID is required}"
printf 'CALIBRATION_CHECK_EVENT {"schema_version":1,"run_id":"%s","check_id":"example_check","phase":"begin","exit_code":null,"covered_seam":"README shell example and its observable output"}\n' "$run_id"
if grep -Fqx "printf 'hello, calibration\\n'" README.md; then
  status=0
else
  status=1
fi
printf 'CALIBRATION_CHECK_EVENT {"schema_version":1,"run_id":"%s","check_id":"example_check","phase":"end","exit_code":%s,"covered_seam":"README shell example and its observable output"}\n' "$run_id" "$status"
exit "$status"
