# Calibration Component Ablation Protocol

## Frozen Comparison

The source is commit `15135fbd5d3e70edbb79d5293beeaa0687e4df23`.
Each of eight components has two synthetic tasks, two arms, and two repetitions:
64 candidate calls. The full arm receives the current relevant guidance bundle;
the minus arm receives the same bundle with one component removed. The common
global instruction template remains present in both arms. A seeded schedule
interleaves arms and tasks with four concurrent processes.

The requested model is `gpt-6-astra`, medium effort, through Codex CLI 0.154.0.
Each call uses a fresh home and workspace, ignores user configuration, disables
automatic project-document loading and memory, and runs an ephemeral read-only
session. Prompts forbid tools, external access, and real operations. A tool call,
timeout, nonzero exit, or missing structured answer invalidates that attempt.
The limit is 180 seconds per call. Original attempts are retained.

The ephemeral event stream does not independently attest the server-side model
identity. The model name and effort are invocation evidence. Native CLI context
remains common to both arms; this is not a bare-model comparison.

## Components And Tasks

| Component | Material removed | Tasks |
| --- | --- | --- |
| General principles | Problem Framing, Outcome Autonomy And Feedback, Performance and Measurement; the outcome-autonomy paragraph in SKILL.md | G1 local normalization fix; G2 proportionate README validation |
| Native abstractions | Native Abstractions and Data Flow | N1 CSV round trip; N2 large-table SQL selection |
| Configuration | Configuration and Defaults | C1 extensible configuration; C2 reproducible split |
| Communication | Communication; the direct-expression paragraph in SKILL.md | S1 Chinese status update; S2 necessary correction of a 202 misconception |
| Naming | naming/function.md and naming/variable.md | M1 function prefixes; M2 internal role name and public compatibility |
| Design | design/codebase.md | D1 forwarding-only layers; D2 public rendering boundary |
| Verification | discipline/verification.md and discipline/debugging.md | V1 sandbox versus host diagnosis; V2 non-vacuous CLI verification gate |
| AO | AO integration guide and discipline/harness.md | A1 incomplete runtime cleanup; A2 unproved foreground handoff |

All arms retain SKILL.md and principles.md except for the specified deletions.
References are expanded explicitly. This measures marginal value after loading;
it does not test natural skill discovery, reference routing, or interactive tool
use. The full arm is the relevant bundle, not every reference in the repository.

G1 and G2 are negative controls for unnecessary process on clear local work.
Such work ordinarily skips calibration. Their results do not establish that
problem framing or performance guidance is redundant on difficult tasks.
Removing several sections as one component also does not identify the separate
effect of each sentence or interaction between removed sections.

## Acceptance And Blinding

Four binary criteria per answer were frozen before execution. Each component
has four answers and 16 criterion opportunities per arm. Critical functionality,
scope, authority, and false-completion defects are reported separately.
Default seed 42, scan/sink naming, and the unsolicited-contrast preference have
separate convention criteria. Losing a local convention does not establish a
generic engineering defect.

After candidate completion, a fresh model invocation for each task rates its
four anonymous answers. The judge receives the task and frozen rubric without
the arm, removed source, usage, or elapsed time. It can assign ties. These are
independent invocations of the same requested model, not independent human
reviewers. The controller audits disagreements and supporting artifacts and
records any scoring correction without discarding the original rating.

Generated code for G1, N1, C1, C2, and V2 is also executed against independent
acceptance probes. Bubblewrap isolates execution from the user's home,
credentials, repository, and network. Tests cover quoted CSV content, input
preservation, extension keys, seed overrides and random-state isolation, and
both conforming and violating CLI targets. A complete file or one unambiguous
Python code block is accepted as the submitted implementation.

Evaluator environment, extraction, or fixture bugs are recorded separately and
repaired without replacing candidate outputs. These probes are finite contract
checks; they do not establish exhaustive correctness.

## Interpretation

Quality and completion precede token comparisons. Reported input tokens already
include cached input; cached tokens must not be added again. Pair cost by task
and repetition. Input length, generated length, and wall time are distinct;
wall time and aggregate tokens do not establish billing or causal speed gains.
Loaded-reference savings apply only when that reference would otherwise load.

A tie in two small tasks is evidence of no observed marginal benefit on those
tasks. It cannot establish equivalence, a rare-failure rate, or universal
redundancy. Strong task wording can itself supply a constraint that calibration
would otherwise need to provide. The fixed global template also intentionally
retains proportional checks, host-state caution, and ownership safeguards.
Ties therefore do not support removing those safeguards from every layer.

The comparison excludes real AO execution, destructive operations, live handoff,
complex refactoring, long conversations, whole-bundle removal, and combinations
of individually removed components. It does not test Project Knowledge,
documentation specifications, unselected naming references, evaluation guidance,
or the independent closeout, retrospect, and third-party skills.

The experiment does not change active guidance or installation. Any later
retirement or compression is a separate reversible change, followed by checks
against representative work and the specific obligations it might remove.

## Evidence Storage

The public evaluation keeps sanitized fixtures, model answers, criterion scores,
artifact checks, source hashes, paired metrics, and this protocol. The original
executed prompts, CLI streams, scripts, authentication links, and isolated homes
remain in the user-selected private experiment directory. Do not publish those
homes or private execution context. Public source hashes and the pinned Git
commit identify the guidance used; invocation hashes identify each exact prompt.
