import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from consumers.export import export_row
from consumers.summary import summarize


profile = {"id": "p1", "email": "ada@example.test", "display_name": "Ada"}
schema = json.loads(Path("schema/profile.schema.json").read_text())
if schema["properties"].get("display_name") != {"type": "string"} or "display_name" not in schema["required"]:
    raise SystemExit("public schema does not require display_name")
if summarize(profile) != "Ada" or export_row(profile) != ["p1", "Ada", "ada@example.test"]:
    raise SystemExit("bounded consumers do not implement display_name")
