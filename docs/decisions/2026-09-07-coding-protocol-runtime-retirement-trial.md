# Coding Protocol Runtime Retirement Trial

Status: user-authorized reversible trial; no general equivalence claim.

## Decision And Evidence

The user authorized archiving the independent runtime entry while preserving
source and body. Both installer profiles now retire the repository-owned
`coding-protocol` link. Foreign links and real directories remain untouched,
including with `--force`. No source, reference, UI metadata, provenance, or
license is removed. Calibration's trigger and rules are not expanded.

The [24-run comparison](../../evaluations/coding-protocol-calibration/README.md)
found 8/8 completed tasks with calibration alone and 8/8 with both skills.
The median paired token difference was +2.8%, with mixed directions; it did not
establish stable overhead. The trial tests the practical value of removing a
repeated entrypoint, not a claim that every protocol rule is obsolete.

## Source Relocation (2026-10-15)

The retained tree now lives in `thirdparty/archive/coding-protocol/`; see the
[archive index](../../thirdparty/archive/README.md). The activation receipt below
records the historical path. The restoration example uses the relocated source.
A durable restoration also needs to move that source back into the active tree.

## Activation And Restoration

The personal entry is `skills/coding-protocol` under the selected Codex home.
Remove it only after verifying it is a symlink to this repository's retained
source. Record its exact target in a private restoration receipt before removal.
Do not run the full installer against the active home just to remove this entry,
and do not modify other homes or live AO workers.

Activation verified: the exact personal symlink was removed, its source body
hash stayed unchanged, and every other personal skill entry retained its inode,
modification time, and link target. The restoration receipt remains in the
user-selected private temporary directory.

Future installer refreshes apply the same owned-link retirement to either
profile. Existing tasks may retain already-loaded skill text; observe the trial
in fresh tasks.

For immediate personal rollback, set `calibration_checkout` to the absolute
path of the retained calibration checkout recorded in the restoration receipt.
Do not infer it from the current project directory. Verify the source exists
and the entry is absent before recreating the symlink:

```bash
calibration_checkout="/absolute/path/to/calibration" # Replace with the recorded checkout
coding_protocol_entry="${CODEX_HOME:-$HOME/.codex}/skills/coding-protocol"
coding_protocol_source="$calibration_checkout/thirdparty/archive/coding-protocol"
test -f "$calibration_checkout/skills/calibration/SKILL.md" && \
  test -f "$coding_protocol_source/SKILL.md" && \
  test ! -e "$coding_protocol_entry" && test ! -L "$coding_protocol_entry" && \
  ln -s "$coding_protocol_source" "$coding_protocol_entry"
```

This restores the entry with its original invocation metadata. A subsequent
installer refresh would retire it again. To end the trial durably, move
`coding-protocol` from the retired shared installer array back to the managed
shared array, remove it from the validator's retired shared set, and update the
installer/validator expectations and current documentation together. Do not
revert unrelated workspace changes to restore this one skill.

## Observation And Validation

Watch fresh real tasks for lost preservation of user work, changes during
read-only requests, skipped required checks, verification without sensitivity,
and unnecessary approval stops. Restore or investigate a concrete regression;
do not automatically add all archived rules to calibration. No monitoring
service or new task is created by this trial.

Installer checks cover both profiles, repeated refreshes, and foreign-link
preservation. Skill validation retains the exact archived metadata exception
while rejecting accidental runtime reactivation. These checks establish
installation behavior, not real-work equivalence. Destructive Git, live AO,
and production migration behavior remain untested by the comparison.

Validation readback: 94 installer, skill-validator, and provenance tests passed;
both isolated installer dry-runs passed. Skill validation, Python lint/type
checks, lock consistency, and diff checks passed. The full repository check was
attempted and exposed six remaining sandbox integration failures in
`tests/test_run_writable_agent_eval.py`, all reporting failure to resolve the
synthetic mount temporary directory `/output/tmp`. That test file and its
owning runner were not changed by this trial. Full-gate success is not claimed;
the sandbox integration compatibility boundary remains unresolved.

## Follow-up: Executor Compatibility Resolved

On 2026-10-11, [PR #65](https://github.com/FuqingZh/calibration/pull/65)
resolved the executor compatibility gap reported above. It supplied the required
executor temporary directory, corrected shell symlink mounts, prepared protected
metadata directories before isolation, and protected login-shell HOME and PATH.
The historical failure counts and trial conclusions above remain unchanged.

The follow-up passed the full local Python 3.12 gate with 581 tests and 100%
script line coverage. GitHub CI passed on the same head with 561 tests and 20
tool-dependent skips; the local run exercised those skipped integrations.
Focused checks also passed with Codex 0.148.0, alongside the full local run using
Codex 0.162.1. These are bounded compatibility results; they do not establish
universal client compatibility, general model improvements, or live AO behavior.
