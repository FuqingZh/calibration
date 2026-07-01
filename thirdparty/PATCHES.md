# Third-party Skill Patches

This file records local behavior changes made to vendored third-party skills.

## brainstorming

Imported from the locally installed Superpowers `brainstorming` skill.

Local changes:

- Set `disable-model-invocation: true` so the skill is user-invoked only.
- Removed the hard gate that forbids implementation before the Superpowers
  design flow completes. The local convention is still to get approval before
  building, but not to block already-approved work.
- Replaced the forced `docs/superpowers/specs/` output path with repository-local
  docs, decision-record, plan, or trace conventions.
- Removed the forced immediate commit requirement. Commit when the user asks,
  the task includes commit/push, or the repository workflow requires it.
- Removed the forced transition to `writing-plans`. Use the active repository or
  environment planning format unless the user invokes `writing-plans`.
- Kept the visual companion assets and pointer for cases where a visual design
  question genuinely benefits from them.
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
