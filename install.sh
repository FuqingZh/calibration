#!/usr/bin/env bash
#
# Install calibration into a Codex configuration home.

set -euo pipefail

DRY_RUN=false
FORCE=false
BACKUP=true
PROFILE=standard
CLI_CODEX_HOME_SET=false
CLI_CODEX_HOME=

usage() {
  cat <<'EOF'
Usage: bash install.sh [OPTIONS]

Options:
  --profile PROFILE   Install profile: standard (default) or ao-worker.
  --codex-home PATH   Override CODEX_HOME. Required for ao-worker.
  --dry-run           Show planned actions without modifying files.
  --force             Replace non-regular AGENTS targets or skill paths.
  --no-backup         Do not back up AGENTS.md before replacing it.
  -h, --help          Show this help text.
EOF
}

fail_usage() {
  echo "$1" >&2
  usage >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      [[ $# -ge 2 ]] || fail_usage "--profile requires a value"
      [[ "$2" != --* ]] || fail_usage "--profile requires a value"
      PROFILE="$2"
      shift
      ;;
    --codex-home)
      [[ $# -ge 2 ]] || fail_usage "--codex-home requires a non-empty path"
      [[ "$2" != --* ]] ||
        fail_usage "--codex-home requires a non-empty path"
      CLI_CODEX_HOME="$2"
      CLI_CODEX_HOME_SET=true
      shift
      ;;
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
      fail_usage "Unknown option: $1"
      ;;
  esac
  shift
done

case "$PROFILE" in
  standard|ao-worker) ;;
  *) fail_usage "Unknown profile: $PROFILE" ;;
esac

if [[ "$PROFILE" == "ao-worker" ]] && ! $CLI_CODEX_HOME_SET; then
  fail_usage "ao-worker requires an explicit --codex-home PATH"
fi
if $CLI_CODEX_HOME_SET; then
  [[ -n "$CLI_CODEX_HOME" ]] ||
    fail_usage "--codex-home requires a non-empty path"
  [[ "$CLI_CODEX_HOME" == /* ]] ||
    fail_usage "--codex-home must be an absolute path"
  CODEX_HOME="$CLI_CODEX_HOME"
elif [[ -n "${CODEX_HOME:-}" ]]; then
  :
elif [[ -n "${HOME:-}" ]]; then
  CODEX_HOME="$HOME/.codex"
else
  fail_usage "Cannot derive default Codex home: HOME and CODEX_HOME are unset"
fi
[[ -n "$CODEX_HOME" ]] || fail_usage "Codex home must not be empty"
SELECTED_CODEX_HOME="$CODEX_HOME"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
CALIBRATION_ROOT="$(realpath -m -- "$SCRIPT_DIR")"
LEXICAL_CODEX_HOME="$(realpath -m -s -- "$CODEX_HOME")"
CODEX_HOME="$(realpath -m -- "$CODEX_HOME")"
[[ "$CODEX_HOME" != "/" ]] || fail_usage "Refusing to use / as Codex home"
case "$CODEX_HOME" in
  "$CALIBRATION_ROOT"|"$CALIBRATION_ROOT"/*)
    fail_usage "Codex home must not equal or be inside the calibration checkout"
    ;;
esac
case "$CALIBRATION_ROOT" in
  "$CODEX_HOME"/*)
    fail_usage "Codex home must not contain the calibration checkout"
    ;;
esac
if [[ "$PROFILE" == "ao-worker" ]]; then
  if [[ "$LEXICAL_CODEX_HOME" != "$CODEX_HOME" ]]; then
    fail_usage "ao-worker Codex home path must not traverse a symlink"
  fi
  if [[ -e "$SELECTED_CODEX_HOME" && ! -d "$SELECTED_CODEX_HOME" ]]; then
    fail_usage "ao-worker Codex home must be a directory"
  fi
  if [[ -d "$SELECTED_CODEX_HOME" ]]; then
    home_mode="$(stat -c '%a' -- "$SELECTED_CODEX_HOME")"
    if (( (8#$home_mode & 8#077) != 0 )); then
      fail_usage "ao-worker Codex home must not grant group or other permissions"
    fi
  fi
fi

if [[ -n "${XDG_CONFIG_HOME:-}" ]]; then
  [[ "$XDG_CONFIG_HOME" == /* ]] ||
    fail_usage "XDG_CONFIG_HOME must be an absolute path"
  HOST_CONFIG_ROOT="$(realpath -m -- "$XDG_CONFIG_HOME")"
else
  [[ "${HOME:-}" == /* ]] || fail_usage "HOME must be an absolute path"
  HOST_CONFIG_ROOT="$(realpath -m -- "$HOME/.config")"
fi

SKILLS_DIR="$CODEX_HOME/skills"
AGENTS_TARGET="$CODEX_HOME/AGENTS.md"
SKILL_SOURCE_ROOT="$CALIBRATION_ROOT/skills"
THIRDPARTY_SKILL_SOURCE_ROOT="$CALIBRATION_ROOT/thirdparty/skills"
TEMPLATE="$CALIBRATION_ROOT/codex/AGENTS.md.template"
HOST_AUTHORITY="$HOST_CONFIG_ROOT/calibration/AGENTS.md"
MANAGED_SKILLS=(
  calibration
  retrospect
  writing-code-docs
)
MANAGED_THIRDPARTY_SKILLS=(
  brainstorming
  grilling
  writing-great-skills
)
RETIRED_SKILLS=(
  engineering-design
  global-defaults
  naming
  personal-strategy
  project-docs
  writing-docstrings
)
RETIRED_THIRDPARTY_SKILLS=(
  writing-plans
  darwin-skill
)
RETIRED_UNMANAGED_SKILLS=(
  grill-me
)

require_file() {
  [[ -f "$1" ]] || {
    echo "Missing required file: $1" >&2
    exit 1
  }
}

require_dir() {
  [[ -d "$1" ]] || {
    echo "Missing required directory: $1" >&2
    exit 1
  }
}

escape_sed_replacement() {
  printf '%s' "$1" | sed 's/[\/&]/\\&/g'
}

render_template() {
  local escaped_root escaped_host_authority
  escaped_root="$(escape_sed_replacement "$CALIBRATION_ROOT")"
  escaped_host_authority="$(escape_sed_replacement "$HOST_AUTHORITY")"
  sed \
    -e "s/{{CALIBRATION_ROOT}}/$escaped_root/g" \
    -e "s/{{HOST_AUTHORITY}}/$escaped_host_authority/g" \
    "$TEMPLATE"
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

install_skill_link() {
  local skill="$1" source_root="$2"
  local target="$SKILLS_DIR/$skill" source="$source_root/$skill"
  require_dir "$source"

  if [[ -L "$target" ]] && [[ "$(readlink "$target")" == "$source" ]]; then
    say "Skill link already current: $target -> $source"
    return
  fi
  if [[ -e "$target" || -L "$target" ]]; then
    if [[ ! -L "$target" ]] && ! $FORCE; then
      echo "Refusing to replace existing skill path without --force: $target" >&2
      exit 1
    fi
    run rm -rf "$target"
  fi
  run ln -s "$source" "$target"
  if $DRY_RUN; then
    say "Skill link planned: $target -> $source"
  else
    say "Skill link installed: $target -> $source"
  fi
}

remove_owned_skill_link() {
  local skill="$1" source_root="$2" label="$3"
  local target="$SKILLS_DIR/$skill" owned_source="$source_root/$skill"
  [[ -L "$target" ]] || return 0
  if [[ "$(readlink "$target")" != "$owned_source" ]]; then
    say "$label left untouched: $target -> $(readlink "$target")"
    return
  fi
  run rm -f "$target"
  if $DRY_RUN; then
    say "$label removal planned: $target"
  else
    say "$label removed: $target"
  fi
}

remove_retired_unmanaged_skill_path() {
  local target="$SKILLS_DIR/$1"
  [[ -e "$target" || -L "$target" ]] || return 0
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
    return 0
  fi
  local backup
  backup="$AGENTS_TARGET.bak.$(date +%Y%m%d%H%M%S)"
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
  render_template >"$tmp"
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
  if [[ "$PROFILE" == "standard" ]]; then
    require_dir "$THIRDPARTY_SKILL_SOURCE_ROOT"
  fi

  say "Profile: $PROFILE"
  say "Calibration root: $CALIBRATION_ROOT"
  say "Codex home: $CODEX_HOME"
  say "Private host authority: $HOST_AUTHORITY"
  say "Skills target root: $SKILLS_DIR"

  if [[ "$PROFILE" == "ao-worker" ]]; then
    if [[ ! -d "$CODEX_HOME" ]]; then
      run install -d -m 0700 "$CODEX_HOME"
    fi
    if [[ ! -e "$SKILLS_DIR" ]]; then
      run install -d -m 0700 "$SKILLS_DIR"
    elif [[ ! -d "$SKILLS_DIR" ]]; then
      echo "AO worker skills target is not a directory: $SKILLS_DIR" >&2
      exit 1
    fi
  else
    run mkdir -p "$SKILLS_DIR"
  fi
  for skill in "${RETIRED_SKILLS[@]}"; do
    remove_owned_skill_link "$skill" "$SKILL_SOURCE_ROOT" "Retired skill"
  done
  for skill in "${MANAGED_SKILLS[@]}"; do
    install_skill_link "$skill" "$SKILL_SOURCE_ROOT"
  done

  if [[ "$PROFILE" == "standard" ]]; then
    for skill in "${RETIRED_THIRDPARTY_SKILLS[@]}"; do
      remove_owned_skill_link \
        "$skill" "$THIRDPARTY_SKILL_SOURCE_ROOT" "Retired skill"
    done
    for skill in "${RETIRED_UNMANAGED_SKILLS[@]}"; do
      remove_retired_unmanaged_skill_path "$skill"
    done
    for skill in "${MANAGED_THIRDPARTY_SKILLS[@]}"; do
      install_skill_link "$skill" "$THIRDPARTY_SKILL_SOURCE_ROOT"
    done
  else
    for skill in "${RETIRED_THIRDPARTY_SKILLS[@]}"; do
      remove_owned_skill_link \
        "$skill" "$THIRDPARTY_SKILL_SOURCE_ROOT" "Retired third-party skill"
    done
    for skill in "${MANAGED_THIRDPARTY_SKILLS[@]}"; do
      remove_owned_skill_link \
        "$skill" "$THIRDPARTY_SKILL_SOURCE_ROOT" "Managed third-party skill"
    done
  fi
  install_agents_file
}

main "$@"
