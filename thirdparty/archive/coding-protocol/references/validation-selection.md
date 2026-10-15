# Validation Selection

> **Apache-2.0 derivative notice.** This local reference adapts the generic
> verification method from GonkaGate `verification-before-completion`,
> [immutable commit `461578373f9c3a8eae3037504f659e0f3e0cc7cd`](https://github.com/GonkaGate/hermes-agent-setup/blob/461578373f9c3a8eae3037504f659e0f3e0cc7cd/.agents/skills/verification-before-completion/SKILL.md),
> under [Apache License 2.0](../../../licenses/GonkaGate-Apache-2.0.txt).
> Local modifications: this is independently written for repository-neutral
> validation selection; it omits upstream wording and any Node, TypeScript, or
> project command matrix. The pinned source root contained no `NOTICE` file.

Use this reference only when the selection is nontrivial or audited, focused
and broad checks compete, evidence is stale or indirect, or a failure creates
pressure to widen. Repository, user, and focused-workflow mandates remain
authoritative.

## Derive One Decision

1. State the exact claim: what outcome is being asserted complete or diagnosed?
2. Name each affected seam and its stable observable: public output, artifact,
   state transition, consumer contract, or declared guard.
3. Convert every seam into a proof obligation. Add mandatory checks from the
   user, repository, and focused workflow before optimizing anything.
4. Classify available evidence for each obligation:
   - **fresh direct**: recent evidence from the current state observes the
     obligation's seam;
   - **fresh partial**: recent evidence covers only part of the obligation;
   - **stale**: evidence predates the current relevant state;
   - **indirect**: evidence supports an inference but does not observe the
     seam; or
   - **missing**: no usable evidence is available.
5. Select the smallest falsifiable repository-owned check set that covers every
   uncovered obligation, alongside mandatory checks. Each selected check must
   be able to disprove the claim it covers.
6. Record why any smaller set leaves a named obligation uncovered. Record why a
   broader set is unnecessary, or why it is required.

A complete or broad gate is required when a more-specific rule mandates it, the
changed seam controls the gate, harness, build, packaging, dependency, lock,
generation, installation, release, or shared compatibility boundary, bounded
consumer checks cannot cover the contract, or no smaller reliable evidence is
available. It is not justified only because the repository has such a gate, the
file is Markdown, a pull request is planned, or a focused check failed.

If a check fails, diagnose its cause before widening. Add another check only
when the diagnosis identifies another seam or proof obligation; failure alone
does not authorize mechanical expansion.

## Record The Verdict

Write one compact decision containing the claim, seams, obligations, evidence
classes, mandatory checks, selected checks, smaller-set and broader-set reasons,
and residual risks from skipped, blocked, stale, indirect, or missing evidence.
End with exactly one verdict:

- **verified_ready** — fresh direct evidence and required checks cover all
  obligations;
- **conditionally_ready** — the stated claim is bounded by disclosed evidence
  gaps and residual risk; or
- **not_yet_verified** — required or essential proof remains absent, failed, or
  unreliable.
