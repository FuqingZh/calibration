from __future__ import annotations

import json
import runpy
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pytest

from scripts.validate_skills import (
    _frontmatter,
    _installer_skills,
    _load_yaml,
    _resolve_local_reference,
    _resolve_vendored_reference,
    _validate_active_references,
    main,
    validate_repository,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class SkillFixture:
    root: Path
    skill_dir: Path


def write_skill(root: Path, parent: str, name: str) -> Path:
    skill_dir = root / parent / name
    (skill_dir / "agents").mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Use for a focused validation task.\n---\n\n"
        f"# {name}\n",
        encoding="utf-8",
    )
    (skill_dir / "agents/openai.yaml").write_text(
        "interface:\n"
        f'  display_name: "{name.title()}"\n'
        '  short_description: "Validate one focused skill contract"\n'
        f'  default_prompt: "Use ${name} for this validation task."\n'
        "policy:\n"
        "  allow_implicit_invocation: true\n",
        encoding="utf-8",
    )
    return skill_dir


@pytest.fixture
def skill_fixture(tmp_path: Path) -> SkillFixture:
    (tmp_path / "skills").mkdir()
    (tmp_path / "thirdparty/skills").mkdir(parents=True)
    (tmp_path / "install.sh").write_text(
        "MANAGED_SKILLS=(\n  sample\n)\nMANAGED_THIRDPARTY_SKILLS=(\n)\n"
        "MANAGED_SHARED_THIRDPARTY_SKILLS=(\n)\n",
        encoding="utf-8",
    )
    write_skill(tmp_path, "thirdparty/skills", "coding-protocol")
    return SkillFixture(
        root=tmp_path,
        skill_dir=write_skill(tmp_path, "skills", "sample"),
    )


def assert_has_error(root: Path, fragment: str) -> None:
    errors = validate_repository(root)
    assert any(fragment in error for error in errors), (
        f"expected {fragment!r} in errors: {errors}"
    )


def test_valid_fixture_passes(skill_fixture: SkillFixture) -> None:
    assert validate_repository(skill_fixture.root) == []


def test_repository_itself_passes() -> None:
    assert validate_repository(REPOSITORY_ROOT) == []


def test_discovers_new_skill_without_a_validator_list(
    skill_fixture: SkillFixture,
) -> None:
    extra = write_skill(skill_fixture.root, "thirdparty/skills", "extra")
    (extra / "SKILL.md").write_text("not frontmatter\n", encoding="utf-8")
    assert_has_error(skill_fixture.root, "must start with YAML frontmatter")


def test_rejects_missing_frontmatter_field(skill_fixture: SkillFixture) -> None:
    (skill_fixture.skill_dir / "SKILL.md").write_text(
        "---\nname: sample\n---\n\n# Sample\n", encoding="utf-8"
    )
    assert_has_error(skill_fixture.root, "description must be a non-empty string")


def test_rejects_nonportable_frontmatter_name(skill_fixture: SkillFixture) -> None:
    (skill_fixture.skill_dir / "SKILL.md").write_text(
        "---\nname: Sample_Name\ndescription: Use for validation.\n---\n",
        encoding="utf-8",
    )
    assert_has_error(skill_fixture.root, "name must be at most 64 lowercase")


def test_rejects_overlong_frontmatter_description(
    skill_fixture: SkillFixture,
) -> None:
    (skill_fixture.skill_dir / "SKILL.md").write_text(
        "---\nname: sample\ndescription: " + ("x" * 1025) + "\n---\n",
        encoding="utf-8",
    )
    assert_has_error(skill_fixture.root, "description must be at most 1024 characters")


def test_rejects_missing_openai_metadata(skill_fixture: SkillFixture) -> None:
    (skill_fixture.skill_dir / "agents/openai.yaml").unlink()
    assert_has_error(skill_fixture.root, "missing required OpenAI skill metadata")


def test_rejects_invalid_openai_structure(skill_fixture: SkillFixture) -> None:
    (skill_fixture.skill_dir / "agents/openai.yaml").write_text(
        "interface: []\npolicy: []\n", encoding="utf-8"
    )
    assert_has_error(skill_fixture.root, "interface must be a mapping")
    assert_has_error(skill_fixture.root, "policy must be a mapping")


