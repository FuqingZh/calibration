from pathlib import Path

from check_event import run


def check() -> None:
    if not Path("content/release-channel.txt").read_text().strip():
        raise ValueError("release channel cannot be empty")


run("docs_only", "source-document-formatting", check)
