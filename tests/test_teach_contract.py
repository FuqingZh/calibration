from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TEACH_ROOT = REPOSITORY_ROOT / "thirdparty/skills/teach"


def read_skill() -> str:
    return (TEACH_ROOT / "SKILL.md").read_text(encoding="utf-8")


def test_teach_is_not_installed_before_evaluation_acceptance() -> None:
    installer = (REPOSITORY_ROOT / "install.sh").read_text(encoding="utf-8")

    managed_block = installer.split("MANAGED_THIRDPARTY_SKILLS=(", 1)[1].split(")", 1)[
        0
    ]
    assert "teach" not in managed_block.split()


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
