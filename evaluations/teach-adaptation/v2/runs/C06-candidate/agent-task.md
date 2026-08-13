# Traceable Teach Evaluation Invocation

Invocation ID: 58933dad-ed47-47c0-af39-a0f0a01f05da
Run ID: C06-candidate
Case: C06
Arm: candidate

This is an isolated synthetic behavioral evaluation. Read
`/tmp/calibration-teach-upstream/thirdparty/skills/teach/SKILL.md` completely and follow that selected skill. Read
only the relative files that skill requires. Do not read other evaluation
runs, result summaries, judge material, or arm maps.

Treat `/tmp/teach-eval-v2/workspaces/C06-candidate/learning` as the current working directory for skill behavior.
The engineering project is `/tmp/teach-eval-v2/workspaces/C06-candidate/project`. It is read-only except
when the user prompt explicitly requests durable team-document promotion.
The personal learning workspace, when the prompt uses one, is /tmp/teach-eval-v2/workspaces/C06-candidate/learning.

Do not modify the calibration checkout or either skill source. Do not use the
network for case C05. Confine evaluated writes to the paths authorized by the
user prompt.

Exact user prompt:

> We finished a personal lesson about a verified vendor parser quirk. Now explicitly turn only the reusable result into durable team documentation.

Return the final user-facing response that the skill would give. Include a
complete created/modified/deleted file manifest and finish with this exact
line:

`Invocation ID: 58933dad-ed47-47c0-af39-a0f0a01f05da`

Before returning, write that exact final response, byte for byte, to
`/tmp/teach-eval-v2/controller-output/58933dad-ed47-47c0-af39-a0f0a01f05da.txt`. This controller envelope is outside the evaluated workspace
and is not counted as skill behavior. Do not write any other controller file.
