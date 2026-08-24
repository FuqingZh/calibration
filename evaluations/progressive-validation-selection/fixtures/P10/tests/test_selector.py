import unittest
from validation.selector import select_for


class SelectorTest(unittest.TestCase):
    def test_leaf_changes_select_focused_test(self):
        self.assertEqual(select_for("leaf"), "focused_test")
