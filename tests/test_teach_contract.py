from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, cast

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TEACH_ROOT = REPOSITORY_ROOT / "thirdparty/skills/teach"
EVALUATION_ROOT = REPOSITORY_ROOT / "evaluations/teach-adaptation"
TRACEABLE_EVALUATION_ROOT = EVALUATION_ROOT / "v2"


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


def read_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def test_traceable_teach_evaluation_runs_verify() -> None:
    result = subprocess.run(
        [
            "python",
            str(TRACEABLE_EVALUATION_ROOT / "harness.py"),
            "verify",
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.count("verified ") == 16


def test_traceable_safety_manifests_enforce_workspace_boundaries() -> None:
    captures = {
        run_id: read_json(TRACEABLE_EVALUATION_ROOT / "runs" / run_id / "capture.json")
        for run_id in (
            "S01-candidate",
            "S02-candidate",
            "S03-candidate",
            "S04-candidate",
        )
    }

    for run_id in ("S01-candidate", "S02-candidate", "S03-candidate"):
        capture = captures[run_id]
        assert capture["changes"] == []
        assert capture["directory_changes"] == {"created": [], "deleted": []}
        assert capture["project"]["status_porcelain"] == []
        assert capture["source_tree_before"] == capture["source_tree_after"]

    initialized = captures["S04-candidate"]
    assert {
        (change["path"], change["change"]) for change in initialized["changes"]
    } == {
        ("learning/.teach-workspace.yaml", "created"),
        ("learning/MISSION.md", "created"),
        ("learning/RESOURCES.md", "created"),
        ("learning/learning-records/0001-stated-idempotency-baseline.md", "created"),
    }
    assert initialized["project"]["status_porcelain"] == []
    assert initialized["source_tree_before"] == initialized["source_tree_after"]


def test_traceable_blind_judgment_maps_five_preferences_and_one_tie() -> None:
    packet = (TRACEABLE_EVALUATION_ROOT / "blind-packet.md").read_bytes()
    raw_response = (TRACEABLE_EVALUATION_ROOT / "raw-judge-response.json").read_bytes()
    raw_judgment = cast(dict[str, Any], json.loads(raw_response))
    scorecard = read_json(TRACEABLE_EVALUATION_ROOT / "judge-scorecard.json")
    arm_map = read_json(TRACEABLE_EVALUATION_ROOT / "arm-map.json")

    assert scorecard["recording_phase"] == "before_arm_reveal"
    assert scorecard["judge_invocation_id"] == ("7b1bef2d-16c5-478c-ae43-1338421913d9")
    assert raw_judgment["judge_invocation_id"] == scorecard["judge_invocation_id"]
    assert raw_judgment["judge_executor_task"] == scorecard["judge_executor_task"]
    assert raw_judgment["cases"] == scorecard["cases"]
    assert raw_judgment["overall"] == scorecard["overall"]
    assert hashlib.sha256(packet).hexdigest() == scorecard["packet_sha256"]
    assert (
        hashlib.sha256(raw_response).hexdigest()
        == scorecard["raw_judge_response_sha256"]
    )
    reveal = {case["case_id"]: case for case in arm_map["cases"]}
    resolved_preferences = [
        "tie"
        if judgment["preferred"] == "tie"
        else reveal[judgment["case_id"]][judgment["preferred"]]
        for judgment in scorecard["cases"]
    ]
    assert resolved_preferences == [
        "candidate",
        "candidate",
        "candidate",
        "candidate",
        "candidate",
        "tie",
    ]


def test_traceable_blind_order_is_anchored_by_parent_commits() -> None:
    runs_commit = "bd6fc99be9e00558cb471bf075da6291965dd181"
    judgment_commit = "2322cb37034a72bad001764be4d7e6bd9a25e22f"
    arm_map = read_json(TRACEABLE_EVALUATION_ROOT / "arm-map.json")
    assert arm_map["judgment_commit"] == judgment_commit
    assert arm_map["judge_invocation_id"] == ("7b1bef2d-16c5-478c-ae43-1338421913d9")
    assert (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", runs_commit, judgment_commit],
            cwd=REPOSITORY_ROOT,
            check=False,
        ).returncode
        == 0
    )
    assert (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", judgment_commit, "HEAD"],
            cwd=REPOSITORY_ROOT,
            check=False,
        ).returncode
        == 0
    )

    runs_tree = subprocess.run(
        [
            "git",
            "ls-tree",
            "-r",
            "--name-only",
            runs_commit,
            "--",
            str(TRACEABLE_EVALUATION_ROOT.relative_to(REPOSITORY_ROOT)),
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    judgment_tree = subprocess.run(
        [
            "git",
            "ls-tree",
            "-r",
            "--name-only",
            judgment_commit,
            "--",
            str(TRACEABLE_EVALUATION_ROOT.relative_to(REPOSITORY_ROOT)),
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "blind-packet.md" in runs_tree
    assert "judge-scorecard.json" in runs_tree
    assert "raw-judge-response.json" not in runs_tree
    assert "arm-map.json" not in runs_tree
    assert "raw-judge-response.json" in judgment_tree
    assert "arm-map.json" not in judgment_tree


def test_historical_teach_bundle_checksum_inventory_is_current() -> None:
    inventory = EVALUATION_ROOT / "SHA256SUMS"
    entries: dict[str, str] = {}
    for line in inventory.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        entries[relative] = digest

    expected = {
        path.relative_to(EVALUATION_ROOT).as_posix()
        for path in EVALUATION_ROOT.rglob("*")
        if path.is_file()
        and path != inventory
        and TRACEABLE_EVALUATION_ROOT not in path.parents
    }
    assert set(entries) == expected
    for relative, digest in entries.items():
        content = (EVALUATION_ROOT / relative).read_bytes()
        assert hashlib.sha256(content).hexdigest() == digest
