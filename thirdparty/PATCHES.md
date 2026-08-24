# Third-party Skill Patches

This file records local behavior changes made to vendored third-party skills.
Exact imported and checked refs live in `sources.tsv`.

## coding-protocol

Imported from lencx `skills/coding-protocol` at
`b848e124111be50a795cc961558247e7751825e2`, with these local changes:

- Add `agents/openai.yaml` with
  `policy.allow_implicit_invocation: true`. This is the single audited
  third-party implicit-invocation exception; its exact name and directory are
  enforced by the local validator, and the shared installer registry installs
  it in both profiles.
- Extend `SKILL.md` section 7 and References with a conditionally loaded,
  repository-neutral validation-selection reference. Exit still loads no
  references.
- Add `references/validation-selection.md` as an Apache-2.0 derivative of
  GonkaGate `verification-before-completion` at
  `461578373f9c3a8eae3037504f659e0f3e0cc7cd`; it is independently written,
  carries source, license, and modification notices, and omits language- or
  project-specific command matrices.
- Extend `references/rule-rationale.md` for verification inflation,
  local-mandate omission, and failure-only widening.
- Add static behavioral prompts for Exit, focused selection, mandatory
  broadening, and failure diagnosis.

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

## teach

Imported from Matt Pocock's `skills/productivity/teach` at release `v1.2.3`.

Local changes:

- Keep explicit invocation, mission grounding, trusted-source research, small
  lessons, retrieval practice, reusable learner state, and tight feedback.
- Separate the read-only installed skill source and engineering-project context
  from an explicitly selected personal learning workspace; provide a
  conversation-only mode that writes no files.
- Confirm a persistent workspace with `.teach-workspace.yaml`, assess starting
  capability before the first lesson, and resume from existing learning state.
- Require current authoritative sources for time-sensitive claims and extend
  resource records with applicable version or date plus check date.
- Add a reusable runtime quiz shuffler so answer position is not fixed, while
  retaining comparable option formatting.
- Add explicit lesson stopping, review-cue, and session-resume behavior without
  claiming an automatic spaced-repetition scheduler.
- Require a separate explicit request before distilling team-neutral learning
  into the owning project's documentation workflow.

## darwin-skill (retired, not vendored)

Imported from `alchaincyf/darwin-skill`.

Historical local changes:

- Set `policy.allow_implicit_invocation: false` in `agents/openai.yaml`.
- Shorten the frontmatter description while preserving the upstream body and
  assets.
- Replace runtime-specific paths in user-facing skill and README guidance.

The retired tree was later removed rather than patching its unverified
third-party screenshot runtime. `sources.tsv` retains the immutable imported
and checked upstream refs. The installer retains owned-link cleanup for the
retired name without claiming that the upstream utility is portable or
supported by calibration.
