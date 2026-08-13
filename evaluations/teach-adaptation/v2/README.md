# Teach Adaptation Traceable Evaluation V2

Date: 2026-08-13

This directory contains a fresh 16-run evaluation created after review found
that the earlier sanitized bundle was internally consistent but could not tie
its records to durable individual invocations.

For every run, `harness.py` now retains:

- a UUID invocation ID and controller-selected executor label;
- the exact controller task and user prompt;
- the raw final response containing the same UUID;
- controller `prepared` and `captured` events;
- before and after SHA-256 filesystem manifests;
- the selected skill commit and tree before and after execution;
- a Git bundle containing the exact pre-run project fixture;
- project Git status and a binary diff after execution; and
- exact changed artifacts with hashes.

The records are controller-captured and reviewable but are not externally
timestamped or cryptographically attested. The runner still does not expose a
backend session ID, exact model build, or reasoning setting; each invocation
records those gaps explicitly.

`blind-packet.md` is generated from captured runs and contains randomized local
A/B arms with paths and UUIDs removed. The Git history establishes ordering:

1. commit `bd6fc99` contains the runs, packet, and empty scorecard without an
   arm map;
2. commit `2322cb3` adds the fresh judge's UUID-bound raw response and filled
   scorecard, still without an arm map; and
3. the following result commit reveals `arm-map.json` and interprets the
   already-frozen judgment.

The judge's canonical task value is an orchestrator namespace, not a filesystem
home. The immutable raw response and its scorecard retain that exact value
under a path-scoped public-portability allowlist.

The reveal maps every non-tie preferred local arm to the candidate. The judge
found no candidate critical failure, found upstream critical failures in C01
through C05, and tied both arms in C06.

Verify completed runs with:

```bash
python evaluations/teach-adaptation/v2/harness.py verify
```

Do not edit raw run files or generated artifacts. If a run is invalid, replace
it with a new UUID and preserve the rejected run separately rather than
rewriting its record.
