---
name: calibration
description: Use for default cross-project engineering rules. Provides shared principles, naming conventions, architecture judgment, interface guidance, and document navigation for coding, refactoring, API, CLI, testing, and documentation tasks.
---

# Calibration

This skill is the user's default cross-project engineering calibration entrypoint.

Use this skill when:
- working on code
- planning or reviewing architecture changes
- deciding module boundaries, interface shape, abstraction depth, or where logic belongs
- reviewing main-path readability, wrapper layers, or implementation tradeoffs
- designing project documentation structure or engineering trace/retro rules
- defining or modifying APIs or CLIs
- naming modules, functions, methods, options, fields, files, or exported artifacts
- updating tests, documentation, or project knowledge records related to code changes

Do not use this skill for:
- casual conversation
- pure translation
- tasks unrelated to engineering work

## Loading order

Read only what is needed, in this order:

1. `../../references/engineering/principles.md`
2. Topic routers only when the current task needs them:
   - naming decisions: `../../references/engineering/naming/README.md`
   - refactor, debugging, or completion checks: `../../references/engineering/discipline/README.md`
   - architecture, module, interface, abstraction, or wrapper decisions: `../../references/engineering/design/README.md`
   - long-form specifications, project-doc routing, or document-type selection:
     `../../references/engineering/docs_index.md`
3. Specific files pointed to by those routers, only when their trigger matches
   the current task.
4. `../../references/engineering/docs/technology/main_path_readability/20260318-v1.0.md`
   when reviewing wrapper layers, orchestration shape, or main-path readability.

## Rules

- Treat `../../references/engineering/principles.md` as the source of truth for stable cross-project engineering principles.
- Treat `../../references/engineering/naming/README.md`, `../../references/engineering/discipline/README.md`, and `../../references/engineering/design/README.md` as routers, not rule dumps.
- Read only the specific routed file needed for the current decision.
- Treat `../../references/engineering/docs_index.md` as navigation only, not as the source of truth for rules.
- Do not load the entire `docs/` tree by default.
- Keep business-critical paths shallow, direct, and auditable.
- Add abstractions only when they create a real semantic, lifecycle, ownership, policy, or reuse boundary.
- Separate corrected problem framing from implementation mechanics when the user's premise is weak.
- Load document-type routing only when the task involves writing, placing, or
  classifying project docs, implementation plans, decisions, or task retros.
- Load workflow documentation only when the task specifically involves project docs architecture, `.traces`, engineering retrospectives, or knowledge-promotion rules.
- Suggest `$retrospect` only after meaningful engineering deltas such as failed
  assumptions, rework, validation surprises, broad refactors, customer-facing
  delivery, deployment risk, repeated patterns, or production-adjacent work.
  Do not run it automatically.
- If repository-local instructions are more specific, follow the repository-local instructions for that repository.
- If the user explicitly requests a different approach, follow the user request.

## Failure Branches

| Trigger | Action |
|---|---|
| Repository-local rules conflict with calibration | Follow the repository-local rule and note the exception briefly. |
| Direct user instructions conflict with calibration | Follow the user instruction unless it requires unsafe or impossible action; state the tradeoff. |
| A routed reference file is missing | Continue from `principles.md`, say which reference was unavailable, and do not invent the missing rule. |
| The task spans multiple routers | Load only the routers needed for the active decision; do not preload the whole docs tree. |
| The task has a meaningful engineering delta | Suggest `$retrospect` once; do not run it without explicit invocation. |
| The user asks for docs but the document type is unclear | Use `docs_index.md` and document-type routing before writing durable docs. |

## Response mode

- Default to English-first responses for substantive engineering work unless the user asks for a different language balance.
- When the user writes in English, first provide a brief corrected version if the message has meaningful grammar, phrasing, or naturalness issues.
- After any brief correction, handle the actual request normally rather than turning the reply into a language lesson.
- Add brief Chinese notes only for critical vocabulary, key grammar points, or places where comprehension risk is high.
- Continuously adapt vocabulary, sentence complexity, abstraction level, and correction strictness to the user's demonstrated English level.
- Do not let language coaching reduce technical accuracy, task completion, or clarity on high-risk topics.

## Expected outcomes

After using this skill, changes should:
- follow the shared principles
- load only the relevant routed reference files
- use consistent naming
- make the main path easier to read and expose the smallest useful interface
- respect project-local exceptions
- avoid unnecessary documentation loading
- support the user's English improvement without distorting the main task
