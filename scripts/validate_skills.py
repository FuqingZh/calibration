#!/usr/bin/env python3
"""Validate repository-owned and vendored Codex skill contracts."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from collections import deque
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

import yaml


SKILL_ROOTS = (Path("skills"), Path("thirdparty/skills"))
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKDOWN_LINK_PATTERN = re.compile(r"(?<!!)\[[^]]*]\(([^)]+)\)")
CODE_PATH_PATTERN = re.compile(
    r"(?<!`)`([^`\n]+\.(?:md|json|ya?ml|py|sh|js|cjs|html))`"
)
INSTALL_ARRAY_PATTERN = re.compile(
    r"(?ms)^\s*(MANAGED_SKILLS|MANAGED_THIRDPARTY_SKILLS)=\(\s*(.*?)^\s*\)"
)
RETIRED_FIELD = "disable-model-invocation"


def discover_skills(root: Path) -> list[Path]:
    """Return every direct first-party and vendored skill directory."""
    skill_dirs: list[Path] = []
    for relative_root in SKILL_ROOTS:
        skill_root = root / relative_root
        if not skill_root.is_dir():
            continue
        skill_dirs.extend(
            path.parent for path in skill_root.glob("*/SKILL.md") if path.is_file()
        )
    return sorted(skill_dirs)


def _load_yaml(path: Path, label: str, errors: list[str]) -> Any | None:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        errors.append(f"{path}: invalid {label}: {exc}")
        return None


def _frontmatter(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        errors.append(f"{path}: cannot read SKILL.md: {exc}")
        return None

    if not lines or lines[0] != "---":
        errors.append(f"{path}: SKILL.md must start with YAML frontmatter")
        return None
    try:
        closing = lines.index("---", 1)
    except ValueError:
        errors.append(f"{path}: SKILL.md frontmatter is not closed")
        return None

    try:
        data = yaml.safe_load("\n".join(lines[1:closing]))
    except yaml.YAMLError as exc:
        errors.append(f"{path}: invalid SKILL.md frontmatter: {exc}")
        return None
    if not isinstance(data, dict):
        errors.append(f"{path}: SKILL.md frontmatter must be a mapping")
        return None
    return data


def _contains_key(value: Any, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(_contains_key(item, key) for item in value.values())
    if isinstance(value, list):
        return any(_contains_key(item, key) for item in value)
    return False


def _required_string(
    mapping: dict[str, Any], key: str, path: Path, errors: list[str]
) -> str | None:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}: {key} must be a non-empty string")
        return None
    return value.strip()


def _validate_frontmatter(
    skill_dir: Path, data: dict[str, Any], errors: list[str]
) -> tuple[str | None, str | None]:
    path = skill_dir / "SKILL.md"
    name = _required_string(data, "name", path, errors)
    description = _required_string(data, "description", path, errors)

    if name is not None:
        if len(name) > 64 or not NAME_PATTERN.fullmatch(name):
            errors.append(
                f"{path}: name must be at most 64 lowercase letters, digits, or hyphens"
            )
        if name != skill_dir.name:
            errors.append(f"{path}: name {name!r} must match directory {skill_dir.name!r}")
    if description is not None and len(description) > 1024:
        errors.append(f"{path}: description must be at most 1024 characters")
    if _contains_key(data, RETIRED_FIELD):
        errors.append(f"{path}: retired field {RETIRED_FIELD!r} is not allowed")
    return name, description


def _validate_openai_metadata(
    root: Path,
    skill_dir: Path,
    name: str | None,
    description: str | None,
    errors: list[str],
) -> None:
    path = skill_dir / "agents/openai.yaml"
    if not path.is_file():
        errors.append(f"{path}: missing required OpenAI skill metadata")
        return
    data = _load_yaml(path, "OpenAI skill metadata", errors)
    if data is None:
        return
    if not isinstance(data, dict):
        errors.append(f"{path}: OpenAI skill metadata must be a mapping")
        return
    if _contains_key(data, RETIRED_FIELD):
        errors.append(f"{path}: retired field {RETIRED_FIELD!r} is not allowed")

    interface = data.get("interface")
    if not isinstance(interface, dict):
        errors.append(f"{path}: interface must be a mapping")
        interface = {}
    display_name = _required_string(interface, "display_name", path, errors)
    short_description = _required_string(interface, "short_description", path, errors)
    default_prompt = _required_string(interface, "default_prompt", path, errors)
    if display_name is not None and len(display_name) > 64:
        errors.append(f"{path}: display_name must be at most 64 characters")
    if short_description is not None and not 25 <= len(short_description) <= 64:
        errors.append(f"{path}: short_description must be 25-64 characters")
    if default_prompt is not None:
        if len(default_prompt) > 500:
            errors.append(f"{path}: default_prompt must be at most 500 characters")
        if name is not None and f"${name}" not in default_prompt:
            errors.append(f"{path}: default_prompt must reference ${name}")

    policy = data.get("policy")
    if not isinstance(policy, dict):
        errors.append(f"{path}: policy must be a mapping")
        policy = {}
    implicit = policy.get("allow_implicit_invocation")
    if not isinstance(implicit, bool):
        errors.append(f"{path}: allow_implicit_invocation must be an explicit boolean")
    elif description is not None:
        is_third_party = skill_dir.is_relative_to(root / "thirdparty/skills")
        is_user_invoked = description.casefold().startswith("user-invoked")
        expected_implicit = not (is_third_party or is_user_invoked)
        if implicit != expected_implicit:
            intended = "enable" if expected_implicit else "disable"
            errors.append(
                f"{path}: repository policy requires this skill to {intended} "
                "implicit invocation"
            )


def _validate_test_prompts(skill_dir: Path, errors: list[str]) -> None:
    path = skill_dir / "test-prompts.json"
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"{path}: invalid behavioral test prompts: {exc}")
        return
    if not isinstance(data, list) or not data:
        errors.append(f"{path}: behavioral test prompts must be a non-empty list")
        return

    seen_ids: set[str | int] = set()
    for index, case in enumerate(data):
        label = f"{path}: case {index + 1}"
        if not isinstance(case, dict):
            errors.append(f"{label} must be a mapping")
            continue
        for key in ("id", "scenario", "prompt", "expected"):
            if key not in case:
                errors.append(f"{label} is missing {key!r}")
        case_id = case.get("id")
        if not isinstance(case_id, (str, int)) or isinstance(case_id, bool):
            errors.append(f"{label} id must be a string or integer")
        elif case_id in seen_ids:
            errors.append(f"{label} has duplicate id {case_id!r}")
        else:
            seen_ids.add(case_id)
        for key in ("scenario", "prompt", "expected"):
            value = case.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{label} {key} must be a non-empty string")


def _installer_skills(root: Path, errors: list[str]) -> list[Path]:
    path = root / "install.sh"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"{path}: cannot read installer: {exc}")
        return []

    arrays = {
        name: shlex.split(body, comments=True)
        for name, body in INSTALL_ARRAY_PATTERN.findall(text)
    }
    expected = {
        "MANAGED_SKILLS": root / "skills",
        "MANAGED_THIRDPARTY_SKILLS": root / "thirdparty/skills",
    }
    active: list[Path] = []
    for array_name, source_root in expected.items():
        names = arrays.get(array_name)
        if names is None:
            errors.append(f"{path}: missing {array_name} array")
            continue
        for name in names:
            skill_dir = source_root / name
            if not (skill_dir / "SKILL.md").is_file():
                errors.append(f"{path}: active skill {name!r} has no SKILL.md at {skill_dir}")
            else:
                active.append(skill_dir)
    return active


def _reference_targets(text: str, include_code_paths: bool) -> set[str]:
    targets = {
        match.group(1).strip().split(maxsplit=1)[0]
        for match in MARKDOWN_LINK_PATTERN.finditer(text)
    }
    if include_code_paths:
        targets.update(match.group(1).strip() for match in CODE_PATH_PATTERN.finditer(text))
    return targets


def _resolve_local_reference(root: Path, source: Path, target: str) -> Path | None:
    target = unquote(target.strip("<>"))
    split = urlsplit(target)
    if split.scheme or split.netloc or not split.path or split.path.startswith("#"):
        return None
    relative = Path(split.path)
    if relative.is_absolute():
        return Path("/__nonportable_absolute_reference__")
    candidates = ((source.parent / relative).resolve(), (root / relative).resolve())
    for candidate in candidates:
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            continue
        if candidate.exists():
            return candidate
    return candidates[0]


def _validate_active_references(
    root: Path, active: list[Path], errors: list[str]
) -> None:
    queue: deque[tuple[Path, bool]] = deque((path / "SKILL.md", True) for path in active)
    visited: set[Path] = set()
    while queue:
        source, include_code_paths = queue.popleft()
        source = source.resolve()
        if source in visited:
            continue
        visited.add(source)
        try:
            text = source.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{source}: cannot read referenced file: {exc}")
            continue
        for target in sorted(_reference_targets(text, include_code_paths)):
            resolved = _resolve_local_reference(root, source, target)
            if resolved is None:
                continue
            if not resolved.exists():
                errors.append(f"{source}: missing repository-local reference {target!r}")
                continue
            if resolved.suffix.lower() == ".md":
                queue.append((resolved, False))


def validate_repository(root: Path) -> list[str]:
    """Return all static skill validation errors under *root*."""
    root = root.resolve()
    errors: list[str] = []
    skill_dirs = discover_skills(root)
    if not skill_dirs:
        errors.append(f"{root}: no skills discovered")
        return errors

    for skill_dir in skill_dirs:
        frontmatter = _frontmatter(skill_dir / "SKILL.md", errors)
        if frontmatter is None:
            name = description = None
        else:
            name, description = _validate_frontmatter(skill_dir, frontmatter, errors)
        _validate_openai_metadata(root, skill_dir, name, description, errors)
        _validate_test_prompts(skill_dir, errors)

    active = _installer_skills(root, errors)
    _validate_active_references(root, active, errors)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the validator's repository)",
    )
    args = parser.parse_args(argv)
    errors = validate_repository(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"Skill validation failed with {len(errors)} error(s).", file=sys.stderr)
        return 1
    print(f"Validated {len(discover_skills(args.root.resolve()))} skills.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
