# Calibration Documentation

This directory records calibration decisions, evaluations, historical plans,
and portable integration guidance. Reusable cross-project engineering guidance
lives with its owning skill under `../skills/calibration/references/`.

Calibration is in stable maintenance mode. The v2.1 relative-replacement run
is now diagnostic history: audit showed that its raw-command evidence oracle
had been collapsed into task completion even though every repository verifier
passed. The corrected v2.2 comparison is complete and inconclusive, so the
frozen baseline remains current authority. Both arms were 7/7 task-valid and
evidence-valid. The candidate reduced forbidden events from five to three, but
P03 favored the baseline while P05 favored the candidate and P02 tied. It did
not establish a net behavioral or speed improvement. G0 at
`ff16714999465ad1acbd130dbb9711725584544f` with Codex 0.148.0 found that
`codex exec --json` lacks structured, correlated approval events; its error
items are not a reliable replacement. Approval statistics were subsequently
removed from the decision scope, so the outcome-only comparison is authorized
without parsing that prose. `Approve for me` remains a symmetric runtime safety
control. The v2.2 contract separates task outcome, runner-owned validation
selection, and evidence integrity; it completed 12 initial runs plus the P05
tiebreak pair. The active user installation and downstream-repository pilot
remain separate work and were not changed by this evaluation. The v2.0 plan
and its 2026-08-24 smoke/recovery results remain historical background only.
This follows the completed v1.0
proportional-wording increment and is layered on the ongoing project-docs
architecture convergence. The user subsequently authorized candidate adoption
despite that inconclusive evidence, so the shared pinned `coding-protocol` was
installed without making a comparative-improvement claim. Its independent
runtime entry is now retired for the user-authorized trial linked below. This does not reopen
the completed runtime or AO
implementation phases. The completed bounded v2.4 closeout-skill increment
adds an explicitly invoked first-party closeout contract and makes no
comparative improvement claim.
The adapted third-party `teach` skill is accepted for standard-profile
installation from a bounded blind regression comparison; that result does not
claim general learning-outcome improvement.
The bounded review-convergence routing v2.3 increment clarifies a portable
contract only and makes no behavioral-improvement claim. The bounded CAL-1
containment public contract is delivered without a behavioral-improvement
claim. The bounded Sol Advisor and Calibration ablation is complete: it rejects
the tested mandatory CAL-MIN route and default Advisor use for a clear local
repair without changing installed global routing. The compact diagnostic-
suppression default is accepted from a bounded same-model W07 comparison; it
adds no general correctness or efficiency claim. Upstream systemd containment
remains a proposal rather than current AO behavior.

The [GPT-6 coding-protocol versus calibration comparison](../evaluations/coding-protocol-calibration/README.md)
completed 24 attempts. Calibration alone and both together completed 8/8 tasks
each; the median paired token change was +2.8% with mixed directions. This
supports considering a reversible retirement trial, not a general overhead or
blinded equivalence claim. The user subsequently authorized the
[runtime retirement trial](decisions/2026-09-07-coding-protocol-runtime-retirement-trial.md);
source and license remain preserved.

The [AO native guidance consolidation](decisions/2026-09-07-ao-native-guidance-consolidation.md)
updates routing for upstream v0.12.12 and centralizes ownership and release
rules in the portable AO guide. Older command restrictions are archived;
installed-version and real-work behavior remain separate evidence boundaries.

## Public Architecture

Calibration has four layers:

1. reusable references under `../skills/calibration/references/`;
2. skills under `../skills/` as model interaction entrypoints;
3. AO as an optional environment adapter; and
4. private host configuration outside this public repository.

Public references and skills must work when AO and the private host profile are
absent. Host paths, credentials, services, proxy configuration, deployment
state, and rollback material belong to private authority. The installer renders
only a conditional pointer to `$XDG_CONFIG_HOME/calibration/AGENTS.md`, falling
back to `$HOME/.config/calibration/AGENTS.md`.

The bounded [GPT-6 skill cleanup](decisions/2026-09-07-gpt6-skill-retirement-and-snippet-scope.md)
retires the writing-great-skills runtime entry and scopes code-documentation
workspace discovery to repository work.

The [whole-conversation closeout contract](decisions/2026-09-07-closeout-whole-conversation-contract.md)
supersedes the older minimal-handoff and unconditional durability gates.

## Current Authority

The [Chinese Humanizer on-demand trial](decisions/2026-09-10-humanizer-zh-on-demand-trial.md)
records a separately installed, pinned Chinese copy-editing skill. It is
explicitly invoked and does not extend calibration's core or global routing.

