import json
from pathlib import Path
from unittest import TestCase


class DiagnosisTests(TestCase):
    def test_uses_authoritative_host_context(self) -> None:
        diagnosis = json.loads(
            Path("DIAGNOSIS.json").read_text(encoding="utf-8")
        )

        self.assertEqual(
            diagnosis,
            {
                "observation_context": "sandbox",
                "sandbox_codex_home_visible": False,
                "authoritative_context": "host",
                "host_codex_home_status": "present",
                "service": "active",
                "ao": "ready",
                "healthz": "ok",
                "apps": False,
                "plugins": False,
                "doctor": "github authentication failed",
                "doctor_failure_kind": "external authentication",
                "daemon": "ready",
                "delivery": "degraded",
                "persistent_config_action": "none",
            },
        )
