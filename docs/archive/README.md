# Historical Records

This index records lifecycle status, not a second set of operating rules.
Completed plans and superseded protocols are archived in place: their existing
paths and evidence remain available, but they are not active execution plans.
Settled adoption decisions can still explain current behavior; follow the
[current authority map](../README.md#current-authority) for runtime contracts.

Original evidence, frozen manifests, hashes, licenses, and provenance are not
rewritten or deduplicated. Historical invocation metadata does not activate a
retired skill. The installer retains owned-link cleanup and foreign-link
preservation.

## Completed Plans And Superseded Protocols

| Record | Lifecycle and current source |
| --- | --- |
| [Self-contained skill migration](../implementation-plans/20260826-v1.0-self-contained-first-party-skills-migration-implementation-plan.md) | Implemented; historical migration evidence. Current package contracts live in the skills and validator. |
| [Proportional validation wording](../implementation-plans/20260807-v1.0-proportional-validation-selection-implementation-plan.md) | Completed wording increment; [principles](../../skills/calibration/references/principles.md) own current guidance. |
| [Progressive validation v2.0](../implementation-plans/20260824-v2.0-progressive-validation-selection-implementation-plan.md) | Historical implementation and smoke/recovery evidence; later comparisons supersede its replacement protocol. |
| [Relative replacement v2.1](../testing/20260825-v2.1-progressive-validation-relative-replacement-test-plan.md) | Executed diagnostic history; its outcome interpretation was superseded by v2.2. |
| [Corrected relative replacement v2.2](../testing/20260825-v2.2-progressive-validation-relative-replacement-correction-plan.md) | Completed comparison; the [corrected decision](../decisions/2026-08-25-progressive-validation-relative-replacement-acceptance.md) supersedes the earlier acceptance interpretation. |
| [Progressive validation evaluation](../../evaluations/progressive-validation-selection/README.md) | Completed comparison, empirically inconclusive; later adoption and retirement are separate user decisions. |
| [Teach first comparison](../../evaluations/teach-adaptation/results.md) | Superseded by [traceable V2](../../evaluations/teach-adaptation/v2/README.md); both evidence bundles remain intact. |
| [Review-convergence routing](../implementation-plans/20260803-v2.3-review-convergence-routing-implementation-plan.md) | Completed increment; [harness](../../skills/calibration/references/discipline/harness.md) owns current routing. |
| [Closeout implementation](../implementation-plans/20260804-v2.4-closeout-skill-implementation-plan.md) | Completed increment; the [whole-conversation contract](../decisions/2026-09-07-closeout-whole-conversation-contract.md) supersedes the earlier durability gates. |
| [CAL-1 containment](../implementation-plans/20260731-v2.1-portable-orchestrator-containment-implementation-plan.md) | Public contract delivered; upstream process containment is a proposal, not verified AO behavior. |

The [project docs convergence plan](../implementation-plans/20260805-v1.0-project-docs-architecture-convergence-implementation-plan.md)
still records pending downstream work and is not archived as a completed plan.
Earlier July harness and delivery plans remain in
[implementation-plans](../implementation-plans/); completed local phases do not
authorize new host operations or reopen downstream work.

The [retired third-party skill archive](../../thirdparty/archive/README.md)
contains brainstorming, coding-protocol, writing-great-skills, and writing-plans
with their source and provenance preserved outside the active skill tree.

## Adoption Decisions And Comparison Evidence

| Topic | Record and limits |
| --- | --- |
| Version naming | [Decision and source comparison](../decisions/2026-10-21-version-naming-reference.md); scoped reference adoption, no agent-performance claim. |
| Brainstorming retirement | [Decision](../decisions/2026-10-22-brainstorming-retirement.md); user-requested removal from installation, unchanged source retained, no model-quality equivalence claim. |
| Design and debugging wording | [Trial](../../evaluations/calibration-wording-20261015/README.md); repeated decision-only regression acceptance, no superiority or whole-skill replacement claim. |
| Multi-client installation | [Decision](../decisions/2026-09-24-multi-client-skill-installation.md); bounded installation and discovery evidence. |
| Body compression | [Decision](../decisions/2026-09-20-calibration-body-compression-and-routing.md), [routing diagnosis](../../evaluations/calibration-routing-diagnosis/README.md); three bodies adopted, metadata candidates remain experimental. |
| Component ablation | [Evaluation](../../evaluations/calibration-component-ablation/README.md); no whole-skill redundancy claim. |
| Coding-protocol retirement | [24-run comparison](../../evaluations/coding-protocol-calibration/README.md), [retirement trial](../decisions/2026-09-07-coding-protocol-runtime-retirement-trial.md); source and license retained. |
| Skill retirement and snippet scope | [Decision](../decisions/2026-09-07-gpt6-skill-retirement-and-snippet-scope.md); writing-great-skills source remains preserved. |
| Teach adaptation | [Decision](../decisions/2026-08-13-teach-adaptation-evaluation.md); bounded regression acceptance, no general learning-outcome claim. |
| Diagnostic suppression | [Decision](../decisions/2026-08-14-diagnostic-suppression-policy.md), [writable fixture protocol](../../evaluations/ai-native-implementation/README.md); bounded W07 evidence. |
| Advisor and calibration ablation | [Results](../../evaluations/sol-advisor-calibration-ablation/results.md); no supported default Advisor or mandatory CAL-MIN benefit for the tested local repair. |
| AI-native convergence | [Direction](../decisions/2026-07-27-ai-native-calibration-review.md), [five-phase closeout](../decisions/2026-07-27-ai-native-calibration-convergence-closeout.md), [writable closeout](../decisions/2026-07-27-ai-native-writable-implementation-evaluation-closeout.md); recorded task and environment boundaries apply. |
| Proportional validation | [Decision](../decisions/2026-08-07-proportional-validation-selection.md); completed wording adoption. |
| Chinese Humanizer | [On-demand trial](../decisions/2026-09-10-humanizer-zh-on-demand-trial.md); separately managed, no core routing expansion. |

Progressive validation also retains its [frozen baseline](../decisions/2026-08-24-progressive-validation-selection-baseline.md),
[activation candidate](../decisions/2026-08-24-progressive-validation-selection-candidate.md),
[invalid smoke and recovery](../decisions/2026-08-24-progressive-validation-selection-smoke-invalid.md),
[approval preflight](../decisions/2026-08-25-progressive-validation-relative-replacement-preflight.md),
and [outcome-only scope](../decisions/2026-08-25-progressive-validation-outcome-only-approval-scope.md).
These retain their historical roles without becoming current execution plans.

## Earlier Architecture And Harness History

- [Rename and skill architecture](../decisions/2026-07-01-calibration-rename-and-skill-architecture.md)
- [Follow-up batches](../decisions/2026-07-01-calibration-follow-up-batches.md)
- [Document types and retrospectives](../decisions/2026-07-01-document-types-retrospect-and-evaluation.md)
- [Code documentation skill](../decisions/2026-07-03-writing-docstrings-skill-design.md)
- [Harness ownership](../decisions/2026-07-20-agent-harness-and-evaluation-ownership.md)
- [Harness closeout](../decisions/2026-07-20-agent-harness-and-evaluation-closeout.md)
- [Successor evaluation](../decisions/2026-07-21-harness-successor-evaluation-closeout.md)
- [AI-native evaluation](../decisions/2026-07-27-ai-native-calibration-evaluation-closeout.md)

## AO And Host History

The [retired AO guide](ao-integration-retired-2026-10-15.md) and these records
retain rationale and historical evidence. They do not define current integration
rules. Detailed host snapshots and deployment material belong to private host
authority.

- [Native guidance consolidation](../decisions/2026-09-07-ao-native-guidance-consolidation.md)
- [Older archived guidance](ao-guidance-before-v0.12.12/)
- [Delivery feedback loop](../decisions/2026-07-21-repository-delivery-feedback-loop.md)
- [Review continuation adoption](../decisions/2026-07-23-ao-review-continuation-adoption.md)
- [Historical native delivery](../decisions/2026-07-29-ao-native-delivery-convergence.md)
- [Quality-gate adoption plan](../implementation-plans/20260723-v1.6-repository-quality-gate-implementation-plan.md)
- [Repository adoption plan](../implementation-plans/20260723-v1.7-ao-repository-adoption-contract-implementation-plan.md)
- [AI-native convergence plan](../implementation-plans/20260727-v1.8-ai-native-calibration-convergence-implementation-plan.md)
- [Persistent intake plan](../implementation-plans/20260728-v1.9-persistent-linear-intake-and-no-product-canary-implementation-plan.md)
- [Three-scenario acceptance plan](../implementation-plans/20260728-v2.0-three-scenario-linear-acceptance-implementation-plan.md)
- [Codex-home compatibility](../decisions/2026-07-30-ao-host-context-and-config-compatibility.md)
- [Dashboard terminal boundary](../decisions/2026-07-30-dashboard-terminal-access-boundary.md)
- [Containment rationale and canary](../decisions/2026-07-31-portable-orchestrator-containment.md)
- [Host CLI closeout](../decisions/2026-08-04-ao-host-calibration-cli-closeout.md)

For further historical decisions, use the [decision directory](../decisions/).

## Retired AO Integration

The [retirement decision](../decisions/2026-10-15-ao-integration-retirement.md)
retires all AO integration entrypoints. The
[former canonical guide](ao-integration-retired-2026-10-15.md) and the AO records
above are historical evidence only. Their adoption, lifecycle, and installation
instructions no longer define calibration behavior. Frozen evaluation bundles
retain their original paths, hashes, and invocation metadata.
