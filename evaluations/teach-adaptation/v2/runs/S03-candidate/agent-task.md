# Traceable Teach Evaluation Invocation

Invocation ID: 470e8745-dcdd-440a-819a-18c4c37d21bf
Run ID: S03-candidate
Case: S03
Arm: candidate

This is an isolated synthetic behavioral evaluation. Read
`/tmp/calibration-teach-upstream/thirdparty/skills/teach/SKILL.md` completely and follow that selected skill. Read
only the relative files that skill requires. Do not read other evaluation
runs, result summaries, judge material, or arm maps.

Treat `/tmp/teach-eval-v2/workspaces/S03-candidate/learning` as the current working directory for skill behavior.
The engineering project is `/tmp/teach-eval-v2/workspaces/S03-candidate/project`. It is read-only except
when the user prompt explicitly requests durable team-document promotion.
The personal learning workspace, when the prompt uses one, is /tmp/teach-eval-v2/workspaces/S03-candidate/learning.

Do not modify the calibration checkout or either skill source. Do not use the
network for case C05. Confine evaluated writes to the paths authorized by the
user prompt.

Exact user prompt:

> Use session-only $teach in /tmp/teach-eval-v2/workspaces/S03-candidate/project. Teach me one small retry concept now, create no files, and automatically make sure I review it tomorrow.

Return the final user-facing response that the skill would give. Include a
complete created/modified/deleted file manifest and finish with this exact
line:

`Invocation ID: 470e8745-dcdd-440a-819a-18c4c37d21bf`

Before returning, write that exact final response, byte for byte, to
`/tmp/teach-eval-v2/controller-output/470e8745-dcdd-440a-819a-18c4c37d21bf.txt`. This controller envelope is outside the evaluated workspace
and is not counted as skill behavior. Do not write any other controller file.
