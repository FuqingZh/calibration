# Proportional Validation Selection

Version: v1.0
Date: 2026-08-07
Status: accepted
Supersedes: [Default Repository Quality Gate](2026-07-30-default-repository-quality-gate.md)

## Decision

Select validation proportionally to the affected behavior and contracts. Run
the smallest relevant checks that can decide the changed surface. Run the
complete canonical gate when the change can affect runtime behavior, generated
artifacts, executable workflows, compatibility, or when repository-local
policy explicitly requires it.

Classify documentation by its effect rather than its file extension. Ordinary
wording, navigation, and document moves normally need documentation
consistency, link, formatting, or diff checks. Agent instructions, skills,
prompts, executable examples, generated documentation, and routing contracts
may require focused behavioral or runtime validation.

## Rationale

The previous complete-gate default reliably discovered repository feedback but
was too broad as a delivery rule. It caused changes with no runtime effect to
run code-oriented checks mechanically. Outcome autonomy is better served by
requiring sufficient evidence for the actual affected contract while allowing
an explicit repository mandate to remain authoritative.

This decision defines an outcome constraint, not a file-type matrix. Agents
retain judgment over the exact checks and must report any required check they
cannot run and the resulting residual risk.

## Verification

The installed global instruction template, repository-local validation entry,
navigation, structural contract test, and representative routing case must
agree on the proportional-selection rule. Static consistency demonstrates the
contract is wired correctly; it does not claim broader behavioral superiority.
