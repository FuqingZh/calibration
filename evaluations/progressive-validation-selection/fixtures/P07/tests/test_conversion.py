import unittest
from src.conversion import to_milliseconds


class ConversionTest(unittest.TestCase):
    def test_seconds_to_milliseconds(self):
        self.assertEqual(to_milliseconds(3), 3000)
