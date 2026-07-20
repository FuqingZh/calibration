# Agent Contribution And Task Isolation

Date: 2026-07-20

Status: Accepted

## Context

Calibration is currently maintained in personal GitHub repositories through
interactive local Codex sessions. The move to protected `main`, short-lived
branches, and pull requests raised two separate questions: whether Codex should
have its own contributor identity, and whether later work should continue in a
long-running local task or use isolated tasks and Worktrees.

## Decision

- Keep the repositories under the current personal ownership. Do not migrate
  them to a GitHub organization solely to represent agent participation.
- Interactive local Codex work uses the repository owner's Git identity and
  credentials. The owner remains accountable for the requested scope, review,
  and merge decision.
- Record material agent involvement in the pull request description. Do not add
  a fabricated `Co-authored-by` identity: GitHub co-author attribution requires
  an email associated with a real account.
- Use a GitHub App or its bot identity only when automation becomes unattended,
  multi-user, permission-separated, or subject to an audit requirement. Do not
  create a general machine user for the current interactive workflow.
- Keep one implementation task focused on one pull request. After that pull
  request is merged, verified on `origin/main`, and cleaned up, archive the task
  and start the next phase in a new task.
- Use a Codex-managed Worktree for a new implementation phase or parallel pull
  request. Keep the local checkout for foreground inspection and integration.
- Run formal blind judging in a separate fresh task that receives only the
  blinded outputs and rubric. Do not pass it the arm map, intended change, or
  earlier conclusions.

## Alternatives Rejected

- **A separate Codex personal account:** adds credential and permission
  management without providing a trustworthy official Codex identity.
- **Immediate organization migration:** adds administration without a current
  team, billing, ownership, or compliance boundary that requires it.
- **One long-running task for successive PRs:** retains useful history but also
  carries stale assumptions, large context, and evaluation contamination into
  independent work.
- **A permanent Worktree per repository:** consumes state and disk without a
  stable long-lived branch that needs its own checkout.

## Consequences

Pull requests, branch protection, validation evidence, and explicit disclosure
provide the audit trail; a separate commit author does not. Each next task must
recover durable context from repository documents and GitHub state rather than
depending on the archived conversation.

If a repository adopts a pull request template, it should include an
`Agent involvement` field. Repository-local contribution rules override this
default when contributing to an external project.

## Reopen When

Reconsider repository ownership or an independent automation identity when a
second maintainer joins, unattended writes become routine, secrets or
permissions need separation, organizational policy requires actor-level audit,
or an official integration supplies a better-scoped bot identity.

## References

- [Codex Worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees)
- [GitHub commit co-authors](https://docs.github.com/en/pull-requests/committing-changes-to-your-project/creating-and-editing-commits/creating-a-commit-with-multiple-authors)
- [GitHub Apps and bot identities](https://docs.github.com/en/enterprise-cloud@latest/apps/oauth-apps/building-oauth-apps/differences-between-github-apps-and-oauth-apps)
