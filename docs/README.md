# Calibration Documentation

This directory records calibration decisions, evaluations, historical plans,
and portable integration guidance. Reusable cross-project engineering guidance
lives under `../references/engineering/`.

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
| Current AI-native direction | `decisions/2026-07-27-ai-native-calibration-review.md` |
| Writable comparative evidence | `decisions/2026-07-27-ai-native-writable-implementation-evaluation-closeout.md` |
| Default repository quality gate | `decisions/2026-07-30-default-repository-quality-gate.md` |
| Dashboard terminal boundary | `decisions/2026-07-30-dashboard-terminal-access-boundary.md` |

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
adoption; and retains exact-head pull-request safety. AO installation and
upgrades belong to upstream Desktop. Calibration does not ship host deployment
artifacts.

`scripts/adopt_ao_repository.py` is an optional plan/apply adapter for an
already installed, CLI-capable AO. It does not make AO a dependency of public
skills or ordinary repository work.

## Historical Records

Historical decision and plan paths remain for link compatibility. Host-specific
operational evidence has been reduced to short public summaries; detailed
snapshots, hashes, credentials, service definitions, patches, and rollback
material belong to private host authority.
