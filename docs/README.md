# Calibration Documentation

This directory records calibration-specific decisions, evaluations, active
plans, and current-host runbooks. Reusable cross-project engineering guidance
lives under `../references/engineering/`.

## Current Authority

Read the smallest source that owns the decision:

| Need | Current authority |
| --- | --- |
| Repository and installer contract | `../README.md` |
| Cross-project judgment defaults | `../references/engineering/principles.md` |
| Calibration routing | `../skills/calibration/SKILL.md` |
| Repository capability and delivery placement | `../references/engineering/discipline/harness.md` |
| Completion and external-result evidence | `../references/engineering/discipline/verification.md` |
| Agent and workflow comparison | `../references/engineering/discipline/evaluation.md` |
| Durable implementation-plan contract | `../references/engineering/docs/document-types/implementation-plan.md` |
| Current AI-native direction | `decisions/2026-07-27-ai-native-calibration-review.md` |
| Writable comparative evidence | `decisions/2026-07-27-ai-native-writable-implementation-evaluation-closeout.md` |
| Five-phase convergence result | `decisions/2026-07-27-ai-native-calibration-convergence-closeout.md` |
| Current-host AO and delivery boundary | `decisions/2026-07-29-ao-native-delivery-convergence.md` |

The current default is outcome autonomy within repository-local, reversible
boundaries. Repository rules and executable feedback choose and revise the
implementation path. Calibration remains the judgment layer for cross-project
decisions, non-local design, compatibility-sensitive contracts, unclear
verification, harness and evaluation work, and durable engineering
documentation.

## Current Operational Surface

### Repository validation

`pdm.lock` is the dependency authority. The repository completion gate is:

```bash
pdm lock --check
pdm run check
CODEX_HOME="$(mktemp -d)" bash install.sh --dry-run
git diff --check
git diff --cached --check
git diff --check "${BASE_REF:-main}...HEAD"
git status --short
```

Use an explicit temporary `CODEX_HOME`; validation must not overwrite an active
Codex installation.

### Writable behavior evaluation

`../evaluations/ai-native-implementation/README.md` owns the isolated writable
fixture protocol and runner commands. The current result is comparative
improvement on W01-W03: candidate 9/9 deterministic passes and six of nine
blind preferences versus baseline 8/9 and three preferences.

Raw trajectories, isolated homes, workspaces, arm maps, and blind judge
packages remain private temporary evidence. Commit only fixtures, protocol,
reviewed findings, and reconstructable hashes.

### AO-native delivery

`runbooks/agent-orchestrator-review-continuation.md` is the current-host
installation, Dashboard, service, permission, recovery, and
repository-adoption contract.
`decisions/2026-07-29-ao-native-delivery-convergence.md` records the accepted
upstream v0.11.1 runtime, trusted-LAN read-only Dashboard compatibility
boundary, Dashboard-only attention policy, Linear retirement, and fail-closed
low-risk GitHub auto-merge policy.
`decisions/2026-07-23-ao-review-continuation-adoption.md` records the accepted
narrow review-to-original-worker bridge.
`decisions/2026-07-27-ao-phase-3-deployment-reproducibility-closeout.md`
records the deployed fork revision, installed artifact, read-only Linear
credential boundary, service override, and rollback evidence.

AO is an environment adapter, not a default part of ordinary engineering
judgment. Repositories opt in individually after an observed continuation need.
An explicit conversation-authorized implementation may start a task-specific
worker in an already accepted repository.

The current conversation and explicit implementation authorization are the
work-intake authority; this is conversation-authorized issue intake, and AO
creates or continues the worker from that authority. GitHub pull requests are
the delivery, CI, review, and merge fact source. Linear integration is deferred,
its intake is removed from the active AO project and service, and its repair
conditions are not on the execution critical path. Historical Linear plans and
canary evidence remain below for audit.

AO retains status and attention events in its durable Dashboard only. The
current host exposes a read-only renderer/API compatibility surface on the
trusted LAN because the v0.11.1 AppImage does not supply a supported headless
Web listener on this GLIBC 2.28 host. Do not describe that adapter as
upstream-native headless support.

## Open Evidence Gaps

- The writable comparison covers small dependency-free Python repositories,
  one model, one reasoning effort, and local verification. It does not
  establish the same result for dependency-heavy, multi-language, production,
  or pull-request delivery tasks.
