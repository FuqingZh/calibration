# calibration

Shared engineering guidance and agent skills for **Codex, Grok Build, and Pi**.

Calibration helps coding agents make cross-project decisions about naming,
architecture, verification, documentation, and delivery. It keeps one source of
guidance in this repository and links skills into each client's configuration.
Project-specific rules and executable checks remain the primary authority.

## Quick start

The installer requires Bash and GNU command-line utilities (`realpath`, `stat`,
`mv`, and related tools). Use Linux or WSL for installation;
macOS and native Windows installation have not been validated.

```bash
git clone https://github.com/FuqingZh/calibration.git
cd calibration

# Preview, then install for Codex.
bash install.sh --dry-run
bash install.sh
```

Install for several clients, or install only skill links:

```bash
bash install.sh --agent codex grok pi --dry-run
bash install.sh --agent codex grok pi
bash install.sh --agent pi --skills-only
```

`--agent all` selects all three clients. Client executables do not need to be on
PATH, so mise activation is not required. Restart or reload the client after
installation to discover the skills.

## Included skills

| Skill | Purpose | Invocation |
| --- | --- | --- |
| [calibration](skills/calibration/SKILL.md) | Cross-project engineering judgment and reference routing | When relevant |
| [writing-code-docs](skills/writing-code-docs/SKILL.md) | Document public APIs and caller/maintainer contracts | When relevant |
| [closeout](skills/closeout/SKILL.md) | Review the whole conversation and document gaps and unresolved work | Explicit only |
| [retrospect](skills/retrospect/SKILL.md) | Derive reusable lessons from completed work and evidence | Explicit only |
| [brainstorming](thirdparty/skills/brainstorming/SKILL.md) | Explore ambiguous problems and design choices | Explicit only |
| [grilling](thirdparty/skills/grilling/SKILL.md) | Stress-test a plan or decision | Explicit only |
| [teach](thirdparty/skills/teach/SKILL.md) | Teach a bounded topic in session-only or learning-workspace mode | Explicit only |

The last three skills are vendored third-party adaptations, included in the
standard profile. Their [sources](thirdparty/sources.tsv),
[local patches](thirdparty/PATCHES.md), and upstream license information are
tracked separately. Installation uses local files and does not download skills.
Archived skills are excluded from installation.

Use your client's native skill command, for example `$closeout` in Codex,
`/closeout` in Grok Build, or `/skill:closeout` in Pi. Closeout documents the
conversation and returns control without automatically archiving it.

## Installation behavior

| Client | Default configuration home | Override |
| --- | --- | --- |
| Codex | `$CODEX_HOME` or `~/.codex` | `--codex-home PATH` |
| Grok Build | `~/.grok` | `--grok-home PATH` |
| Pi | `$PI_CODING_AGENT_DIR` or `~/.pi/agent` | `--pi-home PATH` |

Each skill is a symlink under the selected home's `skills/` directory pointing
to this checkout. Keep the checkout at that path. Updating it updates linked
content; rerun the installer when the managed skill list or global template
changes. Repeated installation is safe for already-current links.

By default, the installer also installs global instructions:

- **Codex:** renders [the shared template](codex/AGENTS.md.template) as the entire
  `AGENTS.md`, backing up an existing file when it changes.
- **Grok and Pi:** updates a marked calibration block in `AGENTS.md`, retaining
  user instructions outside that block and backing up changed files.
- **`--skills-only`:** leaves global instructions untouched, including any
  previously installed calibration block.

All selected destinations are checked before writes. Existing conflicting
skill paths are rejected unless `--force` is supplied; that option can remove
existing files or directories, so inspect `--dry-run --force` first. A filesystem
failure during installation can leave an earlier target installed; resolve the
failure and rerun. See `bash install.sh --help` for all options.

The installer does not change client programs, mise, credentials, MCP servers,
plugins, or approval settings. It only adds a conditional reference to private
host guidance at `${XDG_CONFIG_HOME:-$HOME/.config}/calibration/AGENTS.md`;
that private file is not required for ordinary skill use.

### Optional AO worker profile

Agent Orchestrator (AO) is an optional integration. To install only first-party
skills and global instructions into an isolated Codex worker home:

```bash
bash install.sh --profile ao-worker --codex-home /absolute/path/to/worker-home
```

This profile requires an explicit home and supports only Codex. It does not
install or adopt AO. See the [AO integration guide](skills/calibration/references/agent-orchestrator-review-continuation.md)
for environment and ownership requirements.

## Development

Use Python 3.12+ and PDM to install the locked validation environment:

```bash
pdm sync --clean
pdm lock --check
pdm run check
```

The full gate runs Ruff, Pyright, rumdl, Markdown link checks, ShellCheck,
pytest with 100% line coverage for repository-owned Python tools, and skill
validation. Ruff uses the explicit stable baseline `E`, `F`,
`I`, `UP`, `B`, `SIM`, and `RUF`; preview rules are not enabled.
For a focused installer change:

```bash
pdm run lint-shell
pdm run test tests/test_install.py
pdm run validate-skills
```

Installer tests use isolated configuration homes. Select checks proportionally
to the changed behavior; [AGENTS.md](AGENTS.md) describes contribution and
validation requirements.

## Documentation and support

- [Documentation index](docs/README.md): current decisions, evaluation results,
  migration history, and implementation plans.
- [Engineering references](skills/calibration/references/principles.md): principles
  and the [skill router](skills/calibration/SKILL.md) for focused guidance.
- [Multi-client installation](docs/decisions/2026-09-24-multi-client-skill-installation.md):
  compatibility decisions, native discovery checks, and evidence limits.
- [Issues](https://github.com/FuqingZh/calibration/issues): bug reports and
  improvement proposals. Include the client version, command, and relevant
  sanitized output when reporting installation problems.

Optional GitHub integrations `github:gh-address-comments` and `github:gh-fix-ci`
are not vendored or managed by this installer. Use them when available for
ordinary PR feedback and CI diagnosis; otherwise use native platform tooling.

Behavioral prompts and evaluations support bounded conclusions under their
recorded conditions. Skill discovery and passing static checks do not establish
equal behavior across clients or a general improvement in model performance.
