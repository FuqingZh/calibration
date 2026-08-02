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
        assert "owner cannot write" in authority
        assert "ownership is released" in authority
        assert "runtime release" in authority
        assert "empty containment boundary" in authority
        assert "idle or live owner" in authority
        assert "terminated owner with cleanup pending" in authority
        assert "preserve state and do not transfer" in authority
        assert "rejected filesystem escalation" in authority
        assert "not AO unavailable" in authority or "AO is unavailable" in authority
        assert "security" in authority.lower()
        assert "compatibility" in authority
        assert "irreversible" in authority
        assert "secret" in authority
        assert "permission" in authority

    assert "Send an `active` or `idle` owner directly" in harness
    assert "Hold `waiting_input` for provenance" in harness
    assert "permission or user-decision prompts" in harness
    assert "Restore a terminated owner only after" in harness
    assert "runtime release and an empty containment boundary" in harness
    assert "otherwise preserve state and monitor" in harness

    for authority in (compact("AGENTS.md"), compact("codex/AGENTS.md.template")):
        assert "assigned writable workspace" in authority
        assert "one writer" in authority
        assert "sibling worktree" in authority
        terminated = authority.index("Inspect `session.isTerminated` first")
        restoration = authority.index("If true, only restore")
        activity = authority.index("Only when false, send `activity.state=active`")
        assert terminated < restoration < activity
        assert "runtime release and an empty OS-owned containment boundary" in authority
        assert "otherwise preserve state" in authority
        assert "`activity.state=active` or `idle` directly" in authority
        assert "hold `waiting_input` for provenance" in authority
        assert "route `exited` through REST resume-agent" in authority
        assert "return `blocked` to human authority" in authority
        assert "owner cannot write" in authority
        assert "ownership is released" in authority
        assert "runtime/containment release is complete and empty" in authority
        assert "cleanup-pending is not quiesced" in authority
        assert "do not transfer" in authority
        assert "Do not repeat rejected filesystem escalation" in authority
        assert "same-scope mechanical feedback" in authority
        assert "pull-request-bound work with installed AO" in authority
        assert "an adopted repository" in authority
        assert "supplied local host authority" in authority
        assert "Without supplied local host authority" in authority
        assert "narrowed fallback or existing-owner preservation rule" in authority
        assert "do not perform AO lifecycle routing" in authority
        new_work = authority.index("start a task-specific owning worker for new work")
        unowned = authority.index("that is truly unowned")
        branch = authority.index(
            "before creating its implementation branch or pull request"
        )
        unclaimed_pr = authority.index(
            "An existing ready pull request with no AO owner"
        )
        claim_before_lookup = authority.index(
            "claimed without takeover by an existing or new owner before "
            "owner-state lookup"
        )
        owned = authority.index("Any already AO-owned repository, worktree, or branch")
        lookup = authority.index("enters owner lookup and handoff before mutation")
        no_pr = authority.index("even when no pull request exists")
        claim = authority.index(
            "Only existing-PR claim semantics require an existing pull request"
        )
        compare = authority.index("Compare the assigned writable workspace")
        assert new_work < unowned < branch
        assert branch < unclaimed_pr < claim_before_lookup < owned
        assert owned < lookup < no_pr < claim < compare
        assert "Only an existing pull request enters owner lookup" not in authority
        assert (
            "Blind retries are limited to idempotent transient operations or polling"
            in authority
        )
        assert "bounded attempts or deadline" in authority
        assert "backoff" in authority and "`Retry-After`" in authority
        assert "Stop on head or scope change" in authority
        assert "cancellation" in authority
        assert "non-transient authentication or permission failure" in authority
        assert "or exhaustion" in authority
        assert "external write with unknown outcome" in authority
        assert "authoritative readback and deduplication first" in authority
        assert "retry only when the intended state is absent" in authority

    harness = compact("references/engineering/discipline/harness.md")
    decision = compact("docs/decisions/2026-07-31-portable-orchestrator-containment.md")
    for authority in (
        compact("AGENTS.md"),
        compact("codex/AGENTS.md.template"),
        harness,
        decision,
    ):
        assert "installed AO" in authority
        assert "adopted repository" in authority
        assert "supplied local host authority" in authority
        assert "Without supplied" in authority
        assert "new or unowned" in authority
        assert "isolated-worktree fallback" in authority
        assert "existing AO-owned" in authority
        assert "branch, worktree, and feedback" in authority
        assert "AO lifecycle routing" in authority

    for authority in (harness, decision):
        assert "until authority is available" in authority
        assert "mechanically enforced transfer mechanism" in authority
        assert "authoritatively verified" in authority

    template = compact("codex/AGENTS.md.template")
    assert "pull-request-bound work with installed AO" in template
    assert "supplied local host authority" in template


