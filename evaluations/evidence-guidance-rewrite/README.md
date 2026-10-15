# Evidence Guidance Wording Comparison

Date: 2026-10-13. Status: bounded wording trial proposed for review.

## Change And Sources

Four scoped changes in three existing files make diagnostic decisions and
evidence presentation more explicit:

- [Harness](../../skills/calibration/references/discipline/harness.md): connect
  an actually-read entrypoint to existing authority, and investigate stale or
  conflicting content when navigation already works. Classify mechanical and
  contextual findings; inspect existing checks and their wiring before adding
  another constraint.
- [Retrospect](../../skills/retrospect/SKILL.md): identify the next concrete
  action without requiring a new permanent rule for a local omission. Keep
  unsupported causes and verification gaps explicit.
- [Verification](../../skills/calibration/references/discipline/verification.md):
  match evidence to the claim, distinguish bug-fix comparisons from preserved
  refactor invariants, and disclose unavailable baseline evidence. Explain
  affected consumers and effects that survive a code rollback.

The wording adapts diagnostic and presentation ideas from Matt Pocock's
[retro](https://github.com/mattpocock/skills/blob/49dd158d1076134a641b33efb035946536778336/skills/engineering/retro/SKILL.md)
and [pr](https://github.com/mattpocock/skills/blob/49dd158d1076134a641b33efb035946536778336/skills/engineering/pr/SKILL.md).
The upstream PR skill credits Humanlayer's
[show-me](https://github.com/humanlayer/skills/blob/main/plugins/show-me/skills/show-me/SKILL.md)
for its visual explanations; this change imports neither that template nor its
visual examples. No third-party skill is installed or replaced.

Local evidence, authorization, host-observation, compatibility, proportional
validation, and explicit retrospective invocation boundaries remain in force.
The baseline principles, calibration entrypoint, retrospective metadata and
existing test prompts, installer, lockfile, and evaluation policy are unchanged.
Their hashes and the exact tested candidate hashes are in the
[source manifest](source-manifest.json).

## Protocol And Evidence

Baseline: `f00ef2cc0dde0277c4b8e2768f9fc0f77dd65163`. The candidate is the three
file versions identified by the manifest, not a floating working-tree label.

- [Cases](cases.json): 11 targeted cases plus all nine existing retrospective
  prompts and expectations, copied unchanged. Expected behavior was frozen
  before execution and withheld from evaluators.
- [Protocol](protocol.json): one fresh agent context per arm and guidance group,
  with no conversation-history fork or model override. Cases within a group
  share context. Guidance is directly supplied, so skill selection and routing
  are outside the claim.
- [Responses](responses.json): all 40 original answers, without replacement.
- [Results](results.json): independent blind judgments, including partial
  scores, reasons and the subsequently revealed side mapping.

Each evaluator received only its guidance and user scenarios. Responses were
limited to 180 words per case. The judge received the scenario, predeclared
expectation and anonymous answer pair, with side order shuffled using seed 42.
It judged decisions rather than matching phrases or rewarding length. An
author review checked the completeness of the records and critical failures.

The agent interface inherits the parent configuration but does not expose an
independently verifiable exact model and effort identity. These results cannot
be attributed to a named model family. Shared platform instructions also
remain a possible influence. Four evaluator sessions retried output saving
with `python3` after `python` was unavailable; no scenario was replaced.

## Initial Results

| Cases | Baseline | Candidate |
| --- | --- | --- |
| Targeted H1-H6, V1-V4, R10 | 11 pass | 11 pass |
| Existing retrospective R1-R9 | 7 pass, 2 partial | 7 pass, 2 partial |
| Critical failures | 0 | 0 |

The blind judge rated every pair a tie. The candidate did not show a material
decision-quality advantage or a candidate-only regression in these responses.
Both versions reused existing checks, distinguished working feedback from
missing capability, avoided duplicate authority, and preserved uncertainty,
authorization and compatibility in the supplied cases.

The two partial results remain visible:

- **R5:** both answers bounded investigation around the supplied import/F401
  symptoms, but did not fully describe the search sources or fallback to
  standard depth when no credible search boundary exists.
- **R7:** both recognized persistence authorization and named the required
  references, but did not spell out the retrospective destination and index
  update. The first probe supplied only the entrypoint, withheld the referenced
  persistence guidance, and provided no confirmed lesson content. It therefore
  cannot establish the complete persistence procedure.

The follow-up supplies explicit evidence conditions for these two boundaries
and the unchanged persistence references to both arms. Its
[cases](followup-cases.json) are separate from the original regression prompts;
they do not replace or retroactively upgrade the initial scores.

Both arms passed **2/2 follow-up cases**, with both blind comparisons tied and
no critical failures. F1 explicitly exercises the fallback when no credible
search boundary can be formed. F2 supplies the confirmed lesson and persistence
references; both answers name `.traces/retros/` and the short index update while
preserving evidence and promotion boundaries. The
[follow-up responses](followup-responses.json) and separate judgments in
[results](results.json) remain response-only evidence. No guidance was changed
between the initial comparison and this follow-up.

## Validation And Limits

Local validation used the locked Python 3.12.15 environment and PDM 2.26.9:

- 119 tests passed across skill validation, public portability, document-type
  routing, repository adoption and review-convergence contracts.
- All 64 installer tests passed, and an installer dry run used an isolated
  temporary Codex home.
- Lockfile consistency, repository skill validation and Markdown link checks
  passed. Final Markdown and diff checks cover the evidence record too.
- The system skill-creator quick validator passed for calibration. It rejected
  retrospect's existing `disable-model-invocation` field on both baseline and
  candidate. The repository validator accepts that supported explicit-only
  contract; the field and validator were preserved.

These are response-only probes and deterministic repository checks. They do
not demonstrate real command execution, persistence, enforcement of sandbox
permissions, live host access, automatic skill routing, or client parity. The
cases were authored while the candidate was known, not held out. There is one
answer per case per arm and no latency/token measurement or statistical
superiority claim. The retained partial scores are not complete behavioral
acceptance of every existing retrospective procedure.

The adoption rationale is clearer decision guidance with bounded regression
evidence. General improvement remains unproven; future actual tasks must
establish whether the wording reduces unnecessary rules or makes evidence
easier to review. To reverse, restore only the three changed guidance files
from the baseline after checking intervening edits; retain this evidence.
