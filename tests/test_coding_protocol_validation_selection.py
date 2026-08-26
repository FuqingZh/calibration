from __future__ import annotations

import json
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = REPOSITORY_ROOT / "thirdparty/skills/coding-protocol/SKILL.md"
REFERENCE_PATH = (
    REPOSITORY_ROOT
    / "thirdparty/skills/coding-protocol/references/validation-selection.md"
)
PROMPTS_PATH = REPOSITORY_ROOT / "thirdparty/skills/coding-protocol/test-prompts.json"


def test_conditional_load_and_reference_free_exit() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "For a nontrivial or audited selection" in text
    assert "competing focused and broad checks" in text
    assert "stale\nor indirect evidence" in text
    assert "failure pressure to widen" in text
    exit_section = text.split("- **Exit**", 1)[1].split("## Composition", 1)[0]
    assert "references" in exit_section
    assert "validation-selection.md" not in exit_section
    assert "Load no reference on Exit." in text


def test_reference_has_one_hop_structure_and_no_command_matrix() -> None:
    skill_text = SKILL_PATH.read_text(encoding="utf-8")
    reference_text = REFERENCE_PATH.read_text(encoding="utf-8")
    assert "`references/validation-selection.md`" in skill_text
    assert "references/" not in reference_text
    assert "`references/" not in reference_text
    assert "npm " not in reference_text
    assert "pnpm " not in reference_text
    assert "yarn " not in reference_text
    assert "TypeScript" in reference_text
    assert len(SKILL_PATH.read_text(encoding="utf-8").splitlines()) < 500


def test_reference_requires_a_bounded_evidence_decision() -> None:
    text = " ".join(REFERENCE_PATH.read_text(encoding="utf-8").split())
    for phrase in (
        "exact claim",
        "affected seam",
        "proof obligation",
        "fresh direct",
        "fresh partial",
        "stale",
        "indirect",
        "missing",
        "smallest falsifiable",
        "why any smaller set",
        "why a broader set",
        "diagnose its cause before widening",
        "verified_ready",
        "conditionally_ready",
        "not_yet_verified",
    ):
        assert phrase in text


def test_static_prompts_cover_selection_boundaries() -> None:
    cases = json.loads(PROMPTS_PATH.read_text(encoding="utf-8"))
    assert {case["id"] for case in cases} == {
        "exit-no-reference",
        "focused-leaf-selection",
        "mandatory-local-broadening",
        "failure-diagnosis-no-mechanical-widening",
    }
    assert all(
        case["scenario"] and case["prompt"] and case["expected"] for case in cases
    )


def test_protocol_is_implicitly_active_and_trail_structure_is_independent() -> None:
    metadata = (
        REPOSITORY_ROOT / "thirdparty/skills/coding-protocol/agents/openai.yaml"
    ).read_text(encoding="utf-8")
    assert "allow_implicit_invocation: true" in metadata
    assert "Select honest repository evidence proportionally" in metadata
    assert "only when explicitly requested" not in metadata
    reference_text = REFERENCE_PATH.read_text(encoding="utf-8")
    assert "Trail of Bits" not in reference_text
    assert "CC-BY-SA" not in reference_text
