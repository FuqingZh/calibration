# Traceable Teach Evaluation Invocation

Invocation ID: 6abeda57-542d-43f4-92d8-87b0e2278d64
Run ID: C01-baseline
Case: C01
Arm: baseline

This is an isolated synthetic behavioral evaluation. Read
`/tmp/mattpocock-skills-v1.2.3/skills/productivity/teach/SKILL.md` completely and follow that selected skill. Read
only the relative files that skill requires. Do not read other evaluation
runs, result summaries, judge material, or arm maps.

Treat `/tmp/teach-eval-v2/workspaces/C01-baseline/project` as the current working directory for skill behavior.
The engineering project is `/tmp/teach-eval-v2/workspaces/C01-baseline/project`. It is read-only except
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

`Invocation ID: 6abeda57-542d-43f4-92d8-87b0e2278d64`

Before returning, write that exact final response, byte for byte, to
`/tmp/teach-eval-v2/controller-output/6abeda57-542d-43f4-92d8-87b0e2278d64.txt`. This controller envelope is outside the evaluated workspace
and is not counted as skill behavior. Do not write any other controller file.
