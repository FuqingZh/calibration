from pathlib import Path


readme = Path("README.md").read_text()
if "release guide" not in readme or "docs/release-guide.md" not in readme:
    raise SystemExit("README wording or local guide link is incomplete")
if "reviewed release-notes process" not in readme:
    raise SystemExit("README does not explain the reviewed release-notes process")
