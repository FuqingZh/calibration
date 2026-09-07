# GPT-6 Skill Retirement And Snippet Scope

Status: implemented locally; no comparative improvement claim.

## Decision

Archive the runtime entry for `writing-great-skills`. Retain its vendored
source, license, and immutable upstream provenance. Both installer profiles
remove only links pointing to this repository's source; foreign links remain.

For `writing-code-docs`, standalone snippets use supplied implementation and
requirements plus the language fallback. They do not trigger workspace style
or caller discovery unless the user connects them to a repository. Repository
contract tracing remains active. Consolidate repeated guidance without changing
the caller-example or maintenance-boundary requirements.

## Evidence And Limits

The conversation's GPT-6 Astra medium screening attempted 64 runs: 52 were
valid, 10 timed out, and two failed with model-capacity errors. All valid runs
met their frozen criteria. Three complete writing-great-skills pairs showed
17.8%, 72.4%, and 73.9% more reported tokens with the guidance; both rule-edit
repetitions additionally read its glossary. Two standalone docstring pairs
showed 41.9% and 53.4% more tokens and an extra workspace-convention search.
These small synthetic cases support the scoped cleanup, not general claims
about skill quality, latency, or all GPT-6 workflows. Some answers disclosed
their condition, so the screening was not fully blinded.

The revised wording has static validation and a new behavioral test prompt;
the prompt is evaluation input, not evidence of an executed model comparison.
Raw runs remain in the user-selected private experiment workspace. No other
skills or AO safety contracts are retired by this decision.