def test_rejects_out_of_range_descriptions(skill_fixture: SkillFixture) -> None:
    metadata = skill_fixture.skill_dir / "agents/openai.yaml"
    metadata.write_text(
        metadata.read_text(encoding="utf-8").replace(
            "Validate one focused skill contract", "Too short"
        ),
        encoding="utf-8",
    )
    assert_has_error(skill_fixture.root, "short_description must be 25-64 characters")


def test_rejects_default_prompt_without_skill_reference(
    skill_fixture: SkillFixture,
) -> None:
    metadata = skill_fixture.skill_dir / "agents/openai.yaml"
    metadata.write_text(
        metadata.read_text(encoding="utf-8").replace("$sample", "$other"),
        encoding="utf-8",
    )
    assert_has_error(skill_fixture.root, "default_prompt must reference $sample")


def test_rejects_implicit_user_invocation(skill_fixture: SkillFixture) -> None:
    skill = skill_fixture.skill_dir / "SKILL.md"
    skill.write_text(
        skill.read_text(encoding="utf-8").replace(
            "Use for a focused validation task.",
            "User-invoked mode for a focused validation task.",
        ),
        encoding="utf-8",
    )
    assert_has_error(
        skill_fixture.root,
        "requires this skill to disable implicit invocation",
    )


def test_rejects_implicit_third_party_skill(skill_fixture: SkillFixture) -> None:
    write_skill(skill_fixture.root, "thirdparty/skills", "optional")
    assert_has_error(
        skill_fixture.root,
        "requires this skill to disable implicit invocation",
    )


def test_allows_only_exact_shared_implicit_third_party_skill(
    skill_fixture: SkillFixture,
) -> None:
    assert validate_repository(skill_fixture.root) == []

    write_skill(skill_fixture.root, "thirdparty/skills", "second")
    assert_has_error(
        skill_fixture.root, "requires this skill to disable implicit invocation"
    )

    renamed = write_skill(skill_fixture.root, "thirdparty/skills", "renamed")
    (renamed / "SKILL.md").write_text(
        (renamed / "SKILL.md")
        .read_text(encoding="utf-8")
        .replace("name: renamed", "name: coding-protocol"),
        encoding="utf-8",
    )
    (renamed / "agents/openai.yaml").write_text(
        (renamed / "agents/openai.yaml")
        .read_text(encoding="utf-8")
        .replace("$renamed", "$coding-protocol"),
        encoding="utf-8",
    )
    assert_has_error(
        skill_fixture.root, "requires this skill to disable implicit invocation"
    )
    assert_has_error(skill_fixture.root, "must match directory 'renamed'")


def test_shared_registry_is_exact_and_disjoint_from_standard_only(
    skill_fixture: SkillFixture,
) -> None:
    installer = skill_fixture.root / "install.sh"
    original = installer.read_text(encoding="utf-8")
    installer.write_text(
        original.replace(
            "MANAGED_SHARED_THIRDPARTY_SKILLS=(\n)",
            "MANAGED_SHARED_THIRDPARTY_SKILLS=(\n  coding-protocol\n  sample\n)",
        ),
        encoding="utf-8",
    )
    assert_has_error(
        skill_fixture.root,
        "MANAGED_SHARED_THIRDPARTY_SKILLS must be exactly []",
    )

    installer.write_text(
        original.replace(
            "MANAGED_THIRDPARTY_SKILLS=(\n)",
            "MANAGED_THIRDPARTY_SKILLS=(\n  coding-protocol\n)",
        ).replace(
            "MANAGED_SHARED_THIRDPARTY_SKILLS=(\n)",
            "MANAGED_SHARED_THIRDPARTY_SKILLS=(\n  coding-protocol\n)",
        ),
        encoding="utf-8",
    )
    assert_has_error(
        skill_fixture.root,
        "shared and standard-only third-party arrays overlap: ['coding-protocol']",
    )
    assert_has_error(
        skill_fixture.root,
        "retired runtime skills must not be installed: ['coding-protocol']",
    )


