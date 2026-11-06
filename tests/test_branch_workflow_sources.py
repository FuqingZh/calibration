from __future__ import annotations

from tests.support import REPOSITORY_ROOT

REFERENCE = "docs/workflow/branch_and_pr_collaboration/20260602-v1.0.md"


def test_branch_workflow_routes_to_official_sources_at_existing_path() -> None:
    root = REPOSITORY_ROOT / "skills/calibration/references"
    guide = (root / REFERENCE).read_text(encoding="utf-8")
    index = (root / "docs_index.md").read_text(encoding="utf-8")

    assert REFERENCE in index
    assert "Official GitHub sources" in index
    for source in (
        "https://docs.github.com/en/get-started/using-github/github-flow",
        "https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/"
        "managing-protected-branches/about-protected-branches",
        "https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/"
        "configuring-pull-request-merges/managing-a-merge-queue",
    ):
        assert f"]({source})" in guide

    assert "## Branch Naming" not in guide
    assert "## Type and Verification" not in guide
    assert "`main` is protected." not in guide


def test_branch_sources_preserve_local_authority_and_delivery_boundaries() -> None:
    guide = " ".join(
        (REPOSITORY_ROOT / "skills/calibration/references" / REFERENCE)
        .read_text(encoding="utf-8")
        .split()
    )
    for boundary in (
        "For GitHub-hosted repositories",
        "subject to the repository's own contribution and release contracts",
        "Verify the repository's actual rulesets, branch protection, "
        "and merge settings",
        "does not establish that protection is enabled",
        "Repository-owned rules define release branches, multi-version maintenance",
        "For other hosting platforms, use their official workflow documentation",
        "do not grant operation authority",
        "../../../discipline/harness.md#repository-delivery-feedback-loop",
        "../../../discipline/verification.md",
    ):
        assert boundary in guide
