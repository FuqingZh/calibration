from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class AdoptionDocuments:
    harness: str
    skill: str
    docs_readme: str
    runbook: str
    ao_decision: str


@pytest.fixture(scope="module")
def documents() -> AdoptionDocuments:
    def compact(path: Path) -> str:
        return " ".join(path.read_text(encoding="utf-8").split())

    return AdoptionDocuments(
        harness=compact(
            REPOSITORY_ROOT / "references/engineering/discipline/harness.md"
        ),
        skill=(REPOSITORY_ROOT / "skills/calibration/SKILL.md").read_text(
            encoding="utf-8"
        ),
        docs_readme=(REPOSITORY_ROOT / "docs/README.md").read_text(encoding="utf-8"),
        runbook=(
            REPOSITORY_ROOT / "docs/runbooks/agent-orchestrator-review-continuation.md"
        ).read_text(encoding="utf-8"),
        ao_decision=(
            REPOSITORY_ROOT
            / "docs/decisions/2026-07-23-ao-review-continuation-adoption.md"
        ).read_text(encoding="utf-8"),
    )


def test_adoption_starts_from_evidence_and_allows_no_change(
    documents: AdoptionDocuments,
) -> None:
    assert "## Repository Capability Adoption" in documents.harness
    assert "repository capability assessment, minimal adoption" in documents.skill
    assert "present, missing, or not applicable" in documents.harness
    assert "named tools and artifacts as possible means" in documents.harness
    assert "Leave an adequate capability unchanged" in documents.harness
    assert "Do not assign a generic maturity score" in documents.harness
    assert "a library or CLI does not need a UI" in documents.harness


def test_orchestrator_is_an_optional_engine_not_global_authority(
    documents: AdoptionDocuments,
) -> None:
    assert "such as Symphony, over a custom scheduler" in documents.harness
    assert "it does not own repository authority" in documents.harness
    assert "one bounded representative task" in documents.harness
    assert "do not turn local labels, deployment topology" in documents.harness


def test_authorized_implementation_uses_an_adopted_orchestrator(
    documents: AdoptionDocuments,
) -> None:
    assert "## Implementation Task Intake" in documents.harness
    assert "execute an accepted plan" in documents.harness
    assert (
        "route it to that orchestrator without requiring the user" in documents.harness
    )
    assert "start a task-specific worker" in documents.harness
    assert "claim or restore the owning worker" in documents.harness


def test_planning_only_does_not_start_implementation(
    documents: AdoptionDocuments,
) -> None:
    assert "remains read-only unless it also authorizes the change" in documents.harness
    assert (
        "Use only an already accepted repository, host, identity" in documents.harness
    )
    assert "normal isolated-Worktree delivery path" in documents.harness


def test_unreachable_scheduler_is_not_a_server_continuation_substitute(
    documents: AdoptionDocuments,
) -> None:
    assert (
        "already accepted event-driven continuation orchestrator" in documents.harness
    )
    assert "do not substitute an unreachable scheduler" in documents.harness


def test_accepted_ao_scope_includes_conversation_authorized_intake(
    documents: AdoptionDocuments,
) -> None:
    for authority in (
        documents.docs_readme,
        documents.runbook,
        documents.ao_decision,
    ):
        assert "conversation" in authority
        assert "issue intake" in authority

    assert "task-specific worker start" in documents.ao_decision
    assert "automatic work discovery" in documents.runbook
    assert "1248e3473c86192aa17c48062bf001ea97482d4f" in documents.ao_decision
