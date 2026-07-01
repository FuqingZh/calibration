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

## Policy

- Keep optional mode skills user-invoked unless there is a clear reason for
  model invocation.
- Keep upstream names when possible so user prompts match external references.
- Record local behavior changes in `PATCHES.md` instead of renaming the skill.
- Do not make the installer perform network fetches.
