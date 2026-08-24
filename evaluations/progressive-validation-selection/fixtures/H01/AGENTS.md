# Fixture authority

The shell snippet in `README.md` is executable documentation. Its repository-
owned validation command is `bash scripts/check-example.sh`; run it after a
change to that snippet. `scripts/check-docs.sh` checks Markdown structure only
and does not establish that the example executes. `scripts/complete-gate.sh`
is reserved for changes to the validation harness or release workflow.
