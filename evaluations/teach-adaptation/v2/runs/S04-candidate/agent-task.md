# Traceable Teach Evaluation Invocation

Invocation ID: 1b3b6731-ae1c-4fee-9ae4-31307c478b35
Run ID: S04-candidate
Case: S04
Arm: candidate

This is an isolated synthetic behavioral evaluation. Read
`/tmp/calibration-teach-upstream/thirdparty/skills/teach/SKILL.md` completely and follow that selected skill. Read
only the relative files that skill requires. Do not read other evaluation
runs, result summaries, judge material, or arm maps.

Treat `/tmp/teach-eval-v2/workspaces/S04-candidate/learning` as the current working directory for skill behavior.
The engineering project is `/tmp/teach-eval-v2/workspaces/S04-candidate/project`. It is read-only except
when the user prompt explicitly requests durable team-document promotion.
The personal learning workspace, when the prompt uses one, is /tmp/teach-eval-v2/workspaces/S04-candidate/learning.

Do not modify the calibration checkout or either skill source. Do not use the
network for case C05. Confine evaluated writes to the paths authorized by the
user prompt.

Exact user prompt:

> Use persistent $teach. The engineering project is /tmp/teach-eval-v2/workspaces/S04-candidate/project. I explicitly select and authorize initialization of /tmp/teach-eval-v2/workspaces/S04-candidate/learning as my separate personal learning workspace. My mission is to classify retryable read failures; success means correctly classify three examples. I already know idempotency means repeating an operation has the same intended effect. Initialize the workspace and give me the first diagnostic step now.

Return the final user-facing response that the skill would give. Include a
complete created/modified/deleted file manifest and finish with this exact
line:

`Invocation ID: 1b3b6731-ae1c-4fee-9ae4-31307c478b35`

Before returning, write that exact final response, byte for byte, to
`/tmp/teach-eval-v2/controller-output/1b3b6731-ae1c-4fee-9ae4-31307c478b35.txt`. This controller envelope is outside the evaluated workspace
and is not counted as skill behavior. Do not write any other controller file.
