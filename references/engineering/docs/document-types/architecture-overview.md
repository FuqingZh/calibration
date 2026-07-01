# Architecture Overview

Use this type for current system facts: how the system works now, where the
important boundaries are, and which contracts are active.

## Where It Lives

Prefer project `docs/architecture/`, or the repository-local architecture
location if one already exists.

## Required Content

- Current scope and purpose.
- Main components, ownership boundaries, and data flow.
- Public contracts, schemas, APIs, CLIs, or artifact shapes that callers rely on.
- Current source-of-truth links for deeper details.
- Key decisions that still affect implementation, kept short.

## Do Not Include

- Unapproved future plans.
- Long exploration transcripts.
- Completed task retrospectives.
- Historical material unless it explains an active boundary.

## Complete When

A future contributor can read it before changing code and distinguish current
behavior from historical or proposed behavior.
