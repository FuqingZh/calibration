#!/usr/bin/env bash
#
# Install calibration skills and instructions into selected agent homes.

set -euo pipefail

DRY_RUN=false
FORCE=false
BACKUP=true
PROFILE=standard
CLI_CODEX_HOME_SET=false
CLI_CODEX_HOME=
CLI_GROK_HOME=
CLI_PI_HOME=
CODEX_ENV_HOME="${CODEX_HOME:-}"
SKILLS_ONLY=false
AGENTS=()

usage() {
  cat <<'EOF'
Usage: bash install.sh [OPTIONS]

Options:
  --agent AGENTS...   Select codex (default), grok, pi, or all.
  --skills-only       Install skill links without changing global instructions.
  --grok-home PATH    Override the default ~/.grok directory.
  --pi-home PATH      Override PI_CODING_AGENT_DIR or ~/.pi/agent.
  --profile PROFILE   Install profile: standard (default) or ao-worker.
  --codex-home PATH   Override CODEX_HOME. Required for ao-worker.
  --dry-run           Show planned actions without modifying files.
  --force             Replace existing foreign skill or non-regular AGENTS paths.
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
    --agent)
      shift
      [[ $# -gt 0 && "$1" != --* ]] || fail_usage "--agent requires a value"
      while [[ $# -gt 0 && "$1" != --* ]]; do
        case "$1" in
          codex|grok|pi) AGENTS+=("$1") ;;
          all) AGENTS+=(codex grok pi) ;;
          *) fail_usage "Unknown agent: $1" ;;
        esac
        shift
      done
      continue
      ;;
    --skills-only)
      SKILLS_ONLY=true
      ;;
    --grok-home|--pi-home)
      [[ $# -ge 2 && -n "$2" && "$2" != --* ]] || fail_usage "$1 requires a path"
      [[ "$2" == /* ]] || fail_usage "$1 must be an absolute path"
      if [[ "$1" == --grok-home ]]; then CLI_GROK_HOME="$2"; else CLI_PI_HOME="$2"; fi
      shift
      ;;
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

[[ ${#AGENTS[@]} -gt 0 ]] || AGENTS=(codex)
if [[ "$PROFILE" == "ao-worker" ]]; then
  [[ "${AGENTS[*]}" == codex ]] || fail_usage "ao-worker supports only codex"
fi
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
CALIBRATION_ROOT="$(realpath -m -- "$SCRIPT_DIR")"
configure_target() {
  if [[ "$PROFILE" == "ao-worker" ]] && ! $CLI_CODEX_HOME_SET; then
    fail_usage "ao-worker requires an explicit --codex-home PATH"
  fi
  if $CLI_CODEX_HOME_SET; then
    [[ -n "$CLI_CODEX_HOME" ]] ||
      fail_usage "--codex-home requires a non-empty path"
    [[ "$CLI_CODEX_HOME" == /* ]] ||
      fail_usage "--codex-home must be an absolute path"
    TARGET_HOME="$CLI_CODEX_HOME"
  elif [[ -n "$CODEX_ENV_HOME" ]]; then
    TARGET_HOME="$CODEX_ENV_HOME"
  elif [[ -n "${HOME:-}" ]]; then
    TARGET_HOME="$HOME/.codex"
  else
    fail_usage "Cannot derive default Codex home: HOME and CODEX_HOME are unset"
  fi
  [[ -n "$TARGET_HOME" ]] || fail_usage "Codex home must not be empty"
  case "$AGENT" in
    grok) TARGET_HOME="${CLI_GROK_HOME:-$HOME/.grok}" ;;
    pi) TARGET_HOME="${CLI_PI_HOME:-${PI_CODING_AGENT_DIR:-$HOME/.pi/agent}}" ;;
  esac
  [[ "$TARGET_HOME" == /* ]] || fail_usage "Agent home must be an absolute path"
  SELECTED_TARGET_HOME="$TARGET_HOME"

  LEXICAL_TARGET_HOME="$(realpath -m -s -- "$TARGET_HOME")"
  TARGET_HOME="$(realpath -m -- "$TARGET_HOME")"
  [[ "$TARGET_HOME" != "/" ]] || fail_usage "Refusing to use / as Codex home"
  case "$TARGET_HOME" in
    "$CALIBRATION_ROOT"|"$CALIBRATION_ROOT"/*)
      fail_usage "Codex home must not equal or be inside the calibration checkout"
      ;;
  esac
  case "$CALIBRATION_ROOT" in
    "$TARGET_HOME"/*)
      fail_usage "Codex home must not contain the calibration checkout"
      ;;
  esac
  if [[ "$PROFILE" == "ao-worker" ]]; then
    if [[ "$LEXICAL_TARGET_HOME" != "$TARGET_HOME" ]]; then
      fail_usage "ao-worker Codex home path must not traverse a symlink"
    fi
    if [[ -e "$SELECTED_TARGET_HOME" && ! -d "$SELECTED_TARGET_HOME" ]]; then
      fail_usage "ao-worker Codex home must be a directory"
    fi
    if [[ -d "$SELECTED_TARGET_HOME" ]]; then
      home_mode="$(stat -c '%a' -- "$SELECTED_TARGET_HOME")"
      if (( (8#$home_mode & 8#077) != 0 )); then
        fail_usage "ao-worker Codex home must not grant group or other permissions"
      fi
    fi
  fi

  SKILLS_DIR="$TARGET_HOME/skills"
  AGENTS_TARGET="$TARGET_HOME/AGENTS.md"
  if [[ "$PROFILE" == "ao-worker" ]]; then
    if [[ -L "$SKILLS_DIR" ]]; then
      fail_usage "ao-worker skills target must not be a symlink"
    fi
    if [[ -e "$SKILLS_DIR" && ! -d "$SKILLS_DIR" ]]; then
      fail_usage "ao-worker skills target must be a directory"
    fi
  fi
  for directory in "$TARGET_HOME" "$SKILLS_DIR"; do
    if [[ ( -e "$directory" || -L "$directory" ) && ! -d "$directory" ]]; then
      fail_usage "Agent home and skills root must be directories: $directory"
    fi
  done
}

AGENT="${AGENTS[0]}"
configure_target

if [[ -n "${XDG_CONFIG_HOME:-}" ]]; then
  [[ "$XDG_CONFIG_HOME" == /* ]] ||
    fail_usage "XDG_CONFIG_HOME must be an absolute path"
  HOST_CONFIG_ROOT="$(realpath -m -- "$XDG_CONFIG_HOME")"
else
  [[ "${HOME:-}" == /* ]] || fail_usage "HOME must be an absolute path"
  HOST_CONFIG_ROOT="$(realpath -m -- "$HOME/.config")"
fi

SKILL_SOURCE_ROOT="$CALIBRATION_ROOT/skills"
THIRDPARTY_SKILL_SOURCE_ROOT="$CALIBRATION_ROOT/thirdparty/skills"
TEMPLATE="$CALIBRATION_ROOT/codex/AGENTS.md.template"
HOST_AUTHORITY="$HOST_CONFIG_ROOT/calibration/AGENTS.md"
MANAGED_SKILLS=(
  calibration
  closeout
  retrospect
  writing-code-docs
)
MANAGED_THIRDPARTY_SKILLS=(
  brainstorming
  grilling
  teach
)
MANAGED_SHARED_THIRDPARTY_SKILLS=(
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
  writing-great-skills
  writing-plans
  darwin-skill
)
RETIRED_SHARED_THIRDPARTY_SKILLS=(
  coding-protocol
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

render_body() {
  local escaped_root escaped_host_authority
  escaped_root="$(escape_sed_replacement "$CALIBRATION_ROOT")"
  escaped_host_authority="$(escape_sed_replacement "$HOST_AUTHORITY")"
  sed \
    -e "s/{{CALIBRATION_ROOT}}/$escaped_root/g" \
    -e "s/{{HOST_AUTHORITY}}/$escaped_host_authority/g" \
    "$TEMPLATE"
}

render_template() {
  if [[ "$AGENT" == codex ]]; then
    render_body
    return
  fi
  # Preserve user text outside one unambiguous managed block.
  local body
  body="$(render_body | sed 's/[$]calibration/calibration/g')"
  if [[ -f "$AGENTS_TARGET" && ! -L "$AGENTS_TARGET" ]]; then
    CALIBRATION_RENDERED_BODY="$body" awk '
      BEGIN { body=ENVIRON["CALIBRATION_RENDERED_BODY"]; inside=0; count=0 }
      $0 == "<!-- calibration:begin -->" {
        if (inside || count) exit 2
        inside=1; count++; print; print body; next
      }
      $0 == "<!-- calibration:end -->" {
        if (!inside) exit 2
        inside=0; print; next
      }
      !inside { print }
      END {
        if (inside) exit 2
        if (!count) print "\n<!-- calibration:begin -->\n" body "\n<!-- calibration:end -->"
      }
    ' "$AGENTS_TARGET"
  else
    printf '<!-- calibration:begin -->\n%s\n<!-- calibration:end -->\n' "$body"
  fi
}

preflight_agents_file() {
  render_template >/dev/null
  if [[ ! -e "$AGENTS_TARGET" && ! -L "$AGENTS_TARGET" ]]; then
    return 0
  fi
  if [[ -L "$AGENTS_TARGET" || ! -f "$AGENTS_TARGET" ]] && ! $FORCE; then
    echo "Refusing to replace non-regular AGENTS target without --force: $AGENTS_TARGET" >&2
    exit 1
  fi
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
    if ! $FORCE; then
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

preflight_skill_link() {
  local skill="$1" source_root="$2"
  local target="$SKILLS_DIR/$skill" source="$source_root/$skill"
  require_dir "$source"

  if [[ -L "$target" ]] && [[ "$(readlink "$target")" == "$source" ]]; then
    return
  fi
  if [[ -e "$target" || -L "$target" ]] && ! $FORCE; then
    echo "Refusing to replace existing skill path without --force: $target" >&2
    exit 1
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
  backup="$AGENTS_TARGET.bak.$(date +%Y%m%d%H%M%S).$$"
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
  if [[ ! -L "$AGENTS_TARGET" && -f "$AGENTS_TARGET" ]] &&
    cmp -s "$tmp" "$AGENTS_TARGET"; then
    rm -f "$tmp"
    say "AGENTS.md already current: $AGENTS_TARGET"
    return
  fi
  if [[ -e "$AGENTS_TARGET" || -L "$AGENTS_TARGET" ]]; then
    backup_agents_target
    if [[ -L "$AGENTS_TARGET" || ! -f "$AGENTS_TARGET" ]]; then
      run rm -rf "$AGENTS_TARGET"
    fi
  fi
  if $DRY_RUN; then
    say "[dry-run] write rendered AGENTS.md to $AGENTS_TARGET"
    rm -f "$tmp"
  else
    mv -T "$tmp" "$AGENTS_TARGET"
    say "AGENTS.md installed: $AGENTS_TARGET"
  fi
}

preflight_target() {
  require_file "$TEMPLATE"
  require_dir "$SKILL_SOURCE_ROOT"
  require_dir "$THIRDPARTY_SKILL_SOURCE_ROOT"

  say "Profile: $PROFILE"
  say "Calibration root: $CALIBRATION_ROOT"
  say "Agent: $AGENT"
  say "Codex home / selected agent home: $TARGET_HOME"
  say "Private host authority: $HOST_AUTHORITY"
  say "Skills target root: $SKILLS_DIR"

  for skill in "${MANAGED_SKILLS[@]}"; do
    preflight_skill_link "$skill" "$SKILL_SOURCE_ROOT"
  done
  if [[ "$PROFILE" == "standard" ]]; then
    for skill in "${MANAGED_THIRDPARTY_SKILLS[@]}"; do
      preflight_skill_link "$skill" "$THIRDPARTY_SKILL_SOURCE_ROOT"
    done
  fi
  for skill in "${MANAGED_SHARED_THIRDPARTY_SKILLS[@]}"; do
    preflight_skill_link "$skill" "$THIRDPARTY_SKILL_SOURCE_ROOT"
  done
  if ! $SKILLS_ONLY; then preflight_agents_file; fi
}

install_target() {
  if [[ "$PROFILE" == "ao-worker" ]]; then
    if [[ ! -d "$TARGET_HOME" ]]; then
      run install -d -m 0700 "$TARGET_HOME"
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

  for skill in "${RETIRED_SHARED_THIRDPARTY_SKILLS[@]}"; do
    remove_owned_skill_link \
      "$skill" "$THIRDPARTY_SKILL_SOURCE_ROOT" "Retired shared third-party skill"
  done
  for skill in "${MANAGED_SHARED_THIRDPARTY_SKILLS[@]}"; do
    install_skill_link "$skill" "$THIRDPARTY_SKILL_SOURCE_ROOT"
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
  if ! $SKILLS_ONLY; then install_agents_file; fi
}

# Validate every selected destination before changing any of them.
SELECTED_HOMES=()
for AGENT in "${AGENTS[@]}"; do
  configure_target
  for selected_home in "${SELECTED_HOMES[@]}"; do
    case "$TARGET_HOME/" in
      "$selected_home/"*) fail_usage "Selected agent homes must not overlap" ;;
    esac
    case "$selected_home/" in
      "$TARGET_HOME/"*) fail_usage "Selected agent homes must not overlap" ;;
    esac
  done
  SELECTED_HOMES+=("$TARGET_HOME")
  preflight_target
done
for AGENT in "${AGENTS[@]}"; do
  configure_target
  install_target
done
