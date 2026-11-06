# Schema And Header Contracts

Follow the target protocol, data format, and consumer's existing schema for
field names and exported headers. Repository-owned contracts define any casing
or abbreviation conventions and internal-to-external mappings.

For identifiers, establish the system's identity, uniqueness, stability, and
cross-system mapping requirements. Follow its database, protocol, or domain
standard; reversibility and encoding are choices of the owning contract.

Treat changes to published fields as compatibility changes; preserve mappings
at explicit adapters and verify them against consumers. Use
[verification discipline](../discipline/verification.md) for acceptance evidence.
