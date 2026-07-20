# Third-party Skill Patches

This file records local behavior changes made to vendored third-party skills.
Exact imported and checked refs live in `sources.tsv`.

## brainstorming

Imported from Superpowers `brainstorming`.

Local changes:

- Set `policy.allow_implicit_invocation: false` in `agents/openai.yaml`.
- Preserve the hard gate and visible protocol: inspect the project, ask one
  question at a time, compare 2-3 mutually exclusive approaches, recommend one,
  present a Design Checkpoint, and wait for approval before implementation.
- Remove forced design persistence, the `docs/superpowers/specs/` path,
  immediate commit, and the required `writing-plans` handoff. Use repository
  conventions only when persistence or planning is actually requested.
- Route general codebase-design judgment through repository rules and
  `$calibration` instead of duplicating architecture doctrine in this skill.
- Keep the visual companion and its just-in-time offer. Store persistent helper
  state under `.calibration/brainstorm`, not `.superpowers/brainstorm`.
- Remove the unused Superpowers spec-reviewer prompt that encoded the old path.

## grilling

Imported from Matt Pocock's `skills/productivity/grilling`.

Local changes:

- Set `policy.allow_implicit_invocation: false` in `agents/openai.yaml`.
- Sync the upstream distinction between discoverable facts and user decisions,
  plus the confirmation gate before action.
- Add a stopping condition based on unresolved decisions that can materially
  change scope, interface, risk, or verification.

## writing-great-skills

Imported from Matt Pocock's `skills/productivity/writing-great-skills`.

Local changes:

- Keep the upstream explicit-invocation policy in `agents/openai.yaml` and add a
  local default prompt.
- Sync the Negation failure mode.
- Update invocation guidance for current Codex `agents/openai.yaml` policy.
- Replace the default stronger-adjective remedy for a no-op with removal or an
  explicit scope, evidence requirement, completion criterion, or stopping
  condition.

## writing-plans

Imported from Superpowers `writing-plans`.

Local changes:

- Set `policy.allow_implicit_invocation: false` in `agents/openai.yaml`.
- Replace the forced `docs/superpowers/plans/` output path with repository-local
  planning and documentation conventions.
- Remove forced TDD, frequent commit, subagent-driven development, and
  executing-plans requirements. Keep explicit verification gates while
  following repository-local execution practice.
- Keep `plan-document-reviewer-prompt.md` as an optional reviewer template.
- Retain the source for provenance while excluding it from installer management;
  Codex Plan Mode and the shared implementation-plan reference are active.

## darwin-skill

Imported from `alchaincyf/darwin-skill`.

Local changes:

- Set `policy.allow_implicit_invocation: false` in `agents/openai.yaml`.
- Shorten the frontmatter description while preserving the upstream body and
  assets.
- Replace runtime-specific executable paths with runtime-neutral or
  Codex-compatible paths.
- Retain the source for provenance and study while excluding it from installer
  management.
