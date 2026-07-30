"""Print the fixture's authoritative host-state readback."""

from pathlib import Path


print(Path("host-state.json").read_text(encoding="utf-8"), end="")
