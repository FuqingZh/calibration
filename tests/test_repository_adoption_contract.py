from __future__ import annotations

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (REPOSITORY_ROOT / path).read_text(encoding="utf-8")


def compact(path: str) -> str:
    return " ".join(text(path).split())


def test_public_architecture_keeps_ao_optional() -> None:
    docs = compact("docs/README.md")
    agents = compact("AGENTS.md")
    skill = compact("skills/calibration/SKILL.md")

    for layer in (
        "reusable references",
        "model interaction entrypoints",
        "optional environment adapter",
        "private host configuration",
    ):
        assert layer in docs
    assert "AO is an optional environment adapter" in agents
    assert "not a property of every public clone" in agents
    assert "already installed Agent Orchestrator" in skill


def test_portable_ao_guide_preserves_state_and_adoption_contracts() -> None:
    runbook = compact("docs/runbooks/agent-orchestrator-review-continuation.md")

    for owner in ("sandbox state", "worker state", "daemon state", "host state"):
        assert owner in runbook
    for state in (
        "indeterminate",
        "daemon ready",
        "unavailable",
        "registered",
        "configured",
        "runtime-ready",
        "continuation-proven",
    ):
        assert state in runbook
    assert "isolated worktree" in runbook
    assert "scripts/adopt_ao_repository.py" in runbook
    assert "already installed, CLI-capable AO" in runbook


def test_pull_request_gates_remain_exact_head_and_conditional() -> None:
    for authority in (
        compact("AGENTS.md"),
        compact("references/engineering/discipline/harness.md"),
        compact("docs/runbooks/agent-orchestrator-review-continuation.md"),
    ):
        assert "exact current head" in authority or "exact-head" in authority
        assert "current-head review" in authority
        assert "actionable review threads" in authority
        assert "GitHub native" in authority
        assert "autoMerge" in authority

    agents = compact("AGENTS.md")
    assert "isolated worktree" in agents
    assert "explicit user stop" in agents
    assert "security" in agents


def test_dashboard_terminal_boundary_is_portable_and_safe() -> None:
    runbook = compact("docs/runbooks/agent-orchestrator-review-continuation.md")
    decision = compact(
        "docs/decisions/2026-07-30-dashboard-terminal-access-boundary.md"
    )

    for authority in (runbook, decision):
        assert "off by default" in authority
        assert "exact client IP" in authority
        assert "exact" in authority and "Origin" in authority
        assert "exact `/mux`" in authority
        assert "loopback" in authority
        assert "Origin" in authority and "not authentication" in authority
        assert "Multi-user" in authority
        assert "dynamic-address" in authority
        assert "require authentication" in authority


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


def test_adoption_adapter_and_installer_have_distinct_codex_home_contracts() -> None:
    decision = compact(
        "docs/decisions/2026-07-30-ao-host-context-and-config-compatibility.md"
    )
    runbook = compact("docs/runbooks/agent-orchestrator-review-continuation.md")

    for phrase in (
        "apps = false",
        "plugins = false",
        "no top-level `mcp_servers`",
        "harmless TUI state",
        "extra top-level metadata",
        "non-conflicting feature keys",
        "read-only",
    ):
        assert phrase in decision
    assert "does not read, validate, or modify" in decision
    assert "Linux user-service profile" in runbook
    assert "systemd --user" in runbook
    assert "tmux prerequisites" in runbook
    assert "not a universal Desktop adapter" in runbook


def test_docs_restore_stable_authority_and_historical_navigation() -> None:
    docs = compact("docs/README.md")

    assert "stable maintenance mode with no active implementation plan" in docs
    assert "Five-phase convergence result" in docs
    assert "## Open Evidence Gaps" in docs
    assert "### Architecture And Documentation" in docs
    assert "### Harness And Evaluation" in docs
    assert "### Delivery And Orchestration" in docs
    assert "20260727-v1.8-ai-native-calibration-convergence" in docs