def test_rejects_retired_invocation_field(skill_fixture: SkillFixture) -> None:
    metadata = skill_fixture.skill_dir / "agents/openai.yaml"
    metadata.write_text(
        metadata.read_text(encoding="utf-8") + "disable-model-invocation: true\n",
        encoding="utf-8",
    )
    assert_has_error(skill_fixture.root, "retired field 'disable-model-invocation'")


def test_rejects_malformed_behavioral_prompts(skill_fixture: SkillFixture) -> None:
    (skill_fixture.skill_dir / "test-prompts.json").write_text(
        json.dumps([{"id": 1, "scenario": "case", "prompt": "run"}]),
        encoding="utf-8",
    )
    assert_has_error(skill_fixture.root, "is missing 'expected'")


def test_rejects_unparseable_behavioral_prompts(skill_fixture: SkillFixture) -> None:
    (skill_fixture.skill_dir / "test-prompts.json").write_text("[", encoding="utf-8")
    assert_has_error(skill_fixture.root, "invalid behavioral test prompts")


def test_rejects_missing_active_local_reference(skill_fixture: SkillFixture) -> None:
    skill = skill_fixture.skill_dir / "SKILL.md"
    skill.write_text(
        skill.read_text(encoding="utf-8") + "\nRead `references/missing.md`.\n",
        encoding="utf-8",
    )
    assert_has_error(
        skill_fixture.root,
        "missing repository-local reference 'references/missing.md'",
    )


