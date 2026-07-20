# Agent Harness And Evaluation Ownership

Date: 2026-07-20

Status: Accepted

## Context

Calibration already routes coding, naming, design, refactoring,
verification, and durable documentation decisions. It does not yet give an
agent a clear way to diagnose why a repository repeatedly makes work hard, or
to distinguish a valid current change from a measured improvement in agent or
workflow behavior.

OpenAI's later engineering reports describe two related practices: shape the
repository so agents can find facts and receive mechanical feedback, and turn
reviewed production failures into targeted evaluations before changing the
system. Those practices need a cross-project owner without turning each source
article into a skill or copying project-specific instructions into global
guidance.

## Decision

- Add `references/engineering/discipline/harness.md` as the owner of
  repository-capability diagnosis, capability placement, `AGENTS.md` content
  boundaries, human escalation, harness levels, and orchestration adoption.
- Add `references/engineering/discipline/evaluation.md` as the owner of agent,
  skill, and workflow quality comparison based on representative evidence.
- Keep `verification.md` responsible for whether the current change satisfies
  its contract. Evaluation remains a separate claim about representative
  behavior over repeated tasks.
- Route both topics through the existing `calibration` skill and discipline
  index. Do not create separate harness or evaluation skills.
- Treat `AGENTS.md` as an operational repository map, not a durable document
  type or a replacement for `docs/README.md`.
- Prefer repository-owned scripts, tests, lint, CI, logs, metrics, traces, and
  fixtures over additional prompt reminders when they can provide the missing
  capability mechanically.
- Consider Symphony-style orchestration only after parallel task load,
  resumability, stable task state, per-task workspaces, and permission
  boundaries create a demonstrated need.

## Source Direction

- [Harness Engineering](https://openai.com/index/harness-engineering/) informs
  repository legibility, mechanical constraints, feedback, observability, and
  entropy control.
- [Symphony](https://openai.com/index/open-source-codex-orchestration-symphony/)
  informs the adoption gate for task state, isolated workspaces, retries, and
  orchestration; it is not an implementation requirement.
- [Building self-improving tax agents with Codex](https://openai.com/index/building-self-improving-tax-agents-with-codex/)
  informs the reviewed evidence-to-finding-to-evaluation loop.
- [Codex-maxxing](https://cdn.openai.com/pdf/8a9f00cf-d379-4e20-b06f-dd7ba5196a11/OAI_WhitePaper_Codex-maxxing26.pdf)
  informs the boundary between durable threads, memory, repository facts, and
  verifiable goals.
- [Building an AI-native engineering team](https://cdn.openai.com/business-guides-and-resources/building-an-ai-native-engineering-team.pdf)
  informs delegation, review, ownership, and human escalation.

## Alternatives Rejected

- **New harness and evaluation skills:** adds model-visible trigger and context
  load for topics that belong in the existing engineering router.
- **A full reusable `AGENTS.md` template:** encourages repositories to copy a
  handbook instead of exposing their actual maps, commands, and exceptions.
- **Prompt or memory reminders for repeated operations:** cannot provide the
  execution or mechanical feedback that a repository script or check can own.
- **Immediate Symphony-style orchestration:** adds state and operational
  machinery before task volume and recovery needs justify it.
- **Static validation as proof of improvement:** proves structure, not output
  quality on representative work.

## Consequences

Calibration gains two on-demand references and a small set of behavioral
evaluation inputs. Individual repositories still own their concrete commands,
tests, deployment checks, observability, and local exceptions.

Behavior changes must be evaluated separately from this implementation task.
Adding evaluation cases records hypotheses and acceptance criteria; it does not
by itself prove that calibration improved.

## Reopen When

Reconsider the ownership boundary if harness or evaluation work develops an
independent interaction mode that must be invoked directly, or if a working
orchestrator and sustained parallel task load require a durable workflow
contract beyond repository scripts and project-management state.
