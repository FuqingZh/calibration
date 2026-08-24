from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.activation import activation_state

raise SystemExit(0 if activation_state() == "requires-authoritative-host" else 1)
