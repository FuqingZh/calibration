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


if __name__ == "__main__":
    unittest.main()
