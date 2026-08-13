# Traceable Teach Evaluation Invocation

Invocation ID: d85a62c5-c81e-483f-98b9-10c3f890f582
Run ID: C02-baseline
Case: C02
Arm: baseline

This is an isolated synthetic behavioral evaluation. Read
`/tmp/mattpocock-skills-v1.2.3/skills/productivity/teach/SKILL.md` completely and follow that selected skill. Read
only the relative files that skill requires. Do not read other evaluation
runs, result summaries, judge material, or arm maps.

Treat `/tmp/teach-eval-v2/workspaces/C02-baseline/project` as the current working directory for skill behavior.
The engineering project is `/tmp/teach-eval-v2/workspaces/C02-baseline/project`. It is read-only except
when the user prompt explicitly requests durable team-document promotion.
No personal learning workspace has been selected or created.

Do not modify the calibration checkout or either skill source. Do not use the
network for case C05. Confine evaluated writes to the paths authorized by the
user prompt.

Exact user prompt:

> Please start teaching me how this repository decides when a failed read is safe to retry. I have no course directory yet and have not told you my experience.

Return the final user-facing response that the skill would give. Include a
complete created/modified/deleted file manifest and finish with this exact
line:

`Invocation ID: d85a62c5-c81e-483f-98b9-10c3f890f582`

Before returning, write that exact final response, byte for byte, to
`/tmp/teach-eval-v2/controller-output/d85a62c5-c81e-483f-98b9-10c3f890f582.txt`. This controller envelope is outside the evaluated workspace
and is not counted as skill behavior. Do not write any other controller file.