def test_ao_review_continuation_is_owner_directed_and_retryable() -> None:
    runbook = compact("docs/runbooks/agent-orchestrator-review-continuation.md")

    for phrase in (
        "controller -> owning worker -> commit and push -> exact-head CI",
        "current-head review -> same-scope fix by owning worker",
        "`session.isTerminated` first, then `session.activity.state`",
        "`session.status` is derived board or SCM state",
        "`active` or `idle` activity with `ao send`",
        "Hold `waiting_input` and inspect its provenance",
        "permission or user-decision prompt",
        "ordinary idle prompt within already granted authority",
        "runtime release and its OS-owned containment boundary is empty",
        "otherwise preserve state and monitor",
        "`ao session restore` and then `ao send`",
        "`ao session claim-pr <session> <pr> -p <project> --no-takeover`",
        "`ao spawn --claim-pr ... --no-takeover`",
        "and then use `ao send`",
        "`session.isTerminated=false`",
        "`session.activity.state=exited`",
        "existing REST resume-agent boundary",
        "`session.activity.state=blocked` to human authority",
        "no CLI resume command",
        "controller performs readback only",
        "retries only idempotent transient network operations and polling",
        "explicit attempt or deadline budget",
        "exponential backoff",
        "honors `Retry-After`",
        "Stop on head or scope change",
        "non-transient authentication or permission failure",
        "external write times out with unknown outcome",
        "authoritative readback and deduplication",
        "retry only when the intended state is absent",
        "preserve observable state and report delivery degraded",
        "former owner cannot write",
        "terminated and ownership is released",
        "runtime release is complete with an empty containment boundary",
        "merely idle or live owner",
        "terminated owner with cleanup pending",
        "do not transfer, claim, or spawn",
        "preserve the branch, worktree, pull-request, and feedback state",
        "not AO unavailable or daemon unavailability",
        "Low-risk GitHub native auto-merge may use authority already granted",
        "deploy always requires separate explicit authority",
        "distinct deployment contract",
    ):
        assert phrase in runbook

    for phrase in (
        "If only the owner cannot be restored or claimed",
        "authoritative host evidence establishes AO is unavailable",
        "normal isolated-worktree fallback",
        "only for new or unowned pull-request-bound work",
        "existing AO-owned pull request",
        "preserve the branch, worktree, pull-request, and feedback state",
        "wait for AO or owner restoration",
        "real enforceable containment or write-authority revocation mechanism",
        "process, tmux, session, or writer absence is not equivalent proof",
    ):
        assert phrase in runbook


def test_owner_retry_budget_and_state_routing_cross_authority_surfaces() -> None:
    harness = compact("references/engineering/discipline/harness.md")
    runbook = compact("docs/runbooks/agent-orchestrator-review-continuation.md")
    decision = compact("docs/decisions/2026-07-31-portable-orchestrator-containment.md")

    for authority in (harness, runbook, decision):
        assert "idempotent" in authority
        assert "attempt or deadline budget" in authority
        assert "backoff" in authority
        assert "`Retry-After`" in authority
        assert "head or scope change" in authority
        assert "cancellation" in authority
        assert "non-transient authentication or permission failure" in authority
        assert "budget exhaustion" in authority
        assert "external write" in authority and "unknown outcome" in authority
        assert "authoritative readback and deduplication" in authority
        assert "intended state" in authority and "absent" in authority
        assert "observable state" in authority
        assert "delivery degraded" in authority
        assert "deploy" in authority and "separate explicit authority" in authority
        assert "distinct deployment contract" in authority
        assert "AO" in authority and "unavailable" in authority
        assert "isolated-worktree fallback" in authority
        assert "new or unowned pull-request-bound work" in authority
        assert "existing AO-owned pull request" in authority
        assert (
            "real enforceable containment or write-authority revocation mechanism"
            in authority
        )
        assert (
            "process, tmux, session, or writer absence is not equivalent proof"
            in authority
        )
        assert "preserve state" in authority

    for authority in (compact("AGENTS.md"), compact("codex/AGENTS.md.template")):
        assert "new or unowned PR-bound work" in authority
        assert "existing AO-owned PR" in authority
        assert "branch, worktree, and feedback" in authority
        assert "AO or owner restoration" in authority
        assert "real enforceable containment or write-authority revocation" in authority

    for phrase in (
        "`session.isTerminated` before `session.activity.state`",
        "derived `session.status`",
        "Only `active` and `idle`",
        "Ambiguous `waiting_input` is held",
        "permission or user-decision prompts escalate",
        "already authorized ordinary idle prompt",
        "`session.isTerminated=false`",
        "`session.activity.state=exited`",
        "existing REST resume-agent boundary",
        "`session.activity.state=blocked` to human authority",
    ):
        assert phrase in decision

    prompts = text("skills/calibration/test-prompts.json")
    for phrase in (
        "session.isTerminated=false",
        "activity.state=exited",
        "REST resume-agent boundary",
        "activity.state=blocked 交给 human authority",
        "owner-only restore/claim failure 且 daemon ready 时 preserve/readback",
        "isolated-worktree fallback 只用于 new or unowned PR-bound work",
        "existing AO-owned PR",
        "preserve branch/worktree/feedback",
        "等待 AO/owner restoration",
        "real enforceable containment",
        "write-authority revocation mechanism",
        "不得用 process/tmux/session/writer absence 充当 proof",
    ):
        assert phrase in prompts
    assert "agent exit is not an activity state" not in decision
    assert "agent-exited 不是 activity state" not in prompts
    assert "若 AO unavailable 则保留现有 PR/worktree/feedback state" not in prompts
    assert "pull request #46" not in runbook
    assert "PR #46" not in prompts
    agents = compact("AGENTS.md")
    assert (
        "Otherwise use an isolated worktree for pull-request-bound delivery"
        not in agents
    )
    assert "If AO is unavailable, use an isolated worktree" not in agents
    assert "use an isolated worktree and report that bounded fallback" not in runbook
    assert "continue through the normal isolated-Worktree delivery path" not in harness
    for authority in (agents, runbook, harness):
        assert "new or unowned pull-request-bound work" in authority
        assert "Existing AO-owned pull requests defer" in authority
    assert (
        "an existing AO-owned pull request follows the ownership-preservation rule"
        in agents
    )
    for unprovable in (
        "no former writer process",
        "no process can mutate the owned worktree or branch",
        "host readback proves",
    ):
        assert unprovable not in harness
        assert unprovable not in runbook
        assert unprovable not in decision


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
