# Architecture Overview

## Use When

Use this type for current system facts: how the system works now, where the
important boundaries are, and which contracts are active.

## Method Reference

Use the repository's current source of truth and keep the overview concise.
Deeper contracts may live in architecture subdocuments or schemas.

## Local Requirements

- Place it in project `docs/architecture/`, or the repository-local
  architecture location when one already exists.
- State current scope and purpose.
- Describe main components, ownership boundaries, and data flow.
- Link public contracts, schemas, APIs, CLIs, or artifact shapes that callers
  rely on.
- Keep key decisions that still affect implementation short and link their
  decision records.
- Separate current behavior from proposed or historical material.

## Complete When

A future contributor can read it before changing code and distinguish current
behavior from historical or proposed behavior.
