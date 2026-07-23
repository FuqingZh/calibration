# Harness Successor Evaluation Closeout

Date: 2026-07-21

Status: Rejected

## Context

Draft pull request #7 proposed a narrow successor to the rejected behavior
candidate from pull request #5. It reduced repeated harness instructions, clarified
documentation authority, compressed harness levels into a proportionality
rule, and narrowed the calibration skill trigger without changing the frozen
19 behavior cases.

The v1.2 plan required a six-case targeted gate before running the remaining
13 regression cases. Passing the targeted gate authorized only the regression
run, not merging the candidate.

## Decision

Do not merge pull request #7 or retain candidate
`bcd20499f56646dd31bbabae9ffdec3cd1e5ac3f` as a behavioral baseline. The
candidate passed every targeted continuation gate, but failed two predeclared
Stage B gates: regression required-behavior coverage was below the baseline and
regression pairwise wins were fewer than losses.

There was no critical regression, and the aggregate 19-case result favored the
candidate. Those observations do not override a failed regression-stage gate.
Slice 4 and project pilots remain closed.

The repository-harness and behavior-evaluation ownership boundary remains
accepted. This closeout rejects the pull request #7 implementation candidate,
not that ownership decision.

## Frozen Evaluation Scope

- Accepted baseline: `5a8c0649b8d5301c98d36a77f9520293678fb556`
- Successor candidate: `bcd20499f56646dd31bbabae9ffdec3cd1e5ac3f`
- Candidate pull request: #7, kept Draft during evaluation
- Codex CLI: `0.144.1`
- Model and reasoning effort: `gpt-5.6-sol`, `medium`
- Matrix: 19 cases, 3 repetitions, 2 arms, 114 sessions, 126 turns, and 57
  blind pairs
- Workers and order: 4 workers with a seeded full shuffle using `20260717`
- Experiment fingerprint:
  `34afe52eb8e391f2ed12e26c68b3f983b191a943f6fffe7b3f95e570b50d4f98`
- Case-set SHA-256:
  `ef4daeb4521a6e66d45f3514cbba26dc3497e77156f29ab0ad947b16b68bbcd6`
- Fixture-tree SHA-256:
  `a0e4712e9a59ba69cfca9fcfef511610946e901486d09dc5698137681d56bb61`
- Protocol SHA-256:
  `fa6b0fce6f727f699961b8d83c1c88f5e160a3e9b018c02ce8126c3ff55eb897`
- Frozen Codex system-skill tree SHA-256:
  `55e4e2d4600ac8314750dfac228c7071dbbec674c323b79d9a1f65c45d580d84`

Protocol version 4 added named subset blind packages so Stage A could be
reviewed and gated without requiring or exposing Stage B results. It did not
change case definitions, fixtures, model settings, or arm inputs.

## Evaluation Integrity And Independent Review

- All 114 sessions ran from zero under one frozen fingerprint; none were
  resumed and none failed.
- The targeted stage completed 36 sessions and 18 blind pairs before the
  regression stage was allowed to start.
- Every result was revalidated against its source, case, turn, fixture,
  workspace, model, effort, protocol, and runtime system-skill identity before
  blinding.
- One fresh independent judge task received only left/right transcripts,
  rubrics, a blind manifest, and an empty scorecard. It saw neither arm maps,
  raw execution records, repositories, commits, nor prior conclusions.
- The judge completed and validated all 18 targeted rows before the Stage A
  map was revealed. It later completed all 39 regression rows before the Stage
  B map was revealed.
- Stage-specific blind files and deterministic maps matched the final complete
  57-pair package exactly.
- Targeted scorecard SHA-256:
  `2dece097169e6b256f7052dae3c48a20e8c00deefa6504ba21866e44d4c61961`
- Regression scorecard SHA-256:
  `e528eb6ab834fd2bfa066d1830ed28b67a63fc651660a6d9e9821e85dd92c770`
- Complete scorecard SHA-256:
  `8052c0ac09fbbd1082490ae4c641378e2e18eeb6fe40d5c600ecf061b2ccd66b`
- Raw outputs, scorecards, judge-only material, runtime homes, and private arm
  maps remain local temporary artifacts and are not committed.

## Results

Primary measures are shown before runtime and token measures. Required figures
are mean per-output rubric coverage.

