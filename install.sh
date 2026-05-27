#!/usr/bin/env bash
#
# Install engineering-canon into the local Codex configuration.
#
# Managed targets:
#   ~/.codex/AGENTS.md
#   ~/.codex/skills/global-defaults

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
CANON_ROOT="$SCRIPT_DIR"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
SKILLS_DIR="$CODEX_HOME/skills"
AGENTS_TARGET="$CODEX_HOME/AGENTS.md"
SKILL_TARGET="$SKILLS_DIR/global-defaults"
SKILL_SOURCE="$CANON_ROOT/global-defaults"
TEMPLATE="$CANON_ROOT/codex/AGENTS.md.template"

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
  escaped_root="$(escape_sed_replacement "$CANON_ROOT")"
  sed "s/{{ENGINEERING_CANON_ROOT}}/$escaped_root/g" "$TEMPLATE"
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
  if [[ -L "$SKILL_TARGET" ]]; then
    local current
    current="$(readlink "$SKILL_TARGET")"
    if [[ "$current" == "$SKILL_SOURCE" ]]; then
      say "Skill link already current: $SKILL_TARGET -> $SKILL_SOURCE"
      return
    fi
  elif [[ ! -e "$SKILL_TARGET" ]]; then
    :
  elif ! $FORCE; then
    echo "Refusing to replace existing skill path without --force: $SKILL_TARGET" >&2
    exit 1
  fi

  if [[ -e "$SKILL_TARGET" || -L "$SKILL_TARGET" ]]; then
    run rm -rf "$SKILL_TARGET"
  fi
  run ln -s "$SKILL_SOURCE" "$SKILL_TARGET"
  if $DRY_RUN; then
    say "Skill link planned: $SKILL_TARGET -> $SKILL_SOURCE"
  else
    say "Skill link installed: $SKILL_TARGET -> $SKILL_SOURCE"
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
  require_dir "$SKILL_SOURCE"

  say "Engineering canon root: $CANON_ROOT"
  say "Codex home: $CODEX_HOME"
  say "AGENTS target: $AGENTS_TARGET"
  say "Skill target: $SKILL_TARGET"

  ensure_parent_dirs
  install_skill_link
  install_agents_file
}

main "$@"
