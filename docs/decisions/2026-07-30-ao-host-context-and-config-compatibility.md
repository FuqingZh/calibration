# AO Host Context And Configuration Compatibility

Date: 2026-07-30

Status: accepted portable summary

AO diagnosis separates sandbox, worker, daemon, and host state. Sandbox-only
absence is `indeterminate`; it must not trigger persistent configuration
changes. Authoritative host readback owns conclusions about services,
credentials, installed binaries, and private profiles.

The installer may render a pointer to private local authority into global
instructions, but public skills and references do not discover or depend on
that profile directly. Existing Codex configuration, authentication, Apps,
Plugins, and MCP state are outside the installer boundary.
