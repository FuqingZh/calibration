from unittest import TestCase

from src.slug import normalize_slug


class NormalizeSlugTests(TestCase):
    def test_spaces_are_replaced_with_hyphens(self) -> None:
        self.assertEqual(normalize_slug(" Release Notes "), "release-notes")
