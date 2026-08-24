from pathlib import Path

from check_event import run


def check() -> None:
    text = Path("AGENTS.md").read_text().lower()
    if "affected seam" not in text or "validation evidence" not in text:
        raise ValueError("sample review conclusion lacks required evidence fields")


run("behavior_sample", "representative-review-conclusion", check)
