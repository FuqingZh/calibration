import json
import re
from pathlib import Path

from check_event import run


def check() -> None:
    instruction = Path("AGENTS.md").read_text()
    sample = json.loads(Path("samples/review-finding.json").read_text())
    rule = re.search(
        r"Review conclusions must render `Affected seam: <affected_seam>` followed "
        r"by `Validation evidence: <validation_evidence>`\.",
        instruction,
    )
    if rule is None:
        raise ValueError("review instruction lacks an applicable conclusion rule")
    conclusion = (
        f"Affected seam: {sample['affected_seam']}\n"
        f"Validation evidence: {sample['validation_evidence']}"
    )
    if conclusion != (
        "Affected seam: review result contract\n"
        "Validation evidence: focused review sample passed"
    ):
        raise ValueError("representative review conclusion omits required evidence")


run("behavior_sample", "representative-review-conclusion", check)
