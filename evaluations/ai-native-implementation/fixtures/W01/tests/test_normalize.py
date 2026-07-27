from unittest import TestCase

from src.normalize import normalize_label


class NormalizeLabelTests(TestCase):
    def test_strips_and_lowercases(self) -> None:
        self.assertEqual(normalize_label("  Sample A  "), "sample a")
