from __future__ import annotations

import json
from pathlib import Path

from tests.test_install import REPOSITORY_ROOT, run_installer


def read(path: str) -> str:
    return (REPOSITORY_ROOT / path).read_text(encoding="utf-8")


def compact(path: str) -> str:
    return " ".join(read(path).split())


def test_harness_defines_bounded_review_convergence_routing() -> None:
    harness = compact("references/engineering/discipline/harness.md")

    for phrase in (
        "same-scope mechanical feedback",
        "existing bounded owner loop",
        "exact-current-head review expands beyond the pull request's declared contract",
        "configured retry budget is exhausted",
        "pause remote review",
        "preserve branch, head, worktree, owner, and feedback state",
        "one pull request, independent pull requests, or a dependent stack",
        "platform-native stacking only for genuinely dependent slices",
        "otherwise use ordinary dependent pull requests",
    ):
        assert phrase in harness

    assert "https://dora.dev/capabilities/working-in-small-batches/" in harness
    assert (
        "https://google.github.io/eng-practices/review/developer/small-cls.html"
        in harness
    )
    assert "universal LOC, file-count, or review-round thresholds" in harness


def test_calibration_prompts_cover_both_review_convergence_branches() -> None:
    prompts = json.loads(read("skills/calibration/test-prompts.json"))
    cases = {case["id"]: case for case in prompts}

    same_scope = " ".join(cases[20]["expected"].split())
    assert "继续处理 same-scope mechanical feedback" in same_scope
    assert "不应无谓拆分或重新 calibration" in same_scope

    reroute = " ".join(cases[21]["expected"].split())
    for phrase in (
        "停止 remote review",
        "preserve branch、head、worktree、owner 和 feedback state",
        "invoke calibration",
        "one PR",
        "independent PRs",
        "dependent stack",
        "不得发明 scheduler、review tool",
    ):
        assert phrase in reroute


def test_installer_propagates_global_review_tripwire(tmp_path: Path) -> None:
    expected = (
        "Continue same-scope mechanical review feedback through the existing "
        "bounded owner loop."
    )
    template = compact("codex/AGENTS.md.template")
    assert expected in template
    assert "Invoke calibration when exact-current-head review expands" in template

    for profile in ("standard", "ao-worker"):
        codex_home = tmp_path / profile
        arguments = ["--profile", profile]
        if profile == "ao-worker":
            arguments.extend(["--codex-home", str(codex_home)])
        result = run_installer(codex_home, *arguments)
        assert result.returncode == 0, result.stderr
        installed = " ".join(
            (codex_home / "AGENTS.md").read_text(encoding="utf-8").split()
        )
        assert expected in installed
        assert "configured retry budget is exhausted" in installed
