# Calibration Rename and Skill Architecture

Date: 2026-07-01

## Decision

Rename the engineering calibration system from `engineering-canon` to
`calibration`.

`calibration` is the product name, repository name, and default Codex skill
entrypoint. Skills are one presentation layer of the system, not the system
itself.

## Rationale

The old name, `engineering-canon`, was accurate but had a documentation-library
feel. It described a stable body of accepted guidance, but did not capture the
active purpose of the system: aligning engineering behavior with the user's
working standards.

The new name, `calibration`, better describes the system's role:

- calibrate agent behavior for coding, refactoring, debugging, naming, testing,
  and delivery
- calibrate engineering judgment against evidence, local contracts, and
  repository-specific rules
- keep reusable principles, references, and optional skills under one managed
  engineering calibration system
- emphasize method and judgment over a static rule archive

The name also leaves room for influences from field manuals, methodical
problem decomposition, parallax-style premise checking, and evidence-based
verification without making the repository sound like a cookbook or a generic
skills collection.

## Product Boundary

`calibration` is an engineering calibration system.

It includes:

- Codex skill entrypoints
- engineering principles
- naming references
- design and discipline references
- managed third-party or user-invoked skills
- installer logic for synchronizing local Codex state

It is not only:

- a prompt library
- a skill collection
- a static engineering handbook
- a Codex-only project

## Skill Boundary

The default model-invoked engineering skill should be named `calibration`.

It is the routing entrypoint for ordinary coding, refactoring, architecture,
module boundaries, interface shape, naming, API, CLI, testing, schema, and
documentation tasks.

Optional mode skills remain user-invoked. They should not be folded into the
default engineering entrypoint.

Examples:

- `brainstorming`: user-invoked exploratory design mode
- `grilling`: user-invoked adversarial stress-test mode
- `writing-great-skills`: user-invoked skill evaluation and editing reference

## Reference Architecture

The default skill should read only stable and necessary context first, then use
small routing indexes for topic-specific references.

Recommended shape:

```text
references/engineering/
  principles.md
  naming/
    README.md
    function.md
    type.md
    method.md
    cli.md
    variable.md
    loop.md
    schema.md
    artifact.md
    branch.md
  discipline/
    README.md
    refactor.md
    debugging.md
    verification.md
  design/
    README.md
    codebase.md
  docs_index.md
  docs/
```

`principles.md` remains the stable cross-project engineering source of truth.
It should stay short and should not absorb every operational detail.

Topic directories such as `naming/`, `discipline/`, and `design/` should expose
short routers and small files that can be loaded only when the current task
needs them.

## Naming Reference Split

The old single `references/engineering/naming.md` mixed several different
decision surfaces. It was hard for a model to read and obey during coding
because it required loading and retaining many unrelated naming concerns.

It has been split into:

- `naming/README.md`: router and scope
- `naming/function.md`: public and module-level function prefixes
- `naming/type.md`: class, dataclass, enum, config, plan, report, record,
  builder, buffer, and adapter names
- `naming/method.md`: public object method names
- `naming/cli.md`: CLI option names
- `naming/variable.md`: local variable, parameter, mapping, and structural role
  names
- `naming/loop.md`: loop, lambda, closure, and anonymous-function binders
- `naming/schema.md`: exported headers and public-facing schema fields
- `naming/artifact.md`: workflow artifact filename prefixes
- `naming/branch.md`: git branch names

This split is intended to improve progressive disclosure: the default skill
loads a naming router first, then only the relevant naming reference.

## Migration Policy

This rename is intentionally not backward-compatible.

Retired names should be removed rather than kept as aliases:

- `engineering-canon`
- `global-defaults`

The installer is the source of truth for synchronizing the local Codex home.
After migration, it should manage `calibration` and retire `global-defaults`
and `engineering-design`.

No old local directory symlink should be retained. No old skill symlink should
be retained. The README should mention the rename, but runtime behavior should
use only the new names.

## Execution Order

1. Document the rename and architecture decisions.
2. Rename the default skill from `global-defaults` to `calibration`.
3. Update `codex/AGENTS.md.template` to use `$calibration`.
4. Update `install.sh` to manage `calibration` and retire `global-defaults`
   and `engineering-design`.
5. Update README and references from `engineering-canon` to `calibration`.
6. Verify the installer with `bash install.sh --dry-run`.
7. Run the installer to refresh `/home/fqzhang/.codex`.
8. Commit and push the content migration.
9. Rename the remote repository to `calibration`.
10. Rename the local directory to `/home/fqzhang/project/calibration`.
11. Update the local git remote URL if the remote rename changes it.
12. Re-run the installer from the new local path and verify that no stale
    `global-defaults` skill remains.

## Open Follow-up

Create `discipline/` and `design/` routers in a follow-up pass. The accepted
target structure is clear, but the first migration should keep content changes
focused on the rename and naming-reference split.
