# Debugging Discipline

Use for bugs, runtime failures, failing tests, unclear behavior, and root-cause
analysis.

- Establish the original failing surface before editing. Reproduce it when
  reasonably available; otherwise inspect concrete logs, requests, artifacts,
  or runtime state and name the evidence gap. An existing failure record can
  supply this evidence without manufacturing a fresh failing test.
- Distinguish symptoms, hypotheses, and causes supported by evidence. When
  environment drift is plausible, inspect actual versions, images, service
  configuration, paths, permissions, and generated artifacts.
- Fix the supported cause with the smallest effective change. Do not hide the
  failure through broader exception handling or silent fallback.
- Rerun the original failing check or an equivalent that exercises the same
  path. Claim resolution only with fresh evidence that the fix addresses that
  failure; report any remaining uncertainty and its impact.
