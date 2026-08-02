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

    terminated = harness.index("inspecting `session.isTerminated` first")
    restoration = harness.index("If true, restore the terminated owner only after")
    restoration_readback = harness.index(
        "After successful restoration, perform fresh authoritative"
    )
    restoration_routing = harness.index(
        "route the resulting non-terminated activity state", restoration_readback
    )
    activity = harness.index(
        "When `session.isTerminated` is false, initially or on that fresh"
    )
    assert terminated < restoration < restoration_readback
    assert restoration_readback < restoration_routing < activity
    assert "Hold `waiting_input` for provenance" in harness
    assert "already-authorized ordinary idle prompt" in harness
    assert "permission or user-decision prompts" in harness
    assert "`session.isTerminated=false`" in harness
    assert "`session.activity.state=exited`" in harness
    assert "existing REST resume-agent boundary" in harness
    assert "`session.activity.state=blocked` to human authority" in harness
    assert "runtime release and an empty containment boundary" in harness
    assert "otherwise preserve state and monitor" in harness

    for authority in (compact("AGENTS.md"), compact("codex/AGENTS.md.template")):
        assert "assigned writable workspace" in authority
        assert "one writer" in authority
        assert "sibling worktree" in authority
        terminated = authority.index("Inspect `session.isTerminated` first")
        restoration = authority.index("If true, only restore")
        restoration_readback = authority.index(
            "After restoration, perform fresh authoritative session readback"
        )
        activity = authority.index("Only when false, send `activity.state=active`")
        assert terminated < restoration < restoration_readback < activity
        assert "runtime release and an empty OS-owned containment boundary" in authority
        assert "otherwise preserve state" in authority
        assert "`activity.state=active` or `idle` directly" in authority
        assert "hold `waiting_input` for provenance" in authority
        assert "already-authorized ordinary idle prompt" in authority
        assert "escalate permission or user-decision prompts" in authority
        assert "route `exited` through REST resume-agent" in authority
        assert "return `blocked` to human authority" in authority
        assert "owner cannot write" in authority
        assert "ownership is released" in authority
        assert "runtime/containment release is complete and empty" in authority
        assert "cleanup-pending is not quiesced" in authority
        assert "do not transfer" in authority
        assert "Do not repeat rejected filesystem escalation" in authority
        assert "same-scope mechanical feedback" in authority
        owned_guard = authority.index(
            "Before any mutation, an already AO-owned repository, worktree, or branch"
        )
        owned_read_only = authority.index(
            "the controller remains read-only", owned_guard
        )
        owned_health = authority.index(
            "verify authoritative AO core health is daemon ready", owned_guard
        )
        owned_lookup = authority.index("before owner lookup and handoff", owned_health)
        authorization = authority.index(
            "conversation-authorized implementation intended to cross a pull-request"
        )
        lifecycle = authority.index("use AO lifecycle routing only with installed AO")
        assert "an adopted repository" in authority
        assert "supplied local host authority" in authority
        assert "accepted continuation-proven orchestrator" in authority
        assert "or explicitly bounded canary" in authority
        assert (
            "Review, analysis, or discussion-only requests remain read-only"
            in authority
        )
        assert (
            "when continuation is unproven and the current task is not that "
            "explicitly bounded canary" in authority
        )
        assert "new/unowned fallback or existing-owner preservation rule" in authority
        assert "Without supplied local host authority" in authority
        assert "narrowed fallback or existing-owner preservation rule" in authority
        assert "do not perform AO lifecycle routing" in authority
        health = authority.index("verify AO health before lifecycle routing")
        assert owned_guard < owned_read_only < owned_health < owned_lookup
        assert owned_lookup < authorization
        assert authorization < lifecycle < health
        assert authority.count("verify AO health before lifecycle routing") == 1
        assert "boundary in an adopted environment, verify AO health" not in authority
        new_work = authority.index("start a task-specific owning worker for new work")
        unowned = authority.index("that is truly unowned")
        new_owner_readback = authority.index(
            "Immediately perform fresh authoritative session readback"
        )
        new_owner_handoff = authority.index(
            "hand the task to that owner through normal activity-state routing"
        )
        branch = authority.index(
            "only that owner creates the implementation branch or pull request"
        )
        unclaimed_pr = authority.index(
            "A ready pull request with no AO owner is not thereby unowned"
        )
        writer_gate = authority.index(
            "every controller, human, or non-AO writer is quiesced and cannot write"
        )
        preserve_unclaimed = authority.index(
            "Otherwise preserve state, do not claim or spawn, and escalate"
        )
        owned_draft = authority.index(
            "If an existing draft is already AO-owned, perform owner lookup"
        )
        owner_marks_ready = authority.index("its owning worker marks it ready")
        unclaimed_draft = authority.index("If a draft is unclaimed")
        unclaimed_ready = authority.index(
            "authorized current writer marks it ready before the quiescence-gated claim"
        )
        claim_before_lookup = authority.index(
            "claim without takeover by an existing or new owner before "
            "owner-state lookup"
        )
        claim = authority.index(
            "Only existing-PR claim semantics require an existing pull request"
        )
        compare = authority.index("Compare the assigned writable workspace")
        assert health < new_work < unowned < new_owner_readback
        assert new_owner_readback < new_owner_handoff < branch
        assert owned_lookup < owned_draft < owner_marks_ready
        assert branch < owned_draft < owner_marks_ready < unclaimed_draft
        assert unclaimed_draft < unclaimed_ready < unclaimed_pr < writer_gate
        assert writer_gate < preserve_unclaimed < claim_before_lookup
        assert "AO-owner absence alone is not proof" in authority
        assert claim_before_lookup < claim < compare
        assert "Only an existing pull request enters owner lookup" not in authority
        assert "ready-for-review is only a claim prerequisite" not in authority.lower()
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

        proof = authority.index("accepted continuation-proven orchestrator")
        canary = authority.index("or explicitly bounded canary", proof)
        canary_condition = authority.index(
            "when continuation is unproven and the current task is not that "
            "explicitly bounded canary",
            canary,
        )
        conditional_fallback = authority.index(
            "new/unowned fallback or existing-owner preservation rule",
            canary_condition,
        )
        assert proof < canary < canary_condition < conditional_fallback < health

    for authority in (
        compact("AGENTS.md"),
        compact("codex/AGENTS.md.template"),
        harness,
        runbook,
    ):
        start = authority.index("start a task-specific owning worker")
        readback = authority.index("authoritative session readback", start)
        routing = authority.index("normal activity-state routing", readback)
        owner_branch = authority.index("only that owner creates", routing)
        assert start < readback < routing < owner_branch

    for authority in (
        compact("AGENTS.md"),
        compact("codex/AGENTS.md.template"),
        harness,
        runbook,
        decision,
    ):
        assert "waiting_input" in authority
        assert "authoritative evidence" in authority
        assert "ordinary idle prompt" in authority

    owned_draft = runbook.index("If an existing draft is already AO-owned")
    owner_lookup = runbook.index("perform owner lookup and handoff first", owned_draft)
    owner_ready = runbook.index("owning worker marks it ready", owner_lookup)
    unclaimed_draft = runbook.index("If a draft is unclaimed", owner_ready)
    unclaimed_ready = runbook.index(
        "authorized current writer marks it ready", unclaimed_draft
    )
    continuation_gate = runbook.index(
        "Normal automatic AO lifecycle routing requires the four-stage assessment"
    )
    bounded_canary = runbook.index("an explicitly bounded canary", continuation_gate)
    unproven = runbook.index("When continuation is unproven", bounded_canary)
    fallback = runbook.index("truly unowned new work uses isolated-worktree fallback")
    preservation = runbook.index(
        "existing AO-owned work preserves its branch, worktree, and feedback"
    )
    no_lifecycle = runbook.index("without owner lookup, restore, claim, or spawn")
    proof_gate = runbook.index("Only after the proof gate")
    start = runbook.index("start a task-specific owning worker", proof_gate)
    assert continuation_gate < bounded_canary < unproven < fallback
    assert fallback < preservation < no_lifecycle < proof_gate < start
    unclaimed = runbook.index(
        "then claim or spawn without takeover only after", unclaimed_ready
    )
    writer_gate = runbook.index(
        "every controller, human, or non-AO writer is quiesced and cannot write"
    )
    preserve_unclaimed = runbook.index(
        "Otherwise preserve state, do not claim or spawn, and escalate"
    )
    readback = runbook.index("perform fresh authoritative readback", unclaimed)
    routing = runbook.index("normal activity-state routing", readback)
    assert owned_draft < owner_lookup < owner_ready < unclaimed_draft
    assert unclaimed_draft < unclaimed_ready < unclaimed
    assert unclaimed < writer_gate < preserve_unclaimed
    assert preserve_unclaimed < readback < routing
    assert "Normal automatic AO lifecycle routing" in runbook
    assert runbook.count("start a task-specific owning worker") == 1

    for authority in (
        compact("AGENTS.md"),
        compact("codex/AGENTS.md.template"),
        harness,
        runbook,
        decision,
    ):
        assert "not thereby unowned" in authority or (
            "does not prove the pull request is unowned" in authority
        )
        assert "controller, human" in authority
        assert "quiesced and cannot write" in authority
        assert "do not claim or spawn" in authority
        assert "absence alone is not proof" in authority or (
            "No AO owner does not prove" in authority
        )

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
        assert "mechanically enforced transfer mechanism" in authority
        assert "authoritatively verified" in authority
        assert "accepted `continuation-proven` orchestrator" in authority
        assert "an explicitly bounded canary" in authority
        missing_authority = authority.index("Without supplied authority")
        missing_fallback = authority.index(
            "isolated-worktree fallback", missing_authority
        )
        missing_preservation = authority.index(
            "existing AO-owned work preserves", missing_fallback
        )
        canary_exception = authority.index(
            "when continuation is unproven and the current task is not that "
            "explicitly bounded canary"
        )
        conditional_result = authority.index(
            "the same fallback and preservation apply", canary_exception
        )
        assert missing_authority < missing_fallback < missing_preservation
        assert missing_preservation < canary_exception < conditional_result

    universal_guard = runbook.index(
        "Before any mutation, determine whether the repository, worktree, or branch"
    )
    universal_read_only = runbook.index(
        "the controller remains read-only", universal_guard
    )
    missing_authority = runbook.index("Without authority, preserve", universal_guard)
    authority = runbook.index("With authority and implementation authorization")
    continuation = runbook.index("when continuation is proven", authority)
    bounded_canary = runbook.index(
        "or the current task is the explicitly bounded canary", continuation
    )
    universal_health = runbook.index(
        "verify authoritative AO core health is `daemon ready`", bounded_canary
    )
    universal_lookup = runbook.index("Before owner lookup and handoff", bounded_canary)
    otherwise_preserve = runbook.index(
        "otherwise preserve the owned state", universal_health
    )
    intake = runbook.index("Conversation authorization is sufficient issue intake")
    assert universal_guard < universal_read_only < missing_authority < authority
    assert authority < continuation < bounded_canary < universal_lookup
    assert universal_lookup < universal_health < otherwise_preserve < intake
    assert (
        "regardless of whether a pull request exists or the task is PR-bound" in runbook
    )
    assert (
        "Read-only review, analysis, and discussion requests remain read-only"
        in runbook
    )

    template = compact("codex/AGENTS.md.template")
    assert "conversation-authorized implementation" in template
    assert "use AO lifecycle routing only with installed AO" in template
    assert "supplied local host authority" in template


