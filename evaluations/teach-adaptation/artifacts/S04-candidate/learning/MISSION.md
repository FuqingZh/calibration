# Mission: Classify retryable read failures

## Why
Make safe retry decisions for read failures by applying the engineering project's retry rule consistently.

## Success looks like
- Correctly classify three read-failure examples as retryable or not retryable.
- Justify each classification by checking both operation idempotency and failure transience.

## Constraints
- Treat the engineering project and the installed teaching skill as read-only evidence.
- Keep all personal learner state inside this learning workspace.

## Out of scope
- Implementing or changing retry behavior in the engineering project.
- Broader retry-system design beyond the three-example classification mission.