def test_reports_unreadable_yaml_and_skill_files(tmp_path: Path) -> None:
    errors: list[str] = []

    assert _load_yaml(tmp_path, "metadata", errors) is None
    assert "invalid metadata" in errors[0]

    errors.clear()
    assert _frontmatter(tmp_path, errors) is None
    assert "cannot read SKILL.md" in errors[0]


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("---\nname: sample\n", "frontmatter is not closed"),
        ("---\n: bad\n---\n", "invalid SKILL.md frontmatter"),
        ("---\n- sample\n---\n", "frontmatter must be a mapping"),
    ],
)
def test_rejects_invalid_frontmatter_shapes(
    skill_fixture: SkillFixture,
    content: str,
    message: str,
) -> None:
    (skill_fixture.skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
    assert_has_error(skill_fixture.root, message)


def test_rejects_frontmatter_name_mismatch_and_retired_nested_field(
    skill_fixture: SkillFixture,
) -> None:
    (skill_fixture.skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: different\n"
        "description: Use for validation.\n"
        "metadata:\n"
        "  disable-model-invocation: true\n"
        "---\n",
        encoding="utf-8",
    )
    assert_has_error(skill_fixture.root, "must match directory 'sample'")
    assert_has_error(skill_fixture.root, "retired field 'disable-model-invocation'")


@pytest.mark.parametrize(
    ("metadata", "message"),
    [
        (": bad\n", "invalid OpenAI skill metadata"),
        ("- invalid\n", "OpenAI skill metadata must be a mapping"),
        (
            "interface:\n"
            f'  display_name: "{"x" * 65}"\n'
            '  short_description: "Validate one focused skill contract"\n'
            '  default_prompt: "Use $sample for this validation task."\n'
            "policy:\n"
            "  allow_implicit_invocation: true\n",
            "display_name must be at most 64 characters",
        ),
        (
            "interface:\n"
            '  display_name: "Sample"\n'
            '  short_description: "Validate one focused skill contract"\n'
            f'  default_prompt: "Use $sample. {"x" * 501}"\n'
            "policy:\n"
            "  allow_implicit_invocation: true\n",
            "default_prompt must be at most 500 characters",
        ),
        (
            "interface:\n"
            '  display_name: "Sample"\n'
            '  short_description: "Validate one focused skill contract"\n'
            '  default_prompt: "Use $sample for this validation task."\n'
            "policy: {}\n",
            "allow_implicit_invocation must be an explicit boolean",
        ),
    ],
)
def test_rejects_additional_openai_metadata_errors(
    skill_fixture: SkillFixture,
    metadata: str,
    message: str,
) -> None:
    (skill_fixture.skill_dir / "agents/openai.yaml").write_text(
        metadata,
        encoding="utf-8",
    )
    assert_has_error(skill_fixture.root, message)


def test_rejects_disabled_implicit_invocation_for_first_party_skill(
    skill_fixture: SkillFixture,
) -> None:
    metadata = skill_fixture.skill_dir / "agents/openai.yaml"
    metadata.write_text(
        metadata.read_text(encoding="utf-8").replace(
            "allow_implicit_invocation: true",
            "allow_implicit_invocation: false",
        ),
        encoding="utf-8",
    )
    assert_has_error(
        skill_fixture.root,
        "requires this skill to enable implicit invocation",
    )


@pytest.mark.parametrize(
    "prompts",
    [
        [],
        ["not a mapping"],
        [
            {
                "id": True,
                "scenario": "",
                "prompt": 1,
                "expected": None,
            }
        ],
        [
            {
                "id": "duplicate",
                "scenario": "one",
                "prompt": "run",
                "expected": "pass",
            },
            {
                "id": "duplicate",
                "scenario": "two",
                "prompt": "run",
                "expected": "pass",
            },
        ],
    ],
)
def test_rejects_additional_behavioral_prompt_errors(
    skill_fixture: SkillFixture,
    prompts: object,
) -> None:
    (skill_fixture.skill_dir / "test-prompts.json").write_text(
        json.dumps(prompts),
        encoding="utf-8",
    )
    assert validate_repository(skill_fixture.root)


def test_reports_unreadable_and_incomplete_installer(
    skill_fixture: SkillFixture,
    tmp_path: Path,
) -> None:
    errors: list[str] = []
    installer_root = tmp_path / "installer-root"
    installer_root.mkdir()
    (installer_root / "install.sh").mkdir()

    assert _installer_skills(installer_root, errors) == []
    assert "cannot read installer" in errors[0]

    (skill_fixture.root / "install.sh").write_text(
        "MANAGED_SKILLS=(\n  missing\n)\n",
        encoding="utf-8",
    )
    errors = validate_repository(skill_fixture.root)
    assert any("active skill 'missing' has no SKILL.md" in error for error in errors)
    assert any("missing MANAGED_THIRDPARTY_SKILLS array" in error for error in errors)


def test_resolves_only_portable_repository_local_references(tmp_path: Path) -> None:
    skill_root = tmp_path / "skill"
    source = skill_root / "docs/source.md"
    source.parent.mkdir(parents=True)
    source.write_text("", encoding="utf-8")
    target = skill_root / "target.md"
    target.write_text("", encoding="utf-8")

    assert _resolve_local_reference(skill_root, source, "https://example.com") is None
    assert _resolve_local_reference(skill_root, source, "#section") is None
    assert _resolve_local_reference(skill_root, source, "/tmp/file.md") == Path(
        "/__nonportable_absolute_reference__"
    )
    assert _resolve_local_reference(skill_root, source, "../target.md") == target
    assert _resolve_local_reference(skill_root, source, "../../outside.md") == Path(
        "/__reference_outside_owning_skill__"
    )


def test_vendored_reference_resolver_rejects_absolute_paths(tmp_path: Path) -> None:
    source = tmp_path / "thirdparty/skills/sample/SKILL.md"

    assert _resolve_vendored_reference(tmp_path, source, "/tmp/file.md") == Path(
        "/__nonportable_absolute_reference__"
    )


def test_reference_traversal_handles_cycles_and_unreadable_targets(
    skill_fixture: SkillFixture,
) -> None:
    docs = skill_fixture.skill_dir / "docs"
    docs.mkdir()
    first = docs / "first.md"
    second = docs / "second.md"
    unreadable = docs / "unreadable.md"
    unreadable.mkdir()
    first.write_text(
        "[second](second.md)\n[unreadable](unreadable.md)\n",
        encoding="utf-8",
    )
    second.write_text("[first](first.md)\n", encoding="utf-8")
    skill = skill_fixture.skill_dir / "SKILL.md"
    skill.write_text(
        skill.read_text(encoding="utf-8") + "\n[docs](docs/first.md)\n",
        encoding="utf-8",
    )

    errors = validate_repository(skill_fixture.root)
    assert any("cannot read referenced file" in error for error in errors)


def test_rejects_existing_reference_outside_owning_skill(
    skill_fixture: SkillFixture,
) -> None:
    outside = skill_fixture.root / "outside.md"
    outside.write_text("# Existing outside file\n", encoding="utf-8")
    skill = skill_fixture.skill_dir / "SKILL.md"
    skill.write_text(
        skill.read_text(encoding="utf-8") + "\nRead `../../outside.md`.\n",
        encoding="utf-8",
    )

    assert_has_error(skill_fixture.root, "escapes owning skill root")


def test_repository_root_fallback_cannot_hide_missing_skill_reference(
    skill_fixture: SkillFixture,
) -> None:
    fallback = skill_fixture.root / "references/shared.md"
    fallback.parent.mkdir()
    fallback.write_text("# Repository fallback\n", encoding="utf-8")
    skill = skill_fixture.skill_dir / "SKILL.md"
    skill.write_text(
        skill.read_text(encoding="utf-8") + "\nRead `references/shared.md`.\n",
        encoding="utf-8",
    )

    assert_has_error(skill_fixture.root, "missing repository-local reference")


def test_lexical_skill_link_cannot_escape_to_installed_home(tmp_path: Path) -> None:
    source_skill = tmp_path / "source/skills/sample"
    source_skill.mkdir(parents=True)
    (source_skill / "SKILL.md").write_text(
        "Read `../../references/shared.md`.\n", encoding="utf-8"
    )
    installed_home = tmp_path / "installed-home"
    installed_skill = installed_home / "skills/sample"
    installed_skill.parent.mkdir(parents=True)
    installed_skill.symlink_to(source_skill)
    installed_reference = installed_home / "references/shared.md"
    installed_reference.parent.mkdir()
    installed_reference.write_text("# Wrong lexical owner\n", encoding="utf-8")

    errors: list[str] = []
    _validate_active_references([installed_skill], errors)

    assert any("escapes owning skill root" in error for error in errors)


def test_empty_repository_is_rejected(tmp_path: Path) -> None:
    assert validate_repository(tmp_path) == [f"{tmp_path}: no skills discovered"]


def test_main_reports_success_and_failure(
    skill_fixture: SkillFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["--root", str(skill_fixture.root)]) == 0
    assert "Validated 2 skills." in capsys.readouterr().out

    (skill_fixture.skill_dir / "SKILL.md").write_text("invalid\n", encoding="utf-8")
    assert main(["--root", str(skill_fixture.root)]) == 1
    captured = capsys.readouterr()
    assert "ERROR:" in captured.err
    assert "Skill validation failed with" in captured.err


def test_script_entrypoint_exits_with_main_result(
    skill_fixture: SkillFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["validate_skills.py", "--root", str(skill_fixture.root)],
    )
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(
            str(REPOSITORY_ROOT / "scripts/validate_skills.py"),
            run_name="__main__",
        )
    assert cast(int, exc_info.value.code) == 0


@pytest.mark.parametrize(
    ("value", "message"),
    [("true", "invocation policies disagree"), ("'false'", "must be a boolean")],
)
def test_cross_client_invocation_rejects_inconsistency(
    skill_fixture: SkillFixture, value: str, message: str
) -> None:
    path = skill_fixture.skill_dir / "SKILL.md"
    path.write_text(
        path.read_text().replace(
            "name: sample", f"disable-model-invocation: {value}\nname: sample"
        )
    )
    assert_has_error(skill_fixture.root, message)


def test_cross_client_invocation_accepts_consistent_metadata(
    skill_fixture: SkillFixture,
) -> None:
    path = skill_fixture.skill_dir / "SKILL.md"
    path.write_text(
        path.read_text().replace(
            "name: sample", "disable-model-invocation: false\nname: sample"
        )
    )
    assert validate_repository(skill_fixture.root) == []
