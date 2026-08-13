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
- same current Codex agent configuration and tools for both arms; the exact
  model build and reasoning setting were not exposed to the evaluation runner;
- fresh isolated fixture directories for every run; and
- network access prohibited for the current-authentication case.

The official comparison used 12 agent runs: one run per arm for six pairs. The
critical first-lesson boundary was repeated with two independently worded
prompts. A separate blind judge saw arm labels that changed meaning across
cases and did not receive either skill source.

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

## Integrity

- blind judge packet SHA-256:
  `993a58002ac17b0afb99454dd388b1b9b8ab1b7ed71be739b558891935f02db8`;
- non-Git fixture and output manifest SHA-256:
  `5b79d6ea6f112c45dbf14029f4a5145ed99e223d881befd6230c4a5fb02a5738`;
- behavioral cases are retained in
  `../../thirdparty/skills/teach/test-prompts.json`; and
- raw workspaces, arm mapping, and judge packet remain uncommitted under the
  temporary evaluation root.

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
