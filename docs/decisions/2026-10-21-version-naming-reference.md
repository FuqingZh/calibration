# Version Naming Reference

Status: adopted local guidance; no measured agent-performance claim.

## Decision

Add [version.md](../../skills/calibration/references/naming/version.md) beside
CLI and branch naming, reached through the naming router. It owns version
identifiers and compatibility meaning. Repository release tooling owns concrete
commands and cadence; the existing verification reference owns completion
claims. Calibration's entry description and top-level trigger remain unchanged.

Use independently written guidance with links to primary standards and ecosystem
references. Do not import a complete third-party skill or require a release tool.

## Precedents Reviewed On 2026-10-21

| Primary source | Useful precedent and adoption boundary |
| --- | --- |
| [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html) | Public contract, release increments, deprecation, prereleases, and immutable published versions. Refer to the standard instead of maintaining another copy. |
| [PyPA versioning](https://packaging.python.org/en/latest/discussions/versioning/) | Version syntax and release policy are distinct; SemVer and calendar schemes coexist. Preserve ecosystem prerelease syntax. |
| [PyPA single-sourcing](https://packaging.python.org/en/latest/discussions/single-source-version/) | A version can originate in VCS or project metadata; derive or check other representations. Do not prescribe tags as the universal authority. |
| [Cargo compatibility](https://doc.rust-lang.org/cargo/reference/semver.html) | Compatibility depends on concrete changes and ecosystem policy, including toolchain requirements. Avoid imposing one global classification on support-policy changes. |
| [Go module versions](https://go.dev/doc/modules/version-numbers) | Version semantics affect consumer imports and module identity; ecosystem tooling matters beyond number formatting. Do not generalize Go's module-path rules. |
| [Kubernetes version skew](https://kubernetes.io/releases/version-skew-policy/) | Component interoperability needs an explicit support policy; matching major numbers alone is insufficient. No Kubernetes-specific windows are copied. |
| [Changesets](https://changesets.dev/guide/getting-started) | Record intended release impact and consumer notes, then aggregate through repository automation. Its old GitHub introduction explicitly redirects to this current site. |
| [Release Please configuration](https://github.com/googleapis/release-please/blob/main/docs/customizing.md) and [manifest workflow](https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md) | Multiple release units and configurable increment strategies; follow existing automation rather than imposing manual per-PR bumps. |
| [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) | Structured change intent can feed automation; the actual contract still determines whether that intent is correct. |
| [Addy Osmani's Git Workflow and Versioning](https://github.com/addyosmani/agent-skills/blob/aeac41d4d005999432bb7312f7ff06383a91d59d/skills/git-workflow-and-versioning/SKILL.md) | A direct agent-skill precedent for consumer-oriented versions and separating release execution. Its universal invocation, fixed workflow preferences, blanket SemVer default, and tag-only authority exceed this reference's scope. No wholesale adoption or effectiveness claim. |
| [Matt Pocock's version synchronization](https://github.com/mattpocock/skills/blob/5beb35b040e3de97e54fa9e386d7e42d15c295c2/scripts/sync-plugin-version.mjs) | Concrete example of manifest-derived versions and a read-only consistency check; its Node/plugin implementation stays project-specific. |

The broad search found relevant examples, but no single source suitable for
unmodified cross-project adoption. The short local reference combines the
applicable principles without vendoring upstream text or changing installer
registries. Neither maturity nor effectiveness of a skill is inferred from its
author's reputation or from search ranking.

## Contract Walkthrough

The following are manual checks of the written rules, not model executions or
proof that automatic routing works in a client:

| Scenario | Required interpretation |
| --- | --- |
| CalVer project with Python package metadata | Preserve its calendar policy and Python syntax; do not impose SemVer. |
| A breaking CLI removal followed by a small fix | Assess the entire release against its previous release, including the removal. |
| Dropping a compiler version | Consult the ecosystem and declared support contract rather than always choosing one bump class. |
| An incompatible `0.x` change | Apply the stated policy and resolver semantics, and explain migration impact. |
| Manifest-driven plugin version plus `v`-prefixed tag | Keep one source and an explicit mapping; check consistency mechanically. |
| Backport to an older supported release line | Compare with that line's previous release, not the newest unrelated tag. |
| Existing release artifact is wrong | Issue a new version; do not overwrite its published identity. |
| Routine private refactor | Do not force a release or expand calibration's ordinary-local trigger. |
| Version metadata updated but registry not checked | Report the metadata change; do not claim publication or deployment. |

## Validation And Limits

Validate Markdown, local links, skill reference discovery, and existing routing
contracts with repository entrypoints. No installer, dependency, or release
implementation changes are part of this increment. Full installer/coverage
runs and model-backed comparisons are unnecessary for the stated documentation
contract; automatic discovery and real-work behavior remain unmeasured.
