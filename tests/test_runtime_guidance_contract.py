from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (REPOSITORY_ROOT / path).read_text(encoding="utf-8")


def compact(path: str) -> str:
    return " ".join(text(path).split())


def test_generated_agents_is_the_only_private_profile_discovery_path() -> None:
    template = text("codex/AGENTS.md.template")
    assert "{{HOST_AUTHORITY}}" in template
    assert "if that file exists" in " ".join(template.split())
    assert "Do not load it for ordinary engineering work" in template

    for root in ("skills", "references"):
        for path in (REPOSITORY_ROOT / root).rglob("*"):
            if path.is_file():
                content = path.read_text(encoding="utf-8", errors="ignore")
                assert ".config/calibration" not in content
                assert "calibration/AGENTS.md" not in content

    for skill_dir in (REPOSITORY_ROOT / "skills").iterdir():
        if skill_dir.name == "calibration" or not skill_dir.is_dir():
            continue
        skill = skill_dir / "SKILL.md"
        if skill.is_file():
            assert "Agent Orchestrator" not in skill.read_text(encoding="utf-8")


def test_shared_aggregation_root_has_behavioral_prompt_coverage() -> None:
    prompts = text("skills/calibration/test-prompts.json")

    assert "共享聚合根下的递归搜索边界" in prompts
    assert "sibling worktrees" in prompts
    assert "traversal-aware bound" in prompts
    assert "file size" in prompts
    assert "concurrency" in prompts


def test_docs_separate_current_authority_from_archived_plans() -> None:
    source = REPOSITORY_ROOT / "docs/README.md"
    docs = source.read_text(encoding="utf-8")
    authority = docs.split("## Current Authority\n", 1)[1].split("\n## ", 1)[0]
    current_targets = {
        (source.parent / target.split("#", 1)[0]).resolve()
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", authority)
    }
    assert all("ao-integration" not in str(path) for path in current_targets)
    assert REPOSITORY_ROOT / "skills/calibration/SKILL.md" in current_targets
    archive = REPOSITORY_ROOT / "docs/archive/README.md"
    assert (source.parent / "archive/README.md").resolve() in {
        (source.parent / target.split("#", 1)[0]).resolve()
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", docs)
    }
    archived_targets = {
        (archive.parent / target.split("#", 1)[0]).resolve()
        for target in re.findall(
            r"\[[^]]+\]\(([^)]+)\)", archive.read_text(encoding="utf-8")
        )
    }
    for relative in (
        "docs/implementation-plans/"
        "20260731-v2.1-portable-orchestrator-containment-implementation-plan.md",
        "docs/implementation-plans/"
        "20260826-v1.0-self-contained-first-party-skills-migration-implementation-plan.md",
        "docs/testing/20260825-v2.1-progressive-validation-relative-replacement-test-plan.md",
        "docs/testing/"
        "20260825-v2.2-progressive-validation-relative-replacement-correction-plan.md",
        "evaluations/teach-adaptation/results.md",
        "evaluations/teach-adaptation/v2/README.md",
    ):
        assert REPOSITORY_ROOT / relative in archived_targets
        assert REPOSITORY_ROOT / relative not in current_targets


def test_retired_guidance_preserves_exact_bytes_outside_skill_loading() -> None:
    archive = REPOSITORY_ROOT / "docs/archive/ao-guidance-before-v0.12.12"
    records = json.loads(text("docs/archive/retired-guidance-manifest.json"))["files"]
    recorded_paths = {row["path"] for row in records}
    assert len(recorded_paths) == len(records)
    assert recorded_paths == {
        "docs/implementation-plans/"
        "20260731-v2.1-portable-orchestrator-containment-implementation-plan.md",
        *(
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for path in archive.rglob("*")
            if path.is_file()
        ),
    }
    for row in records:
        path = REPOSITORY_ROOT / row["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"], path
    for path in (
        "skills/calibration/SKILL.md",
        "skills/calibration/references/discipline/harness.md",
    ):
        assert "docs/archive" not in text(path)


def test_runtime_entrypoints_are_independent_of_retired_integration() -> None:
    for path in (
        "AGENTS.md",
        "codex/AGENTS.md.template",
        "skills/calibration/SKILL.md",
        "skills/calibration/references/discipline/harness.md",
        "skills/calibration/test-prompts.json",
    ):
        current = text(path)
        assert not re.search(r"\bAO\b|agent-orchestrator|using-ao", current)
    assert not (REPOSITORY_ROOT / "scripts/adopt_ao_repository.py").exists()
    assert not (
        REPOSITORY_ROOT
        / "skills/calibration/references/agent-orchestrator-review-continuation.md"
    ).exists()
    assert (
        REPOSITORY_ROOT / "docs/archive/ao-integration-retired-2026-10-15.md"
    ).is_file()


def test_generic_ownership_and_release_rules_survive_retirement() -> None:
    template = compact("codex/AGENTS.md.template")
    harness = compact("skills/calibration/references/discipline/harness.md")
    for surface in (template, harness):
        assert "write-authority revocation and runtime release" in surface
        assert "sibling worktree" in surface
        assert "empty OS-owned containment boundary" in surface
    assert "traversal-aware bound" in template
    assert "terminated session is not proof" in template
