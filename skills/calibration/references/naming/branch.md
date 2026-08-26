# Branch Naming

Use branch names to encode ownership, change intent, affected scope, and the
concrete review target.

Codex-created branches:

```text
codex/<type>/<scope>-<short-topic>
```

Human-created branches:

```text
<type>/<scope>-<short-topic>
```

Examples:

```text
codex/fix/bio-plot-chat-fallback-timeout
docs/calibration-branch-policy
feat/bioextract-kegg-resource-builder
hotfix/bio-plot-nginx-routing
```

## Change Types

Use `type` to classify the intent of the change, not the touched file type or
the amount of work.

| Type | Use |
| --- | --- |
| `feat` | new capability, workflow, API, CLI option, supported behavior, or user-visible feature |
| `fix` | broken, incorrect, regressed, or unintended behavior |
| `docs` | documentation, comments, examples, or engineering guidance without runtime behavior changes |
| `refactor` | internal structure changes that preserve public behavior |
| `test` | tests, fixtures, test helpers, or test infrastructure without production behavior changes |
| `chore` | maintenance work that does not fit another type and does not change user-facing behavior |
| `ci` | CI, deployment automation, build pipelines, or repository automation |
| `perf` | performance improvement with preserved behavior |
| `revert` | revert of a previous change |
| `hotfix` | expedited production fix branch when repository policy allows a hotfix path |

Use `!` in PR titles or commit messages, not as a separate branch type, when a
change is breaking.

## Scope and Topic

- `scope` names the repo, product, module, or stable subsystem.
- `short-topic` uses lowercase kebab-case and names the concrete review target.
- Prefer concrete nouns over vague verbs.
- Avoid non-descriptive names such as `wip`, `tmp`, `test`, `fix`, `update`,
  `new`, or `my-branch`.
- Add issue ids, task ids, or dates only when they are part of an external
  tracking contract.

Repositories may define additional branch types only when the type changes
routing, review ownership, release handling, or automation.
