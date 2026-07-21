# Repository Delivery Feedback Loop

Date: 2026-07-21

Status: Candidate pending cross-repository smoke validation

## Context

The accepted harness boundary already places repeated operations in repository
tools and mechanically decidable constraints in tests or CI. A live Codex
cloud smoke task for `FuqingZh/calibration` supplied concrete delivery evidence:

- the hosted environment checked out the repository and found its CI workflow;
- it could not inherit the developer's global `AGENTS.md` because no
  repository-level file was committed;
- automatic setup did not discover `requirements-validation.txt`;
- agent-phase dependency installation failed with a proxy `403`, leaving
  PyYAML unavailable; and
- shell validation and installer dry-run checks passed while the final tree
  remained clean.

The evidence supports a smaller problem than universal repository
provisioning: start with platform defaults, expose repository-owned entrypoints,
and improve the feedback loop only after a representative failure.

## Decision

- Route repository delivery feedback through the existing calibration skill
  and repository harness reference. Do not add a delivery or bootstrap skill.
- Discover and reuse repository-owned setup and validation entrypoints across
  local work, CI, and cloud environments.
- Start hosted environments with automatic setup. Add custom environment
  configuration only after a concrete task exposes a gap.
- Use platform-native pull-request review when available and keep only useful
  repository-specific review guidance in `AGENTS.md`.
- Iterate on actionable CI and agent-review feedback until declared checks pass
  or a human-authority decision remains.
- Treat GitHub rulesets, Codex cloud environments and review settings, and
  scheduled tasks as external control-plane state. Observe or change them when
  the current surface is authorized, then read them back; otherwise report the
  exact remaining action.
- Use shared recurring tasks for selected repositories only after recurring
  volume justifies them. Do not create one task per repository by default.
- Keep auto-merge disabled unless a repository explicitly adopts a risk policy
  that allows it.

## Ownership

| Capability | Owner |
| --- | --- |
| Setup and validation entrypoints | repository |
| CI workflow definition | repository |
| CI results, required checks, and rulesets | GitHub |
| Hosted environment and automatic review settings | Codex cloud |
| Recurring task schedule and run state | Scheduled control plane |
| Auto-merge risk policy | repository maintainers |
| Cross-project capability-placement judgment | calibration |

## Boundaries

- No universal `AGENTS.md` template or delivery configuration schema.
- No requirement that every repository have CI or a cloud environment.
- No bulk cloud-environment provisioning in calibration.
- No new orchestrator or `WORKFLOW.md`.
- No change to the frozen prior evaluation cases in this candidate.

## Acceptance

Accept the candidate only after local static validation and read-only cloud
smoke tasks in two real repositories. A smoke task must report the commands and
evidence it checked, leave no diff, and distinguish a repository gap from an
external authorization or environment limitation.