| Need | Current authority |
| --- | --- |
| Repository and installer contract | `../README.md` |
| Cross-project judgment defaults | `../skills/calibration/references/principles.md` |
| Calibration routing | `../skills/calibration/SKILL.md` |
| Explicit task closeout | `../skills/closeout/SKILL.md` |
| Repository capability and delivery placement | `../skills/calibration/references/discipline/harness.md` |
| Completion and external-result evidence | `../skills/calibration/references/discipline/verification.md` |
| Agent and workflow comparison | `../skills/calibration/references/discipline/evaluation.md` |
| Sol Advisor and Calibration ablation | `../evaluations/sol-advisor-calibration-ablation/results.md` |
| Diagnostic suppression policy | `decisions/2026-08-14-diagnostic-suppression-policy.md` |
| Teach adaptation evidence | `decisions/2026-08-13-teach-adaptation-evaluation.md` |
| Project docs architecture | `../skills/calibration/references/docs/workflow/project_docs_architecture/20260805-v1.1-project-docs-architecture.md` |
| Durable implementation-plan contract | `../skills/calibration/references/docs/document-types/implementation-plan.md` |
| Self-contained first-party skills migration | `implementation-plans/20260826-v1.0-self-contained-first-party-skills-migration-implementation-plan.md` |
| Project docs architecture convergence plan | `implementation-plans/20260805-v1.0-project-docs-architecture-convergence-implementation-plan.md` |
| Progressive validation relative-replacement test plan | `testing/20260825-v2.1-progressive-validation-relative-replacement-test-plan.md` |
| Progressive validation corrected relative-replacement plan | `testing/20260825-v2.2-progressive-validation-relative-replacement-correction-plan.md` |
| Progressive validation corrected decision | `decisions/2026-08-25-progressive-validation-relative-replacement-acceptance.md` |
| Progressive validation v2.0 historical implementation plan | `implementation-plans/20260824-v2.0-progressive-validation-selection-implementation-plan.md` |
| Progressive validation approval-observability preflight | `decisions/2026-08-25-progressive-validation-relative-replacement-preflight.md` |
| Progressive validation frozen baseline | `decisions/2026-08-24-progressive-validation-selection-baseline.md` |
| Progressive validation activation candidate | `decisions/2026-08-24-progressive-validation-selection-candidate.md` |
| Progressive validation invalid smoke and C01 recovery | `decisions/2026-08-24-progressive-validation-selection-smoke-invalid.md` |
| Portable AO integration | `../skills/calibration/references/agent-orchestrator-review-continuation.md` |
| AO native routing and consolidation | `decisions/2026-09-07-ao-native-guidance-consolidation.md` |
| Historical AO delivery decision | `decisions/2026-07-29-ao-native-delivery-convergence.md` |
| Current AI-native direction | `decisions/2026-07-27-ai-native-calibration-review.md` |
| Writable comparative evidence | `decisions/2026-07-27-ai-native-writable-implementation-evaluation-closeout.md` |
| Five-phase convergence result | `decisions/2026-07-27-ai-native-calibration-convergence-closeout.md` |
| Proportional validation selection | `decisions/2026-08-07-proportional-validation-selection.md` |
| Codex-home adoption compatibility | `decisions/2026-07-30-ao-host-context-and-config-compatibility.md` |
| AO host calibration CLI closeout | `decisions/2026-08-04-ao-host-calibration-cli-closeout.md` |
| Dashboard terminal boundary | `decisions/2026-07-30-dashboard-terminal-access-boundary.md` |
| Containment rationale and historical canary | `decisions/2026-07-31-portable-orchestrator-containment.md` |
| CAL-1 implementation status | `implementation-plans/20260731-v2.1-portable-orchestrator-containment-implementation-plan.md` |
| Review-convergence routing status | `implementation-plans/20260803-v2.3-review-convergence-routing-implementation-plan.md` |
| Closeout skill status | `decisions/2026-09-07-closeout-whole-conversation-contract.md` |

The current default is outcome autonomy within repository-local, reversible
boundaries. AO is optional and conditional. Ordinary engineering tasks do not
load private AO material.

## Repository Validation

`pdm.lock` is the dependency authority:

Select validation proportionally to the affected behavior and contracts. The
commands below are the complete repository gate used by CI, not a mandatory
local checklist for every change; run the smallest relevant checks unless a
repository rule explicitly requires the complete gate.

```bash
pdm lock --check
pdm run check
CODEX_HOME="$(mktemp -d)" bash install.sh --dry-run
bash install.sh --profile ao-worker --codex-home "$(mktemp -d)" --dry-run
git diff --check
git diff --cached --check
git diff --check "${BASE_REF:-main}...HEAD"
git status --short
```

