import unittest
from pathlib import Path

from scripts.harness import canonical_gate_steps
from validation.selector import select_for


class CompleteGateIntegrationTest(unittest.TestCase):
    def test_validation_changes_select_complete_gate(self):
        self.assertEqual(select_for("validation"), "complete_gate")

    def test_lockfile_tracks_gate_selector_authority(self):
        self.assertIn("gate-selector==2.0", Path("dependency.lock").read_text())

    def test_harness_runs_complete_gate_and_lockfile_check(self):
        self.assertEqual(canonical_gate_steps(), ("complete_gate", "dependency.lock"))
