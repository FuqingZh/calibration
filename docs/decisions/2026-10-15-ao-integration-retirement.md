# Retire the AO integration

## Decision

On 2026-10-15, the user authorized removing calibration's active Agent
Orchestrator integration. Calibration's 44 recorded sessions were terminated,
its AO worktree directory was empty, and the 14 remaining remote `ao/`
branches were deleted with expected-head leases and an atomic push. Remote
readback confirmed zero remaining `ao/` branches.

Calibration now uses repository-native engineering and pull-request tooling.
It no longer owns AO onboarding, lifecycle routing, worker installation, or
continuation policy. This retirement does not uninstall AO, unregister its
projects, terminate other projects' sessions, or change host services.

## Compatibility

- Remove `scripts/adopt_ao_repository.py` and its dedicated tests. Historical
  invocations require an older Git revision and are not supported by this tree.
- Remove the installer `ao-worker` profile. The default and explicit
  `--profile standard` continue to install the normal client skill set.
  `--profile ao-worker` fails with exit code 2 before any destination writes,
  including when `--force` is supplied. Do not silently install the broader
  standard skill set into an old worker home.
- Remove AO routing from the skill, repository map, generated global
  instructions, and harness. Preserve generic single-writer, ownership transfer,
  runtime release, host-state verification, and shared-storage boundaries.
- Archive the [former guide](../archive/ao-integration-retired-2026-10-15.md)
  outside installed skills. Historical Markdown links now resolve to the archive.
  Frozen evaluation bundles, result hashes, and invocation metadata stay intact.
- Keep mixed evaluation and installer tests that cover supported behavior;
  retire dedicated AO cases and generalize ownership and host-diagnosis cases.
  Case IDs remain stable, including gaps left by retired cases.

Installed skills that link to this checkout change with the source. Generated
client `AGENTS.md` files must also be refreshed; otherwise they retain a pointer
to the removed guide. Refresh only the authorized client homes. Historical
worker homes and private host configuration remain under their existing owner.

## Validation

The completion boundary is a passing full repository gate, an isolated installer
dry-run, supported-client installer tests, and readback of refreshed global
instructions. Static checks establish packaging, links, and executable installer
contracts. They do not establish model behavior or a workflow performance gain.

Host uninstall, AO runtime release, downstream repository migration, and remote
CI or merge are separate outcomes and are not implied by local validation.

Validated locally on Python 3.13.11 with the locked environment:

- `pdm lock --check` and `pdm run check` passed: 486 tests, 100% script line
  coverage, plus lint, format, strict type checking, shell checks, Markdown links,
  and skill validation.
- An isolated installer dry-run left its target home absent. Supported-client
  installation, repeat installation, removed-profile zero-write failure, and
  configuration preservation are covered by executable installer tests.
- The personal Codex global instructions were backed up, refreshed, and read
  back as an exact match to the rendered template with no retired guide pointer.
  Grok had no instruction file; Pi had no retired pointer and was left unchanged
  after the test recovery described below.

During the first full run, a migrated invalid-argument test accidentally selected
the valid standard Pi profile. Its original instruction file was restored
byte-for-byte from the installer backup, and the seven newly created skill links
were removed. The test now uses an invalid profile and temporary HOME and Pi
home paths. The corrected full run passed. The recovery backup remains available
outside the repository. This incident does not change historical evaluation
results or establish a broader runtime-isolation claim.
