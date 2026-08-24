import unittest
from src.greeting import format_greeting


class GreetingTest(unittest.TestCase):
    def test_formats_complete_greeting(self):
        self.assertEqual(format_greeting("Ada"), "Hello, Ada!")
