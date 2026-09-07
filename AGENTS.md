# Repository Agent Map

## Authority

- Read `README.md` for the repository and installer contract.
- Read `docs/README.md` for current decisions and active implementation plans.
- Reusable engineering guidance owned by calibration lives under
  `skills/calibration/references/`.
- First-party skills live under `skills/`; do not change behavioral cases as
  part of an unrelated implementation.

## Conditional AO Delivery

AO is an optional environment adapter, not a property of every public clone.
Use it only when the current environment has already installed AO, explicitly
adopted this repository, and supplied local host authority. Otherwise use an
isolated worktree only for new or unowned pull-request-bound work; an existing
AO-owned pull request follows the canonical ownership-preservation rule. Ordinary
local engineering tasks continue directly under repository rules without
requiring AO or a new worktree.

Conversation authorization for a low-risk implementation also authorizes the
worker to request GitHub native auto-merge without a second merge
authorization, but only after required CI passes on the exact current head,
current-head review is clean, and no actionable review threads remain. Read
those gates back immediately before the request. Repository-local stricter
policy, an explicit user stop, or a high-risk, irreversible, permission,
security, secret, release, or compatibility decision withholds auto-merge and
requires escalation.

This authority applies to GitHub's native per-pull-request auto-merge after the
exact-head gate. It does not grant blanket merge or deployment permission.

Before any mutation, an already AO-owned repository, worktree, or branch stays
with its owner; the controller remains read-only and must not cross-write an
owner's sibling worktree. Follow the
[canonical AO integration guide](skills/calibration/references/agent-orchestrator-review-continuation.md)
for adoption, daemon readiness, quiescence, state routing, retries, and release.
Read it before AO lifecycle actions. Missing authority, proof, or guidance means
preserve owned state; isolated-worktree fallback is only for new or unowned
PR-bound work. Ordinary local engineering still needs neither AO nor a worktree.

## Validation

Install the locked validation environment with:

```bash
pdm sync --clean
```

Select validation proportionally to the affected behavior and contracts. Run
the smallest relevant checks that can decide the changed surface. The complete
repository gate is:

```bash
pdm lock --check
pdm run check
CODEX_HOME="$(mktemp -d)" bash install.sh --dry-run
git diff --check
git diff --cached --check
git diff --check "${BASE_REF:-main}...HEAD"
git status --short
```

`pdm.lock` is the dependency authority for local and CI validation. Use an
explicit temporary `CODEX_HOME`; never overwrite the user's active Codex
installation during validation.
Run the complete gate when the affected behavior or contracts, or an explicit
repository policy, require it. Otherwise select the relevant checks without
treating a file extension as proof of behavioral impact. When diff checks are
selected, remember that the worktree, staged changes, and committed branch
range are distinct surfaces. Set `BASE_REF` to the pull request base SHA or an
available local base branch when `main` is unavailable.
Treat unexpected status entries after validation as artifacts to remove or
classify before delivery.

## Review Guidelines

- Treat skill trigger expansion, instruction precedence, and routing changes
  as behavior changes, not documentation-only edits.
- Keep project-specific commands and checks in the owning repository rather
  than copying them into cross-project calibration guidance.
- Do not claim a workflow or harness improvement from static validation alone;
  require representative evidence for the stated improvement.
