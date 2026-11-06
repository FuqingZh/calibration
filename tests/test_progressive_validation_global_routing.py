from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _compact(relative_path: str) -> str:
    return " ".join(
        (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8").split()
    )


def test_global_fallback_keeps_bounded_validation_and_routes_details() -> None:
    template = _compact("codex/AGENTS.md.template")

    assert "select validation proportionally" in template
    assert "smallest relevant checks at a repository-owned validation entrypoint" in (
        template
    )
    assert "Broaden for required repository policy or uncovered obligations" in template
    assert "Report evidence, unchecked boundaries, and residual risk" in template
    assert "verification reference for completion details" in template
    assert "complete canonical gate when the change can affect runtime" not in template


def test_shared_principle_routes_to_complete_verification_contract() -> None:
    principles = _compact("skills/calibration/references/principles.md")
    verification = _compact("skills/calibration/references/discipline/verification.md")

    assert "[verification discipline](discipline/verification.md)" in principles
    assert "completion claim and affected seam" in verification
    assert "repository-owned validation entrypoint that can falsify the claim" in (
        verification
    )
    assert "repository-local policy explicitly requires it" in verification
    assert "evidence leaves an obligation uncovered" in verification
    assert "For checks not run, state the exact command or evidence path" in (
        verification
    )
    assert "why it was skipped, and the remaining risk" in verification


def test_calibration_excludes_ordinary_prose_but_keeps_contract_documentation() -> None:
    skill = _compact("skills/calibration/SKILL.md").lower()

    assert "repository prose" in skill
    assert "cross-boundary contract documentation" in skill
    assert "durable engineering documentation" not in skill
