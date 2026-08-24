import json
from pathlib import Path

from check_event import run


def check() -> None:
    schema = json.loads(Path("schema/profile.schema.json").read_text())
    if schema["properties"].get("display_name") != {"type": "string"}:
        raise ValueError("display_name must be a string property")
    if "display_name" not in schema["required"]:
        raise ValueError("display_name must be required")
    if not {"id", "email"}.issubset(schema["properties"]):
        raise ValueError("existing public fields must remain")


run("schema_contract", "public-profile-schema", check)
