from pathlib import Path

from check_event import run


def check() -> None:
    text = Path("AGENTS.md").read_text()
    if "Review conclusions" not in text:
        raise ValueError("review instruction must describe conclusions")
    if "Affected seam:" not in text or "Validation evidence:" not in text:
        raise ValueError("review instruction must define the conclusion fields")


run("structural_check", "review-instruction-structure", check)