- W01 still showed variable pre-edit failure reproduction. Reopen the candidate
  if repeated real work skips executable feedback where it materially changes
  diagnosis or safety.
- No repeated writable evidence supports changing the durable
  implementation-plan contract. Phase 3 therefore closed `NO-CHANGE`.
- No writable case loaded irrelevant host AO details or failed an
  orchestration gate. Phase 4 therefore closed `NO-CHANGE`.
- Detailed debugging, verification, harness, evaluation, and AO layers have
  scoped owners, but their deletion still requires a representative ablation
  or real-task replacement capability.
- The Symphony readiness path remains closed at its 2026-07-22 `NO-GO` until
  its pinned dependency and full-suite reopen conditions pass.

## Historical Decisions

These files preserve why the current authority exists. They are not the default
reading path.

### Architecture and documentation

- `decisions/2026-07-01-calibration-rename-and-skill-architecture.md`:
  implemented initial architecture.
- `decisions/2026-07-01-calibration-follow-up-batches.md`: superseded batch
  record.
- `decisions/2026-07-01-document-types-retrospect-and-evaluation.md`: partially
  superseded document-type decision.
- `decisions/2026-07-03-writing-docstrings-skill-design.md`: superseded by
  `writing-code-docs`.

### Harness and evaluation

- `decisions/2026-07-20-skill-optimization-evaluation-closeout.md`: accepted
  earlier skill baseline and evaluation limitations.
- `decisions/2026-07-20-agent-contribution-and-task-isolation.md`: current
  collaboration boundary.
- `decisions/2026-07-20-agent-harness-and-evaluation-ownership.md`: accepted
  harness and evaluation ownership.
- `decisions/2026-07-20-agent-harness-and-evaluation-closeout.md`: rejected
  Slice 2 candidate and retained Slice 3 evidence.
- `decisions/2026-07-21-harness-successor-evaluation-closeout.md`: rejected
  v1.2 successor.
- `decisions/2026-07-27-ai-native-calibration-evaluation-closeout.md`:
  historical read-only regression acceptance that motivated the writable
  comparison.
- `decisions/2026-07-27-ai-native-writable-implementation-evaluation-closeout.md`:
  current writable comparative result.

### Repository delivery and orchestration

- `decisions/2026-07-21-repository-delivery-feedback-loop.md`: accepted
  failure-driven delivery loop.
- `decisions/2026-07-21-repository-engineering-capability-adoption-closeout.md`:
  closed proportional adoption pilots and bounded Symphony `NO-GO`.
- `decisions/2026-07-22-symphony-readiness-and-bounded-canary-closeout.md`:
  closed readiness plan at Slice 1.
- `implementation-plan/20260722-v1.5-symphony-readiness-and-bounded-canary-implementation-plan.md`:
  closed Symphony plan and reopen gates.
- `implementation-plan/20260723-v1.6-repository-quality-gate-implementation-plan.md`:
  closed repository-local validation convergence.
- `decisions/2026-07-23-ao-review-continuation-adoption.md`: accepted bounded
  AO successor on the current host.
- `decisions/2026-07-27-ao-phase-3-deployment-reproducibility-closeout.md`:
  records the current-host Phase 3 Linear deployment and its verification
  boundary.
- `implementation-plan/20260723-v1.7-ao-repository-adoption-contract-implementation-plan.md`:
  closed behavior-validated adoption contract.
- `implementation-plan/20260728-v1.9-persistent-linear-intake-and-no-product-canary-implementation-plan.md`:
  superseded historical FUQ-14 rollout and manual canary procedure.
- `implementation-plan/20260728-v2.0-three-scenario-linear-acceptance-implementation-plan.md`:
  current failed-canary evidence, disabled-intake closeout, and repair gates.

### Current convergence history

- `decisions/2026-07-27-ai-native-calibration-review.md`: accepted trigger and
  outcome-autonomy direction.
- `implementation-plan/20260727-v1.8-ai-native-calibration-convergence-implementation-plan.md`:
  implemented five-phase plan.
- `decisions/2026-07-27-ai-native-calibration-convergence-closeout.md`: final
  phase decisions, retirement ledger, and reopen conditions.

Historical files remain in place. Repair a historical document only when a
fact or link is broken; record current interpretation in a new decision or the
current authority map. Do not add a `README.html` mirror.
