from __future__ import annotations

import pytest

from tests.support import REPOSITORY_ROOT

REFERENCES = REPOSITORY_ROOT / "skills/calibration/references"
BRANCH_GUIDE = "docs/workflow/branch_and_pr_collaboration/20260602-v1.0.md"
GITHUB_BRANCHES = (
    "https://docs.github.com/en/repositories/"
    "configuring-branches-and-merges-in-your-repository/"
)


@pytest.mark.parametrize(
    ("path", "sources"),
    [
        (
            "naming/README.md",
            (
                "https://peps.python.org/pep-0008/#naming-conventions",
                "https://rust-lang.github.io/api-guidelines/naming.html",
                "https://style.tidyverse.org/syntax.html#object-names",
            ),
        ),
        (
            "naming/version.md",
            (
                "https://semver.org/spec/v2.0.0.html",
                "https://packaging.python.org/en/latest/discussions/versioning/",
                "https://packaging.python.org/en/latest/discussions/single-source-version/",
            ),
        ),
        (
            BRANCH_GUIDE,
            (
                "https://docs.github.com/en/get-started/using-github/github-flow",
                GITHUB_BRANCHES
                + "managing-protected-branches/about-protected-branches",
                GITHUB_BRANCHES
                + "configuring-pull-request-merges/managing-a-merge-queue",
            ),
        ),
    ],
)
def test_adopted_upstream_sources_remain_linked(
    path: str, sources: tuple[str, ...]
) -> None:
    text = (REFERENCES / path).read_text(encoding="utf-8")
    for source in sources:
        assert f"]({source})" in text


def test_legacy_naming_paths_reach_current_sources() -> None:
    for name in ("function", "method", "type", "variable", "loop"):
        text = (REFERENCES / f"naming/{name}.md").read_text(encoding="utf-8")
        assert "](README.md)" in text
    branch = (REFERENCES / "naming/branch.md").read_text(encoding="utf-8")
    assert f"](../{BRANCH_GUIDE})" in branch
    index = (REFERENCES / "docs_index.md").read_text(encoding="utf-8")
    assert f"`{BRANCH_GUIDE}`" in index
