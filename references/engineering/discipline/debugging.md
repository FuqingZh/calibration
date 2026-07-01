# Debugging Discipline

Use this for bugs, runtime failures, failing tests, unclear behavior, and
root-cause analysis.

## Loop

- Start from the concrete failing artifact: command, stack trace, log line,
  generated file, request, test case, or runtime state.
- Reproduce or inspect the failure before explaining it when reproduction is
  reasonably available.
- Make the loop red before changing code: identify the observable condition that
  currently fails.
- Separate symptom, suspected cause, proven cause, and fix. Do not present a
  hypothesis as the root cause until evidence links it to the failure.
- Inspect the actual runtime environment when environment drift is plausible:
  installed versions, image contents, service env, file paths, permissions, and
  generated artifacts.
- Prefer the smallest fix that addresses the proven cause without hiding the
  failure behind broader exception handling or silent fallback.
- After the fix, rerun the failing check or a narrower equivalent that proves
  the same path.

## Completion Criteria

A debugging task is complete only when:

- the original failure surface is identified precisely
- the root cause is supported by evidence
- the fix changes the failing path, not just an adjacent symptom
- the verification command or artifact is fresh enough to support the claim
- any remaining uncertainty is named with its impact
