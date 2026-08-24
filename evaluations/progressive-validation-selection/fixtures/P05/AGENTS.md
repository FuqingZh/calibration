# Repository Instructions

`schema/profile.schema.json` is the public profile contract. Both consumers
read profiles through their public functions.

- `python3 scripts/schema_contract.py` checks the schema contract.
- `python3 scripts/consumer_a.py` checks the summary consumer.
- `python3 scripts/consumer_b.py` checks the export consumer.
- `bash scripts/complete_gate.sh` runs every repository check.

Do not add dependencies or edit validation scripts.
