# Trace Index

## Recent Retros

- `retros/20260701-calibration-global-retro.md`: global deep retrospective for
  the calibration repository rename, skill-boundary cleanup, document-type
  routing, first-party `retrospect`, test prompts, and installer sync.

## Repeated Patterns

- Default engineering guidance works best as a thin executable router backed by
  small references, not as a broad skill catalog.
- Optional modes should stay user-invoked even when managed by the installer.
- Test prompts are evaluation assets; they are not evidence of optimized skill
  behavior until a real evaluation pass is run.

## Promoted Observations

- Skill architecture and rename decisions are documented under
  `docs/decisions/`.
- Trace and retro conventions are documented under
  `references/engineering/docs/workflow/task_traces_and_retros/` and
  `references/engineering/docs/document-types/trace-retro.md`.

## Under Watch

- Whether first-party skills pass a full Darwin evaluation once explicitly run.
- Whether `retrospect` produces useful retros without becoming an automatic
  end-of-task ritual.
