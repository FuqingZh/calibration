# Calibration Wording Trial

## Decision

Accept the small interface, deletion-test, completion, and debugging wording
changes in the two existing references. Keep calibration's trigger, router,
precedence, and other references unchanged. Do not replace them with Matt's
skills. This is regression acceptance, with no demonstrated quality gain.

The baseline and candidate each passed 16/16 scenario answers (eight scenarios
in two fresh sessions per arm); no critical decision failures or tool calls
were observed. These are 32 answers in four sessions, not 32 independent runs.

## Finding And Scope

The design reference described interface elements but did not explicitly name
configuration, ordering, or performance obligations. Its completion criterion
used the ambiguous phrase “passes the deletion test”. Debugging allowed an
equivalent check that exercised the same path without explicitly requiring it
to detect the original symptom. These are wording ambiguities, not observed
production defects. Existing principles and verification guidance may already
supply the missing constraints.

The candidate clarifies caller knowledge, makes abstraction removal conditional
on preserving policy, complexity ownership, and contracts, and requires the
final bug check to detect the original symptom. Single-caller lifecycle and
compatibility boundaries remain valid. Existing failure records remain usable.

The comparison was motivated by Matt Pocock's
[codebase design](https://github.com/mattpocock/skills/blob/49dd158d1076134a641b33efb035946536778336/skills/engineering/codebase-design/SKILL.md)
and
[bug diagnosis](https://github.com/mattpocock/skills/blob/49dd158d1076134a641b33efb035946536778336/skills/engineering/diagnosing-bugs/SKILL.md).
The candidate uses locally written wording and retains calibration's contracts.
No upstream skill was installed or made a runtime dependency.

## Frozen Protocol

- Baseline: `92bc477b3b6459dfa1351a914c19dc130fab9593`.
- Sources: skill entry, principles, codebase design, debugging, verification.
  [Source hashes](sources.json) identify both frozen arms. Baseline content is
  reconstructable from Git; candidate content is in this change.
- [Cases and acceptance criteria](cases.json) were frozen before model calls.
  The model received scenario IDs and prompts, without acceptance criteria.
- Codex CLI `0.162.1`; requested model `gpt-6-astra`, reasoning `medium`.
  The event stream does not independently attest the serving model revision.
- Four serial sessions in baseline, candidate, candidate, baseline order.
  Each received all eight cases in a single turn and a JSON output schema
  requiring an `answers` array of `id`, `decision`, and `reason` strings.
- Separate temporary HOME, CODEX_HOME, and empty workspace per session;
  ephemeral mode, ignored user config and rules, read-only sandbox.
  Auth was available by a private symlink; no credentials are retained here.
- Apps, plugins, multi-agent, browser tools, shell, memory, goals, and shell
  snapshots were disabled; web search was disabled. Events confirm no tool use.
- Prompt: “Evaluate the following synthetic engineering scenarios using the
  supplied guidance. This is a decision-only test: do not call tools, inspect
  files, or execute actions. Give a concise decision and observable justification
  for every case. Do not discuss the evaluation.” Followed by the five complete
  source texts in the order above, then the scenario IDs and prompts.
- The author reviewed every answer against its frozen criterion, including
  justification and missing boundaries. This was unblinded review, with no
  independent reviewer or held-out cases. Any candidate critical failure or
  regression against a passing baseline case would block adoption.

## Results And Limits

[Reviewed answers](results.json) preserve decisions, justifications, per-answer
judgments, session timing, token counters, and tool counts. Both arms correctly
removed a pure forwarder, retained shared policy and a single lifecycle adapter,
recognized the full caller contract, rejected exit-code-only repair evidence,
accepted recorded failure evidence with equivalent replay, preserved local
execution autonomy, and withheld unsupported downstream completion.

One baseline repeat additionally mentioned an unavailable discipline router.
This is an artifact of supplying selected guidance without repository access;
it did not change its decision. CLI diagnostics included temporary-home helper
alias warnings and model-list refresh timeouts; all four turns completed with
exit zero. Timing is not used to infer efficiency.

This small, authored decision-only smoke test checks interpretation under
explicitly supplied guidance. It does not test automatic skill triggering,
actual code edits, production debugging, other clients, or long-run behavior.
It cannot establish superiority, statistical confidence, or that Matt's skills
would perform worse: there was no Matt replacement arm. The narrow wording
change is accepted for local use; broader workflow-performance claims require
a representative real-work rollout that has not been performed here.

## Verification

The adopted files exactly match the frozen candidate hashes. Repository skill,
Markdown, link, and runtime-guidance contract checks validate packaging and
existing boundaries separately from the model comparison. Installer, runtime,
and dependency code did not change; full installer and coverage gates were not
needed for this wording-only seam.
