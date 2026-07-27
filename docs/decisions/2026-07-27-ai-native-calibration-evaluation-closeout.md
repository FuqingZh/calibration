# AI-Native Calibration Evaluation Closeout

Version: v1.0
Date: 2026-07-27
Status: historical read-only regression acceptance; succeeded by
`2026-07-27-ai-native-writable-implementation-evaluation-closeout.md`

## Decision

Retain the outcome-autonomy direction and the current candidate for bounded
delivery, but do not claim that it improves model behavior over the accepted
baseline.

The candidate passed every targeted and regression critical gate and matched
the baseline's required-behavior coverage. It therefore has representative
regression acceptance for the evaluated surface.

It did not win the blind comparison. Across both stages, the baseline received
more pairwise preferences, and combined runtime was effectively unchanged.
The candidate is retained because the narrower trigger and outcome-autonomy
language are an explicitly accepted policy direction with no measured critical
or required-behavior regression, not because the experiment demonstrated
comparative superiority.

Do not use this closeout to justify additional process removal, wider
autonomous permissions, implementation-plan simplification, or host-specific
orchestrator changes.

## Evaluated Candidate

- Baseline: `a4a9a711fbfc50ee093242091af85074341480e9`
- Candidate: the same `HEAD` plus the captured 2026-07-27 worktree changes
- Candidate patch SHA-256:
  `8f83e439bbbf52c654572a7695a3a2053e5d9ccb3946a7988cc8a6eef1e0cdc7`
- Candidate surfaces:
  - outcome-autonomy principles;
  - narrower global and skill trigger language;
  - three lightweight autonomy behavior cases;
  - static contract assertions and documentation.

The evaluation snapshot was frozen before model execution. Repository files
were not changed during either arm run.

## Frozen Protocol

- Codex CLI: `0.144.1`
- Model: `gpt-5.6-sol`
- Reasoning effort: `medium`
- Repetitions: 3
- Arms: 2
- Cases: 8
- Sessions and turns: 48 sessions, 48 turns
- Blind pairs: 24
- Sandbox: read-only arm execution
- Web search: disabled
- Context: fresh ephemeral session and isolated Codex home per arm
- Case-set SHA-256:
  `ae4d61a01f56e6fe5546e851afe1a15e53bfa13f3b117257c1ba66d58768dae8`
- Fixture-tree SHA-256:
  `838e32136b63fc1b7750d0a8395a70a1ec5d1c4e1f391d6b0357d74b02758fb2`
- Runner SHA-256:
  `1c92ca0583532c3630c6ec028e89f9de8452b9b5461924f166383a5e8ac14699`
- Blind-package generator SHA-256:
  `b96373a135e3b7331a6b0ef73e902a90f88b6615ca64c8b3931089a730942ca7`
- Summarizer SHA-256:
  `09f829319bad8f9f6aea7a8932acd1e5517e06ff4b505c9aff44cd52f258c57c`

The targeted stage contained the three new autonomy cases. Regression started
only after both arms passed every targeted critical gate. The regression stage
then covered calibrated non-local review, repository-local priority, negative
implicit invocation, human escalation, and orchestration adoption.

## Blind Review Integrity

Targeted and regression outputs were judged in separate fresh isolated Codex
tasks. Each judge received only:

- left and right transcripts;
- the case rubric;
- an empty scorecard.

Neither judge received the source map, candidate diff, intended conclusion,
other-stage results, repository history, or previous evaluation decisions.
Each completed and mechanically validated every scorecard row before the map
was revealed.

- Targeted scorecard SHA-256:
  `55780e5dac1b7f544f84d6a92ad54248c24a0a76b074f8968ff19d4943f93f84`
- Regression scorecard SHA-256:
  `ae4096dd4af200c5b16741200e2b4fe88604266e449a1746fe2a816ba09c5806`

Raw outputs, isolated homes, private arm maps, and judge-only packages remain
temporary local artifacts and are not committed.

## Results

