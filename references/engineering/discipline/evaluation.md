# Agent And Workflow Evaluation

Use this reference to determine whether an agent, skill, harness, or workflow
performs better on representative work.

Evaluation is not [verification](verification.md). Verification checks whether
the current change satisfies its stated contract. Evaluation compares behavior
across selected tasks, repetitions, conditions, or versions and supports a
broader quality claim.

## Evidence Loop

Use the following progression:

```text
production or task evidence
-> expert review
-> repeated failures grouped
-> actionable finding
-> targeted evaluation
-> scoped change
-> targeted and regression evaluation
-> measured rollout
```

A single correction, complaint, or surprising output is evidence to review. It
does not automatically become a rule, prompt, task, or evaluation case.

## Findings

Before authoring an evaluation, distinguish among:

- product or workflow defect;
- grader or rubric defect;
- noisy, incomplete, or incorrectly interpreted evidence;
- unsupported or intentionally out-of-scope behavior.

An actionable finding states:

- the representative input and relevant context;
- the observed failure;
- the expected result or required behavior;
- why the difference matters;
- a success condition that can be judged.

Group related failures only when one bounded cause or intervention can
plausibly address them. Preserve uncertain explanations as hypotheses.

## Evaluation Proportionality

Choose the smallest evidence surface that can support the claim:

- use static validation and ordinary verification for wording, navigation,
  link, ownership, or deduplication changes that do not claim changed agent
  behavior;
- use focused representative cases when one scoped behavior may change; and
- use repeated blinded targeted-and-regression comparison only for an
  important behavior change, adoption of a new behavioral baseline, or a
  decision where model variance could materially change the outcome.

Do not start a broad model-backed A/B merely because a skill or engineering
reference changed. State the behavioral claim and decision it must support
before choosing the evaluation size.

## Evaluation Design

Match the evaluation to the claim. For comparative agent or skill evaluation:

- freeze baseline and candidate sources;
- use the same model, reasoning effort, tools, fixtures, and turn protocol;
- start each run in a fresh context and isolate mutable homes or workspaces;
- repeat cases when model variance can change the conclusion;
- hide arm identity during comparative judging;
- keep holdout cases separate from cases used to author the change;
- require every expected scorecard field before treating a blind comparison as
  complete or summarizing arm preferences;
- record interrupted or resumed run identity so conditions cannot drift.

Static validation, parseable cases, and a successful runner prove that the
evaluation machinery works. They do not prove that the candidate is better.

## Metrics And Decision Gates

Treat task correctness, required behavior, and critical failures as primary.
Use time, turns, and tokens as secondary measures after quality gates pass.

Do not treat shorter output, fewer tokens, or faster completion as improvement
when the candidate loses required behavior or introduces a critical failure.
State when results support only regression acceptance rather than comparative
superiority or statistical confidence.

## Evidence And Privacy

Customer data, private production traces, credentials, isolated agent homes,
and private arm maps do not belong in a public repository. Commit synthetic or
sanitized fixtures, compact reviewed findings, hashes, schemas, and
reconstructable references instead.

Keep raw evidence only in an approved private location with the minimum
retention and access needed for review.

## Rollout

After targeted and regression evaluations pass, test the change on a bounded
real workflow. Measure the expected effect and watch for adjacent failures.
Promote a project observation into cross-project guidance only after its
evidence and applicability boundary are stable.

## Completion

Complete an evaluation claim only when the finding, inputs, conditions,
scoring, repetitions, results, limitations, and rollout decision are recorded.
If judging is incomplete, report the incomplete state rather than inferring a
winner.
