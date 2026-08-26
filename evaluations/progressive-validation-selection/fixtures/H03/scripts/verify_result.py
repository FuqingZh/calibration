from pathlib import Path


if Path("generated/release-summary.txt").read_text() != "release-status: published\n":
    raise SystemExit("generated summary is not the expected final artifact")
