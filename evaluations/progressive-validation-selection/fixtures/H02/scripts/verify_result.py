import importlib
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
normalize = importlib.import_module("src.normalize").normalize


if normalize("  one   two  ") != "one two":
    raise SystemExit("normalization repair is incomplete")
