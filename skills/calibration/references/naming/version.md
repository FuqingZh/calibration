# Version Sources And Release Contracts

Identify the versioned unit and the repository's declared versioning and release
policy. Consult the relevant source rather than inferring compatibility from a
version string or imposing one scheme across ecosystems:

- [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html) for projects adopting SemVer.
- [PyPA versioning](https://packaging.python.org/en/latest/discussions/versioning/)
  for Python version syntax, scheme choices, and ecosystem behavior.
- [PyPA single-source guidance](https://packaging.python.org/en/latest/discussions/single-source-version/)
  for Python version-source integration. Use the native build and release tools
  for other ecosystems.

Keep repository-specific version sources, tag mappings, release automation, and
migration commitments in the owning repository. Preserve the existing release
contract when changing them; use native tooling for parsing and ordering.

Version selection does not authorize publication or prove deployment. Follow
[verification discipline](../discipline/verification.md) for release completion.
