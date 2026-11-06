# Docs Index

This file is navigation only. It points to longer documents under `docs/` that
may be loaded selectively when the task requires more detail.

## Default Loading Policy

- Do not load `docs/` by default.
- Load a specific document only when the current task materially depends on its
  rules.
- Prefer `principles.md` and `naming/README.md` unless the task is specifically about
  document-type selection, project documentation architecture, engineering traces,
  retrospectives, or main-path readability.

## Technology

- `docs/technology/main_path_readability/20260318-v1.0.md`
  - Use when reviewing wrapper layers, orchestration shape, or whether the main
    business path is too deeply hidden.

## Workflow

- `docs/document-types/README.md`
  - Use when writing, placing, or classifying architecture overviews, design
    proposals, decision records, implementation plans, or task retrospectives.
  - Do not use it for PR body generation unless the user asks how PR summaries
    relate to durable project docs.
- `docs/workflow/branch_and_pr_collaboration/20260602-v1.0.md`
  - Official GitHub sources for collaboration flow, branch protection, and merge
    queues. Use when a decision depends on those platform behaviors; repository
    rules own release and deployment exceptions.
- `docs/workflow/project_docs_architecture/20260805-v1.1-project-docs-architecture.md`
  - Use when defining project `docs/` layout, documentation file names,
    README navigation, document lifecycle, and long-lived knowledge placement.
- `$retrospect`
  - Use when defining `.traces/` layout, task retrospectives, evidence
    handling, and when to promote trace observations into project docs or canon.

## Schema

- `naming/schema.md` and `naming/artifact.md`
  - Use for locating repository-owned field and artifact contracts; follow the
    applicable protocol or workflow engine instead of a cross-project layout.

## Selection Rule

- If a repository already has a stricter local contract for one of these areas,
  follow the repository-local contract for that repository.
