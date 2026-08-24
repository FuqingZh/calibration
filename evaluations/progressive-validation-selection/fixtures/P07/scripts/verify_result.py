from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.conversion import to_milliseconds

raise SystemExit(0 if to_milliseconds(3) == 3000 else 1)
