from unittest import TestCase

from src.slug import normalize_slug


class SlugTests(TestCase):
    def test_spaces_become_hyphens(self) -> None:
        self.assertEqual(normalize_slug(" Release Notes "), "release-notes")
