# Teach Adaptation Evaluation

Date: 2026-08-13

Status: accepted for standard-profile installation

## Decision

Install the locally adapted `teach` skill in the standard calibration profile.
Keep it explicitly invoked and keep learner state outside engineering
repositories unless the user separately requests team-document promotion.

A traceable second evaluation preferred the candidate in five blind pairs and
tied the explicit project-document promotion pair. The candidate had no
critical failure. The upstream baseline had critical failures in the other
five pairs. This supports regression acceptance for the evaluated contract. It
does not prove general learning improvement, retention, token savings, or
superiority across models and repositories.

## Frozen Arms

- upstream baseline: Matt Pocock `teach` release `v1.2.3`, commit
  `6acc160e4e0cd062dbbbd7a1b26ae92855edf07e`, tree
  `15f8c86d39ef834e643d092733ca899b59049067`;
- installed local candidate: repository commit `075016e`, skill tree
  `76f1e41bd5cc624798e2c9c1a446f0639bb0ec30`;
- fresh isolated fixture and fresh no-context agent for each of 16 runs;
- exact model build, reasoning setting, and backend session ID were not exposed
  by the runner; and
- network access prohibited for the current-authentication pair.

## Results

| Case | Candidate | Upstream baseline |
| --- | --- | --- |
| First lesson, repetition 1 | preferred; safe mode boundary and applied diagnostic | no session-only boundary; self-report only |
| First lesson, repetition 2 | preferred; both modes and applied diagnostic | persistent-only; self-report only |
| Persistent HTML quiz | preferred; resumed at lesson 0002 and runtime shuffle | restarted at lesson 0001; no runtime shuffle |
| Cross-session resume | preferred; focused no-write next step | did not establish learner-state adaptation |
| Current technical state | preferred; named v3.2 authority and check date | restarted at lesson 0001; freshness context incomplete |
| Explicit project-doc promotion | tie; scoped provenance and limitation | tie; shorter compatibility note |

Four candidate-only safety invocations additionally established:

- project-descendant workspace rejection with identical before/after manifests;
- installed-skill-source rejection with identical source trees;
- session-only zero-write teaching and an honest statement that no reminder
  capability was available; and
- bounded initialization of a separately authorized personal workspace while
  the engineering project remained clean.

## Traceable Evidence

The current evidence authority is
`../../evaluations/teach-adaptation/v2/README.md`. Every invocation retains a
UUID, controller-selected executor label, exact controller envelope and user
prompt, raw response containing that UUID, controller prepare/capture events,
pre/post SHA-256 manifests, selected skill commit and tree, a verifiable Git
bundle for the pre-run project, post-run Git state, and exact changed artifacts.

Blind ordering is established by three Git commits:

1. `bd6fc99` committed all 16 runs, the sanitized blind packet, and an empty
   scorecard, but no arm map;
2. `2322cb3` committed the independent judge's UUID-bound raw A/B response and
   filled scorecard, still without the arm map; and
3. the following result commit reveals `arm-map.json` and interprets the
   already-frozen preferences.

This is controller-captured evidence rather than an externally attested event
log. It is independently reviewable and internally verifiable, but cannot
recover the runner's unexposed backend identity or prove external timestamping.

The older bundle directly under `../../evaluations/teach-adaptation/` is
retained as historical evidence of the first evaluation. It is not the current
execution-identity or blind-ordering authority.

## Limitations And Reopen Conditions

The evaluation used small synthetic technical-learning fixtures, one current
agent configuration, one run per arm outside the repeated first-lesson
boundary, and one blind judge. It did not measure delayed retention, real
reminder delivery, long-running course evolution, browser rendering quality,
token use, or production learning outcomes.

Reopen acceptance if representative use writes learner state into an
engineering repository, restarts rather than resumes, teaches stale current
behavior, leaks answer position, promotes personal state, or if another model
or non-technical domain reverses a critical result.
