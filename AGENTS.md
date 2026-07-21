# Repository Agent Map

## Authority

- Read `README.md` for the repository and installer contract.
- Read `docs/README.md` for current decisions and active implementation plans.
- Reusable engineering guidance lives under `references/engineering/`.
- First-party skills live under `skills/`; do not change behavioral cases as
  part of an unrelated implementation.

## Validation

Install the validation dependency with:

```bash
python -m pip install --requirement requirements.txt
```

Before delivery, run:

```bash
python -m unittest discover --start-directory tests --verbose
python scripts/validate_skills.py
bash -n install.sh
CODEX_HOME="$(mktemp -d)" bash install.sh --dry-run
git diff --check
```

Use an explicit temporary `CODEX_HOME`; never overwrite the user's active
Codex installation during validation.

## Review Guidelines

- Treat skill trigger expansion, instruction precedence, and routing changes
  as behavior changes, not documentation-only edits.
- Keep project-specific commands and checks in the owning repository rather
  than copying them into cross-project calibration guidance.
- Do not claim a workflow or harness improvement from static validation alone;
  require representative evidence for the stated improvement.
