# Repository Instructions

- Changes to the validation selector, lockfile authority, or harness cross the
  fixture-wide gate seam.
- After such a change, run `python scripts/check.py complete_gate`. A selector
  unit check is not sufficient evidence for this integration contract.
- These commands and their precedence are repository-local instructions.
