# Teach Adaptation Evaluation

Date: 2026-08-13

Status: accepted for standard-profile installation

## Decision

Install the locally adapted `teach` skill in the standard calibration profile.
Keep it explicitly invoked and keep learner state outside engineering
repositories unless the user separately requests a team-document promotion.

The candidate had no critical failure in six blind comparison pairs. It was
preferred in all five distinguishing pairs and tied the upstream baseline on
the explicit project-document promotion case. The upstream baseline lost
critical behavior in five pairs. This supports regression acceptance for the
evaluated teaching contract; it does not prove a general improvement in
learning outcomes, retention, token use, or every model and repository.

## Frozen Arms

- upstream baseline: Matt Pocock `teach` from release `v1.2.3`, commit
  `6acc160e4e0cd062dbbbd7a1b26ae92855edf07e`, tree
  `15f8c86d39ef834e643d092733ca899b59049067`;
- local candidate: commit `6dd41c2`, tree
  `513481274e5b900ea30ac6291e967794b2bde7ad`;
- installed candidate: commit `e3152e5`, tree
  `76f1e41bd5cc624798e2c9c1a446f0639bb0ec30`; its delta from the
  comparative candidate only adds repository-required Markdown emphasis;
- same current Codex agent configuration and tools for both arms; the exact
  model build and reasoning setting were not exposed to the evaluation runner;
- fresh isolated fixture directories for every run; and
- network access prohibited for the current-authentication case.

The official comparison used 12 agent runs: one run per arm for six pairs. The
critical first-lesson boundary was repeated with two independently worded
prompts. A separate blind judge saw arm labels that changed meaning across
cases and did not receive either skill source. Four candidate-only safety runs
then verified descendant-path rejection, skill-source rejection, session-only
zero-write behavior without an invented reminder, and initialization of an
explicitly selected separate learning workspace.

## Results

| Case | Candidate | Upstream baseline |
| --- | --- | --- |
| First lesson, repetition 1 | preferred; no critical failure | missed explicit mode boundary and executable diagnostic |
| First lesson, repetition 2 | preferred; no critical failure | same critical gaps |
| Persistent HTML quiz | preferred; runtime answer shuffle | fixed answer order |
| Cross-session resume | preferred; direct state-based next step | resumed correctly but emitted another fixed-order quiz |
| Current technical state | preferred; current authority and check context | incomplete source freshness and fixed-order check |
| Explicit project-doc promotion | tie; passed | tie; passed |

The candidate preserved the engineering repository during ordinary teaching,
offered session-only no-write teaching, confined persistent state to a selected
personal workspace, assessed starting capability, resumed existing learning,
used current project authority, randomized quiz display order, and excluded
personal state during explicit project-document promotion.

## Protocol Correction

The first exploratory first-lesson fixtures had no valid Git `HEAD`, and a
fixture-construction mistake concatenated several intended files into one
README. Those outputs were excluded. The fixtures were rebuilt as clean Git
repositories with one committed source file before all official pairs. No
excluded artifact was reused by an official run.

## Durable Evidence

The sanitized evaluation bundle is retained in
`../../evaluations/teach-adaptation/`:

- `protocol.md` specifies execution, filesystem capture, blind judging, and
  verification limits;
- `cases.json` freezes fixture contents, actual prompts, arm source commits,
  and run conditions;
- `runs.json` retains stable run identities, prompt and response hashes,
  before/after manifests, changed paths, Git status, and artifact hashes;
- `artifacts/` retains the generated or modified outputs named by those
  manifests;
- `judge-packet.md` and `judge-scorecard.json` retain the blind rubric, inputs,
  and structured pre-reveal decision, while `arm-map.json` is the separate
  reveal; and
- `responses.txt` retains the exact sanitized final responses, while
  `results.md` explains the bounded interpretation.

The skill's reusable behavioral inputs remain in
`../../thirdparty/skills/teach/test-prompts.json`. Raw temporary workspaces are
not committed. `SHA256SUMS` and the focused contract test verify the committed
bundle. The evidence is independently checkable from committed files, but is
not externally timestamped or cryptographically attested and cannot identify
an unexposed backend session or model build.

## Limitations And Reopen Conditions

This evaluation used small synthetic technical-learning fixtures, one current
agent configuration, and one run per arm outside the repeated first-lesson
boundary. It did not measure delayed retention, real reminder delivery,
long-running course evolution, visual quality across browsers, token use, or
production work.

Reopen installation acceptance if representative use writes learner state into
an engineering repository, restarts instead of resuming, teaches stale current
behavior, leaks answer position, promotes personal state, or if another model
or non-technical learning domain reverses a critical result.
