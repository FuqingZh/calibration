# Coding Protocol And Calibration Comparison

Status: comparison complete; user subsequently authorized the
[runtime retirement trial](../../docs/decisions/2026-09-07-coding-protocol-runtime-retirement-trial.md).

## Question And Frozen Design

Does the current `coding-protocol` add observable value when `calibration` is
available, and does removing it leave a gap on ordinary local work where
calibration's own trigger says to skip?

Compare three arms: calibration, coding-protocol, and both. Four fixtures cover
local repair with an existing user edit, an extensible configuration contract,
a read-only compatibility review, and repair of a vacuous CLI verification gate.
Each arm repeats each fixture twice, for 24 attempts. The model is
`gpt-6-astra` at medium effort, with four concurrent isolated CLI processes and
a 180-second limit per attempt. No failed run is silently replaced.

The current skill trees and shared global instruction template are frozen by
SHA-256 before execution. Each run has a fresh home and workspace, the same
native CLI defaults, and identical task-specific instructions. It explicitly
reads the selected skill entrypoints and follows their applicability and
reference routing; this does not measure implicit skill discovery. The shared
global template remains present in all arms. No live AO or external writes are
part of the fixtures.

Quality and authorization compliance are primary. Token usage is paired by
fixture and repetition only after checking quality. Input plus output tokens
are reported CLI usage, not a billing amount; cached input is not added twice.
Missing, timed-out, or wrong-model runs remain visible and cannot establish an
arm preference. Wall time is descriptive, not evidence of a skill's causal
latency effect. All four frozen criteria must be assessed for every valid run.

Raw evidence and the frozen runnable harness live in the user-selected private
experiment directory. They include source hashes, prompts, artifacts, CLI
streams, model identity, and per-run outcomes. They must not be copied into the
public repository with isolated homes or authentication material.

## Static Comparison

| Concern | Calibration and shared host rules | Coding-protocol difference |
| --- | --- | --- |
| Applicable scope | Calibration skips clear ordinary local implementation | Covers local execution and read-only code evidence too |
| Local authority and proportional checks | Explicit in principles and the shared global template | Repeats the principle with a more prescriptive selection record |
| Compatibility and truthful completion | Contract routing and verification require evidence and limits | Adds explicit runtime-mismatch and authorization examples |
| Work preservation and authority | Native executor rules and global ownership rules remain active | Consolidates preservation, diagnosis-only, and external-action boundaries |
| Check sensitivity | Verification emphasizes final observable contracts | Its verification reference explicitly requires a negative control for a new or changed check |
| Reference loading | Decision-specific routers | Execution applicability gate plus three conditional references |

Static overlap alone does not establish behavioral redundancy. In particular,
calibration is not an unconditional execution protocol. The experiment tests
both overlap and potential lost coverage; it does not assume calibration should
be expanded to compensate for removal.

## Results

All 24 attempts completed with the requested model and effort, with no timeout
or nonzero CLI exit. CLI completion and task completion are separate: one
coding-protocol-only run stopped without implementing its requested gate fix.

| Fixture | Calibration complete | Both complete | Both versus calibration tokens, repetitions 1 / 2 |
| --- | --- | --- | --- |
| Local repair | 2/2 | 2/2 | -25.1% / -2.3% |
| Extensible contract | 2/2 | 2/2 | -15.7% / +9.0% |
| Read-only review | 2/2 | 2/2 | +36.4% / +35.9% |
| Verification gate | 2/2 | 2/2 | +7.8% / -7.6% |

Calibration and both each completed 8/8 tasks and satisfied all four frozen
criteria per task. The median paired token change for both over calibration is
+2.8%; four pairs are higher and four lower. Aggregate reported tokens are
876,172 for calibration and 907,042 for both (+3.5%). These figures do not show
a stable general overhead or efficiency benefit. The two read-only reviews do
show consistent extra reported tokens in this fixture without a quality gain.

The coding-protocol-only arm completed 7/8 tasks. In `gate-cp-1`, the agent
identified the vacuous gate but stopped because the common global instructions
required calibration for harness changes and that arm lacked calibration.
Its final response honestly reported no change. The original gate still
accepted violating programs. This exposes a dependency in the installed policy,
not an isolated estimate of coding-protocol harm. The coding-protocol-only arm
is diagnostic; calibration versus both is the valid primary removal comparison.

Independent sandbox checks exercised additional whitespace inputs, both required
configuration fields and extension preservation, and six gate targets covering
compliant formatting, wrong values, wrong exits, and invalid JSON. All completed
implementations passed. Read-only reviews all identified the zero-value caller
regression and illegal coercions, remained read-only, and distinguished the
existing passing tests from compatibility proof. Command traces confirmed the
required local checks. Every run preserved protected files and guidance.

## Interpretation And Decision

The current standalone coding-protocol entrypoint is a reasonable candidate for
a reversible retirement trial: its central constraints overlap with calibration,
the fixed global instructions, and native executor behavior, and adding it gave
no observed quality benefit in this comparison. Calibration alone also handled
the ordinary repair and verification sensitivity cases without an observed gap.

This is a recommendation, not adoption of a new baseline. The evaluation itself kept source, license, and installation intact. Do not copy the whole
protocol into calibration or broaden calibration's trigger to preserve ritual.
A future retirement should remove only the managed runtime entrypoint, retain
provenance, and be followed on representative real work with an easy restoration
path. The subsequent user-authorized retirement is recorded separately in the trial
decision above.

## Evidence And Limits

- Public artifacts: [fixtures](cases.json), [criterion scores](scores.json),
  [independent artifact checks](artifact-checks.json), and
  [paired token results](paired-results.json).
- The executed frozen harness and raw records are in the private directory
  selected by the user. Its `manifest.json` records source hashes and its
  original `run.py` is execution authority. Execution and verification scripts
  remain with that private record. Public fixtures and the prompt prefix
  preserve the evaluated inputs; no second batch was launched.
- All frozen source hashes were verified after execution. Public fixture data
  matches the executed manifest. Fresh homes and workspaces were used; this
  tests the current global template plus explicitly loaded skills, not bare
  GPT-6 or the full desktop installation and implicit discovery chain.
- The controller reviewed outputs and actual commands and ran independent
  artifact probes. Judging was not independently blinded: arm identities were
  visible during trajectory inspection. This is bounded diagnostic evidence,
  not a blinded adoption evaluation or a statistical equivalence result.
- Tasks have strong explicit contracts and are small synthetic fixtures. There
  is no held-out real-work rollout, destructive Git test, live AO handoff,
  migration recovery, multi-worktree contention, or production authorization
  test. Two repeats cannot establish rare-failure rates or general redundancy.
- A formatting error in the controller's independent local-repair probe briefly
  produced a Python string syntax error. The probe was corrected and all final
  artifacts rechecked. This was a verifier defect, not a model failure; final
  artifact results contain the corrected checks.
- No elapsed-time or monetary saving is claimed. Do not count the blocked
  coding-protocol-only task as a successful low-cost result.

The public `prompt.txt` omits the original trailing blank separator line; the
private execution record retains the exact prompt bytes.
