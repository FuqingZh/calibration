from pathlib import Path

from check_event import run


def check() -> None:
    channel = Path("content/release-channel.txt").read_text().strip()
    expected = f"# Release channel\\n\\nCurrent channel: {channel}\\n"
    if Path("docs/generated-release.md").read_text() != expected:
        raise ValueError("generated document does not match its source")


run("artifact_readback", "committed-generated-artifact", check)
