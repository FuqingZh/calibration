from pathlib import Path

from src.resource_publication import publish


def test_publish() -> None:
    destination, metadata = publish(Path("out.db"), "K1")
    assert destination.name == "out.db"
    assert metadata == {"resource": "example", "key": "K1"}
