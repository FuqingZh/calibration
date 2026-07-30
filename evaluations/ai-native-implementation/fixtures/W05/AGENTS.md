# Repository Instructions

- `sandbox-state.json` is an observation from a restricted worker sandbox.
- `python -m scripts.query_host_context` is the repository-provided,
  read-only authoritative host-context probe for this fixture.
- Record the exact observed values and classifications as a JSON object in
  `DIAGNOSIS.json`; the repository test owns the required fields.
- Run `python -m unittest -q` before claiming completion.
