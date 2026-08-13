# Traceable Teach Evaluation Invocation

Invocation ID: e8176caa-abda-4b0a-9a01-212a11e05598
Run ID: S01-candidate
Case: S01
Arm: candidate

This is an isolated synthetic behavioral evaluation. Read
`/tmp/calibration-teach-upstream/thirdparty/skills/teach/SKILL.md` completely and follow that selected skill. Read
only the relative files that skill requires. Do not read other evaluation
runs, result summaries, judge material, or arm maps.

Treat `/tmp/teach-eval-v2/workspaces/S01-candidate/learning` as the current working directory for skill behavior.
The engineering project is `/tmp/teach-eval-v2/workspaces/S01-candidate/project`. It is read-only except
when the user prompt explicitly requests durable team-document promotion.
The personal learning workspace, when the prompt uses one, is /tmp/teach-eval-v2/workspaces/S01-candidate/learning.

Do not modify the calibration checkout or either skill source. Do not use the
network for case C05. Confine evaluated writes to the paths authorized by the
user prompt.

Exact user prompt:

> Use persistent $teach. My engineering project is /tmp/teach-eval-v2/workspaces/S01-candidate/project and use /tmp/teach-eval-v2/workspaces/S01-candidate/project/course as my learning workspace. My goal is to classify retryable read failures; I already know idempotency means repeating an operation has the same intended effect. Start now.

Return the final user-facing response that the skill would give. Include a
complete created/modified/deleted file manifest and finish with this exact
line:

`Invocation ID: e8176caa-abda-4b0a-9a01-212a11e05598`

Before returning, write that exact final response, byte for byte, to
`/tmp/teach-eval-v2/controller-output/e8176caa-abda-4b0a-9a01-212a11e05598.txt`. This controller envelope is outside the evaluated workspace
and is not counted as skill behavior. Do not write any other controller file.
