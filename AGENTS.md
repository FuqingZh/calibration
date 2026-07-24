# Repository Agent Map

## Authority

- Read `README.md` for the repository and installer contract.
- Read `docs/README.md` for current decisions and active implementation plans.
- Reusable engineering guidance lives under `references/engineering/`.
- First-party skills live under `skills/`; do not change behavioral cases as
  part of an unrelated implementation.

## AO Delivery

For conversation-authorized implementation intended to cross a pull-request
boundary, keep execution isolated in a task-specific coding session, branch,
or worktree. Cloud-reproducible work defaults to the accepted native Linear
Coding Sessions with Codex and GitHub delivery path.

This repository remains opted into the accepted user-level AO service as
`calibration`, but AO is required only for host-coupled work or for review
continuation already proven on the accepted host. For those cases, verify AO
health and start a task-specific worker before creating the implementation
branch or pull request. If a pull request already exists, mark it ready for
review if it is a draft, then restore its owning worker or claim it with
`--no-takeover`; do not create a replacement branch or pull request.
Ready-for-review is only an AO claim prerequisite. If AO is required but
unavailable, use an isolated worktree and report that fallback.

The 2026-07-24 decision authorizes GitHub native auto-merge only for pull
requests explicitly enrolled in its five-pull-request pilot and only after its
fresh effective-settings gates pass. Outside that pilot, merge and risk
decisions remain with the user.

## Validation

Install the locked validation environment with:

```bash
pdm sync --clean
```

Before delivery, run:

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
Run all three diff checks before delivery: the worktree, staged changes, and
the committed branch range are distinct surfaces. Set `BASE_REF` to the pull
request base SHA or an available local base branch when `main` is unavailable.
Treat unexpected status entries after validation as artifacts to remove or
classify before delivery.

## Review Guidelines

- Treat skill trigger expansion, instruction precedence, and routing changes
  as behavior changes, not documentation-only edits.
- Keep project-specific commands and checks in the owning repository rather
  than copying them into cross-project calibration guidance.
- Do not claim a workflow or harness improvement from static validation alone;
  require representative evidence for the stated improvement.
