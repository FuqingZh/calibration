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


def test_orchestrator_containment_is_portable_and_bounded() -> None:
    harness = compact("references/engineering/discipline/harness.md")
    template = compact("codex/AGENTS.md.template")
    runbook = compact("docs/runbooks/agent-orchestrator-review-continuation.md")
    decision = compact("docs/decisions/2026-07-31-portable-orchestrator-containment.md")
    plan = compact(
        "docs/implementation-plan/"
        "20260731-v2.1-portable-orchestrator-containment-implementation-plan.md"
    )

    for authority in (harness, runbook, decision):
        assert "assigned" in authority and "workspace" in authority
        assert "aggregation root" in authority
        assert "sibling worktrees" in authority
    for authority in (template, runbook, decision):
        assert "remote mount" in authority
        assert "network filesystem" in authority
        assert "large shared filesystem" in authority
        assert "traversal-aware bound" in authority
        assert "file type" in authority
        assert "file size" in authority
        assert "depth" in authority
        assert "result count" in authority
        assert "concurrency" in authority

    assert "{{HOST_AUTHORITY}}" in text("codex/AGENTS.md.template")
    assert "explicit" in template and "host-operation tasks only" in template
    assert "discovery and mutations" in template
    for authority in (harness, runbook, decision, plan):
        assert "proposed" in authority
        assert "current AO behavior" in authority
    assert "CAL-1 public contract delivered" in plan
    assert "no behavioral-improvement claim" in plan
    assert "does not modify" in plan
    assert "agent-orchestrator" not in plan


def test_process_release_requires_empty_observable_retryable_containment() -> None:
    template = compact("codex/AGENTS.md.template")
    harness = compact("references/engineering/discipline/harness.md")
    runbook = compact("docs/runbooks/agent-orchestrator-review-continuation.md")
    decision = compact("docs/decisions/2026-07-31-portable-orchestrator-containment.md")

    for authority in (template, harness, runbook, decision):
        assert "OS-owned containment boundary" in authority
        assert "empty" in authority
        assert "termination as complete" in authority
        assert "runtime" in authority and "released only after" in authority
        assert "terminated state" in authority or "terminated session" in authority
        assert "cleanup" in authority and "pending" in authority
        assert "not proof" in authority
        assert "observable" in authority
        assert "retryable" in authority
    for authority in (harness, runbook, decision):
        assert "Current AO does not yet enforce" in authority


def test_workspace_mismatch_routes_mutation_to_single_owner() -> None:
    harness = compact("references/engineering/discipline/harness.md")
    runbook = compact("docs/runbooks/agent-orchestrator-review-continuation.md")
    decision = compact("docs/decisions/2026-07-31-portable-orchestrator-containment.md")

    for authority in (harness, runbook, decision):
        assert "workspace capability mismatch" in authority
        assert "assigned writable workspace" in authority
        assert "Git root" in authority
        assert "owning AO worker" in authority
        assert "patch" in authority and "stage" in authority
        assert "commit" in authority and "push" in authority
        assert "one writer" in authority
        assert "former owner to be quiesced" in authority
        assert "rejected filesystem escalation" in authority
        assert "not AO unavailable" in authority or "AO is unavailable" in authority
        assert "security" in authority.lower()
        assert "compatibility" in authority
        assert "irreversible" in authority
        assert "secret" in authority
        assert "permission" in authority

    for authority in (compact("AGENTS.md"), compact("codex/AGENTS.md.template")):
        assert "assigned writable workspace" in authority
        assert "one writer" in authority
        assert "sibling worktree" in authority
        assert "restore and send the owner" in authority
        assert "quiesce the former owner before transfer" in authority
        assert "Do not repeat rejected filesystem escalation" in authority
        assert "same-scope mechanical feedback" in authority

    template = compact("codex/AGENTS.md.template")
    assert "pull-request-bound work" in template
    assert "already installed and adopted AO environment" in template


def test_ao_review_continuation_is_owner_directed_and_retryable() -> None:
    runbook = compact("docs/runbooks/agent-orchestrator-review-continuation.md")

    for phrase in (
        "controller -> owning worker -> commit and push -> exact-head CI",
        "current-head review -> same-scope fix by owning worker",
        "`active`, `idle`, or `waiting_input` state with `ao send`",
        "authoritative readback confirms its OS-owned containment boundary is empty",
        "`ao session restore` and then `ao send`",
        "`ao session claim-pr <session> <pr> -p <project> --no-takeover`",
        "`ao spawn --claim-pr ... --no-takeover`",
        "and then use `ao send`",
        "existing REST resume boundary",
        "no CLI resume command",
        "controller performs readback only",
        "autonomously retries transient network operations and polling",
        "preserve the branch, worktree, pull-request, and feedback state",
        "not AO unavailable or daemon unavailability",
        "merge or deploy decisions not already authorized",
        "low-risk native auto-merge contract",
    ):
        assert phrase in runbook


def test_v11_decision_records_contract_and_bounded_routing_canary() -> None:
    decision = compact("docs/decisions/2026-07-31-portable-orchestrator-containment.md")

    assert "Version: v1.1" in decision
    assert "Static contract evidence" in decision
    assert "pull request #46" in decision.lower()
    assert "one bounded representative routing canary" in decision
    assert "controller stopped cross-worktree writes" in decision
    assert "original owner completed" in decision
    assert "local gates, push, CI, and exact-head review" in decision
    assert "no actionable feedback" in decision
    assert "does not establish a universal model or workflow improvement" in decision


def test_shared_aggregation_root_has_behavioral_prompt_coverage() -> None:
    prompts = text("skills/calibration/test-prompts.json")

    assert "共享聚合根下的递归搜索边界" in prompts
    assert "sibling worktrees" in prompts
    assert "traversal-aware bound" in prompts
    assert "file size" in prompts
    assert "concurrency" in prompts
    assert "upstream proposal" in prompts


def test_future_behavior_evaluation_is_conditional_and_correctly_scoped() -> None:
    plan = compact(
        "docs/implementation-plan/"
        "20260731-v2.1-portable-orchestrator-containment-implementation-plan.md"
    )

    for phrase in (
        "assigned repository itself as the Git root",
        "task prompt supplies neither the containment rule",
        "structured command and tool events",
        "resolved root escapes the assigned repository",
        "sibling manifest",
        "read-only answer cannot pass",
        "candidate source",
        "Codex CLI version",
        "reasoning effort",
        "scoring method",
        "private evidence location",
    ):
        assert phrase in plan
    assert "behavior evaluation is not an active phase" in plan
    assert "separately reviewed executable protocol" in plan
    assert "No model evaluation is part of this plan" in plan


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

    assert "stable maintenance mode" in docs
    assert "CAL-1 containment public contract is delivered" in docs
    assert "without a behavioral-improvement claim" in docs
    assert "future evaluation is not an active phase" in docs
    assert "systemd containment remains a proposal" in docs
    assert "Five-phase convergence result" in docs
    assert "## Open Evidence Gaps" in docs
    assert "### Architecture And Documentation" in docs
    assert "### Harness And Evaluation" in docs
    assert "### Delivery And Orchestration" in docs
    assert "20260727-v1.8-ai-native-calibration-convergence" in docs
