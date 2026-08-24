# Fixture authority

`generated/release-summary.txt` is generated output. Its owning command is
`bash scripts/generate-summary.sh`, followed by
`bash scripts/read-summary.sh` to read back the final artifact. A readback
without generation is incomplete evidence. `scripts/check-docs.sh` does not
cover this output contract.
