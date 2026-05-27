# Docs Index

This file is navigation only. It points to longer documents under `docs/` that
may be loaded selectively when the task requires more detail.

## Default Loading Policy

- Do not load `docs/` by default.
- Load a specific document only when the current task materially depends on its
  rules.
- Prefer `principles.md` and `naming.md` unless the task is specifically about
  pipeline layout, artifact contracts, identifiers, project documentation
  architecture, engineering traces, retrospectives, or main-path readability.

## Technology

- `docs/technology/main_path_readability/20260318-v1.0.md`
  - Use when reviewing wrapper layers, orchestration shape, or whether the main
    business path is too deeply hidden.

## Workflow

- `docs/workflow/project_docs_architecture/20260527-v1.0-project-docs-architecture.md`
  - Use when defining project `docs/` layout, documentation file names,
    README navigation, document lifecycle, and long-lived knowledge placement.
- `docs/workflow/task_traces_and_retros/20260527-v1.0-task-traces-and-retros.md`
  - Use when defining `.traces/` layout, task retrospectives, evidence
    handling, and when to promote trace observations into project docs or canon.

## Schema

- `docs/schema/pipeline_directory_layout_specification/20260304-v1.1.md`
  - Use for step-based pipeline directory layout, stage root shape, and
    manifest placement.
- `docs/schema/step_to_step_artifact_flow_specification/20260304-v1.1.md`
  - Use for public/private artifact boundaries and cross-stage handoff rules.
- `docs/schema/identifier/20260304-v1.1.md`
  - Use for reversible technical identifiers and cross-module join keys.

## Selection Rule

- If a repository already has a stricter local contract for one of these areas,
  follow the repository-local contract for that repository.
