# Traceable Teach Evaluation Invocation

Invocation ID: 311c506a-5fb2-4992-858e-4baa8a42ddce
Run ID: C01-candidate
Case: C01
Arm: candidate

This is an isolated synthetic behavioral evaluation. Read
`/tmp/calibration-teach-upstream/thirdparty/skills/teach/SKILL.md` completely and follow that selected skill. Read
only the relative files that skill requires. Do not read other evaluation
runs, result summaries, judge material, or arm maps.

Treat `/tmp/teach-eval-v2/workspaces/C01-candidate/project` as the current working directory for skill behavior.
The engineering project is `/tmp/teach-eval-v2/workspaces/C01-candidate/project`. It is read-only except
when the user prompt explicitly requests durable team-document promotion.
No personal learning workspace has been selected or created.

Do not modify the calibration checkout or either skill source. Do not use the
network for case C05. Confine evaluated writes to the paths authorized by the
user prompt.

Exact user prompt:

> Teach me the retry model in this repository. I have not created a learning workspace and have not stated what I already know.

Return the final user-facing response that the skill would give. Include a
complete created/modified/deleted file manifest and finish with this exact
line:

`Invocation ID: 311c506a-5fb2-4992-858e-4baa8a42ddce`

Before returning, write that exact final response, byte for byte, to
`/tmp/teach-eval-v2/controller-output/311c506a-5fb2-4992-858e-4baa8a42ddce.txt`. This controller envelope is outside the evaluated workspace
and is not counted as skill behavior. Do not write any other controller file.
