# Calibration Documentation

This directory records calibration decisions, evaluations, historical plans,
and portable integration guidance. Reusable cross-project engineering guidance
lives under `../references/engineering/`.

Calibration is in stable maintenance mode. The bounded CAL-1 containment
public contract is delivered without a behavioral-improvement claim. A future
evaluation is not an active phase; upstream systemd containment remains a
proposal rather than current AO behavior.

## Public Architecture

Calibration has four layers:

1. reusable references under `../references/engineering/`;
2. skills under `../skills/` as model interaction entrypoints;
3. AO as an optional environment adapter; and
4. private host configuration outside this public repository.

Public references and skills must work when AO and the private host profile are
absent. Host paths, credentials, services, proxy configuration, deployment
state, and rollback material belong to private authority. The installer renders
only a conditional pointer to `$XDG_CONFIG_HOME/calibration/AGENTS.md`, falling
back to `$HOME/.config/calibration/AGENTS.md`.

## Current Authority

| Need | Current authority |
| --- | --- |
| Repository and installer contract | `../README.md` |
| Cross-project judgment defaults | `../references/engineering/principles.md` |
| Calibration routing | `../skills/calibration/SKILL.md` |
| Repository capability and delivery placement | `../references/engineering/discipline/harness.md` |
| Completion and external-result evidence | `../references/engineering/discipline/verification.md` |
| Agent and workflow comparison | `../references/engineering/discipline/evaluation.md` |
| Durable implementation-plan contract | `../references/engineering/docs/document-types/implementation-plan.md` |
| Portable AO integration | `runbooks/agent-orchestrator-review-continuation.md` |
| Native AO delivery and auto-merge boundary | `decisions/2026-07-29-ao-native-delivery-convergence.md` |
| Current AI-native direction | `decisions/2026-07-27-ai-native-calibration-review.md` |
| Writable comparative evidence | `decisions/2026-07-27-ai-native-writable-implementation-evaluation-closeout.md` |
| Five-phase convergence result | `decisions/2026-07-27-ai-native-calibration-convergence-closeout.md` |
| Default repository quality gate | `decisions/2026-07-30-default-repository-quality-gate.md` |
| Codex-home adoption compatibility | `decisions/2026-07-30-ao-host-context-and-config-compatibility.md` |
| Dashboard terminal boundary | `decisions/2026-07-30-dashboard-terminal-access-boundary.md` |
| Portable orchestrator containment | `decisions/2026-07-31-portable-orchestrator-containment.md` |
| CAL-1 implementation status | `implementation-plan/20260731-v2.1-portable-orchestrator-containment-implementation-plan.md` |

The current default is outcome autonomy within repository-local, reversible
boundaries. AO is optional and conditional. Ordinary engineering tasks do not
load private AO material.

## Repository Validation

`pdm.lock` is the dependency authority:

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
- Detailed debugging, verification, harness, and evaluation layers still need
  representative ablation evidence before any consolidation.

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

### Delivery And Orchestration

- `decisions/2026-07-21-repository-delivery-feedback-loop.md`
- `decisions/2026-07-23-ao-review-continuation-adoption.md`
- `decisions/2026-07-29-ao-native-delivery-convergence.md`
- `implementation-plan/20260723-v1.6-repository-quality-gate-implementation-plan.md`
- `implementation-plan/20260723-v1.7-ao-repository-adoption-contract-implementation-plan.md`
- `implementation-plan/20260727-v1.8-ai-native-calibration-convergence-implementation-plan.md`
- `implementation-plan/20260728-v1.9-persistent-linear-intake-and-no-product-canary-implementation-plan.md`
- `implementation-plan/20260728-v2.0-three-scenario-linear-acceptance-implementation-plan.md`
- `implementation-plan/20260731-v2.1-portable-orchestrator-containment-implementation-plan.md`
