# AI-Native Implementation Evaluation

This evaluation tests whether a calibration candidate improves writable
repository work rather than read-only descriptions of intended behavior.

## Cases

- `W01`: repair a reversible local defect without producing a durable plan.
- `W02`: replace an incorrect plan hypothesis when executable evidence points
  to the real ownership boundary.
- `W03`: use failing focused and smoke checks to complete a repair loop.
- `W04`: discover and run a repository-owned quality gate whose second check
  exposes a contract missed by the focused unit test.

Every case is a tiny dependency-free Python repository. The runner copies a
fixture into a fresh workspace, creates an initial Git commit, runs one Codex
turn, executes deterministic verification, and records the final repository
state. Model transcripts and isolated Codex homes belong in a private temporary
output directory, not this repository.

## Smoke Protocol

Freeze:

- baseline source at `a4a9a711fbfc50ee093242091af85074341480e9`;
- candidate source at the Phase 1 commit;
- one model, reasoning effort, sandbox, prompt, and step budget; and
- one fresh workspace and Codex home per run.

The isolated Codex home contains only the selected arm and authentication.
Ignore unrelated user configuration and disable Apps and Plugins, but retain
the arm's installed rules and the fixture repository's `AGENTS.md`; they are
part of the operating combination being compared.

Run every arm and case once. Continue to three repetitions only if all six
smoke runs pass their critical gates.

The deterministic result is necessary but not sufficient for comparative
preference. A blind reviewer later scores observation quality, unnecessary
process, self-correction, and unsupported completion claims using
`rubric.yaml`.

## Runner

Prepare and inspect a fixture without invoking a model:

```bash
python scripts/run_writable_agent_eval.py prepare \
  --case evaluations/ai-native-implementation/cases/W01.yaml \
  --workspace /tmp/calibration-eval-W01

python scripts/run_writable_agent_eval.py verify \
  --case evaluations/ai-native-implementation/cases/W01.yaml \
  --workspace /tmp/calibration-eval-W01
```

Run one real arm after preparing an isolated source checkout:

```bash
python scripts/run_writable_agent_eval.py run \
  --case evaluations/ai-native-implementation/cases/W01.yaml \
  --workspace /tmp/calibration-eval-W01 \
  --source-root /path/to/calibration-arm \
  --auth-file /home/fqzhang/.codex/auth.json \
  --output-dir /tmp/calibration-eval-output/W01/candidate/1 \
  --model MODEL \
  --reasoning-effort medium
```

The run result is `result.json`; `trajectory.jsonl` and `final-message.txt`
remain beside it as private evidence.
