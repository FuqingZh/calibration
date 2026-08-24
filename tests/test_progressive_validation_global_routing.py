from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _compact(relative_path: str) -> str:
    return " ".join(
        (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8").split()
    )


def test_global_fallback_selects_validation_from_claim_and_affected_seam() -> None:
    template = _compact("codex/AGENTS.md.template")

    assert "completion claim and affected seam" in template
    assert (
        "smallest relevant checks using a repository-owned validation entrypoint"
        in template
    )
    assert "repository-local policy explicitly requires it" in template
    assert "narrower evidence leaves an obligation uncovered" in template
    assert "unchecked boundary" in template
    assert "complete canonical gate when the change can affect runtime" not in template


def test_shared_principle_keeps_broadening_bounded_and_reported() -> None:
    principles = _compact("references/engineering/principles.md")

    assert "completion claim and affected seam" in principles
    assert "smallest repository-owned check that can falsify the claim" in principles
    assert "explicit repository-local mandate or an uncovered obligation" in principles
    assert "unchecked boundaries and residual risk" in principles


def test_calibration_excludes_ordinary_prose_but_keeps_contract_documentation() -> None:
    skill = _compact("skills/calibration/SKILL.md").lower()

    assert "repository prose" in skill
    assert "cross-boundary contract documentation" in skill
    assert "durable engineering documentation" not in skill
