# Calibration Body Compression And Routing Diagnosis

Status: three reference bodies adopted locally for a reversible trial;
entrypoint descriptions and routing retained. No general efficiency claim.

## Decision

Adopt the reviewed compression of `principles.md`,
`discipline/verification.md`, and `discipline/debugging.md` under
`skills/calibration/references/`. Together they shrink from 7,808 to 5,507 bytes
(29.5%). Consolidate repeated workflow, communication, API, verification, and
debugging prose. Configuration/defaults and project-knowledge sections remain
byte-identical. Preserve compatibility checks, final-artifact evidence,
external-state readback, and explicit unchecked boundaries.

Debugging may start from an existing concrete failure record when fresh
reproduction is unavailable or unnecessary. The original failing surface,
causal evidence, final verification, and remaining uncertainty still matter.
The guidance does not prohibit a fresh failing test.

Keep both skill descriptions, calibration's entrypoint body and completion
rule, the global instruction template, repository overview-reading rules, and
`design/codebase.md` unchanged. The previous comparison did not exercise the
design reference; it did not attribute extra skill selection to any one of
the candidate changes.

## Evidence And Adoption Boundary

The preceding comparison used baseline
`15135fbd5d3e70edbb79d5293beeaa0687e4df23` and a frozen seven-file candidate:
eight cases, two arms, and two repeats, requesting GPT-6 Astra at medium effort.
Both arms passed all 16 independent artifact checks and had no critical blind
review failures. Candidate cumulative input plus output tokens increased 4.8%,
while uncached input decreased 2.0%. Calibration reads increased from 7/16 to
10/16. This supports a bounded regression acceptance, not an efficiency or
whole-bundle adoption claim. These three reference bodies were actually loaded
in that comparison; each individual edit was not separately ablated.

The user authorized body compression first and trigger diagnosis afterward.
The follow-up [routing diagnosis](../../evaluations/calibration-routing-diagnosis/README.md)
holds the adopted bodies fixed and varies only entrypoint descriptions or
repository overview-reading instructions. It records observed first reads,
functional outcomes, and attribution limits. It does not authorize promotion
of the metadata candidates.

The local installed calibration entry is a symlink to this repository, so new
reference reads see the adopted bodies. This installation observation is
specific to the implementing environment. No installer or invocation-policy
change is needed or implied.

## Validation And Reversal

Validation passed: `pdm run validate-skills` (10 skills),
`pdm run validate-markdown-links` (137 Markdown files), and
`pdm run rumdl check` for the six affected Markdown files. The system
skill-creator quick validator passed for calibration. Worktree, staged, and
committed-range diff checks passed. The adopted reference bytes match the
executed trial sources; unchanged entrypoints match the baseline commit.

The executed model experiments supply behavioral evidence separately from
those static checks; they do not establish production performance or
statistical equivalence. The full `pdm run check` suite and installer dry run
were not repeated for this reference-and-record-only increment: runtime code,
installer behavior, metadata, and routing are unchanged. Real-world rollout
performance remains unverified.

To reverse this trial, restore only the three named reference bodies from
the baseline commit after inspecting intervening edits. Preserve unrelated
work and all experiment records. Source hashes and the exact adopted scope
are recorded with the routing diagnosis.
