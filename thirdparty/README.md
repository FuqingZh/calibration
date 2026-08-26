# Third-party Skills

This directory vendors selected third-party Codex skills that are useful for the
calibration workflow.

The installer uses these local copies only. It does not download skills at
install time. Updates are manual so prompt changes remain reviewable and local
patches stay explicit.

## Layout

- `skills/`: vendored skill directories installed into `$CODEX_HOME/skills`
- `sources.tsv`: upstream source and local policy for each vendored skill
- `PATCHES.md`: local modifications from the upstream or imported copy
- `import-manifests/`: machine-readable source roles, license treatment, and
  byte hashes for multi-source imports

Retired sources may remain in `sources.tsv` after their vendored trees are
removed. Their entries retain immutable provenance and use an explicit
`retired-not-vendored` policy.

The progressive-validation-selection provenance uses three more specific
states:

- `vendored+patched+shared`: an imported runtime tree with a documented local
  patch, installed by the shared registry in both profiles. It is a singular
  audited exception, not a general third-party installation or invocation rule.
- `method-adapted-not-vendored`: an upstream method source for a separately
  attributed local derivative; no upstream skill tree is distributed.
- `method-reference-not-vendored`: a source used only to inform independently
  expressed structure; neither its text nor its files are distributed.

## Policy

- Keep optional mode skills user-invoked unless there is a clear reason for
  model invocation.
- Express invocation policy in each skill's `agents/openai.yaml`; keep
  `SKILL.md` frontmatter portable.
- Keep upstream names when possible so user prompts match external references.
- Record local behavior changes in `PATCHES.md` instead of renaming the skill.
- Do not make the installer perform network fetches.
