# Archived Third-party Skills

Status: retired source archive. These directories are not installed or included
in runtime skill discovery. Their instructions and invocation metadata are
historical material, not current operating guidance.

| Archive | Reason and current owner |
| --- | --- |
| [brainstorming](brainstorming/SKILL.md) | User-requested retirement of the separate design-dialogue workflow and visual companion; ordinary design discussion remains available. See the [decision](../../docs/decisions/2026-10-22-brainstorming-retirement.md). |
| [coding-protocol](coding-protocol/SKILL.md) | Independent runtime entry retired after a bounded comparison; repository rules, native execution, and calibration remain current. See the [retirement trial](../../docs/decisions/2026-09-07-coding-protocol-runtime-retirement-trial.md). |
| [writing-great-skills](writing-great-skills/SKILL.md) | Runtime entry retired after limited screening; retain as historical authoring reference. See the [decision](../../docs/decisions/2026-09-07-gpt6-skill-retirement-and-snippet-scope.md). |
| [writing-plans](writing-plans/SKILL.md) | Planning belongs to the environment's planning flow and the shared [implementation-plan reference](../../skills/calibration/references/docs/document-types/implementation-plan.md). |

The original three directories moved from `thirdparty/skills/` on 2026-10-15.
All 13 retained files are byte-identical to their pre-move versions;
[manifest.json](manifest.json)
records original paths, archived paths, and SHA-256 hashes. Source, license
material, local patches, and upstream revisions remain preserved. Shared
provenance stays in [sources.tsv](../sources.tsv) and [PATCHES.md](../PATCHES.md).
Historical import manifests and evaluation snapshots retain their original
paths and hashes; relocation does not rewrite past evidence.

`brainstorming` moved on 2026-10-22. Its eight files are unchanged;
[brainstorming-manifest.json](brainstorming-manifest.json) records original and
archived paths with SHA-256 hashes. The original manifest remains unchanged.

The installer removes only exact repository-owned links to either the former
or archived location, including dangling links after migration. Foreign links
and real directories remain untouched even with `--force`. A dry run changes
nothing. No installer operation against a user's active home is required for
this source migration.

Restoration is a separate explicit change: return the source to the active
skill tree, update the managed and retired registries and validator policy, and
validate the installation and invocation contracts. Recreating a link alone is
not durable; the installer retires it again. Archiving does not establish that
all preserved principles are obsolete or that another workflow is superior.
