from __future__ import annotations

from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
GUIDE = "skills/calibration/references/agent-orchestrator-review-continuation.md"


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


def test_dashboard_terminal_boundary_is_portable_and_safe() -> None:
    runbook = compact(
        "skills/calibration/references/agent-orchestrator-review-continuation.md"
    )
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
        "docs/implementation-plans/"
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
    runbook = compact(
        "skills/calibration/references/agent-orchestrator-review-continuation.md"
    )

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
    assert "Sol Advisor and Calibration ablation is complete" in docs
    assert "rejects the tested mandatory CAL-MIN route" in docs
    assert "systemd containment remains a proposal" in docs
    assert "Five-phase convergence result" in docs
    assert "## Open Evidence Gaps" in docs
    assert "### Architecture And Documentation" in docs
    assert "### Harness And Evaluation" in docs
    assert "### Delivery And Orchestration" in docs
    assert "20260727-v1.8-ai-native-calibration-convergence" in docs


def test_all_runtime_entrypoints_route_to_one_ao_authority() -> None:
    guide = REPOSITORY_ROOT / GUIDE
    assert guide.is_file()
    for path in (
        "AGENTS.md",
        "codex/AGENTS.md.template",
        "skills/calibration/references/discipline/harness.md",
        "skills/calibration/SKILL.md",
    ):
        entry = compact(path)
        assert "agent-orchestrator-review-continuation.md" in entry
        if path != "skills/calibration/SKILL.md":
            assert "before" in entry.lower() and "lifecycle actions" in entry
            assert "preserve" in entry.lower() and "owned" in entry
            assert "new or unowned" in entry
            assert "sibling worktree" in entry
            # Detailed routing must not be copied back into every entrypoint.
            assert "session.activity.state" not in entry


def test_version_corrections_do_not_expand_authority() -> None:
    guide = compact(GUIDE)
    assert "84fb37ce5aa947ceb9b19b0c2435b242ac92ce26" in guide
    assert "source evidence, not proof of the installed daemon version" in guide
    assert "using-ao" in guide and "--help" in guide
    assert "open draft PR can be claimed without marking it ready" in guide
    assert "ao session resume-agent" in guide
    assert "typed project configuration has no `autoMerge` field" in guide
    assert "capabilities grant no ownership or merge authority" in guide
    assert "On older versions, check actual capabilities" in guide
    assert "successful claim does not prove branch checkout" in guide
    for path in (
        GUIDE,
        "AGENTS.md",
        "codex/AGENTS.md.template",
        "skills/calibration/references/discipline/harness.md",
        "skills/calibration/test-prompts.json",
    ):
        current = compact(path)
        assert "REST resume-agent boundary" not in current
        assert "marks it ready before the quiescence-gated claim" not in current
        assert "keep AO project `autoMerge` off" not in current


@pytest.mark.parametrize(
    "requirement",
    [
        "sandbox state",
        "worker state",
        "daemon state",
        "host state",
        "indeterminate",
        "registered",
        "configured",
        "runtime-ready",
        "continuation-proven",
        "controller remains read-only, even without a PR",
        "Review, analysis, and discussion alone authorize no implementation",
        "installed AO, an adopted repository, supplied local host authority",
        "accepted continuation-proven orchestrator or an explicitly bounded canary",
        "Verify authoritative `daemon ready` before owner lookup and handoff",
        "Without these gates, do not send, restore, claim, or spawn",
        "isolated-worktree fallback only for new or unowned pull-request-bound work",
        "preserve an existing AO-owned PR's branch, worktree, and feedback",
        "only that owner creates the implementation branch or PR",
        "prove every controller, human, or non-AO writer is quiesced and cannot write",
        "AO-owner absence alone is not proof",
        "Otherwise preserve state, do not claim or spawn, and escalate",
        "Claim without takeover",
        "assigned writable workspace and Git root",
        "Do not patch, stage, commit, or push in an owner's sibling worktree",
        "Do not repeat rejected filesystem escalation",
        "owner cannot write, ownership is released",
        "runtime release is complete with an empty containment boundary",
        "terminated owner with cleanup pending, is not quiesced",
        "enforceable containment or write-authority revocation mechanism",
        "preserve state and do not transfer",
        "Process, tmux, session, or writer absence is not equivalent proof",
        "OS-owned containment boundary is empty",
        "terminal, tmux, shell, or session disappearance is not proof",
        "Keep partial release observable and retryable",
    ],
)
def test_canonical_guide_retains_each_safety_obligation(requirement: str) -> None:
    assert requirement in compact(GUIDE)


