# AI-Native Writable Implementation Evaluation Closeout

Version: v1.0
Date: 2026-07-27
Status: comparative improvement

## Decision

Retain the Phase 1 outcome-autonomy candidate and describe the bounded writable
result as a comparative improvement over the accepted baseline.

The candidate passed all nine deterministic runs, received six of nine blind
preferences, improved required-behavior coverage, and reduced mean wall time in
the W01 and W03 case families. The baseline failed one W02 scope gate after
changing a test outside the allowed implementation path.

This result supports the narrower calibration entry and outcome-autonomy
direction for the evaluated reversible Python repairs. It does not establish a
general model, language, repository, or production-delivery improvement.

## Evaluated Arms

- Baseline: `a4a9a711fbfc50ee093242091af85074341480e9`
- Candidate: `c2e91d55f05845f962c7a9082de6adcfa0d283a1`
- Protocol correction: `ba065f1`
- Codex CLI: `0.144.1`
- Model: `gpt-5.6-sol`
- Reasoning effort: `medium`
- Sandbox: `workspace-write`
- Apps and Plugins: disabled
- Context: fresh workspace and isolated Codex home for every run
- Repetitions: 3 per arm and case
- Writable sessions: 18
- Blind pairs: 9

The isolated home contained only authentication and the selected arm. Unrelated
user configuration was ignored. The selected arm's installed rules and each
fixture repository's `AGENTS.md` remained enabled because they are part of the
operating combination under evaluation.

## Protocol Correction

The first 18-run attempt used `--ignore-rules`. Its mechanical result was
candidate 9/9 and baseline 8/9, while blind preference was candidate 4 and
baseline 5. The blind review exposed that the command had also disabled the
selected arm's installed rules and the fixture repository's automatic
instructions.

That attempt is diagnostic only. It did not evaluate the declared combination
of model, loaded context, tools, writable environment, and executable feedback.
The runner was corrected to keep the isolated home and disabled features while
preserving the rules under comparison. Tests now assert that
`--ignore-user-config` is present and `--ignore-rules` is absent. All official
results below come from fresh workspaces after that correction.

## Results

### Primary gates

| Measure | Candidate | Baseline |
| --- | ---: | ---: |
| Deterministic passes | 9 / 9 | 8 / 9 |
| Critical passes in blind review | 9 / 9 | 8 / 9 |
| Required behaviors | 30 / 36 | 27 / 36 |
| Blind preferences | 6 | 3 |
| Ties | 0 | 0 |

The baseline-only critical failure occurred in W02 repetition 3. It correctly
changed `src/schema.py` but also changed `tests/test_adapter.py`, outside the
frozen allowed path set, and then claimed completion despite the deterministic
result reporting failure.

### Preference and wall time by case

| Case | Candidate preferences | Baseline preferences | Candidate mean | Baseline mean |
| --- | ---: | ---: | ---: | ---: |
| W01 direct local repair | 1 | 2 | 31.68 s | 60.56 s |
| W02 evidence overrides a plan | 2 | 1 | 62.33 s | 66.70 s |
| W03 repair and reverification | 3 | 0 | 44.84 s | 68.58 s |
| Combined | 6 | 3 | 46.28 s | 65.28 s |

W01 and W03 satisfy the predeclared repeated-friction gate: every candidate
repetition was faster than its same-case baseline distribution, while final
repository verification remained successful.

### Diagnostic and secondary measures

| Measure | Candidate | Baseline |
| --- | ---: | ---: |
| Unnecessary-process score, lower is better | 3 | 15 |
| Mean input tokens | 107,315 | 141,450 |
| Mean output tokens | 971 | 1,447 |

The candidate's largest advantage was not shorter prose alone. Its trajectories
generally avoided loading the shared calibration reference stack for ordinary
local repairs while still closing the repository test loop. The baseline often
loaded several cross-project references and sometimes scanned above the
workspace before making the same implementation change.

## Findings

### W01: lighter execution is real, but pre-edit feedback remains variable

The candidate won one pair and the baseline won two. Candidate runs were
consistently faster and more scoped, but two candidate repetitions diagnosed
the one-token typo from code and test inspection rather than executing the
failing test before editing.

This is not a critical regression because the final repository check passed and
the defect was directly observable. It prevents using W01 alone as evidence
that lighter calibration improves every required behavior.

### W02: current evidence overrode the prescribed path

Both arms rejected the incorrect `PLAN.md` adapter rewrite. The candidate won
two pairs, passed every deterministic gate, and preserved `src/adapter.py`.
The baseline's third repetition added an unauthorized test change.

This supports treating plans as working hypotheses and executable repository
evidence as the authority for the implementation path.

### W03: the candidate preserved the full feedback loop

The candidate won all three pairs. Every candidate run changed only
`src/metrics.py`, ran the focused and full suites, and completed final
verification. One baseline run demonstrated a useful two-edit
self-correction, but its process cost did not produce a better final outcome.

## Phase Gates

### Phase 3: `NO-CHANGE`

The start gate for changing update placement or the implementation-plan
contract was not met:

- no run created an unnecessary durable plan;
- both arms corrected the stale W02 plan from executable evidence;
- no outcome-only task omitted a material durable boundary; and
- no repeated observation required a new cross-project rule.

Keep the existing implementation-plan contract unchanged.

### Phase 4: `NO-CHANGE`

The start gate for separating current-host AO operation from core judgment was
not met. No writable run loaded AO host details, took an AO action, requested
unnecessary orchestration confirmation, or failed because of the orchestration
route.

Keep the existing general adoption boundary and host runbook unchanged.

## Integrity And Reproduction

- Case tree Git object:
  `d0eed1953b16acb20b19a00e7b4f47f2e829890d`
- Fixture tree Git object:
  `4e0766cefbed2808b36d6419a3526cce39592a95`
- Rubric SHA-256:
  `28e431dbdc5beb3394056bded13d55167e9857465d2a08cc1d5391ead8ce2067`
- Runner SHA-256:
  `db52fccc6b570f0fb7fdcc685b86a6fb3ba1787881f7b8213061627b89ba2d76`
- Blind scorecard SHA-256:
  `b52224391ccc923dc0fd7d69a6e456e18d731e684360a8b73f6bfd7d53697e8c`

The private arm map was revealed only after the scorecard contained all nine
unique pair IDs. Raw trajectories, isolated homes, workspaces, arm maps, and
judge packages remain under temporary local paths and are not committed.

## Limitations

- The fixtures are intentionally small, dependency-free Python repositories.
- All runs used one model and one reasoning effort on one host.
- Concurrent execution introduces timing noise, especially in W02.
- The blind reviewer gave repository-verification credit only when a trajectory
  visibly opened `AGENTS.md`, even though the rules were automatically loaded
  for every run. The required-behavior counts are therefore conservative
  evidence about visible discovery, not a claim that uncredited runs lacked the
  rule context.
- The evaluation covers implementation and local verification, not a pull
  request, CI, review continuation, deployment, or irreversible operation.

## Reopen Conditions

Reopen this decision if:

- a representative local task misses a compatibility or repository boundary;
- another model, language, or dependency-heavy repository reverses the
  critical or preference result;
- repeated work recreates unnecessary planning or shared-reference loading;
- a successor candidate changes the trigger, rule-loading, verification, or
  permission boundary; or
- production delivery evidence contradicts the isolated fixture result.
