from unittest import TestCase

from src.metrics import mean_observed


class MetricsSmokeTests(TestCase):
    def test_missing_values_are_ignored(self) -> None:
        self.assertEqual(mean_observed([2.0, None, 4.0]), 3.0)
