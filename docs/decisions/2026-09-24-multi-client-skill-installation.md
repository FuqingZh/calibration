# Multi-client skill installation

## Decision

The installer supports `--agent codex grok pi` (or `--agent all`) with one
source checkout and individual skill symlinks per client. No client binary,
package manager, credential, MCP, or permission configuration is changed.
The existing no-argument Codex installation and `ao-worker` profile remain
compatible; `ao-worker` accepts only Codex.

`--skills-only` leaves global instruction files untouched. Otherwise Codex
retains whole-file template rendering, while Grok and Pi receive the same
shared guidance inside a managed block in their global AGENTS.md. Existing
text outside the block is retained. The rendered Grok/Pi text uses the skill
name without Codex's dollar invocation notation.

Targets default to `CODEX_HOME` or `~/.codex`, `~/.grok`, and
`PI_CODING_AGENT_DIR` or `~/.pi/agent`. Explicit home flags override defaults.
The installer does not detect clients through PATH, so mise activation is not
required. All targets are preflighted before writes; overlapping homes and
malformed instruction blocks fail before installation. This is not an atomic
multi-directory transaction: an application-time filesystem error can leave
an earlier target installed. Rerunning repairs a partial installation.

Explicit-only skills retain OpenAI metadata and add top-level
`disable-model-invocation: true` for Pi/Grok. The validator accepts a boolean
at that location and rejects disagreement with the OpenAI invocation policy;
misplaced fields remain rejected. Archived skills remain excluded.

## Sources

- [Agent Skills specification](https://agentskills.io/specification)
- [Vercel skills installer](https://github.com/vercel-labs/skills)
- [Grok skill discovery and invocation](https://docs.x.ai/build/features/skills-plugins-marketplaces)
- [Pi skill discovery and invocation](https://pi.dev/docs/latest/skills)

This design uses direct links to the maintained checkout. It does not introduce
a package-manager-owned copy or synchronize credentials between machines.

## Validation

Isolated checks used the installed Grok 1.0.41, Pi 0.87.1, and Codex 0.156.0:

- Grok `inspect --json` discovered all seven managed skills and global AGENTS.md.
- Pi's native skill and context loaders discovered all seven skills and global
  AGENTS.md without diagnostics. Its prompt formatter excluded the five
  explicit-only skills from automatic selection.
- Codex app-server `skills/list` discovered all seven managed user skills
  through their symlinks, in addition to its system skills.
- Installer tests cover original Codex behavior, multi-target preflight,
  repeat installation, block refresh, user text preservation, malformed blocks,
  skills-only installation, home overrides, and directory conflicts.
- Skill validator tests cover cross-client metadata type and policy mismatch.

The full repository check reached 100% Python line coverage, with 565 tests
passing and six unrelated sandbox/FIFO tests failing. All six also failed in
an isolated archive of the unchanged HEAD with the same installed Codex:
its sandbox could not resolve `/output/tmp`. No test was disabled or changed
to conceal these failures. Two additional installer obstruction tests were
subsequently added and passed in the focused suite.

This evidence verifies installation and resource discovery. Grok's inspect
output does not expose its automatic-invocation flag; that setting is supported
by its documented contract, without a live model invocation test. No comparative
model-quality claim or universal compatibility claim is made. Client-specific
tools referenced by skill bodies still depend on the client environment.
