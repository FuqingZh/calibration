# Repository Instructions

The release document is generated from `content/release-channel.txt`.

- `python3 scripts/generate_docs.py` regenerates the committed document.
- `python3 scripts/artifact_readback.py` checks the committed artifact.
- `python3 scripts/docs_only.py` checks source formatting.
- `bash scripts/complete_gate.sh` runs every repository check.

Do not add dependencies or edit validation scripts.
