# Calibration Component Ablation, 2026-09-11

Status: bounded screening complete; active guidance and installation unchanged.

The clearest compression candidates are repeated general principles and basic
engineering reminders. Seed and naming conventions show a repeatable local
effect. This run finds no component whose removal consistently improves answer
quality, and does not justify archiving an entire skill or removing operational
boundaries.

## Design And Completion

At source commit `15135fbd5d3e70edbb79d5293beeaa0687e4df23`, compare eight
components individually: two tasks per component, full versus minus one
component, two repetitions. All 64 candidate calls completed with zero tool
calls, timeouts, or nonzero exits. All 16 subsequent anonymous judging calls
completed. Independent code acceptance passed 20/20 submitted implementations.
No critical functionality, authority, or false-completion defect was identified
within the frozen cases and probes.

The requested model was `gpt-6-astra`, medium effort, through Codex CLI 0.154.0.
This records the invocation; the ephemeral stream does not independently attest
the server-side model. The fixed global template and native CLI context remain
in both arms. The [protocol](PROTOCOL.md) defines loading, exclusions, blinding,
and interpretation limits.

## Results

Scores count four frozen criteria for each of four answers per arm, with a
maximum of 16 per component. Local seed, naming, and expression preferences are
separately identified in the [rubric](rubric.json) and [scores](scores.json).
Token changes are the median paired change in reported input plus output when
removing the component. They are descriptive loaded-context costs, not billing
amounts or measured speed improvements.

| Removed component | Full / 16 | Minus / 16 | Removed prompt bytes | Paired token change | Reading |
| --- | --- | --- | --- | --- | --- |
| General principles | 16 | 16 | 1,781 | -1.7% | No observed gain on the local-work negative controls |
| Native abstractions | 16 | 16 | 1,187 | -1.6% | CSV parser and SQL choices remained correct |
| Configuration | 16 | 14 | 932 | -0.7% | Both removed runs lost default seed 42; functional probes passed |
| Communication | 16 | 16 | 706 | -0.6% | Both expression cases tied |
| Function and variable naming | 16 | 14 | 8,429 | -8.6% | Both removed runs lost scan/sink consistency |
| Codebase design | 16 | 16 | 2,040 | -1.9% | Both abstraction and compatibility cases tied |
| Verification and debugging | 16 | 16 | 2,695 | -2.6% | Host diagnosis and gate proposals tied after symmetric adjudication |
| AO guide and harness | 15 | 14 | 27,972 | -21.0% | One full answer retained a finite observation budget; effect did not repeat |

All source and candidate-prompt hashes matched the frozen records. The prompt
byte differences include reference separators. See [aggregate data](aggregate.json)
for every paired result and [integrity accounting](integrity.json) for totals.
Candidate calls used 1,317,847 input and 18,545 output tokens; judging used
305,431 input and 4,354 output tokens. Cached input is included in input totals
and is not added again.

### Stable convention effects

For C2, both full answers chose `seed=42`; both removed answers chose
`seed=None`. Every implementation accepted caller seeds, preserved inputs and
global random state, and passed the functional probes. The guide supplies a
specific reproducibility default that the task itself intentionally omitted.

For M1, both full answers used `scan_data_batches` and `sink_data_batches`.
Removed answers used `iter_file_batches` with `stream_batches_to_target` or
`write_batches`. All names were understandable, and both arms preserved the
validate/ensure and filter/select distinctions. The observed value is adherence
to the user's vocabulary. It is not evidence that the alternate names are
generically incorrect.

### AO effect and retained dependencies

All four A1 answers preserved dirty work and rejected restoration or ownership
transfer before runtime release. Full sample `run-054` explicitly limited the
observation budget; full sample `run-030` and both removed answers omitted that
limit. All four A2 answers rejected premature completion and identified missing
notification and later-stage coverage.

The removed AO answers also noted the missing canonical guide. That dependency
remains in the fixed global instructions. These results cannot establish that
the model can replace the guide in real lifecycle operations, or that the guide
and the global safeguards can be deleted together. The 21% loaded-context
reduction is a reason to investigate narrower routing, with those contracts
retained. The guide and harness are already conditional; this overhead is not
paid on every calibration task.

