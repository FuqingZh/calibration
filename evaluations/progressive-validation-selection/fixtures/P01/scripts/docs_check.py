from pathlib import Path

from check_event import run


def check() -> None:
    readme = Path("README.md").read_text()
    if "release guide" not in readme or "docs/release-guide.md" not in readme:
        raise ValueError("README must describe and link to the release guide")
    if "reviewed release-notes process" not in readme:
        raise ValueError("README must explain the reviewed release-notes process")
    if not Path("docs/release-guide.md").is_file():
        raise ValueError("release guide is missing")


run("docs_check", "readme-wording-and-local-link", check)
