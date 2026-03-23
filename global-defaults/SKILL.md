---
name: global-defaults
description: Use for default cross-project engineering rules. Provides shared principles, naming conventions, and document navigation for coding, refactoring, architecture, API, CLI, testing, and documentation tasks.
---

# Global Defaults

This skill contains the user's default cross-project engineering guidance.

Use this skill when:
- working on code
- planning or reviewing architecture changes
- defining or modifying APIs or CLIs
- naming modules, functions, methods, options, fields, files, or exported artifacts
- updating tests or documentation related to code changes

Do not use this skill for:
- casual conversation
- pure translation
- tasks unrelated to engineering work

## Loading order

Read only what is needed, in this order:

1. `references/principles.md`
2. `references/naming.md`
3. `references/docs_index.md`
4. Specific files under `docs/` only if `docs_index.md` points to them for the current task

## Rules

- Treat `references/principles.md` as the source of truth for cross-project engineering principles.
- Treat `references/naming.md` as the source of truth for cross-project naming and interface conventions.
- Treat `references/docs_index.md` as navigation only, not as the source of truth for rules.
- Do not load the entire `docs/` tree by default.
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
- respect project-local exceptions
- avoid unnecessary documentation loading
- support the user's English improvement without distorting the main task