## Compression Recommendations

These are candidates for a later reversible change, not adopted replacements.

1. **Consolidate repeated outcome and validation prose first.** SKILL.md,
   principles.md, and the fixed global template repeat outcome autonomy and
   proportional validation. Preserve the operative constraint in its authority
   source and shorten repetition. G1/G2 only support the local-work scope; this
   run did not separately test false-premise correction, benchmark design, or
   autonomous recovery on complex work.
2. **Shorten the native-abstraction examples and ordinary communication list.**
   Basic parser, bulk-query, conclusion-first, and evidence-reporting reminders
   had no measured marginal benefit here. Preserve the user's short direct-style
   rule as an explicit preference: two short writing cases cannot show that the
   preference has become reliably implicit. The rule is not a quality failure.
3. **Consider compressing design/codebase.md into its distinctive decisions.**
   Both arms rejected forwarding-only layers and preserved a public caller
   contract. The simple examples provide a compression lead; complex boundary
   design and refactoring remain untested.
4. **Keep seed and naming conventions, reduce their explanatory duplication.**
   These were the only effects repeated in both runs of their respective cases.
   Keep naming references on demand. The experiment does not justify deleting
   the full vocabulary based on six function names, or removing extension-key
   preservation because explicitly specified configuration tasks passed.
5. **Keep verification, host-state, ownership, release, and handoff contracts.**
   The fixed global template already supplies several of them. Their remaining
   repetition can be consolidated, but this ablation does not remove every
   authority source. For AO, test a narrower guide/harness slice before adopting
   it; no such slice was evaluated in this run.

No whole-skill retirement follows from this screening. Project Knowledge,
documentation specifications, other naming references, evaluation guidance,
closeout, retrospect, and third-party skills were outside its measured scope.
No jointly compressed bundle or held-out real-work task was evaluated. There is
no statistical equivalence claim. Small synthetic tasks with explicit contracts
leave considerable ceiling effects.

## Review And Evaluator Corrections

The raw blind judge incorrectly required actual test execution for V2 criterion
four, despite the task asking for code and how to verify it and the frozen
prefix forbidding real operations. All four V2 answers supplied positive and
negative verification plans and avoided execution claims. The controller
corrected this criterion symmetrically after unblinding, changing verification
from 14/14 to 16/16. It did not change the between-arm comparison. The original
[blind judgments](blind-judgments.json), [raw scores](scores-raw.json),
[raw aggregate](aggregate-raw.json), and explicit [adjudications](adjudications.json)
are retained. Candidate outputs and frozen criteria were not changed.

Independent artifact acceptance also required three evaluator repairs: use an
explicit minimal subprocess environment with this Bubblewrap version; extract
one complete Python code block when the files array is empty; and repair nested
JSON quoting in the V2 synthetic target fixture. The quoting error occurred
before candidate execution. Original affected records and scripts remain in the
private experiment directory. All 20 original implementations passed final
acceptance after those repairs; these incidents are not model failures.

## Evidence

- [Frozen tasks](cases.json), [rubric](rubric.json), and [prompt prefix](prompt-prefix.txt).
- [Source manifest](manifest.json) and [source inventory](source-inventory.json).
- [All 64 anonymous answers](answers.json) and [per-run records](run-records.json).
- [Independent code checks](artifact-checks.json), [adjudicated scores](scores.json),
  and [paired aggregates](aggregate.json).
- [Blind judgments](blind-judgments.json), [adjudications](adjudications.json),
  and [integrity accounting](integrity.json).

Exact prompts, execution scripts, CLI streams, workspaces, and isolated homes
remain in the user-selected private run directory. The public manifest's
`global-template.txt` hash corresponds to the frozen copy of
`codex/AGENTS.md.template`; the remaining source paths are relative to
`skills/calibration/`. Raw homes and authentication links are not public evidence.