def test_ao_review_continuation_is_owner_directed_and_retryable() -> None:
    runbook = compact("docs/runbooks/agent-orchestrator-review-continuation.md")

    assert "An already AO-owned draft routes to its owner before" in runbook
    assert "unclaimed draft's authorized current writer marks it ready" in runbook
    assert "must become ready before owner lookup or claim" not in runbook
    assert "ready-for-review is only a claim prerequisite" not in runbook.lower()

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
        "Otherwise preserve state and monitor",
        "`ao session restore`; then perform fresh authoritative readback",
        "normal resulting activity-state routing",
        "use `ao send` only when permitted",
        "`ao session claim-pr <session> <pr> -p <project> --no-takeover`",
        "`ao spawn --claim-pr ... --no-takeover`",
        "After claim or spawn, perform fresh authoritative readback",
        "use `ao send` only when that routing permits it",
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
        "preserve observable state and report the actual stop reason",
        "`delivery degraded` only for the corresponding external integration",
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

    for authority in (
        harness,
        runbook,
        decision,
        compact("AGENTS.md"),
        compact("codex/AGENTS.md.template"),
    ):
        assert "report the actual stop reason" in authority
        assert "delivery degraded" in authority
        assert "external integration or authentication failure" in authority
        assert "core daemon remains ready" in authority

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

    restoration = decision.index("restores a terminated owner only after")
    readback = decision.index("After restoration, it performs fresh authoritative")
    routing = decision.index("normal resulting activity-state routing", readback)
    permitted_send = decision.index("using `ao send` only when permitted", routing)
    assert restoration < readback < routing < permitted_send

    prompts = text("skills/calibration/test-prompts.json")
    for phrase in (
        "session.isTerminated=false",
        "仅有 adopted AO environment 不足以触发生命周期路由",
        "normal automatic routing 还要求 continuation-proven",
        "explicitly bounded canary",
        "continuation unproven",
        "existing AO-owned work preserve branch/worktree/feedback",
        "不 send/restore/claim/spawn",
        "truly unowned new work 使用 isolated-worktree fallback",
        "通过 proof gate 后",
        "activity.state=exited",
        "REST resume-agent boundary",
        "activity.state=blocked 交给 human authority",
        "ao session restore、fresh authoritative readback",
        "claim/spawn 后 fresh authoritative readback",
        "仅在 permitted 时 ao send",
        "没有 AO owner 不代表 truly unowned",
        "controller/human/non-AO writer 已 quiesced 且 cannot write",
        "do not claim/spawn 并 escalate",
        "AO-owner absence alone is not proof",
        "报告 actual stop reason",
        "delivery degraded 只用于 core daemon ready 时相应的 external "
        "integration/authentication failure",
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
