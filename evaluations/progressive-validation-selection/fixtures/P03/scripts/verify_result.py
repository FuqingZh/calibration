from pathlib import Path


text = Path("AGENTS.md").read_text()
if "Affected seam:" not in text or "Validation evidence:" not in text:
    raise SystemExit("review instruction must define seam and evidence fields")