| Scope | Pairs | Candidate critical | Baseline critical | Candidate required | Baseline required |
| --- | ---: | ---: | ---: | ---: | ---: |
| Targeted Stage A | 18 | 18 pass / 0 fail | 17 pass / 1 fail | 87.2% | 79.7% |
| Regression Stage B | 39 | 36 pass / 3 fail | 36 pass / 3 fail | 94.0% | 95.7% |
| All cases | 57 | 54 pass / 3 fail | 53 pass / 4 fail | 91.9% | 90.7% |

| Scope | Candidate wins | Baseline wins | Ties | Exploratory two-sided sign p |
| --- | ---: | ---: | ---: | ---: |
| Targeted Stage A | 12 | 5 | 1 | 0.1435 |
| Regression Stage B | 15 | 20 | 4 | 0.4996 |
| All cases | 27 | 25 | 5 | 0.8899 |

Stage A passed all four continuation gates:

- the candidate had 18/18 critical passes;
- `harness-human-escalation` passed 3/3 candidate repetitions;
- candidate required coverage exceeded the baseline; and
- candidate pairwise wins exceeded baseline wins.

Stage B passed both critical gates but failed both comparative gates:

- no baseline-pass/candidate-fail critical regression occurred;
- candidate and baseline each had three critical failures, all in
  `docs-five-public-modes`;
- candidate required coverage was 94.0%, below the baseline's 95.7%, with the
  observed deficit in `docs-private-helper` and `grilling-plan`; and
- candidate pairwise wins were 15, below the baseline's 20.

The strongest regression preference losses were `calibration-routing`,
`grilling-plan`, and `writing-great-skills-negation`, each 0-3. These
associations do not establish that the narrow harness edits caused the losses.

Runtime remained secondary. Mean turn time was 79.19 seconds for the candidate
and 82.37 seconds for the baseline. Mean input/output tokens were
76,328.4/2,494.5 for the candidate and 82,573.3/2,652.1 for the baseline.

## Decision Boundary

| Question | Decision | Reason |
| --- | --- | --- |
| Stage A continuation | Yes | All targeted critical, human-escalation, coverage, and pairwise gates passed |
| Stage B acceptance | No | Candidate coverage was lower and pairwise wins were 15-20 |
| Critical regression | No | Both arms had three failures and no baseline-pass/candidate-fail pair occurred |
| Retain successor | No | The staged protocol requires every Stage B gate to pass |
| Open Slice 4 pilots | No | Candidate retention is a prerequisite |

## Limitations

- The six targeted cases were selected from the intended change and are not a
  held-out benchmark.
- Fixtures are synthetic and do not establish production impact.
- The matrix used one model, one reasoning effort, three repetitions, and one
  blind judge; it does not measure inter-rater agreement.
- Stage A and Stage B used the same independent judge task. The task remained
  blind to all mappings, but this does not measure reviewer-to-reviewer
  variance.
- Sign-test values are exploratory and do not override staged hard gates.
- The Stage B coverage deficit occurred in unchanged skill areas, and several
  strongest preference losses also occurred outside the edited harness text.
  The run supports rejection under the frozen gate, not a causal attribution.
- Aggregate results cannot be used to bypass the predeclared regression gate.

## Alternatives Rejected

- **Merge because Stage A passed:** rejected because Stage A authorized only
  running regression.
- **Merge because the complete aggregate favored the candidate:** rejected
  because the regression stage separately failed coverage and pairwise gates.
- **Keep rerunning the unchanged candidate:** rejected as outcome shopping
  after a complete valid run.
- **Open a project pilot despite the NO-GO:** rejected because Slice 4 requires
  a closeout that retains the candidate and confirms regression acceptance.

## Consequences And Follow-up

1. Close pull request #7 without merging it.
2. Keep `5a8c0649b8d5301c98d36a77f9520293678fb556` as the accepted behavioral
   baseline; do not treat the pull request #5 or #7 implementations as accepted
   behavior merely because related commits exist on `main` or a branch.
3. Preserve the 19 frozen cases for any immediate comparison, but do not rerun
   this unchanged candidate.
4. If work resumes, first decide whether to isolate the trigger-description
   change from the documentation cleanup or to revert to the accepted baseline
   before proposing another scoped candidate.
5. Keep Slice 4 closed until a later closeout explicitly retains a candidate,
   confirms no critical regression, and passes its declared regression gates.

## Reopen When

Reopen successor work only for a materially scoped new candidate with a new
fingerprint and predeclared evaluation boundary. Reopen project pilots only
after that candidate passes its complete acceptance protocol.
