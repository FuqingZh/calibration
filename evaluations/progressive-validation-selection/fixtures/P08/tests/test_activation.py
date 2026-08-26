import unittest
from src.activation import activation_state


class ActivationTest(unittest.TestCase):
    def test_remains_host_owned(self):
        self.assertEqual(activation_state(), "requires-authoritative-host")
