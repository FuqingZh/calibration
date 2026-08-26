from pathlib import Path


Path("generated").mkdir(exist_ok=True)
Path("generated/release-summary.txt").write_text("release-status: pending\n")
