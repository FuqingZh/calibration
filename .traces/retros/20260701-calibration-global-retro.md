# Calibration Repository Global Retrospective

Date: 2026-07-01
Project: calibration
Status: current
Mode: deep

## Expected

- Goal: Turn a loose personal engineering skill repository into a coherent
  `calibration` system with one default engineering entrypoint, explicit
  optional modes, managed installation into `/home/fqzhang/.codex`, and durable
  documentation of the decisions.
- Risk: The default skill could remain too broad to follow; optional skills
  could accidentally become always-on policy; third-party skills could drift
  from upstream without source records; retrospectives could become another
  undocumented chat pattern instead of an evidence-backed workflow.
- Validation plan: Use semantic commits, decision docs, targeted reference
  routers, `test-prompts.json`, `bash install.sh --dry-run`, a real installer
  run, bounded keyword search, and git status/log evidence.
- Key assumptions: The installer is the source of truth for the active
  home-directory Codex state; repository-local rules override calibration;
  optional modes should remain user-invoked; long-term rule promotion should be
  explicit rather than automatic.

## Actual

- Changes: The repository was renamed from `engineering-canon` to
  `calibration`; the old `global-defaults` role became `skills/calibration/`;
  duplicate engineering entrypoints were retired; naming, discipline, design,
  and document-type references were split into routers; selected third-party
  skills were vendored; `retrospect` was added as a first-party managed skill;
  `personal-strategy` was narrowed to explicit use; first-party Darwin test
  prompts were added.
- Validation: Recent git history shows focused commits from `ebbb090` through
  `ce0a64a`; `git status --short` was clean before this retro; `bash
  install.sh --dry-run` reported all managed first-party and vendored skills as
  current; `readlink /home/fqzhang/.codex/skills/retrospect` resolves to this
  repository's `skills/retrospect` directory.
- Result: The active repository now has a clearer product identity, one default
  engineering skill, explicit optional-mode boundaries, installer-managed local
  Codex state, and a documented trace/retro workflow. The remaining gap is not
  structure, but future empirical evaluation and repeated-use calibration.

## Delta

- Underestimated: The amount of boundary work needed after the initial skill
  consolidation. Cleaning duplicate entrypoints exposed related questions about
  naming granularity, optional skill vendoring, document types, retrospectives,
  and persona-trigger leakage.
- Overestimated: The value of adding more always-visible guidance into the
  default skill. The repeated user correction was that the default path should
  stay thin and enforce coding-time engineering behavior, not become a catalog
  of optional modes.
- Surprise: The missing retrospective layer was not just another document type.
  The repository already had a `trace-retro` contract, but still lacked an
  interaction workflow for gathering evidence, deciding depth, and preventing
  automatic promotion of uncertain lessons.

## Rule To Carry Forward

- Future rule: For calibration-level skill changes, distinguish three layers
  before editing: default engineering behavior, user-invoked interaction modes,
  and reference/document contracts. Do not solve a behavior problem by adding
  another always-on rule unless the failure is actually in the always-on path.
- Future rule: Treat `test-prompts.json` as evaluation assets, not proof.
  Actual quality claims require an explicit Darwin or equivalent evaluation
  pass with results recorded separately.
- Future rule: A repository-wide skill refactor should close with both install
  verification and a `.traces/retros/` artifact, because the important learning
  is often about routing, trigger boundaries, and missed validation, not only
  file diffs.

## Promotion Recommendation

- Promote: no immediate promotion.
- Target: none for this pass.
- Reason: The stable decisions have already been promoted into decision docs,
  skill files, README, installer behavior, and document-type references. The
  remaining observations should stay in this retro until repeated future use
  proves that a new calibration rule is needed.

## Root Cause

The original failure pattern was not lack of more principles. It was a mismatch
between broad reference material and coding-time execution pressure. The old
shape made it too easy for guidance to be correct but not operational: large
principles, a broad default skill, duplicate design entrypoints, and optional
modes that were not clearly separated from the default path.

The effective correction was structural: make `calibration` a thin default
router, split references by decision surface, keep optional modes
user-invoked, and put evidence-heavy post-task learning into `retrospect`
rather than into the default engineering skill.

## Missed Detection

The repository did not initially have a local retro artifact for this sequence,
even though the work touched the repository name, home-directory installer,
skill boundaries, third-party vendoring, and first-party evaluation assets.
That meant several important decisions lived in conversation until the final
batch of decision docs was written.

The first-party test prompts were also added late. They now define intended
behavior for `calibration`, `retrospect`, and `personal-strategy`, but they have
not yet been exercised by a full independent Darwin evaluation.

## Prevention

- Keep `.traces/` available for high-learning maintenance work, not only code
  failures.
- For every future skill-boundary change, check these four surfaces together:
  `SKILL.md`, README/installer, decision docs, and test prompts.
- When a skill is user-invoked, encode that boundary in both metadata and
  prose, then verify that the default `calibration` skill does not suggest or
  auto-load it unless that is explicitly intended.
- Run `bash install.sh --dry-run` after installer or managed-skill changes, and
  run real `bash install.sh` when local Codex state must be refreshed.

## Stale Or Superseded Rule

- `engineering-canon` is now a historical repository name, not the active
  product name.
- `global-defaults` is now a historical default-skill name, not the active
  entrypoint.
- `engineering-design`, `naming`, and `project-docs` remain retired managed
  skill names in the installer cleanup path.
- `grill-me` is a retired unmanaged local skill name; `grilling` is the active
  vendored optional mode.

## Evidence Quality

- Strong evidence: current decision docs, skill files, installer behavior,
  README, first-party test prompts, recent git log, clean git status before
  writing this retro, installer dry-run output, and the live `retrospect`
  symlink readback.
- Bounded historical evidence: memory and rollout summary entries for
  `engineering-canon`, `global-defaults`, optional-mode boundaries, and
  execution-discipline concerns.
- Missing evidence: no full Darwin evaluation results, no `results.tsv`, and no
  independent baseline-versus-skill comparison for the first-party skills yet.
- Sensitivity: no sensitive raw logs or long transcript excerpts were copied
  into this retro.
