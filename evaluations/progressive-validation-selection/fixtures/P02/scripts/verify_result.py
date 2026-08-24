from pathlib import Path


channel = Path("content/release-channel.txt").read_text().strip()
artifact = Path("docs/generated-release.md").read_text()
if channel != "stable" or artifact != "# Release channel\\n\\nCurrent channel: stable\\n":
    raise SystemExit("source and generated release artifact must both describe stable")
