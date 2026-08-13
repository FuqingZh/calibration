# Teach Adaptation Evaluation Protocol

Date: 2026-08-13

This bundle preserves the bounded evaluation used to decide whether the local
`teach` adaptation could enter the standard installation profile. It is not a
general benchmark of teaching quality.

## Run Identity And Invocation

`cases.json` assigns a stable case ID and stores the byte content used to build
each synthetic fixture. `runs.json` assigns every execution a stable run ID,
arm, fixture, workspace label, prompt hash, response hash, source commit, and
source tree.

Each execution used a fresh Codex subagent with no forked conversation context.
The evaluator supplied the selected skill source, isolated fixture path, and
case prompt. It did not supply an intended answer. The current-authentication
case prohibited network access. The runner did not expose a durable backend
session ID, exact model build, or reasoning setting, so the bundle says so
instead of inventing them.

The 12 comparative executions used the frozen candidate at `6dd41c2` and the
upstream baseline at `6acc160`. The installed candidate at `e3152e5` differs
from the comparative candidate only by repository Markdown formatting that
emphasizes file names. Four candidate-only safety executions exercised that
installed tree.

## Filesystem Evidence

The evaluator retained every isolated workspace through evidence capture.
`runs.json` contains, for each run:

- the fixture's before-file and before-directory manifest;
- the controller-captured post-run manifest;
- SHA-256 hashes and byte lengths;
- computed created, modified, and deleted paths;
- project Git `HEAD` and porcelain status; and
- hashes and repository paths for every changed artifact copied under
  `artifacts/`.

The before manifests are the fixture-construction inputs. They were reconciled
byte-for-byte with preserved unchanged run surfaces after the earlier prose
bundle was found to normalize line wrapping. The post-run manifests came from
the preserved workspaces before cleanup. The evidence is reviewable and
machine-checkable, but it is not externally timestamped or cryptographically
attested.

Files under `artifacts/` are exact generated outputs, not repository-authored
documentation. Markdown formatting and local-link gates deliberately exclude
that subtree so validation cannot rewrite the evidence or reject links whose
meaning depended on the original isolated workspace. Their bytes and paths are
instead governed by `runs.json` and `SHA256SUMS`; all surrounding evaluation
documents remain in the normal Markdown gates.

The skill-source rejection run additionally records the selected skill tree
before and after the run. Zero-write claims are decided from manifest equality
and clean Git state, not from the agent's final response.

## Blind Judgment

The judge received only `judge-packet.md`. It did not receive source trees or
`arm-map.json`, and arm letters changed meaning between cases. The critical
requirements in that packet were fixed before judging.

`judge-scorecard.json` is the structured pre-reveal judgment. It contains only
local A/B labels. `arm-map.json` is the separate reveal. This separation makes
the preferred-arm calculation independently checkable.

## Verification

Run:

```bash
(cd evaluations/teach-adaptation && sha256sum -c SHA256SUMS)
pdm run pytest tests/test_teach_contract.py -q
```

The test verifies all declared changed-artifact hashes, the zero-write safety
manifests, source-tree stability, the separate blind scorecard and reveal, and
the bundle checksum inventory.

## Limits

The evaluation used synthetic fixtures, one current agent configuration, one
run per arm outside the repeated first-lesson boundary, and a single blind
judge. It did not measure delayed retention, actual reminder delivery,
long-running course evolution, browser rendering quality, token use, or
production learning outcomes.
