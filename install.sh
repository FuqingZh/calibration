#!/usr/bin/env bash
#
# Install calibration into the local Codex configuration.
#
# Managed targets:
#   ~/.codex/AGENTS.md
#   ~/.codex/skills/{calibration,retrospect,writing-docstrings}
#   ~/.codex/skills/{brainstorming,grilling,writing-great-skills,writing-plans,darwin-skill}

set -euo pipefail

DRY_RUN=false
FORCE=false
BACKUP=true

usage() {
  cat <<'EOF'
Usage: bash install.sh [--dry-run] [--force] [--no-backup]

Options:
  --dry-run    Show planned actions without modifying files.
  --force      Replace non-regular AGENTS targets or existing skill paths.
  --no-backup  Do not back up an existing AGENTS.md before replacing it.
  -h, --help   Show this help text.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      ;;
    --force)
      FORCE=true
      ;;
    --no-backup)
      BACKUP=false
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
CALIBRATION_ROOT="$SCRIPT_DIR"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
SKILLS_DIR="$CODEX_HOME/skills"
AGENTS_TARGET="$CODEX_HOME/AGENTS.md"
SKILL_SOURCE_ROOT="$CALIBRATION_ROOT/skills"
THIRDPARTY_SKILL_SOURCE_ROOT="$CALIBRATION_ROOT/thirdparty/skills"
TEMPLATE="$CALIBRATION_ROOT/codex/AGENTS.md.template"
MANAGED_SKILLS=(
  calibration
  retrospect
  writing-docstrings
)
MANAGED_THIRDPARTY_SKILLS=(
  brainstorming
  grilling
  writing-great-skills
  writing-plans
  darwin-skill
)
RETIRED_SKILLS=(
  engineering-design
  global-defaults
  naming
  personal-strategy
  project-docs
)
RETIRED_UNMANAGED_SKILLS=(
  grill-me
)

require_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    echo "Missing required file: $path" >&2
    exit 1
  fi
}

require_dir() {
  local path="$1"
  if [[ ! -d "$path" ]]; then
    echo "Missing required directory: $path" >&2
    exit 1
  fi
}

escape_sed_replacement() {
  printf '%s' "$1" | sed 's/[\/&]/\\&/g'
}

render_template() {
  local escaped_root
  escaped_root="$(escape_sed_replacement "$CALIBRATION_ROOT")"
  sed "s/{{CALIBRATION_ROOT}}/$escaped_root/g" "$TEMPLATE"
}

say() {
  printf '%s\n' "$*"
}

run() {
  if $DRY_RUN; then
    say "[dry-run] $*"
  else
    "$@"
  fi
}

ensure_parent_dirs() {
  run mkdir -p "$SKILLS_DIR"
}

install_skill_link() {
  local skill="$1"
  local source_root="$2"
  local target="$SKILLS_DIR/$skill"
  local source="$source_root/$skill"

  require_dir "$source"

  if [[ -L "$target" ]]; then
    local current
    current="$(readlink "$target")"
    if [[ "$current" == "$source" ]]; then
      say "Skill link already current: $target -> $source"
      return
    fi
  elif [[ ! -e "$target" ]]; then
    :
  elif ! $FORCE; then
    echo "Refusing to replace existing skill path without --force: $target" >&2
    exit 1
  fi

  if [[ -e "$target" || -L "$target" ]]; then
    run rm -rf "$target"
  fi
  run ln -s "$source" "$target"
  if $DRY_RUN; then
    say "Skill link planned: $target -> $source"
  else
    say "Skill link installed: $target -> $source"
  fi
}

remove_retired_skill_link() {
  local skill="$1"
  local target="$SKILLS_DIR/$skill"
  local retired_source="$SKILL_SOURCE_ROOT/$skill"

  if [[ ! -L "$target" ]]; then
    return
  fi

  local current
  current="$(readlink "$target")"
  if [[ "$current" != "$retired_source" ]]; then
    say "Retired skill left untouched: $target -> $current"
    return
  fi

  run rm -f "$target"
  if $DRY_RUN; then
    say "Retired skill removal planned: $target"
  else
    say "Retired skill removed: $target"
  fi
}

remove_retired_unmanaged_skill_path() {
  local skill="$1"
  local target="$SKILLS_DIR/$skill"

  if [[ ! -e "$target" && ! -L "$target" ]]; then
    return
  fi

  if ! $FORCE; then
    say "Retired unmanaged skill left untouched without --force: $target"
    return
  fi

  run rm -rf "$target"
  if $DRY_RUN; then
    say "Retired unmanaged skill removal planned: $target"
  else
    say "Retired unmanaged skill removed: $target"
  fi
}

backup_agents_target() {
  if ! $BACKUP || [[ ! -e "$AGENTS_TARGET" && ! -L "$AGENTS_TARGET" ]]; then
    return
  fi
  local stamp backup
  stamp="$(date +%Y%m%d%H%M%S)"
  backup="$AGENTS_TARGET.bak.$stamp"
  run cp -a "$AGENTS_TARGET" "$backup"
  if $DRY_RUN; then
    say "Backup planned for existing AGENTS.md: $backup"
  else
    say "Backed up existing AGENTS.md: $backup"
  fi
}

install_agents_file() {
  local tmp
  tmp="$(mktemp)"
  render_template > "$tmp"

  if [[ -f "$AGENTS_TARGET" ]] && cmp -s "$tmp" "$AGENTS_TARGET"; then
    rm -f "$tmp"
    say "AGENTS.md already current: $AGENTS_TARGET"
    return
  fi

  if [[ -e "$AGENTS_TARGET" || -L "$AGENTS_TARGET" ]]; then
    if [[ ! -f "$AGENTS_TARGET" && ! -L "$AGENTS_TARGET" ]] && ! $FORCE; then
      rm -f "$tmp"
      echo "Refusing to replace non-regular AGENTS target without --force: $AGENTS_TARGET" >&2
      exit 1
    fi
    backup_agents_target
  fi

  if $DRY_RUN; then
    say "[dry-run] write rendered AGENTS.md to $AGENTS_TARGET"
    rm -f "$tmp"
  else
    mv "$tmp" "$AGENTS_TARGET"
    say "AGENTS.md installed: $AGENTS_TARGET"
  fi
}

main() {
  require_file "$TEMPLATE"
  require_dir "$SKILL_SOURCE_ROOT"
  require_dir "$THIRDPARTY_SKILL_SOURCE_ROOT"

  say "Calibration root: $CALIBRATION_ROOT"
  say "Codex home: $CODEX_HOME"
  say "AGENTS target: $AGENTS_TARGET"
  say "Skill source root: $SKILL_SOURCE_ROOT"
  say "Third-party skill source root: $THIRDPARTY_SKILL_SOURCE_ROOT"
  say "Skills target root: $SKILLS_DIR"

  ensure_parent_dirs
  for skill in "${RETIRED_SKILLS[@]}"; do
    remove_retired_skill_link "$skill"
  done
  for skill in "${RETIRED_UNMANAGED_SKILLS[@]}"; do
    remove_retired_unmanaged_skill_path "$skill"
  done
  for skill in "${MANAGED_SKILLS[@]}"; do
    install_skill_link "$skill" "$SKILL_SOURCE_ROOT"
  done
  for skill in "${MANAGED_THIRDPARTY_SKILLS[@]}"; do
    install_skill_link "$skill" "$THIRDPARTY_SKILL_SOURCE_ROOT"
  done
  install_agents_file
}

main "$@"
