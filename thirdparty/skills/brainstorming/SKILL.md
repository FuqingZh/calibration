---
name: brainstorming
description: User-invoked exploratory design mode for ambiguous problems, feature shape, behavior changes, or implementation approaches.
---

# Brainstorming Ideas Into Designs

Use this skill when the user explicitly invokes it or asks to brainstorm before
implementation. Turn the idea into an approved design through the protocol
below.

<HARD-GATE>
Do NOT write code, scaffold projects, edit repo-tracked files, or take any
implementation action until you have presented a design and the user has
approved it. The design can be short, but it must exist and be approved.
</HARD-GATE>

## Protocol

1. **Explore the project.** Inspect relevant files, documentation, recent
   commits, and local conventions before asking questions when the context is
   discoverable. If the request spans independent subsystems, help decompose it
   before refining a design.
2. **Clarify one decision at a time.** Ask at most one question per message and
   wait for the answer. Focus on purpose, constraints, success criteria,
   audience, failure behavior, and the tradeoff most likely to change the
   design. Prefer multiple choice when the decision space is already known.
3. **Compare 2-3 approaches.** Make them mutually exclusive and materially
   different. Lead with the recommended approach and explain its tradeoffs;
   keep unnecessary features out of every option.
4. **Present the design.** Scale detail to the problem and cover affected
   components, boundaries, data or control flow when relevant, failure behavior,
   and verification. Follow repository-local design rules, using the
   `$calibration` design route when shared guidance is needed.
5. **Get approval.** End with the Design Checkpoint and wait for explicit user
   approval. Return to clarification when the design is not yet accepted.

After approval, use the repository's normal planning and implementation path.
Capture the design or commit it only when the user asks or the repository
workflow requires it; do not force a spec path or a `writing-plans` handoff.

## Design Checkpoint

End the brainstorming phase with:

- the problem being solved
- the selected approach and rejected alternatives
- the affected components and boundaries
- the data or control flow when relevant
- the verification path
- remaining risks or assumptions

## Visual Companion

Offer the visual companion only when the first genuinely visual design question
would be clearer as a mockup, diagram, or side-by-side comparison. At that point
send only this offer and wait:

> This next part might be easier if I show you. I can put together mockups,
> diagrams, and comparisons in a browser tab as we go. It is still new and can
> be token-intensive. Want me to open it?

If accepted, read `visual-companion.md` before using its helper scripts. Keep
requirements, scope, and ordinary tradeoffs in text; use the companion for
questions that benefit from visual comparison.
