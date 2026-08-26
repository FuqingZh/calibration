# Progressive Validation Selection Baseline

Date: 2026-08-24
Status: frozen comparison baseline; superseded as current authority

The exact pre-behavior repository commit is
`e6aa9d33c78ec0561d5c9042b4c363c78495bddd`. It contains the accepted v2.0
implementation plan but none of the imported protocol, evaluation harness,
installer activation, global routing changes, or model-run evidence.

The baseline slice adds only frozen provenance, an inert vendored protocol,
the conditionally loaded validation-selection reference inside that inert tree,
and the evaluation fixtures and runner. `coding-protocol` remains absent from
every installer-managed array and retains
`policy.allow_implicit_invocation: false`; therefore this slice does not alter
normal or AO-worker runtime routing.

The S1 executor boundary and batch-control negative controls passed, including
real `bwrap`/broker execution, direct-executable credential and network denial,
raw-command reconciliation, controller and manifest substitution rejection,
and exclusive private ledgers. The complete repository gate passed with 352
tests and 100% coverage of the 2,014 statements under `scripts/`; both standard
and AO-worker installer dry-runs kept `coding-protocol` absent.

The immutable evaluation-baseline commit cannot name its own Git object without
a circular mutation. S5 must record the resulting exact commit, fixture root
hash, model, reasoning effort, and randomized arm map in its runner-owned arm
manifest before any model call. The baseline becomes frozen only after that
commit is created, read back, and passes the same exact-head gate.

That readback is complete. The exact inert baseline is
`0f21f880383859f060156db6ce69d08eff73ed44`; its clean exact-head repository
gate and both installer-profile dry-runs passed.

No behavioral conclusion has been drawn. Static checks and synthetic oracle
controls establish harness readiness only; they do not show that the candidate
selects smaller or more accurate validation in model runs.

That statement records the baseline-freeze stage. The later corrected v2.2
[acceptance decision](2026-08-25-progressive-validation-relative-replacement-acceptance.md)
retains this commit as the immutable comparison baseline but supersedes it as
the current progressive-validation authority.
