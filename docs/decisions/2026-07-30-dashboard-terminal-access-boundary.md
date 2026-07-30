# Dashboard Terminal-Access Boundary

Date: 2026-07-30

Status: accepted for repository delivery; host deployment remains separately
authorized

## Decision

Preserve the AO v0.11.1 compatibility Dashboard renderer and GET-only API for
clients in `192.168.30.0/24`. Add terminal attachment only through the exact
`/mux` WebSocket route, proxying to the existing AO loopback endpoint at
`127.0.0.1:3001/mux`.

The terminal route allows exactly these client addresses:

- `192.168.30.134`
- `192.168.30.205`

Every other client is denied, including other addresses in
`192.168.30.0/24`. Prefix variants such as `/mux/` do not reach the WebSocket
proxy.

This change does not authorize REST mutations, standalone shell creation,
public exposure, shared-subnet terminal access, host deployment, or a change to
the AO daemon listener. The compatibility artifact and service filenames remain
`ao-dashboard-readonly.*` because external installation and rollback procedures
depend on them.

## Rationale

The renderer and GET-only API are observation surfaces. Terminal attachment is
a control surface because it can interact with an existing AO-managed session.
That difference requires an independent network boundary rather than inheriting
the Dashboard's shared-subnet allowlist.

Authentication is preferable where the serving stack supports it. On this
bounded current-host compatibility adapter, the accepted alternative is an
exact-client private-network allowlist. Terminal access must never be exposed
to a shared subnet or the public Internet.

## Verification Contract

Static repository checks must prove that:

- only `location = /mux` proxies to `127.0.0.1:3001/mux`;
- only `192.168.30.134` and `192.168.30.205` are allowed there;
- the route accepts only GET handshakes, retains bounded proxy timeouts and
  WebSocket upgrade headers, and denies all other clients;
- Dashboard, health, and API reads retain the `192.168.30.0/24` boundary;
- API and renderer mutations remain denied; and
- no standalone shell endpoint or REST mutation route is introduced.

Deployment verification, if separately authorized, must additionally exercise
the WebSocket handshake from both allowed clients and at least one denied
same-subnet client. This decision and pull request do not deploy host
configuration.
