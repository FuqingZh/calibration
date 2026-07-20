from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_skills import validate_repository


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class ValidateSkillsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        (self.root / "skills").mkdir()
        (self.root / "thirdparty/skills").mkdir(parents=True)
        (self.root / "install.sh").write_text(
            "MANAGED_SKILLS=(\n  sample\n)\n"
            "MANAGED_THIRDPARTY_SKILLS=(\n)\n",
            encoding="utf-8",
        )
        self.skill_dir = self._write_skill("skills", "sample")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _write_skill(self, parent: str, name: str) -> Path:
        skill_dir = self.root / parent / name
        (skill_dir / "agents").mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Use for a focused validation task.\n---\n\n"
            f"# {name}\n",
            encoding="utf-8",
        )
        (skill_dir / "agents/openai.yaml").write_text(
            "interface:\n"
            f"  display_name: \"{name.title()}\"\n"
            "  short_description: \"Validate one focused skill contract\"\n"
            f"  default_prompt: \"Use ${name} for this validation task.\"\n"
            "policy:\n"
            "  allow_implicit_invocation: true\n",
            encoding="utf-8",
        )
        return skill_dir

    def assert_has_error(self, fragment: str) -> None:
        errors = validate_repository(self.root)
        self.assertTrue(
            any(fragment in error for error in errors),
            msg=f"expected {fragment!r} in errors: {errors}",
        )

    def test_valid_fixture_passes(self) -> None:
        self.assertEqual(validate_repository(self.root), [])

    def test_repository_itself_passes(self) -> None:
        self.assertEqual(validate_repository(REPOSITORY_ROOT), [])

    def test_discovers_new_skill_without_a_validator_list(self) -> None:
        extra = self._write_skill("thirdparty/skills", "extra")
        (extra / "SKILL.md").write_text("not frontmatter\n", encoding="utf-8")
        self.assert_has_error("must start with YAML frontmatter")

    def test_rejects_missing_frontmatter_field(self) -> None:
        (self.skill_dir / "SKILL.md").write_text(
            "---\nname: sample\n---\n\n# Sample\n", encoding="utf-8"
        )
        self.assert_has_error("description must be a non-empty string")

    def test_rejects_nonportable_frontmatter_name(self) -> None:
        (self.skill_dir / "SKILL.md").write_text(
            "---\nname: Sample_Name\ndescription: Use for validation.\n---\n",
            encoding="utf-8",
        )
        self.assert_has_error("name must be at most 64 lowercase")

    def test_rejects_overlong_frontmatter_description(self) -> None:
        (self.skill_dir / "SKILL.md").write_text(
            "---\nname: sample\ndescription: " + ("x" * 1025) + "\n---\n",
            encoding="utf-8",
        )
        self.assert_has_error("description must be at most 1024 characters")

    def test_rejects_missing_openai_metadata(self) -> None:
        (self.skill_dir / "agents/openai.yaml").unlink()
        self.assert_has_error("missing required OpenAI skill metadata")

    def test_rejects_invalid_openai_structure(self) -> None:
        (self.skill_dir / "agents/openai.yaml").write_text(
            "interface: []\npolicy: []\n", encoding="utf-8"
        )
        self.assert_has_error("interface must be a mapping")
        self.assert_has_error("policy must be a mapping")

    def test_rejects_out_of_range_descriptions(self) -> None:
        metadata = self.skill_dir / "agents/openai.yaml"
        metadata.write_text(
            metadata.read_text(encoding="utf-8").replace(
                "Validate one focused skill contract", "Too short"
            ),
            encoding="utf-8",
        )
        self.assert_has_error("short_description must be 25-64 characters")

    def test_rejects_default_prompt_without_skill_reference(self) -> None:
        metadata = self.skill_dir / "agents/openai.yaml"
        metadata.write_text(
            metadata.read_text(encoding="utf-8").replace("$sample", "$other"),
            encoding="utf-8",
        )
        self.assert_has_error("default_prompt must reference $sample")

    def test_rejects_implicit_user_invocation(self) -> None:
        skill = self.skill_dir / "SKILL.md"
        skill.write_text(
            skill.read_text(encoding="utf-8").replace(
                "Use for a focused validation task.",
                "User-invoked mode for a focused validation task.",
            ),
            encoding="utf-8",
        )
        self.assert_has_error("requires this skill to disable implicit invocation")

    def test_rejects_implicit_third_party_skill(self) -> None:
        self._write_skill("thirdparty/skills", "optional")
        self.assert_has_error("requires this skill to disable implicit invocation")

    def test_rejects_retired_invocation_field(self) -> None:
        metadata = self.skill_dir / "agents/openai.yaml"
        metadata.write_text(
            metadata.read_text(encoding="utf-8")
            + "disable-model-invocation: true\n",
            encoding="utf-8",
        )
        self.assert_has_error("retired field 'disable-model-invocation'")

    def test_rejects_malformed_behavioral_prompts(self) -> None:
        (self.skill_dir / "test-prompts.json").write_text(
            json.dumps([{"id": 1, "scenario": "case", "prompt": "run"}]),
            encoding="utf-8",
        )
        self.assert_has_error("is missing 'expected'")

    def test_rejects_unparseable_behavioral_prompts(self) -> None:
        (self.skill_dir / "test-prompts.json").write_text("[", encoding="utf-8")
        self.assert_has_error("invalid behavioral test prompts")

    def test_rejects_missing_active_local_reference(self) -> None:
        skill = self.skill_dir / "SKILL.md"
        skill.write_text(
            skill.read_text(encoding="utf-8") + "\nRead `references/missing.md`.\n",
            encoding="utf-8",
        )
        self.assert_has_error("missing repository-local reference 'references/missing.md'")


if __name__ == "__main__":
    unittest.main()
