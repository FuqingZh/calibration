# Default Repository Quality Gate

Version: v1.0
Date: 2026-07-30
Status: accepted

## Decision

For code changes, the installed global agent instructions now require agents
to discover and run the repository-owned validation entrypoint, plus focused
checks for the changed surface. When a canonical repository gate exists, the
agent runs the complete gate before delivery. Missing or unrunnable checks must
be reported with their residual risk.

This is a discovery and completion default, not a universal language checklist.
Repository-local instructions and configured tools remain authoritative.

## Evidence

The static installer contract asserts that the generated global instructions
retain both repository-gate discovery and complete-gate execution.

Two isolated writable runs supplied representative behavioral evidence:

| Case | Expected behavior | Result |
| --- | --- | --- |
| W04 quality-gate discovery | Infer `make check` from repository instructions, run both the unit and contract checks, and change only `src/slug.py` | Pass |
| W01 bounded local repair | Preserve the existing one-file repair boundary and pass its repository verification | Pass |

Both runs used Codex CLI 0.144.1, `gpt-5.6-sol`, medium reasoning, a fresh
workspace, and an isolated Codex home. W04's prompt did not name the validation
command. Its successful trajectory discovered the repository harness, ran it
before and after the repair, and the deterministic verifier observed only the
allowed source change.

An initial W04 diagnostic run exposed an invalid fixture command: invoking the
contract verifier by file path made the fixture package unavailable. That run
was rejected because the agent repaired the Makefile outside the allowed path.
The committed fixture invokes the verifier as a module; the accepted result
comes from a new workspace after that correction.

## Scope And Limits

- The evidence covers two small dependency-free Python fixtures, one model,
  one reasoning effort, and local verification.
- It supports the default discovery behavior and bounded-task regression only;
  it does not establish cross-language or production-delivery improvement.
- Language-specific tools such as Ruff, Pyright, ty, Cargo, or Go checks run
  when the owning repository exposes them through its instructions or harness.
  Their names are intentionally not copied into the global rule.
- A future representative failure may justify extending the evaluation, but
  not silently replacing repository authority with a global checklist.
