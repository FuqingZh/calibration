from __future__ import annotations

import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class RepositoryAdoptionContractTests(unittest.TestCase):
    def setUp(self) -> None:
        harness = (
            REPOSITORY_ROOT / "references/engineering/discipline/harness.md"
        ).read_text(encoding="utf-8")
        self.harness = " ".join(harness.split())
        self.skill = (REPOSITORY_ROOT / "skills/calibration/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.docs_readme = (REPOSITORY_ROOT / "docs/README.md").read_text(
            encoding="utf-8"
        )
        self.runbook = (
            REPOSITORY_ROOT
            / "docs/runbooks/agent-orchestrator-review-continuation.md"
        ).read_text(encoding="utf-8")
        self.ao_decision = (
            REPOSITORY_ROOT
            / "docs/decisions/2026-07-23-ao-review-continuation-adoption.md"
        ).read_text(encoding="utf-8")

    def test_adoption_starts_from_evidence_and_allows_no_change(self) -> None:
        self.assertIn("## Repository Capability Adoption", self.harness)
        self.assertIn("repository capability assessment, minimal adoption", self.skill)
        self.assertIn("present, missing, or not applicable", self.harness)
        self.assertIn("named tools and artifacts as possible means", self.harness)
        self.assertIn("Leave an adequate capability unchanged", self.harness)
        self.assertIn("Do not assign a generic maturity score", self.harness)
        self.assertIn("a library or CLI does not need a UI", self.harness)

    def test_orchestrator_is_an_optional_engine_not_global_authority(self) -> None:
        self.assertIn("such as Symphony, over a custom scheduler", self.harness)
        self.assertIn("it does not own repository authority", self.harness)
        self.assertIn("one bounded representative task", self.harness)
        self.assertIn("do not turn local labels, deployment topology", self.harness)

    def test_authorized_implementation_uses_an_adopted_orchestrator(self) -> None:
        self.assertIn("## Implementation Task Intake", self.harness)
        self.assertIn("execute an accepted plan", self.harness)
        self.assertIn("route it to that orchestrator without requiring the user", self.harness)
        self.assertIn("start a task-specific worker", self.harness)
        self.assertIn("claim or restore the owning worker", self.harness)

    def test_planning_only_does_not_start_implementation(self) -> None:
        self.assertIn("remains read-only unless it also authorizes the change", self.harness)
        self.assertIn("Use only an already accepted repository, host, identity", self.harness)
        self.assertIn("normal isolated-Worktree delivery path", self.harness)

    def test_unreachable_scheduler_is_not_a_server_continuation_substitute(
        self,
    ) -> None:
        self.assertIn("already accepted event-driven continuation orchestrator", self.harness)
        self.assertIn("do not substitute an unreachable scheduler", self.harness)

    def test_accepted_ao_scope_includes_conversation_authorized_intake(
        self,
    ) -> None:
        for authority in (self.docs_readme, self.runbook, self.ao_decision):
            self.assertIn("conversation", authority)
            self.assertIn("issue intake", authority)

        self.assertIn("task-specific worker start", self.ao_decision)
        self.assertIn("automatic work discovery", self.runbook)
        self.assertIn("1248e3473c86192aa17c48062bf001ea97482d4f", self.ao_decision)


if __name__ == "__main__":
    unittest.main()
