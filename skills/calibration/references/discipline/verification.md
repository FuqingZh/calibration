# Verification Discipline

Use before completion claims for public or cross-boundary contracts,
user-visible behavior, generated outputs, external writes, or deployments.

- Use current evidence for the final contract. Inspect generated outputs at
  their expected path and check relevant content; generator exit status alone
  does not establish the result.
- Read back external writes when practical. For deployments and services,
  verify the live endpoint, process, rollout, or service state the user relies on.
- For APIs, CLIs, schemas, and compatibility surfaces, verify naming, backward
  compatibility, tests, and documentation impact, using checks proportionate
  to the affected contract.
- Report what changed, what was verified, and the command, artifact, endpoint,
  or readback supporting the claim. For checks not run, state the exact command
  or evidence path, why it was skipped, and the remaining risk to the user.
- Match evidence to each material claim. For a bug fix, show before and after
  under the same triggering conditions, using available failure records or
  execution results. For a behavior-preserving refactor, name the invariants
  and the checks that establish they still hold. When before evidence is
  unavailable, state the gap; do not invent a prior failure or imply an old
  version was executed. Keep the original evidence accessible through a
  reconstructable reference or an approved evidence location.
- Describe risk through the affected consumers or operations and any effects
  that would remain after reverting the code. Preserve compatibility and
  permission boundaries; a rollback claim does not authorize destructive
  actions or acceptance of an unresolved risk.
