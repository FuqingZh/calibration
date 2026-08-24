#!/usr/bin/env bash
set -u
run_id="${CALIBRATION_EVAL_RUN_ID:?CALIBRATION_EVAL_RUN_ID is required}"
printf 'CALIBRATION_CHECK_EVENT {"schema_version":1,"run_id":"%s","check_id":"artifact_readback","phase":"begin","exit_code":null,"covered_seam":"final generated/release-summary.txt content"}\n' "$run_id"
if grep -Fqx 'release-status: published' generated/release-summary.txt; then status=0; else status=1; fi
printf 'CALIBRATION_CHECK_EVENT {"schema_version":1,"run_id":"%s","check_id":"artifact_readback","phase":"end","exit_code":%s,"covered_seam":"final generated/release-summary.txt content"}\n' "$run_id" "$status"
exit "$status"
