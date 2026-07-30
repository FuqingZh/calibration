# Dashboard Terminal-Access Boundary

Date: 2026-07-30

Status: accepted portable boundary

Dashboard Terminal is off by default. Terminal attachment is a control surface,
even when read-only status pages and GET-only APIs are available more broadly.

A trusted single-user private LAN may opt in only with an exact client IP,
exact WebSocket Origin, exact `/mux` path, and loopback upstream. Origin is
defense in depth, not authentication. Multi-user, dynamic-address, public, or
untrusted-network deployments require authentication.

This decision does not authorize REST mutations, standalone shell creation,
host deployment, or public proxy artifacts. Deployment values and verification
commands belong to private host authority.
