# Decision Record

## Use When

Use this type for a settled, high-impact choice where the reason matters and
cannot be cheaply recovered from current code or architecture documents.

## Method Reference

Use the [Architectural Decision Records](https://adr.github.io/) model. The
[MADR templates](https://adr.github.io/adr-templates/) are an optional format
reference, not an additional local requirement.

## Local Requirements

- Prefer project `docs/decisions/`, or a repository-local decision directory
  when one already exists.
- Record the decision date and status.
- Explain the context that made the decision necessary.
- Compare the viable alternatives that materially affected the choice.
- State the chosen decision and its consequences, including follow-up
  obligations.
- Record conditions that would justify reopening it.

## Complete When

A future contributor can understand why the current direction exists and avoid
re-litigating the same tradeoff without new evidence.
