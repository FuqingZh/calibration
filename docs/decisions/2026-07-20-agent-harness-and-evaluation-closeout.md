# Agent Harness And Evaluation Closeout

Date: 2026-07-20

Status: Rejected

## Context

Pull request #5 implemented the repository-harness and behavior-evaluation
references defined by the v1.1 plan. Because those references and their six new
behavioral cases encode hypotheses rather than proof of improvement, Slice 3
compared the accepted pre-Slice-2 baseline with the pull request #5 merge under
one frozen expanded matrix.

## Decision

Do not accept the pull request #5 candidate as the next behavioral baseline.
The candidate showed useful targeted effects, but it failed more critical gates
than the baseline, covered fewer required behaviors overall, and lost the
regression subset 20-9. Those primary measures fail before runtime or token
measures are considered.

Slice 4 is closed. Do not start the `workflows` or `trait_association` pilots
from this candidate. Pull request #5 is already present on `main`; this closeout
does not change skill or reference bodies. A separate fresh task must choose a
narrow correction or reversal and complete a new independent evaluation before
the pilot gate can reopen.

## Frozen Evaluation Scope

- Baseline: `5a8c0649b8d5301c98d36a77f9520293678fb556`
- Candidate: `ab13e379f34b9532c837b624dcd4ff5af96ea17d`
- Codex CLI: `0.144.1`
- Model and reasoning effort: `gpt-5.6-sol`, `medium`
- Matrix: 19 cases, 3 repetitions, 2 arms, 114 sessions, 126 turns,
  and 57 blind pairs
- Workers and order: 4 workers with a full seeded shuffle using `20260717`
- Experiment fingerprint:
  `c382a7d2e0bb233f91685b67b37e2faf58fb938374b2166ba8dfd45bb9dea5a1`
- Case-set SHA-256:
  `ef4daeb4521a6e66d45f3514cbba26dc3497e77156f29ab0ad947b16b68bbcd6`
- Fixture-tree SHA-256:
  `a0e4712e9a59ba69cfca9fcfef511610946e901486d09dc5698137681d56bb61`
- Protocol SHA-256:
  `6ea8f3252221018ac8e0a7072fecc1e01c94acbece9fdc809d33073c6343ac9c`
- Frozen Codex system-skill tree SHA-256:
  `55e4e2d4600ac8314750dfac228c7071dbbec674c323b79d9a1f65c45d580d84`

The final protocol used exact source archives, synthetic fixtures, read-only
workspaces, disabled web search, ignored user configuration and rules, fresh
initial contexts, and isolated per-session Codex homes. Each session received a
private skills root containing a frozen system-skill copy and arm-specific
business-skill links.

## Evaluation Integrity And Independent Review

- All 114 final sessions ran from zero under the same fingerprint; none were
  resumed and none failed.
- Every successful result was revalidated against its source, case, turn,
  fixture, workspace, model, effort, protocol, and runtime system-skill
  identity before blind pairs were created.
- A fresh blind-review task received only the 57 left/right transcripts, their
  rubrics, the blind manifest, and an empty scorecard. It had no arm map, raw
  execution records, repository plan, or previous conclusion.
- The judge completed 57 unique score rows before arm identity was revealed.
  The final scorecard SHA-256 is
  `10157d018c5b4385c38a79b3fcf03d6157033db34ffd513ba50be010fc61759a`.
- A feasibility run was discarded before formal evaluation. A later 114-session
  run with fingerprint `f0ae767746e4894d9a5e3121ed4c45b37187a4a6e4f7d7c605fde7c817749d19`
  was also rejected before blinding when post-run verification detected that
  Codex had installed model-visible system skills into shared arm templates.
  No output, score, or mapping from either discarded run was reused.
- The corrected protocol froze the system-skill input, copied it privately per
  session, verified it before and after each session, and then reran the entire
  matrix.
- Raw outputs, judge-only material, runtime homes, and the private arm map
  remain local temporary artifacts and are not committed.

## Results

Primary measures are shown before pairwise preference and resource measures.
Required-behavior figures are mean per-output rubric coverage.

