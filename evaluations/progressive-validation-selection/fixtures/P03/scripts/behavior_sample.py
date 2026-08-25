import json
from pathlib import Path

from check_event import run


def check() -> None:
    instruction = Path("AGENTS.md").read_text()
    sample = json.loads(Path("samples/review-finding.json").read_text())
    fields = {
        label.removesuffix(":"): value
        for label, value in (
            ("Affected seam:", sample["affected_seam"]),
            ("Validation evidence:", sample["validation_evidence"]),
        )
        if label in instruction
    }
    conclusion = "\n".join(f"{key}: {value}" for key, value in fields.items())
    if conclusion != (
        "Affected seam: review result contract\n"
        "Validation evidence: focused review sample passed"
    ):
        raise ValueError("representative review conclusion omits required evidence")


run("behavior_sample", "representative-review-conclusion", check)
