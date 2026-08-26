#!/usr/bin/env bash
set -u
run_id="${CALIBRATION_EVAL_RUN_ID:?CALIBRATION_EVAL_RUN_ID is required}"
printf 'CALIBRATION_CHECK_EVENT {"schema_version":1,"run_id":"%s","check_id":"focused_test","phase":"begin","exit_code":null,"covered_seam":"whitespace normalization behavior"}\n' "$run_id"
if python -c "from src.normalize import normalize; assert normalize('  one   two  ') == 'one two'"; then status=0; else status=1; fi
printf 'CALIBRATION_CHECK_EVENT {"schema_version":1,"run_id":"%s","check_id":"focused_test","phase":"end","exit_code":%s,"covered_seam":"whitespace normalization behavior"}\n' "$run_id" "$status"
exit "$status"
