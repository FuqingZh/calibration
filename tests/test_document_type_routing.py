from __future__ import annotations

import json

from tests.test_install import REPOSITORY_ROOT


def _prompt_cases() -> dict[int, dict[str, str]]:
    path = REPOSITORY_ROOT / "skills/calibration/test-prompts.json"
    return {case["id"]: case for case in json.loads(path.read_text())}


def test_document_routing_overview_covers_all_current_neighbors() -> None:
    case = _prompt_cases()[2]
    expected = case["expected"]

    for document_type in (
        "architecture-overview",
        "decision-record",
        "implementation-plan",
        "tutorial",
        "how-to-guide",
        "runbook",
        "compatibility-record",
        "test-plan",
        "benchmark-record",
        "trace-retro",
    ):
        assert document_type in expected
    assert "PR body 不是长期文档" in expected
    assert "archive 是生命周期状态\uff0c不是文档类型" in expected


def test_focused_document_routing_cases_choose_one_primary_type() -> None:
    cases = _prompt_cases()
    expected_routes = {
        23: ("tutorial", "docs/tutorials/", ("how-to guide", "architecture overview")),
        24: ("how-to guide", "docs/how-to-guides/", ("tutorial", "runbook")),
        25: ("runbook", "docs/runbooks/", ("how-to guide", "未经验证")),
        26: (
            "compatibility record",
            "docs/compatibility/",
            ("architecture overview", "tutorial", ".traces/"),
        ),
        27: (
            "decision record",
            "docs/decisions/",
            ("architecture overview", "尚未决定"),
        ),
        28: (
            "implementation plan",
            "docs/implementation-plans/",
            ("design proposal", "decision record", "PR body"),
        ),
    }

    for case_id, (primary_type, path, rejected_neighbors) in expected_routes.items():
        expected = cases[case_id]["expected"]
        assert expected.count("主类型应是") == 1
        assert primary_type in expected
        assert path in expected
        for neighbor in rejected_neighbors:
            assert neighbor in expected
