# Mission: Classify Retryable Read Failures

## Why
Make safe retry decisions for read failures in the engineering project.

## Success looks like
- Correctly classify three read-failure examples as retryable or not retryable.
- Justify each classification using both required conditions: an idempotent operation and a transient failure.

## Constraints
- Focus on the project's stated retry-safety contract.
- Begin with one small diagnostic before teaching a reusable lesson.

## Out of scope
- Retry policy implementation, backoff design, and write-operation retries.
