# AO Host Context And Configuration Compatibility

Date: 2026-07-30

Status: accepted portable contract

## State Ownership

AO diagnosis separates sandbox, worker, daemon, and host state. Sandbox-only
absence is `indeterminate`; it must not trigger persistent configuration
changes. Authoritative host readback owns conclusions about services,
credentials, installed binaries, and private profiles.

## Adoption-Adapter Codex Home

The optional Linux adoption adapter validates its configured worker Codex home
read-only. It requires:

- `[features] apps = false`;
- `[features] plugins = false`; and
- no top-level `mcp_servers`.

It accepts harmless TUI state, extra top-level metadata, and additional
non-conflicting feature keys. Validation must not normalize, rewrite, or delete
the configuration.

This is an adoption-adapter compatibility check, not installer behavior.
`install.sh` does not read, validate, or modify `config.toml`, `auth.json`,
Apps, Plugins, or MCP state.

## Private Authority

The installer may render a conditional pointer to private local authority into
global instructions, but public skills and references do not discover or
depend on that profile directly.
