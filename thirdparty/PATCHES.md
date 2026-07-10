# Third-party Skill Patches

This file records local behavior changes made to vendored third-party skills.

## brainstorming

Imported from the locally installed Superpowers `brainstorming` skill.

Local changes:

- Set `disable-model-invocation: true` so the skill is user-invoked only.
- Kept the original brainstorming interaction protocol: explore first, ask one
  question at a time, propose multiple approaches, recommend one, present a
  design checkpoint, and require user approval before implementation.
- Replaced the forced `docs/superpowers/specs/` output path with repository-local
  docs, decision-record, plan, or trace conventions.
- Removed the forced immediate commit requirement. Commit when the user asks,
  the task includes commit/push, or the repository workflow requires it.
- Removed the forced transition to `writing-plans`. Use the active repository or
  environment planning mode.
- Kept the visual companion assets and pointer for cases where a visual design
  question genuinely benefits from them.
- Changed persistent visual-companion session paths from `.superpowers/brainstorm`
  to `.calibration/brainstorm`.
- Removed the unused Superpowers spec-reviewer prompt because it still encoded
  the old `docs/superpowers/specs/` path.

## grilling

Imported from the locally installed `grilling` skill.

Local changes:

- Set `disable-model-invocation: true` so the skill is user-invoked only.
- Kept the adversarial one-question-at-a-time interview behavior unchanged.

## writing-great-skills

Imported from the locally installed `writing-great-skills` skill.

Local changes:

- None at import time. The skill was already user-invoked.

## writing-plans

Imported from Superpowers `writing-plans`.

Local changes:

- Set `disable-model-invocation: true` so the skill is user-invoked only.
- Replaced the forced `docs/superpowers/plans/` output path with repository-local
  planning and documentation conventions.
- Removed forced TDD, frequent commit, subagent-driven-development, and
  executing-plans requirements. The local version still requires explicit
  verification gates but follows repository-local execution practice.
- Kept `plan-document-reviewer-prompt.md` as an optional reviewer template.
- Retained the vendored source for provenance, but removed it from installer
  management after Codex Plan Mode and the shared implementation-plan reference
  became the active planning control surfaces.

## darwin-skill

Imported from `alchaincyf/darwin-skill`.

Local changes:

- Set `disable-model-invocation: true` so the skill is user-invoked only.
- Shortened the frontmatter description to avoid a large always-visible trigger
  surface while preserving the full upstream body and assets.
- Replaced runtime-specific executable paths in the body and README with
  runtime-neutral or Codex-compatible paths.
- Retained the vendored source for provenance and study, but removed it from
  installer management because its large-scale rubric-and-ratchet optimization
  model is not part of the daily calibration workflow.
