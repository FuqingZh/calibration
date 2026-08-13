from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TEACH_ROOT = REPOSITORY_ROOT / "thirdparty/skills/teach"
EVALUATION_ROOT = REPOSITORY_ROOT / "evaluations/teach-adaptation"


def read_skill() -> str:
    return (TEACH_ROOT / "SKILL.md").read_text(encoding="utf-8")


def test_teach_is_installed_after_evaluation_acceptance() -> None:
    installer = (REPOSITORY_ROOT / "install.sh").read_text(encoding="utf-8")

    managed_block = installer.split("MANAGED_THIRDPARTY_SKILLS=(", 1)[1].split(")", 1)[
        0
    ]
    assert "teach" in managed_block.split()


def test_teach_keeps_writes_inside_an_explicit_learning_workspace() -> None:
    skill = read_skill()

    assert "Never infer that the current directory" in skill
    assert "In session-only mode, create or edit no files" in skill
    assert ".teach-workspace.yaml" in skill
    assert "not the skill source, current engineering Git root" in skill
    assert "Never promote these personal artifacts" in skill


def test_teach_requires_assessment_resume_and_current_sources() -> None:
    skill = read_skill()

    assert "small diagnostic question or task" in skill
    assert "Inspect the latest relevant\nrecords, lesson titles" in skill
    assert "Verify facts that may have changed" in skill
    assert "applicable version or date, and check date" in skill
    assert "automatically schedules or delivers spaced reviews" in skill


