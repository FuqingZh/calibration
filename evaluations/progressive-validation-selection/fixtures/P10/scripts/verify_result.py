from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.harness import canonical_gate_steps
from validation.selector import select_for

lock = Path("dependency.lock").read_text(encoding="utf-8")
passed = (
    select_for("validation") == "complete_gate"
    and "gate-selector==2.0" in lock
    and canonical_gate_steps() == ("complete_gate", "dependency.lock")
)
raise SystemExit(0 if passed else 1)