### Targeted autonomy stage

| Measure | Candidate | Baseline |
| --- | ---: | ---: |
| Critical gates | 9 pass / 0 fail | 9 pass / 0 fail |
| Required-behavior coverage | 85.2% | 85.2% |
| Pairwise preferences | 2 | 4 |
| Ties | 3 | 3 |
| Mean turn time | 40.51 s | 50.93 s |
| Mean input tokens | 41,606 | 71,759 |
| Mean output tokens | 877 | 1,451 |

The targeted stage passed its continuation gate because neither arm had a
critical failure. The candidate was cheaper on this stage, but the baseline
received more blind preferences.

All six `autonomy-bounded-repair` outputs omitted one required detail: an
explicit user request for staged approval would override the normal autonomous
default. This is a case sensitivity shared by both arms, not evidence that the
candidate introduced a regression.

### Regression stage

| Measure | Candidate | Baseline |
| --- | ---: | ---: |
| Critical gates | 15 pass / 0 fail | 15 pass / 0 fail |
| Required-behavior coverage | 96.7% | 96.7% |
| Pairwise preferences | 3 | 9 |
| Ties | 3 | 3 |
| Mean turn time | 63.44 s | 56.32 s |
| Mean input tokens | 85,528 | 70,490 |
| Mean output tokens | 1,950 | 1,801 |

The candidate won two of three calibrated non-local review pairs. It lost
pairwise preferences on repository-local priority, negative implicit
invocation, and human-escalation cases mainly at equal required coverage.

The strongest preference loss was the orchestration gate, where the baseline
won all three pairs. Both arms passed every gate, but candidate outputs more
often added irrelevant current-host AO detail instead of stopping at the
proportional adoption decision. The edited autonomy and trigger text does not
directly establish causation for that output difference.

### Combined result

| Measure | Candidate | Baseline |
| --- | ---: | ---: |
| Critical gates | 24 pass / 0 fail | 24 pass / 0 fail |
| Required-behavior coverage | 92.36% | 92.36% |
| Pairwise preferences | 5 | 13 |
| Ties | 6 | 6 |
| Mean turn time | 54.84 s | 54.30 s |
| Mean input tokens | 69,058 | 70,966 |
| Mean output tokens | 1,548 | 1,669 |

The combined result supports regression acceptance only. Token use was
slightly lower for the candidate, but runtime was effectively unchanged and
pairwise preference favored the baseline.

## Interpretation

The accepted baseline already behaved autonomously on the three new targeted
cases. The new guidance therefore clarified policy without producing a
measurable correctness or coverage gain on this read-only fixture.

This evaluation also does not demonstrate that the narrower trigger reduces
friction during real implementation. The targeted prompts asked the model to
inspect and explain how it would proceed without modifying files. They measure
decision behavior and context cost, not autonomous code-edit completion,
self-correction after a failing test, or delivery quality.

The pairwise result is not evidence that outcome autonomy is the wrong
direction. It is evidence that this candidate and evaluation do not support a
claim of general behavioral improvement.

## Rollout Decision

- Keep the three candidate changes in the current bounded calibration change.
- Describe the result as regression acceptance, not optimization.
- Do not broaden the trigger reduction or remove existing compatibility,
  verification, permission, or human-authority gates.
- Do not add more skill prose merely to win the staged-approval wording case;
  direct user instructions already have higher precedence.
- Treat irrelevant AO narration as an observation. Require repeated evidence
  before changing the harness route.
- If a later change claims reduced implementation friction, evaluate writable
  isolated tasks with actual edit, failing-test, self-correction, and final
  artifact gates.

## Reopen Conditions

Reopen this candidate decision if:

- a real repository task shows that the narrower trigger misses a public or
  compatibility-sensitive boundary;
- repeated tasks show that ordinary local implementation still invokes
  calibration unnecessarily;
- autonomous writable-task evaluation shows a critical or required-behavior
  regression; or
- a successor candidate declares and passes a stronger comparative gate.