Use disposable Codex homes. Validation must not overwrite an active
installation.

## Evaluation

`../evaluations/ai-native-implementation/README.md` owns the writable fixture
protocol. Raw trajectories, credentials, isolated homes, workspaces, and
private host snapshots remain outside the public repository. Commit only
portable fixtures, reviewed findings, and reconstructable public evidence.

## AO Integration

The portable AO guide keeps sandbox, worker, daemon, and host state distinct;
defines registered, configured, runtime-ready, and continuation-proven
adoption; retains exact-head pull-request safety; and bounds recursive
discovery and mutation to the assigned workspace. It also requires an empty
OS-owned containment boundary before process release can be reported, with
incomplete release kept observable and retryable. AO installation, upgrades,
and proposed per-worker systemd process containment belong upstream. Current
AO behavior does not provide that proposed systemd guarantee, and calibration
does not ship host deployment artifacts.

`scripts/adopt_ao_repository.py` is an optional plan/apply adapter for an
already installed, CLI-capable AO on its supported Linux `systemd --user` and
tmux profile. It is not a universal Desktop adapter and does not make AO a
dependency of public skills or ordinary repository work. Other platforms use
upstream Desktop directly.

## Open Evidence Gaps

- Writable comparisons cover small dependency-free Python fixtures, one model,
  one reasoning effort, and local verification; they do not establish the same
  result for production, multi-language, dependency-heavy, or deployment work.
- Variable pre-edit reproduction remains a reason to reopen the candidate if
  real tasks skip executable feedback where it changes safety or diagnosis.
- No repeated writable evidence supports changing the durable implementation
  plan contract.
- Public AO guidance defines portable integration, but current-host operation
  requires rendered private authority and representative host readback.
- One Proteomics WGCNA event-chain audit identifies repeated replanning,
  post-compaction decision loss, and scope churn as the leading causes of a
  slow turn; AO performed only one read-and-fallback route, and Calibration was
  explicitly routed once. This is an actionable finding, not causal ablation.
- The completed same-model ablation found no local-repair benefit from default
  Sol Advisor use or the tested CAL-MIN bundle. It does not isolate a shorter
  AO safety kernel from mandatory Calibration routing, establish Advisor value
  for consequential work, or support a Sol-to-Luna quality claim.
- The W07 comparison found no correctness difference between the old and new
  diagnostic-suppression wording. Its lower candidate token and wall-time
  medians are bounded efficiency evidence from one small Python fixture, not a
  general model or multi-language result.

## Historical Records

Historical decision and plan paths remain for link compatibility. Current-host
AO operational evidence has been reduced to short public summaries; detailed AO
snapshots, hashes, credentials, service definitions, patches, and rollback
material belong to private host authority. Unrelated portable historical
evidence remains in its owning public decisions.

### Architecture And Documentation

- `decisions/2026-07-01-calibration-rename-and-skill-architecture.md`
- `decisions/2026-07-01-calibration-follow-up-batches.md`
- `decisions/2026-07-01-document-types-retrospect-and-evaluation.md`
- `decisions/2026-07-03-writing-docstrings-skill-design.md`

### Harness And Evaluation

- `decisions/2026-07-20-agent-harness-and-evaluation-ownership.md`
- `decisions/2026-07-20-agent-harness-and-evaluation-closeout.md`
- `decisions/2026-07-21-harness-successor-evaluation-closeout.md`
- `decisions/2026-07-27-ai-native-calibration-evaluation-closeout.md`
- `decisions/2026-07-27-ai-native-writable-implementation-evaluation-closeout.md`
- `implementation-plans/20260807-v1.0-proportional-validation-selection-implementation-plan.md`

### Delivery And Orchestration

- `decisions/2026-07-21-repository-delivery-feedback-loop.md`
- `decisions/2026-07-23-ao-review-continuation-adoption.md`
- `decisions/2026-07-29-ao-native-delivery-convergence.md`
- `implementation-plans/20260723-v1.6-repository-quality-gate-implementation-plan.md`
- `implementation-plans/20260723-v1.7-ao-repository-adoption-contract-implementation-plan.md`
- `implementation-plans/20260727-v1.8-ai-native-calibration-convergence-implementation-plan.md`
- `implementation-plans/20260728-v1.9-persistent-linear-intake-and-no-product-canary-implementation-plan.md`
- `implementation-plans/20260728-v2.0-three-scenario-linear-acceptance-implementation-plan.md`
- `implementation-plans/20260731-v2.1-portable-orchestrator-containment-implementation-plan.md`