| Scope | Pairs | Candidate critical | Baseline critical | Candidate required | Baseline required |
| --- | ---: | ---: | ---: | ---: | ---: |
| All cases | 57 | 51 pass / 6 fail | 53 pass / 4 fail | 90.5% | 91.4% |
| Six targeted cases | 18 | 15 pass / 3 fail | 16 pass / 2 fail | 73.6% | 81.9% |
| Thirteen regression cases | 39 | 36 pass / 3 fail | 37 pass / 2 fail | 98.3% | 95.7% |

| Scope | Candidate wins | Baseline wins | Ties | Exploratory two-sided sign p |
| --- | ---: | ---: | ---: | ---: |
| All cases | 20 | 26 | 11 | 0.4614 |
| Six targeted cases | 11 | 6 | 1 | 0.3323 |
| Thirteen regression cases | 9 | 20 | 10 | 0.0614 |

The targeted result was mixed rather than a clean acceptance:

- `evaluation-reviewed-finding` and `harness-orchestration-gate` each favored
  the candidate in all three repetitions.
- `harness-agents-map` and `harness-repeated-operation` each favored the
  candidate 2-1.
- `harness-proportional-small-library` favored the baseline 2-1.
- `harness-human-escalation` favored the baseline 2-0 with one tie. The
  candidate failed its critical gate in all three repetitions by delegating
  discoverable repository facts to the user instead of resolving them first.

The regression subset did not pass. The candidate lost 20-9 with 10 ties and
failed three critical gates in `docs-five-public-modes`, compared with two
baseline failures in the same case. Its higher regression required-behavior
coverage does not override the critical failures or the pairwise loss.

Runtime measures were secondary. Mean turn time was 92.90 seconds for the
candidate and 84.13 seconds for the baseline. Mean input/output tokens were
82,902.1/2,840.2 for the candidate and 84,389.5/2,780.3 for the baseline. These
measures do not repair the failed behavioral gate.

## Decision Boundary

| Question | Decision | Reason |
| --- | --- | --- |
| Regression acceptance | No | More candidate critical failures and a 9-20 pairwise result |
| Comparative superiority | No | Aggregate primary measures do not favor the candidate; p=0.4614 |
| Retain candidate as baseline | No | Targeted gains are offset by targeted and regression failures |
| Open Slice 4 pilots | No | The plan requires retaining the candidate before pilots start |

## Limitations

- The six targeted cases were authored from the intended change and are not a
  held-out benchmark.
- Fixtures are synthetic and do not establish production impact.
- The matrix used one model, one reasoning effort, three repetitions, and one
  blind judge; it does not measure inter-rater agreement.
- Sign-test values are exploratory and do not override critical gates.
- The expanded 19-case aggregate is not directly comparable with the earlier
  13-case evaluation aggregate.
- The regression association does not establish that the new harness and
  evaluation references caused the `docs-five-public-modes` failures.
- Four-worker concurrency and runtime measurements describe this harness run,
  not a general resource benchmark.

## Alternatives Considered

- **Retain the candidate because targeted preferences were positive:** rejected
  because targeted critical and required-behavior results were worse, including
  three failures on human escalation.
- **Accept the candidate because regression required coverage was higher:**
  rejected because critical failures and pairwise preference are prior gates.
- **Keep rerunning the same candidate:** rejected because a new run without a
  scoped correction would turn ordinary variance into outcome shopping.
- **Start bounded pilots while documenting the limitations:** rejected because
  Slice 4 explicitly depends on candidate retention.

## Consequences And Follow-up

1. Treat the current pull request #5 merge as an unaccepted candidate, not the
   next behavior baseline.
2. In a fresh task, choose either a narrow reversal or a successor that fixes
   discoverable-fact escalation without weakening the successful finding and
   orchestration boundaries.
3. Preserve the 19 case definitions for the immediate successor comparison and
   add held-out cases only as a separately versioned evaluation surface.
4. Re-run targeted and regression arms from frozen sources, complete blind
   review before mapping, and fail closed on any incomplete integrity evidence.
5. Keep project pilots closed until a later closeout explicitly reopens them.

## Reopen When

Reconsider this decision only for a scoped successor or reversal evaluated
under a complete blind protocol. Reopen Slice 4 only when that closeout shows
no critical regression, supports retaining the evaluated candidate, and states
the remaining evidence limitations.
