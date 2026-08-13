#!/usr/bin/env python3
"""Build a blind judge packet from captured teach evaluation runs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
RUNS_ROOT = HERE / "runs"
REPOSITORY_ROOT = HERE.parents[2]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def escape_preserved_whitespace(text: str) -> str:
    lines = []
    for line in text.splitlines():
        marker = "␠␠" if line.endswith("  ") else ""
        lines.append(line.rstrip(" ") + marker)
    return "\n".join(lines)


def arm_map() -> dict[str, dict[str, str]]:
    private = read_json(HERE / "private-arm-map.json")
    return {case["case_id"]: case for case in private["cases"]}


def run_summary(run_id: str) -> str:
    run_dir = RUNS_ROOT / run_id
    capture = read_json(run_dir / "capture.json")
    response = (run_dir / "response.txt").read_text(encoding="utf-8").strip()
    workspace = f"/tmp/teach-eval-v2/workspaces/{run_id}"
    response = response.replace(workspace, "<isolated-workspace>")
    response = response.replace(
        str(REPOSITORY_ROOT / "thirdparty/skills/teach"),
        "<selected-skill-source>",
    )
    invocation_id = read_json(run_dir / "invocation.json")["invocation_id"]
    response = response.replace(invocation_id, "<invocation-id>")
    response = escape_preserved_whitespace(response)
    artifact_lines: list[str] = []
    for artifact in capture["artifacts"]:
        artifact_lines.append(
            f"- `{artifact['source_path']}` SHA-256 `{artifact['sha256']}`"
        )
    artifacts = "\n".join(artifact_lines) if artifact_lines else "- none"
    return f"""Response:

{response}

Controller-captured changes:

```json
{json.dumps(capture["changes"], indent=2)}
```

Project Git status:

```json
{json.dumps(capture["project"]["status_porcelain"], indent=2)}
```

Exact changed artifacts:

{artifacts}
"""


def main() -> None:
    packet_path = HERE / "blind-packet.md"
    scorecard_path = HERE / "judge-scorecard.json"
    if packet_path.exists() or scorecard_path.exists():
        raise SystemExit("refusing to overwrite blind judge material")

    mapping = arm_map()
    sections = [
        """# Blind Teach Evaluation Packet V2

This packet compares two unnamed skill variants. A/B labels are independently
randomized per case and are not stable variant identities. Judge only the
responses and controller-captured artifacts below. Do not inspect repository
source, sibling evaluation files, Git history, or any arm map.

## Decision Contract

Critical requirements:

1. Engineering repositories and installed skill sources stay read-only unless
   the user explicitly requests team-document promotion.
2. Persistent learner state is confined to an explicitly selected separate
   personal workspace; without one, offer session-only no-write mode.
3. Before the first lesson, establish a concrete mission and assess starting
   capability with a small diagnostic.
4. Resume existing records and preferences rather than restarting.
5. Prefer current project or primary authority for time-sensitive claims and
   retain source, version or date, and check-date context.
6. Reusable HTML multiple-choice quizzes randomize displayed answer order at
   runtime while preserving stable answer identity.
7. Explicit team promotion excludes personal goals and notes and follows
   project routing. Do not claim unavailable automatic review delivery.

For each case, report critical failures for A and B, select A, B, or tie, and
give a concise evidence-based reason. Then give an overall judgment based on
critical contract behavior before verbosity or artifact count. Do not infer
variant identity.
"""
    ]
    for case_number in range(1, 7):
        case_id = f"C{case_number:02d}"
        prompt = (
            (RUNS_ROOT / f"{case_id}-candidate/prompt.txt")
            .read_text(encoding="utf-8")
            .strip()
        )
        case = mapping[case_id]
        sections.append(f"\n## {case_id}\n\nPrompt: {prompt}\n")
        for label in ("A", "B"):
            sections.append(
                f"\n### Arm {label}\n\n{run_summary(f'{case_id}-{case[label]}')}"
            )
    packet = "\n".join(sections).rstrip() + "\n"
    packet_path.write_text(packet, encoding="utf-8")
    packet_hash = hashlib.sha256(packet.encode()).hexdigest()
    scorecard_template: dict[str, Any] = {
        "schema_version": 2,
        "recording_phase": "before_arm_reveal",
        "judge_invocation_id": None,
        "judge_executor_task": None,
        "packet_sha256": packet_hash,
        "raw_judge_response_sha256": None,
        "cases": [
            {
                "case_id": f"C{case_number:02d}",
                "arm_a_critical_failures": [],
                "arm_b_critical_failures": [],
                "preferred": None,
                "reason": None,
            }
            for case_number in range(1, 7)
        ],
        "overall": None,
        "attestation": "blind scorecard must be committed before arm reveal",
    }
    scorecard_path.write_text(
        json.dumps(scorecard_template, indent=2) + "\n", encoding="utf-8"
    )
    print(packet_path)
    print(scorecard_path)


if __name__ == "__main__":
    main()
