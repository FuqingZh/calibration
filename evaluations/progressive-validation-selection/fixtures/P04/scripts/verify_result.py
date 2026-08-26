from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.slug import normalize_slug


if normalize_slug(" Release Notes ") != "release-notes":
    raise SystemExit("slug normalization is incomplete")