def test_owner_state_routing_is_ordered_and_permission_sensitive() -> None:
    guide = compact(GUIDE)
    assert "Inspect `session.isTerminated` before `session.activity.state`" in guide
    assert "`session.status` is board/SCM state, not the activity authority" in guide
    assert guide.index("| Terminated |") < guide.index("| Non-terminated, `active`")
    for obligation in (
        "Restore only after runtime release and an empty OS-owned containment",
        "otherwise preserve state and monitor",
        "Hold for provenance",
        "authoritative evidence proves an already-authorized ordinary idle prompt",
        "escalate permission or user-decision prompts",
        "Non-terminated, `exited`",
        "native resume-agent command",
        "Non-terminated, `blocked` | Return to human authority",
        "After spawn, claim, restore, or resume, perform fresh authoritative readback",
        "apply this table before sending",
        "Native message guards do not authorize replying to a permission prompt",
    ):
        assert obligation in guide


def test_merge_release_and_retry_authority_survive_consolidation() -> None:
    guide = compact(GUIDE)
    for obligation in (
        "GitHub native per-PR auto-merge",
        "required CI passes on the exact current head",
        "current-head review is clean",
        "no actionable review threads remain",
        "An explicit user stop",
        "security, secrets, permissions, release, compatibility, or irreversible",
        "Deploy needs separate explicit authority",
        "distinct deployment contract",
        "per-session terminate-on-PR-merge policy and read it back",
        "It grants no merge authority",
        "retain the terminated session record as audit history",
        "cancelled, no-PR, or closed-unmerged",
        "state and dirty-worktree checks",
        "Preserve dirty worktrees",
        "`preserved_dirty`, `failed`",
        "do not claim full process release",
        "idempotent transient operations and polling",
        "attempt or deadline budget, backoff, and `Retry-After`",
        "Stop on head or scope change, cancellation",
        "non-transient authentication or permission failure, or budget exhaustion",
        "external write with unknown outcome",
        "authoritative readback and deduplication first",
        "retry only if the intended state is absent",
        "Preserve observable state and report the actual stop reason",
        "external integration or authentication failure while the core daemon",
        "exhausted review-convergence budget routes back to calibration",
    ):
        assert obligation in guide


def test_discovery_and_release_contracts_remain_portable() -> None:
    guide = compact(GUIDE)
    for obligation in (
        "assigned workspace",
        "parent aggregation root containing sibling worktrees",
        "remote mount",
        "network filesystem",
        "large shared filesystem",
        "traversal-aware bound",
        "maximum depth",
        "file type, file size, result count, and concurrency",
        "per-worker systemd scopes remain a proposed mechanism",
        "not verified current AO behavior",
    ):
        assert obligation in guide
    template = compact("codex/AGENTS.md.template")
    assert "discovery and mutations" in template
    assert "traversal-aware bound" in template
    assert "empty OS-owned containment boundary" in template
    assert "terminated session is not proof" in template


def test_old_rules_are_archived_outside_skill_loading() -> None:
    archive = REPOSITORY_ROOT / "docs/archive/ao-guidance-before-v0.12.12"
    assert {p.name for p in archive.iterdir()} == {
        "global-agents.txt",
        "repository-agents.txt",
        "harness.txt",
        "ao-guide.txt",
    }
    assert "REST resume-agent" in (archive / "global-agents.txt").read_text()
    assert "no CLI resume command" in (archive / "ao-guide.txt").read_text()
    for path in (GUIDE, "skills/calibration/references/discipline/harness.md"):
        assert "docs/archive" not in text(path)
