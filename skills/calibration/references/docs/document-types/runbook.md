# Runbook

## Use When

Use this type for a controlled operational procedure, especially one that is
production-adjacent, high-risk, or requires explicit recovery and escalation.

## Method Reference

Use the [AWS runbook guidance](https://docs.aws.amazon.com/wellarchitected/2023-10-03/framework/ops_ready_to_support_use_runbooks.html)
as a method reference. Repository-local commands, permissions, and rollback
rules remain authoritative.

## Local Requirements

- Place it in project `docs/runbooks/` when the project maintains runbooks
  there.
- State purpose, scope, owner, prerequisites, access requirements, and
  conditions for use.
- Give ordered steps with checkpoints and expected observations.
- Define verification, recovery, rollback, escalation, and stop conditions.
- Identify version, environment, and dependency assumptions that affect safety.
- Keep secrets, private host state, and unreconstructable raw evidence out of
  the public document.

## Complete When

An authorized operator can execute the procedure safely, verify the result,
and know what to do when a checkpoint or recovery step fails.
