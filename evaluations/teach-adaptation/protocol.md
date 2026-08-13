# Teach Adaptation Evaluation Protocol

Date: 2026-08-13

The first evaluation bundle in this directory froze fixtures, responses,
generated outputs, hashes, and a reconstructed blind scorecard. Review later
found that it did not durably bind those records to individual executor
invocations and did not establish scorecard-before-reveal ordering in Git
history. It remains historical context, not current acceptance authority.

The replacement traceable protocol is under `v2/`. It records invocation UUIDs,
controller events, raw responses, before and after manifests, skill trees,
pre-run Git bundles, post-run patches and status, and exact artifacts. Its blind
packet and empty scorecard were committed before judgment; the raw judgment and
filled scorecard were committed before the arm map was revealed.

Verify the current runs with:

```bash
python evaluations/teach-adaptation/v2/harness.py verify
```

The records are controller-captured and internally verifiable, but they are not
externally timestamped or cryptographically attested. The runner did not expose
backend session IDs, exact model build, or reasoning setting.
