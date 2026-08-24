#!/usr/bin/env bash
set -u
run_id="${CALIBRATION_EVAL_RUN_ID:?CALIBRATION_EVAL_RUN_ID is required}"
printf 'CALIBRATION_CHECK_EVENT {"schema_version":1,"run_id":"%s","check_id":"generator","phase":"begin","exit_code":null,"covered_seam":"source-to-generated-summary transformation"}\n' "$run_id"
if python src/generate-summary.py; then status=0; else status=1; fi
printf 'CALIBRATION_CHECK_EVENT {"schema_version":1,"run_id":"%s","check_id":"generator","phase":"end","exit_code":%s,"covered_seam":"source-to-generated-summary transformation"}\n' "$run_id" "$status"
exit "$status"
