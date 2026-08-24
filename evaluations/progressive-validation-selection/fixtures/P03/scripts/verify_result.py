from pathlib import Path


text = Path("AGENTS.md").read_text().lower()
if "affected seam" not in text or "validation evidence" not in text:
    raise SystemExit("review instruction must require seam and evidence")
