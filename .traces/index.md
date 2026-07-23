# Trace Index

## Recent Retros

- `retros/20260723-orchestration-route-convergence-retro.md`: Scheduled Tasks,
  Symphony, and AO evidence converged on a narrow event-to-original-worker
  bridge instead of a new scheduler or full workflow control plane; the stable
  decision and host contract were promoted to `docs/`.
- `retros/20260701-calibration-global-retro.md`: global deep retrospective for
  the calibration repository rename, skill-boundary cleanup, document-type
  routing, first-party `retrospect`, test prompts, and installer sync.

## Repeated Patterns

- Default engineering guidance works best as a thin executable router backed by
  small references, not as a broad skill catalog.
- Optional modes should stay user-invoked even when managed by the installer.
- Test prompts are evaluation assets; they are not evidence of optimized skill
  behavior until a real evaluation pass is run.
- Start from the exact state transition still consuming human attention;
  preserve native owners around it and validate the smallest missing bridge
  with one real event before adding broader orchestration.

## Promoted Observations

- Skill architecture and rename decisions are documented under
  `docs/decisions/`.
- Trace and retro conventions are documented under
  `references/engineering/docs/workflow/task_traces_and_retros/` and
  `references/engineering/docs/document-types/trace-retro.md`.
- AO review continuation rationale and reconstruction are documented under
  `docs/decisions/2026-07-23-ao-review-continuation-adoption.md` and
  `docs/runbooks/agent-orchestrator-review-continuation.md`.

## Under Watch

- Whether first-party skills pass a full Darwin evaluation once explicitly run.
- Whether `retrospect` produces useful retros without becoming an automatic
  end-of-task ritual.
- Whether upstream AO absorbs the two retained local patches and whether the
  bounded continuation loop saves attention across additional repositories.
