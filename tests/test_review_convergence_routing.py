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
        "current explicitly declared and authorized pull request contract",
        "existing bounded owner loop",
        "exact-current-head review proposes work beyond that contract",
        "pause remote review",
        "preserve branch, head, worktree, owner, and feedback state",
        "reject or escalate the feedback",
        "accept an authorized contract expansion",
        "distinct configured review-convergence budget is exhausted",
        "one pull request, independent pull requests, or a dependent stack",
        "Independent slices remain independent pull requests",
        "For genuinely dependent slices, use platform-native stacking",
        "otherwise use ordinary dependent pull requests",
        "transport, polling, or idempotent-operation retry budget",
        "preserve-and-report path and is not a topology signal",
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
    assert "当前明确声明且已授权契约内的 same-scope mechanical feedback" in same_scope
    assert "不应无谓拆分或重新 calibration" in same_scope

    reroute = " ".join(cases[21]["expected"].split())
    for phrase in (
        "停止 remote review",
        "preserve branch、head、worktree、owner 和 feedback state",
        "越界 review feedback 不授予 scope authority",
        "calibration 必须先决定 reject/escalate",
        "接受已授权的 contract expansion",
        "one PR",
        "independent PRs",
        "dependent stack",
        "不是 topology signal",
        "Independent slices 保持 independent PRs",
        "不得发明 scheduler、review tool",
    ):
        assert phrase in reroute


def test_installer_propagates_global_review_tripwire(tmp_path: Path) -> None:
    expected = (
        "Continue mechanical review feedback within the current explicitly "
        "declared and authorized pull request contract through the existing "
        "bounded owner loop."
    )
    template = compact("codex/AGENTS.md.template")
    assert expected in template
    assert "invoke calibration first to reject or escalate" in template

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
        assert "distinct configured review-convergence budget is exhausted" in installed
        assert "is not a topology signal" in installed