def test_teach_quiz_helper_randomizes_without_changing_identity() -> None:
    helper = TEACH_ROOT / "assets/quiz.js"
    source = helper.read_text(encoding="utf-8")

    assert "data-option-id" in source
    assert "Math.random" in source
    assert "module.exports" in source
    assert "DOMContentLoaded" in source

    node = shutil.which("node")
    if node is None:
        return

    result = subprocess.run(
        [
            node,
            "-e",
            "const q=require(process.argv[1]);"
            "const values=[0.2,0.8,0.1];let i=0;"
            "const shuffled=q.shuffle(['a','b','c','d'],()=>values[i++]);"
            "if (shuffled.join(',') !== 'b,d,c,a') process.exit(1);"
            "if (new Set(shuffled).size !== 4) process.exit(2);",
            str(helper),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_teach_behavior_cases_cover_the_acceptance_surface() -> None:
    cases = json.loads((TEACH_ROOT / "test-prompts.json").read_text(encoding="utf-8"))
    scenarios = {case["scenario"] for case in cases}

    assert scenarios == {
        "First lesson from an engineering repository",
        "Persistent personal learning workspace",
        "Resume prior learning",
        "Current technical state",
        "Quiz answer-position resistance",
        "Session-only teaching",
        "Explicit team documentation promotion",
        "No automatic spaced-review claim",
    }


def test_teach_metadata_remains_explicit_only() -> None:
    metadata = yaml.safe_load(
        (TEACH_ROOT / "agents/openai.yaml").read_text(encoding="utf-8")
    )

    assert metadata["policy"]["allow_implicit_invocation"] is False
    assert "$teach" in metadata["interface"]["default_prompt"]


def test_teach_evaluation_bundle_is_reconstructable() -> None:
    cases = json.loads((EVALUATION_ROOT / "cases.json").read_text(encoding="utf-8"))
    runs = json.loads((EVALUATION_ROOT / "runs.json").read_text(encoding="utf-8"))
    scorecard = json.loads(
        (EVALUATION_ROOT / "judge-scorecard.json").read_text(encoding="utf-8")
    )
    arm_map = json.loads((EVALUATION_ROOT / "arm-map.json").read_text(encoding="utf-8"))
    results = (EVALUATION_ROOT / "results.md").read_text(encoding="utf-8")
    responses = (EVALUATION_ROOT / "responses.txt").read_text(encoding="utf-8")

    comparative_ids = {case["id"] for case in cases["comparative_cases"]}
    safety_ids = {case["id"] for case in cases["candidate_safety_cases"]}
    assert comparative_ids == {"C01", "C02", "C03", "C04", "C05", "C06"}
    assert safety_ids == {"S01", "S02", "S03", "S04"}
    assert set(cases["fixtures"]) == {
        "retry",
        "quiz",
        "resume",
        "current",
        "promotion",
        "safety",
    }
    assert cases["conditions"]["comparative_runs"] == 12
    assert cases["conditions"]["candidate_safety_runs"] == 4
    assert cases["frozen_arms"]["candidate"]["commit"] == "6dd41c2"
    assert cases["frozen_arms"]["installed_candidate"]["commit"] == "e3152e5"
    for case_id in comparative_ids | safety_ids:
        assert f"### {case_id}:" in results
        assert f"=== {case_id} " in responses
    assert "## Arm Map" in results
    assert "## Blind Judgment Before Arm Reveal" in results

    by_run = {run["run_id"]: run for run in runs["runs"]}
    assert len(by_run) == 16
    assert set(by_run) == {
        f"{case_id}-{arm}"
        for case_id in comparative_ids
        for arm in ("baseline", "candidate")
    } | {f"{case_id}-candidate" for case_id in safety_ids}
    assert runs["capture"]["backend_session_ids"] == "not exposed by runner"
    assert runs["capture"]["attestation"].startswith("not externally")

    prompt_by_case = {
        case["id"]: case["prompt"]
        for group in ("comparative_cases", "candidate_safety_cases")
        for case in cases[group]
    }
    response_sections: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []
    for line in responses.splitlines(keepends=True):
        if line.startswith("=== ") and line.rstrip().endswith(" ==="):
            if current_key is not None:
                response_sections[current_key] = "".join(current_lines).rstrip() + "\n"
            _, case_id, arm, _ = line.rstrip().split()
            current_key = f"{case_id}-{arm}"
            current_lines = []
        elif current_key is not None:
            current_lines.append(line)
    assert current_key is not None
    response_sections[current_key] = "".join(current_lines).rstrip() + "\n"

    for run in by_run.values():
        prompt = prompt_by_case[run["case_id"]].encode()
        response = response_sections[run["run_id"]].encode()
        assert hashlib.sha256(prompt).hexdigest() == run["invocation"]["prompt_sha256"]
        assert hashlib.sha256(response).hexdigest() == run["response_sha256"]

        fixture = cases["fixtures"][run["fixture"]]
        expected_before = {
            relative: {
                "path": relative,
                "type": "file",
                "bytes": len(content.encode()),
                "sha256": hashlib.sha256(content.encode()).hexdigest(),
            }
            for relative, content in fixture.items()
        }
        actual_before = {entry["path"]: entry for entry in run["before"]["entries"]}
        assert actual_before == expected_before

        before_entries = {entry["path"]: entry for entry in run["before"]["entries"]}
        after_entries = {entry["path"]: entry for entry in run["after"]["entries"]}
        expected_changes: list[dict[str, str]] = []
        for relative in sorted(before_entries.keys() | after_entries.keys()):
            if relative not in before_entries:
                expected_changes.append({"path": relative, "change": "created"})
            elif relative not in after_entries:
                expected_changes.append({"path": relative, "change": "deleted"})
            elif before_entries[relative] != after_entries[relative]:
                expected_changes.append({"path": relative, "change": "modified"})
        assert run["changes"] == expected_changes

        before_directories = set(run["before"]["directories"])
        after_directories = set(run["after"]["directories"])
        assert run["directory_changes"] == {
            "created": sorted(after_directories - before_directories),
            "deleted": sorted(before_directories - after_directories),
        }

        changed_after: dict[str, Any] = {
            change["path"]: after_entries[change["path"]]
            for change in expected_changes
            if change["change"] != "deleted"
        }
        committed_by_source = {
            artifact["path"].removeprefix(f"artifacts/{run['run_id']}/"): artifact
            for artifact in run["committed_changed_artifacts"]
        }
        assert set(committed_by_source) == set(changed_after)

        for artifact in run["committed_changed_artifacts"]:
            artifact_path = EVALUATION_ROOT / artifact["path"]
            assert artifact_path.is_file()
            digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
            assert digest == artifact["sha256"]
            source_path = artifact["path"].removeprefix(f"artifacts/{run['run_id']}/")
            assert digest == changed_after[source_path]["sha256"]

    for run_id in ("S01-candidate", "S02-candidate", "S03-candidate"):
        run = by_run[run_id]
        assert run["changes"] == []
        assert run["directory_changes"] == {"created": [], "deleted": []}
        assert run["project_git"]["status_porcelain"] == []

    source = by_run["S02-candidate"]["selected_skill_source"]
    assert source["tree_before"] == source["tree_after"]
    assert source["status_porcelain_after"] == []
    assert {
        (change["path"], change["change"])
        for change in by_run["S04-candidate"]["changes"]
    } == {
        ("learning/.teach-workspace.yaml", "created"),
        ("learning/MISSION.md", "created"),
        ("learning/RESOURCES.md", "created"),
    }
    assert by_run["S04-candidate"]["project_git"]["status_porcelain"] == []

    packet = (EVALUATION_ROOT / "judge-packet.md").read_bytes()
    assert scorecard["recording_phase"] == "before_arm_reveal"
    assert hashlib.sha256(packet).hexdigest() == scorecard["packet_sha256"]
    assert {case["case_id"] for case in scorecard["cases"]} == comparative_ids
    reveal = {case["case_id"]: case for case in arm_map["cases"]}
    preferred_variants: list[str] = []
    for judgment in scorecard["cases"]:
        preferred = judgment["preferred"]
        if preferred == "tie":
            preferred_variants.append("tie")
        else:
            preferred_variants.append(str(reveal[judgment["case_id"]][preferred]))
    assert preferred_variants == [
        "candidate",
        "candidate",
        "candidate",
        "candidate",
        "candidate",
        "tie",
    ]


def test_teach_evaluation_checksum_inventory_is_current() -> None:
    inventory = EVALUATION_ROOT / "SHA256SUMS"
    entries: dict[str, str] = {}
    for line in inventory.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        entries[relative] = digest

    expected = {
        path.relative_to(EVALUATION_ROOT).as_posix()
        for path in EVALUATION_ROOT.rglob("*")
        if path.is_file() and path != inventory
    }
    assert set(entries) == expected
    for relative, digest in entries.items():
        content = (EVALUATION_ROOT / relative).read_bytes()
        assert hashlib.sha256(content).hexdigest() == digest
