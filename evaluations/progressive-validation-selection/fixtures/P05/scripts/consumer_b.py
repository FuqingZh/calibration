from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from check_event import run
from consumers.export import export_row


def check() -> None:
    profile = {"id": "p1", "email": "ada@example.test", "display_name": "Ada"}
    if export_row(profile) != ["p1", "Ada", "ada@example.test"]:
        raise ValueError("export consumer must include display_name")


run("consumer_b", "export-consumer", check)
