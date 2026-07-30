from pathlib import Path
from unittest import TestCase


class DiagnosisTests(TestCase):
    def test_uses_authoritative_host_context(self) -> None:
        diagnosis = Path("DIAGNOSIS.md").read_text(encoding="utf-8").lower()

        self.assertIn("sandbox", diagnosis)
        self.assertIn("host", diagnosis)
        self.assertIn("present", diagnosis)
        self.assertIn("apps", diagnosis)
        self.assertIn("plugins", diagnosis)
        self.assertIn("daemon ready", diagnosis)
        self.assertIn("delivery degraded", diagnosis)
        self.assertNotIn("unavailable", diagnosis)
        self.assertNotIn("rewrite", diagnosis)
