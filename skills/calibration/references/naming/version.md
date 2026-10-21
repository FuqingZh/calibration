# Version Naming And Compatibility

Use for version identifiers, release increments, and the compatibility meaning
of a version. Follow the repository's declared policy and the target ecosystem's
syntax. For SemVer projects, follow [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html).
A calendar-based policy may be appropriate; do not infer compatibility from
its date fields. [PyPA's versioning guide](https://packaging.python.org/en/latest/discussions/versioning/)
illustrates the distinction between version syntax and versioning policy.

Local additions:

- Identify the versioned unit and its public contract: package, application,
  API, schema, or dataset. Follow its independent or coordinated release policy;
  a shared repository does not by itself require a shared version.
- Assess consumer-visible changes since the preceding release on the target
  release line. Select the increment for the complete release, including
  deprecations and incompatible changes, rather than from the latest commit
  alone. Follow configured commit-based automation and check that its proposed
  increment matches the actual compatibility impact.
- Include documented CLI behavior, configuration, schemas, outputs, and support
  requirements in the compatibility assessment. Use the ecosystem's guidance
  and repository support policy to classify changes; a small diff or a bug-fix
  label does not establish compatibility. When impact is uncertain, identify
  affected consumers and the evidence needed before claiming a compatible bump.
- For `0.x` and prereleases, follow explicit repository policy and dependency
  resolver semantics. Do not treat an unstable version as permission to ignore
  consumer migration needs or as a guarantee of compatibility.
- Keep one authoritative version source per release unit, whether a manifest,
  VCS tag, or build configuration. Derive other representations or check their
  consistency mechanically, following the repository's declared mapping.
  See [PyPA's single-source guidance](https://packaging.python.org/en/latest/discussions/single-source-version/).
- Use native tooling for version parsing, ordering, and prerelease spelling.
  Package versions, Git tags, and container tags may use different spellings;
  preserve their mapping instead of forcing identical strings.
- Keep published version identities and release artifacts immutable. Publish
  corrections under a new version; do not repoint a released version tag or
  overwrite an artifact. Distinguish moving channel aliases such as `latest`
  from immutable version identifiers.
- Record consumer-visible changes and migration guidance in the repository's
  release-note mechanism, especially for deprecations, removals, and incompatible
  changes. Version bumps and release timing follow repository policy; a commit
  or pull request alone does not require a new release.

Version selection does not authorize publication or prove deployment. Use
[verification](../discipline/verification.md) for release completion claims;
keep release commands, credentials, and deployment steps in the owning repository.
