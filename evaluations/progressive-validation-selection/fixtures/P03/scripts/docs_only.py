from pathlib import Path

from check_event import run


def check() -> None:
    if not Path("AGENTS.md").read_text().startswith("# Repository Instructions"):
        raise ValueError("instruction heading is missing")


run("docs_only", "markdown-formatting", check)
