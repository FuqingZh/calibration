# Verification Discipline

Use this before claiming completion, especially for user-visible behavior,
external writes, generated outputs, deployments, cross-language contracts,
public APIs, CLIs, schemas, reports, and package artifacts.

## Evidence

- Prefer fresh evidence from the current state over memory or earlier runs.
- Validate the final contract, not only an intermediate implementation detail.
- For generated outputs, inspect the final expected path and relevant content,
  not only the generator's exit code.
- For external writes, read back the created or updated record when practical.
- For deployments or services, verify the live endpoint, process, rollout, or
  service state that the user actually depends on.
- For public APIs, CLIs, schemas, and compatibility surfaces, check naming,
  backward compatibility, tests, and documentation impact.
- If a check is too expensive or unsafe to run, state the exact skipped command
  or evidence path and the residual risk.

## Completion Criteria

A completion claim should include:

- what changed
- what was verified
- the exact command, artifact, endpoint, or readback used as evidence
- any checks not run and why
- any residual risk that could affect the user
