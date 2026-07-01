# Decision Record

Use this type for settled, high-impact choices where the reason matters and
cannot be cheaply recovered from current code or architecture docs.

## Where It Lives

Prefer project `docs/architecture/` or a repository-local decision directory if
one already exists.

## Required Content

- Decision date and status.
- Context that made the decision necessary.
- Alternatives considered.
- Chosen decision.
- Consequences, including costs and follow-up obligations.
- Conditions that would justify reopening the decision.

## Do Not Include

- Routine implementation choices.
- Decisions with no real alternative.
- Current architecture explanation that belongs in `architecture-overview.md`.
- Unsettled proposals that belong in `design-proposal.md`.

## Complete When

A future contributor can understand why the current direction exists and avoid
re-litigating the same tradeoff without new evidence.
