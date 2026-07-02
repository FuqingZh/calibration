---
name: brainstorming
description: User-invoked exploratory design mode for ambiguous problems, feature shape, behavior changes, or implementation approaches.
disable-model-invocation: true
---

# Brainstorming Ideas Into Designs

Use this skill only when the user explicitly invokes it or clearly asks to
brainstorm before implementation. It is an optional mode, not a default coding
workflow.

Help turn ideas into fully formed designs through natural collaborative
dialogue. Start by understanding the current project context, then ask
questions one at a time to refine the idea. Once you understand what is being
designed, present the design and get user approval before implementation.

<HARD-GATE>
Do NOT write code, scaffold projects, edit repo-tracked files, or take any
implementation action until you have presented a design and the user has
approved it. This applies to every brainstorming request regardless of perceived
simplicity. The design can be short for small changes, but it must exist and be
approved first.
</HARD-GATE>

## Checklist

You MUST complete these items in order:

1. **Explore project context** - check relevant files, docs, recent commits, and
   local conventions before asking questions when the context is discoverable.
2. **Offer the visual companion just-in-time** - not upfront. The first time a
   question would genuinely be clearer shown than described, offer it then. If
   no visual question arises, never offer it.
3. **Ask clarifying questions** - one at a time, focused on purpose,
   constraints, success criteria, and the tradeoff that most changes the design.
4. **Propose 2-3 approaches** - make them meaningfully different, include
   tradeoffs, and lead with your recommendation and reasoning.
5. **Present the design** - scale detail to the problem, cover the important
   boundaries and verification path, and get user approval before moving on.
6. **Capture the validated design only when needed** - use the repository's
   docs, decision-record, plan, or trace convention. Do not force a
   `docs/superpowers/specs/` path.
7. **Move into implementation planning only when appropriate** - use the active
   repository or environment format. Do not force a `writing-plans` transition
   unless the user invokes it or the repository workflow requires it.
8. **Commit only when appropriate** - commit only when the user asks, the task
   includes commit/push, or a repository workflow explicitly requires a
   committed design or plan.

## The Process

**Understanding the idea:**

- Check the current project state first when files, docs, or conventions are
  relevant.
- Before asking detailed questions, assess scope. If the request spans multiple
  independent subsystems, flag that immediately and help decompose it instead
  of refining a too-large design.
- For appropriately scoped work, ask questions one at a time.
- Prefer multiple-choice questions when possible, but open-ended questions are
  fine when the decision space is not yet clear.
- Ask only one question per message. If a topic needs more exploration, break it
  into multiple turns.
- Focus on purpose, constraints, success criteria, audience, and failure modes.

**Exploring approaches:**

- Propose 2-3 different approaches with tradeoffs.
- Present options conversationally with your recommendation and reasoning.
- Lead with the recommended option when the evidence favors one.
- Remove unnecessary features from all designs.

**Presenting the design:**

- Once you understand the design target, present the design.
- Scale each section to its complexity: a few sentences for straightforward
  changes, more detail for nuanced tradeoffs.
- Ask whether the design looks right before moving into planning or
  implementation.
- Cover the affected components, boundaries, data or control flow when relevant,
  error handling or failure behavior when relevant, and verification path.
- Be ready to go back and clarify if something does not make sense.

**Design for isolation and clarity:**

- Break the system into units that each have one clear purpose, communicate
  through well-defined interfaces, and can be understood and tested
  independently.
- For each unit, be able to answer what it does, how it is used, and what it
  depends on.
- If a consumer cannot understand a unit without reading its internals, or if
  internals cannot change without breaking consumers, the boundary needs work.
- Smaller, well-bounded units are easier to reason about and edit reliably.

**Working in existing codebases:**

- Explore the current structure before proposing changes.
- Follow existing patterns unless they are part of the problem being solved.
- Where existing code has problems that affect the work, include targeted
  improvements as part of the design.
- Do not propose unrelated refactors. Stay focused on what serves the current
  goal.

## Design Checkpoint

End the brainstorming phase with a clear design checkpoint. It should state:

- the problem being solved
- the selected approach and rejected alternatives
- the affected components and boundaries
- the data or control flow when relevant
- the verification path
- the remaining risks or assumptions

The checkpoint does not have to be written to disk unless the design should
outlive the conversation or the repository workflow requires it.

## Key Principles

- **One question at a time** - do not overwhelm with multiple questions.
- **Multiple choice preferred** - easier to answer than open-ended questions
  when the tradeoff is already known.
- **YAGNI ruthlessly** - remove unnecessary features from all designs.
- **Explore alternatives** - always propose 2-3 approaches before settling.
- **Incremental validation** - present the design and get approval before
  moving on.
- **Be flexible** - go back and clarify when something does not make sense.

## Visual Companion

Use the visual companion only when a design question is genuinely clearer as a
mockup, diagram, or side-by-side visual comparison. Do not offer it for ordinary
textual scope or tradeoff questions.

Offer the companion just in time. The first time a question would genuinely be
clearer shown than told, send only this offer and wait for the user's response:

> This next part might be easier if I show you. I can put together mockups,
> diagrams, and comparisons in a browser tab as we go. It is still new and can
> be token-intensive. Want me to open it?

Even after the user accepts, decide for each question whether to use the
browser or text. Use the browser for mockups, wireframes, layout comparisons,
architecture diagrams, and side-by-side visual designs. Use text for
requirements questions, conceptual choices, tradeoff lists, scope decisions, and
ordinary implementation choices.

If visual support is useful, read `visual-companion.md` before using the helper
scripts.
