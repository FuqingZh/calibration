---
name: global-defaults
description: Use for default cross-project engineering rules. Provides shared principles, naming conventions, architecture judgment, interface guidance, and document navigation for coding, refactoring, API, CLI, testing, and documentation tasks.
---

# Global Defaults

This skill contains the user's default cross-project engineering guidance.

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
2. `../../references/engineering/naming.md`
3. `../../references/engineering/docs_index.md`
4. Specific files under `../../references/engineering/docs/` only if
   `docs_index.md` points to them for the current task
5. `../../references/engineering/docs/technology/main_path_readability/20260318-v1.0.md`
   when reviewing wrapper layers, orchestration shape, or main-path readability

## Rules

- Treat `../../references/engineering/principles.md` as the source of truth for cross-project engineering principles.
- Treat `../../references/engineering/naming.md` as the source of truth for cross-project naming and interface conventions.
- Treat `../../references/engineering/docs_index.md` as navigation only, not as the source of truth for rules.
- Do not load the entire `docs/` tree by default.
- Keep business-critical paths shallow, direct, and auditable.
- Add abstractions only when they create a real semantic, lifecycle, ownership, policy, or reuse boundary.
- Separate corrected problem framing from implementation mechanics when the user's premise is weak.
- Load workflow documentation only when the task specifically involves project docs architecture,
  `.traces`, engineering retrospectives, or knowledge-promotion rules.
- If repository-local instructions are more specific, follow the repository-local instructions for that repository.
- If the user explicitly requests a different approach, follow the user request.

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
- use consistent naming
- make the main path easier to read and expose the smallest useful interface
- respect project-local exceptions
- avoid unnecessary documentation loading
- support the user's English improvement without distorting the main task
