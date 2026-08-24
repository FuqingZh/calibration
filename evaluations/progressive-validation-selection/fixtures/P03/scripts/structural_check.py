from pathlib import Path

from check_event import run


def check() -> None:
    text = Path("AGENTS.md").read_text()
    if "Review conclusions" not in text or "validation evidence" not in text:
        raise ValueError("review instruction must describe conclusion evidence")


run("structural_check", "review-instruction-structure", check)
