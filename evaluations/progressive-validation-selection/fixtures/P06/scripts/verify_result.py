from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.greeting import format_greeting

readme = Path("README.md").read_text(encoding="utf-8")
raise SystemExit(0 if format_greeting("Ada") == "Hello, Ada!" and "Hello, Ada!" in readme else 1)
