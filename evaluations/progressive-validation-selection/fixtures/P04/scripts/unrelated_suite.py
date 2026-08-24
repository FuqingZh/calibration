import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from check_event import run


def check() -> None:
    result = unittest.defaultTestLoader.loadTestsFromName("tests.test_unrelated")
    if not unittest.TextTestRunner(verbosity=0).run(result).wasSuccessful():
        raise ValueError("unrelated suite failed")


run("unrelated_suite", "unrelated-notification-suite", check)
