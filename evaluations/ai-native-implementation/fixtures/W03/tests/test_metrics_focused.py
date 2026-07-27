from unittest import TestCase

from src.metrics import mean_observed


class EmptyMetricsTests(TestCase):
    def test_empty_values_return_zero(self) -> None:
        self.assertEqual(mean_observed([]), 0.0)
