---
name: brainstorming
description: User-invoked exploratory design mode for ambiguous problems, feature shape, behavior changes, or implementation approaches.
disable-model-invocation: true
---

# Brainstorming

Use this skill only when the user explicitly invokes it or clearly asks to
brainstorm before implementation. It is an optional mode, not a default coding
workflow.

The goal is to turn an ambiguous idea into an approved design that can be
implemented with the repository's normal planning and documentation practice.

## Process

1. Explore the current project context first: files, docs, recent commits, and
   local conventions relevant to the idea.
2. Ask clarifying questions one at a time. Prefer a concrete recommended answer
   when the tradeoff is clear.
3. Propose two or three approaches with tradeoffs and a recommendation.
4. Present the selected design at the right level of detail and get user
   approval before implementation.
5. Capture the validated design when it should outlive the conversation. Use
   the repository's docs, decision-record, plan, or trace convention; do not
   force `docs/superpowers/specs/`.
6. Move into implementation planning using the active repository or environment
   format. Do not force a `writing-plans` transition unless the user invokes it
   or the repository workflow requires it.
7. Commit only when the user asks, the current task includes commit/push, or a
   repository workflow explicitly requires a committed plan.

## Scope Control

- If the idea spans multiple independent subsystems, first decompose it into
  smaller design targets.
- Do not propose unrelated refactors. Include only targeted structure changes
  that materially improve the current design.
- Treat direct user instructions and repository-local conventions as stronger
  than this skill's defaults.

## Design Quality

A design is ready when it states:

- the problem being solved
- the selected approach and rejected alternatives
- the affected components and boundaries
- the data or control flow when relevant
- the verification path
- the remaining risks or assumptions

## Visual Companion

Use the visual companion only when a design question is genuinely clearer as a
mockup, diagram, or side-by-side visual comparison. Do not offer it for ordinary
textual scope or tradeoff questions.

If visual support is useful, read `visual-companion.md` before using the helper
scripts.
