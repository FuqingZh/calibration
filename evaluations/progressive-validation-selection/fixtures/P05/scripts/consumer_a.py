from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from check_event import run
from consumers.summary import summarize


def check() -> None:
    profile = {"id": "p1", "email": "ada@example.test", "display_name": "Ada"}
    if summarize(profile) != "Ada":
        raise ValueError("summary consumer must use display_name")


run("consumer_a", "summary-consumer", check)
