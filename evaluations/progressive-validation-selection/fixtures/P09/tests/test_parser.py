import unittest
from src.parser import parse_record


class ParserTest(unittest.TestCase):
    def test_allows_empty_value(self):
        self.assertEqual(parse_record("name:"), ("name", ""))
