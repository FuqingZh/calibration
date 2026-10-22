# Brainstorming Retirement

Date: 2026-10-22

Status: accepted; user-requested runtime retirement

## Decision

Remove `brainstorming` from standard installation for Codex, Grok Build, and Pi.
Preserve the complete locally adapted skill, visual companion, and invocation
metadata under `thirdparty/archive/brainstorming/`, without adopting new upstream
behavior or transferring its mandatory dialogue protocol into another skill.

The separate workflow's fixed questioning, option count, and design approval
sequence are no longer part of the installed package. Users can still request
design exploration through ordinary conversation and repository-native planning.
Existing calibration references retain their engineering scope. This decision
does not make another skill a mandatory replacement.

## Evidence And Limits

The local skill was explicit-only. Retirement therefore removes an available
workflow and its maintenance surface; it does not establish lower always-loaded
context cost or better model performance. The visual companion is also retired;
equivalent visual interaction across all three clients has not been established.

The [July evaluation](2026-07-20-skill-optimization-evaluation-closeout.md)
compared two versions of the skill, not its presence against its absence. Its
recorded limitations remain unchanged. No new model comparison is claimed for
this user-directed removal.

The eight source files are preserved byte-for-byte in the
[archive manifest](../../thirdparty/archive/brainstorming-manifest.json).
Existing import manifests, upstream revisions, local patch history, and shared
[license material](../../thirdparty/licenses/) remain intact. Historical
snapshots keep their original paths and hashes.

## Compatibility And Verification

Installer refresh removes only exact repository-owned symlinks to either
`thirdparty/skills/brainstorming` or `thirdparty/archive/brainstorming`, including
dangling links. Foreign symlinks and real directories remain untouched even
with `--force`. Dry runs preserve existing links, and repeated installation
does not restore the retired entry.

Verify fresh installation and retirement across Codex, Grok Build, and Pi using
the installer tests, plus skill validation, shell checks, documentation checks,
and archive hash verification. These checks establish packaging and cleanup
behavior, not equivalent model behavior after removal.

Restoration requires an explicit decision, moving the source into the active
tree and updating the active and retired installer registries with their tests.
Creating a runtime link alone is insufficient because refresh removes it again.
