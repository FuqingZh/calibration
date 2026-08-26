import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from check_event import run


def check() -> None:
    result = unittest.defaultTestLoader.loadTestsFromName("tests.test_slug")
    if not unittest.TextTestRunner(verbosity=0).run(result).wasSuccessful():
        raise ValueError("slug normalization test failed")


run("focused_test", "slug-normalization", check)
