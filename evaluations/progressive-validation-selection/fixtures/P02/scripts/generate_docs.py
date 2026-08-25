from pathlib import Path

from check_event import run


def generate() -> None:
    channel = Path("content/release-channel.txt").read_text().strip()
    Path("docs/generated-release.md").write_text(
        f"# Release channel\n\nCurrent channel: {channel}\n"
    )


run("generator", "generated-release-document", generate)
