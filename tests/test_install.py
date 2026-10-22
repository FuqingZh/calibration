from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from scripts.validate_skills import _validate_active_references
from tests.support import REPOSITORY_ROOT
from tests.support.installer import run_installer

MANAGED_SKILLS = ("calibration", "closeout", "retrospect", "writing-code-docs")
MANAGED_THIRDPARTY_SKILLS = (
    "grilling",
    "teach",
)
MANAGED_SHARED_THIRDPARTY_SKILLS: tuple[str, ...] = ()


def assert_first_party_installed(repository_root: Path, codex_home: Path) -> str:
    agents = (codex_home / "AGENTS.md").read_text(encoding="utf-8")
    assert str(repository_root) in agents
    for name in MANAGED_SKILLS:
        assert (codex_home / "skills" / name).readlink() == (
            repository_root / "skills" / name
        )
    return agents


def assert_shared_third_party_installed(
    repository_root: Path, codex_home: Path
) -> None:
    for name in MANAGED_SHARED_THIRDPARTY_SKILLS:
        assert (codex_home / "skills" / name).readlink() == (
            repository_root / "thirdparty/skills" / name
        )


def assert_standard_installed(repository_root: Path, codex_home: Path) -> str:
    agents = assert_first_party_installed(repository_root, codex_home)
    assert_shared_third_party_installed(repository_root, codex_home)
    for name in MANAGED_THIRDPARTY_SKILLS:
        assert (codex_home / "skills" / name).readlink() == (
            repository_root / "thirdparty/skills" / name
        )
    assert not (codex_home / "skills/brainstorming").is_symlink()
    assert not (codex_home / "skills/brainstorming").exists()
    return agents


def snapshot_tree(root: Path) -> list[tuple[str, str, bytes | str]]:
    snapshot: list[tuple[str, str, bytes | str]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            snapshot.append((relative, "link", os.readlink(path)))
        elif path.is_file():
            snapshot.append((relative, "file", path.read_bytes()))
        else:
            snapshot.append((relative, "dir", b""))
    return snapshot


def test_default_and_explicit_standard_are_equivalent(tmp_path: Path) -> None:
    default_home = tmp_path / "default"
    explicit_home = tmp_path / "explicit"

    default = run_installer(default_home)
    explicit = run_installer(explicit_home, "--profile", "standard")

    assert default.returncode == 0, default.stderr
    assert explicit.returncode == 0, explicit.stderr
    assert snapshot_tree(default_home) == snapshot_tree(explicit_home)
    assert_standard_installed(REPOSITORY_ROOT, default_home)


@pytest.mark.parametrize("profile", ["standard"])
def test_installed_first_party_skills_are_lexically_self_contained(
    tmp_path: Path, profile: str
) -> None:
    codex_home = tmp_path / profile
    arguments = ["--profile", profile]

    result = run_installer(codex_home, *arguments)

    assert result.returncode == 0, result.stderr
    for name in MANAGED_SKILLS:
        lexical_skill_root = codex_home / "skills" / name
        assert lexical_skill_root.is_symlink()
        errors: list[str] = []
        _validate_active_references([lexical_skill_root], errors)
        assert errors == []


def test_each_first_party_skill_is_portable_without_repository_context(
    tmp_path: Path,
) -> None:
    portable_root = tmp_path / "portable-skills"
    for name in MANAGED_SKILLS:
        skill_root = portable_root / name
        shutil.copytree(REPOSITORY_ROOT / "skills" / name, skill_root)
        errors: list[str] = []
        _validate_active_references([skill_root], errors)
        assert errors == []


def test_missing_home_and_codex_home_is_controlled_zero_write_failure(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "marker"
    marker.write_text("preserve\n", encoding="utf-8")

    result = run_installer(
        None,
        "--dry-run",
        unset_env=("HOME", "CODEX_HOME"),
    )

    assert result.returncode == 2
    assert (
        "Cannot derive default Codex home: HOME and CODEX_HOME are unset"
        in result.stderr
    )
    assert "unbound variable" not in result.stderr
    assert marker.read_text(encoding="utf-8") == "preserve\n"
    assert list(tmp_path.iterdir()) == [marker]


@pytest.mark.parametrize("profile", ["standard"])
def test_dry_runs_do_not_write_target_home(tmp_path: Path, profile: str) -> None:
    codex_home = tmp_path / profile
    arguments = ["--profile", profile, "--dry-run"]

    result = run_installer(codex_home, *arguments)

    assert result.returncode == 0, result.stderr
    assert "[dry-run]" in result.stdout
    assert not codex_home.exists()


def test_relative_xdg_config_home_is_rejected_before_writes(
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "codex-home"

    result = run_installer(
        codex_home,
        env_updates={"XDG_CONFIG_HOME": "relative-config"},
    )

    assert result.returncode == 2
    assert "XDG_CONFIG_HOME must be an absolute path" in result.stderr
    assert not codex_home.exists()


def test_standard_environment_home_cannot_overlap_source(
    tmp_path: Path,
) -> None:
    marker = REPOSITORY_ROOT / "README.md"
    before = marker.read_bytes()

    result = run_installer(REPOSITORY_ROOT)

    assert result.returncode == 2
    assert "calibration checkout" in result.stderr
    assert marker.read_bytes() == before
    assert not (REPOSITORY_ROOT / "skills/AGENTS.md").exists()


def test_private_profile_absence_does_not_block_install(tmp_path: Path) -> None:
    worker_home = tmp_path / "worker"
    config_root = tmp_path / "missing-config"

    result = run_installer(
        None,
        "--profile",
        "standard",
        "--codex-home",
        str(worker_home),
        env_updates={"XDG_CONFIG_HOME": str(config_root)},
    )

    assert result.returncode == 0, result.stderr
    agents = assert_first_party_installed(REPOSITORY_ROOT, worker_home)
    assert "if that file exists" in " ".join(agents.split())
    assert not config_root.exists()


def test_retired_protocol_preserves_foreign_link_even_with_force(
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "codex-home"
    skills = codex_home / "skills"
    skills.mkdir(parents=True)
    foreign = tmp_path / "foreign-coding-protocol"
    foreign.mkdir()
    shared = skills / "coding-protocol"
    shared.symlink_to(foreign, target_is_directory=True)

    for arguments in [(), ("--force",)]:
        result = run_installer(codex_home, *arguments)
        assert result.returncode == 0, result.stderr
        assert shared.is_symlink() and shared.readlink() == foreign


@pytest.mark.parametrize("profile", ["standard"])
def test_retired_shared_protocol_removes_only_owned_links_idempotently(
    tmp_path: Path, profile: str
) -> None:
    repository_root = tmp_path / "retired-shared-repository"
    (repository_root / "codex").mkdir(parents=True)
    (repository_root / "thirdparty").mkdir()
    installer = (REPOSITORY_ROOT / "install.sh").read_text(encoding="utf-8")
    (repository_root / "install.sh").write_text(installer, encoding="utf-8")
    (repository_root / "codex/AGENTS.md.template").write_bytes(
        (REPOSITORY_ROOT / "codex/AGENTS.md.template").read_bytes()
    )
    (repository_root / "skills").symlink_to(REPOSITORY_ROOT / "skills")
    (repository_root / "thirdparty/skills").symlink_to(
        REPOSITORY_ROOT / "thirdparty/skills"
    )

    codex_home = tmp_path / f"{profile}-home"
    skills = codex_home / "skills"
    skills.mkdir(parents=True)
    owned = skills / "coding-protocol"
    owned.symlink_to(repository_root / "thirdparty/skills/coding-protocol")
    foreign_target = tmp_path / "foreign-shared-target"
    foreign_target.mkdir()
    arguments = ["--profile", profile]

    first = run_installer(
        codex_home,
        *arguments,
        repository_root=repository_root,
    )
    assert first.returncode == 0, first.stderr
    assert not owned.exists() and not owned.is_symlink()

    owned.symlink_to(foreign_target, target_is_directory=True)
    second = run_installer(
        codex_home,
        *arguments,
        repository_root=repository_root,
    )
    third = run_installer(
        codex_home,
        *arguments,
        repository_root=repository_root,
    )

    assert second.returncode == third.returncode == 0
    assert owned.is_symlink() and owned.readlink() == foreign_target


@pytest.mark.parametrize("profile", ["standard"])
def test_first_party_preflight_fails_before_creating_home(
    tmp_path: Path, profile: str
) -> None:
    repository_root = tmp_path / "missing-first-party-source"
    (repository_root / "codex").mkdir(parents=True)
    (repository_root / "skills").mkdir()
    (repository_root / "thirdparty/skills").mkdir(parents=True)
    (repository_root / "install.sh").write_bytes(
        (REPOSITORY_ROOT / "install.sh").read_bytes()
    )
    (repository_root / "codex/AGENTS.md.template").write_bytes(
        (REPOSITORY_ROOT / "codex/AGENTS.md.template").read_bytes()
    )
    codex_home = tmp_path / f"{profile}-home"
    arguments = ["--profile", profile]

    result = run_installer(
        codex_home,
        *arguments,
        repository_root=repository_root,
    )

    assert result.returncode == 1
    assert "Missing required directory" in result.stderr
    assert not codex_home.exists()


def test_standard_preserves_foreign_teach_link_until_force(tmp_path: Path) -> None:
    codex_home = tmp_path / "codex-home"
    skills = codex_home / "skills"
    skills.mkdir(parents=True)
    foreign = tmp_path / "upstream-teach"
    foreign.mkdir()
    teach = skills / "teach"
    teach.symlink_to(foreign, target_is_directory=True)
    before = snapshot_tree(codex_home)

    refused = run_installer(codex_home)

    assert refused.returncode == 1
    assert "without --force" in refused.stderr
    assert snapshot_tree(codex_home) == before
    assert teach.is_symlink() and teach.readlink() == foreign

    preview = run_installer(codex_home, "--dry-run", "--force")

    assert preview.returncode == 0, preview.stderr
    assert "removal planned" not in preview.stdout
    assert "Skill link planned" in preview.stdout
    assert snapshot_tree(codex_home) == before

    forced = run_installer(codex_home, "--force")

    assert forced.returncode == 0, forced.stderr
    assert teach.readlink() == REPOSITORY_ROOT / "thirdparty/skills/teach"


def test_nonregular_agents_target_is_preflighted_before_home_mutation(
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "codex-home"
    agents = codex_home / "AGENTS.md"
    agents.mkdir(parents=True)
    marker = agents / "user-content"
    marker.write_text("preserve\n", encoding="utf-8")
    before = snapshot_tree(codex_home)

    refused = run_installer(codex_home)

    assert refused.returncode == 1
    assert "non-regular AGENTS target without --force" in refused.stderr
    assert snapshot_tree(codex_home) == before
    assert not (codex_home / "skills").exists()

    forced = run_installer(codex_home, "--force")

    assert forced.returncode == 0, forced.stderr
    assert_standard_installed(REPOSITORY_ROOT, codex_home)
    backups = list(codex_home.glob("AGENTS.md.bak.*"))
    assert len(backups) == 1
    assert (backups[0] / "user-content").read_text(encoding="utf-8") == ("preserve\n")


def test_force_replaces_matching_external_agents_symlink(tmp_path: Path) -> None:
    source_home = tmp_path / "source-home"
    source_install = run_installer(source_home)
    assert source_install.returncode == 0, source_install.stderr

    external = tmp_path / "external-agents.md"
    external.write_bytes((source_home / "AGENTS.md").read_bytes())
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    agents = codex_home / "AGENTS.md"
    agents.symlink_to(external)

    forced = run_installer(codex_home, "--force")

    assert forced.returncode == 0, forced.stderr
    assert agents.is_file() and not agents.is_symlink()
    assert agents.read_bytes() == external.read_bytes()
    backups = list(codex_home.glob("AGENTS.md.bak.*"))
    assert len(backups) == 1
    assert backups[0].is_symlink() and backups[0].readlink() == external


def test_installer_preserves_unowned_codex_state_byte_exactly(
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "worker"
    auth_target = tmp_path / "private-auth.json"
    auth_target.write_bytes(b'{"token":"private"}\n')
    markers = {
        "config.toml": b"model = 'private'\n",
        "Apps/marker.bin": b"\x00apps\xff",
        "Plugins/marker.bin": b"\x00plugins\xff",
        "MCP/marker.bin": b"\x00mcp\xff",
    }
    for relative, content in markers.items():
        path = codex_home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    codex_home.chmod(0o700)
    auth_link = codex_home / "auth.json"
    auth_link.symlink_to(auth_target)

    result = run_installer(
        None,
        "--profile",
        "standard",
        "--codex-home",
        str(codex_home),
    )

    assert result.returncode == 0, result.stderr
    for relative, content in markers.items():
        assert (codex_home / relative).read_bytes() == content
    assert auth_link.is_symlink()
    assert auth_link.readlink() == auth_target
    assert auth_link.read_bytes() == b'{"token":"private"}\n'


def test_dry_run_preserves_content_and_uses_planned_wording(
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "worker"
    skills = codex_home / "skills"
    skills.mkdir(parents=True)
    codex_home.chmod(0o700)
    owned = skills / "grilling"
    owned.symlink_to(REPOSITORY_ROOT / "thirdparty/skills/grilling")
    retired = skills / "writing-plans"
    retired.symlink_to(REPOSITORY_ROOT / "thirdparty/skills/writing-plans")
    agents = codex_home / "AGENTS.md"
    agents.write_text("preserve me\n", encoding="utf-8")

    result = run_installer(
        None,
        "--profile",
        "standard",
        "--codex-home",
        str(codex_home),
        "--dry-run",
    )

    assert result.returncode == 0, result.stderr
    assert "removal planned" in result.stdout
    assert "Backup planned" in result.stdout
    assert " removed:" not in result.stdout
    assert "Backed up" not in result.stdout
    assert owned.is_symlink()
    assert retired.is_symlink()
    assert agents.read_text(encoding="utf-8") == "preserve me\n"
    assert list(codex_home.glob("AGENTS.md.bak.*")) == []


def test_no_backup_preserves_explicit_policy(tmp_path: Path) -> None:
    codex_home = tmp_path / "standard"
    codex_home.mkdir()
    agents = codex_home / "AGENTS.md"
    agents.write_text("replace without backup\n", encoding="utf-8")

    result = run_installer(codex_home, "--no-backup")

    assert result.returncode == 0, result.stderr
    assert list(codex_home.glob("AGENTS.md.bak.*")) == []
    assert "replace without backup" not in agents.read_text(encoding="utf-8")


def test_existing_skill_requires_force_and_agents_backup_is_compatible(
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "codex-home"
    conflict = codex_home / "skills/calibration"
    conflict.mkdir(parents=True)
    marker = conflict / "user-content"
    marker.write_text("keep", encoding="utf-8")

    refused = run_installer(codex_home)
    assert refused.returncode == 1
    assert marker.read_text(encoding="utf-8") == "keep"

    agents = codex_home / "AGENTS.md"
    agents.parent.mkdir(parents=True, exist_ok=True)
    agents.write_text("user content\n", encoding="utf-8")
    forced = run_installer(codex_home, "--force")
    assert forced.returncode == 0, forced.stderr
    assert_standard_installed(REPOSITORY_ROOT, codex_home)
    backups = list(codex_home.glob("AGENTS.md.bak.*"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "user content\n"


def test_retired_paths_remain_compatible(tmp_path: Path) -> None:
    codex_home = tmp_path / "codex-home"
    skills = codex_home / "skills"
    skills.mkdir(parents=True)
    owned = skills / "writing-docstrings"
    owned.symlink_to(REPOSITORY_ROOT / "skills/writing-docstrings")
    foreign = skills / "global-defaults"
    foreign.symlink_to(tmp_path / "foreign-skill")
    unmanaged = skills / "grill-me"
    unmanaged.mkdir()

    normal = run_installer(codex_home)
    assert normal.returncode == 0, normal.stderr
    assert not owned.exists() and not owned.is_symlink()
    assert foreign.is_symlink()
    assert unmanaged.is_dir()

    forced = run_installer(codex_home, "--force")
    assert forced.returncode == 0, forced.stderr
    assert foreign.is_symlink()
    assert not unmanaged.exists()


def test_repository_and_home_paths_with_spaces_are_supported(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository with spaces"
    (repository_root / "codex").mkdir(parents=True)
    (repository_root / "thirdparty").mkdir()
    (repository_root / "install.sh").write_bytes(
        (REPOSITORY_ROOT / "install.sh").read_bytes()
    )
    (repository_root / "codex/AGENTS.md.template").write_bytes(
        (REPOSITORY_ROOT / "codex/AGENTS.md.template").read_bytes()
    )
    (repository_root / "skills").symlink_to(REPOSITORY_ROOT / "skills")
    (repository_root / "thirdparty/skills").symlink_to(
        REPOSITORY_ROOT / "thirdparty/skills"
    )
    codex_home = tmp_path / "codex home"

    result = run_installer(codex_home, repository_root=repository_root)

    assert result.returncode == 0, result.stderr
    assert_standard_installed(repository_root, codex_home)


@pytest.mark.parametrize("agent", ["codex", "grok", "pi"])
@pytest.mark.parametrize("source_root", ["thirdparty/skills", "thirdparty/archive"])
@pytest.mark.parametrize(
    "name",
    ["brainstorming", "coding-protocol", "writing-great-skills", "writing-plans"],
)
def test_archived_skill_removes_only_owned_link(
    tmp_path: Path, agent: str, source_root: str, name: str
) -> None:
    home = tmp_path / "home"
    skills = home / "skills"
    skills.mkdir(parents=True)
    home.chmod(0o700)
    link = skills / name
    source = REPOSITORY_ROOT / source_root / name
    link.symlink_to(source)
    arguments = ["--agent", agent, f"--{agent}-home", str(home)]
    preview = run_installer(home, *arguments, "--dry-run")
    assert preview.returncode == 0, preview.stderr
    assert link.is_symlink()
    applied = run_installer(home, *arguments)
    assert applied.returncode == 0, applied.stderr
    assert not link.is_symlink() and not link.exists()
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    link.symlink_to(foreign)
    preserved = run_installer(home, *arguments, "--force")
    assert preserved.returncode == 0, preserved.stderr
    assert link.is_symlink() and link.readlink() == foreign
    link.unlink()
    link.mkdir()
    marker = link / "user-owned.txt"
    marker.write_text("preserve")
    preserved_directory = run_installer(home, *arguments, "--force")
    assert preserved_directory.returncode == 0, preserved_directory.stderr
    assert marker.read_text() == "preserve"


@pytest.mark.parametrize("agent", ["grok", "pi"])
def test_other_clients_preserve_instructions_and_refresh_block(
    tmp_path: Path, agent: str
) -> None:
    home = tmp_path / agent
    home.mkdir()
    agents = home / "AGENTS.md"
    agents.write_text("My existing instructions.\n", encoding="utf-8")
    args = ("--agent", agent, f"--{agent}-home", str(home))
    result = run_installer(tmp_path / "untouched-codex", *args)
    assert result.returncode == 0, result.stderr
    text = assert_standard_installed(REPOSITORY_ROOT, home)
    assert text.startswith("My existing instructions.\n")
    assert text.count("<!-- calibration:begin -->") == 1
    assert "$calibration" not in text
    assert not (tmp_path / "untouched-codex").exists()
    agents.write_text(text.replace("# Global AGENTS.md", "# Old block"))
    result = run_installer(None, *args)
    assert result.returncode == 0, result.stderr
    assert agents.read_text() == text
    before = snapshot_tree(home)
    assert run_installer(None, *args).returncode == 0
    assert snapshot_tree(home) == before


@pytest.mark.parametrize("agent", ["codex", "grok", "pi"])
def test_skills_only_preserves_even_nonregular_instructions(
    tmp_path: Path, agent: str
) -> None:
    home = tmp_path / agent
    (home / "AGENTS.md").mkdir(parents=True)
    marker = home / "AGENTS.md" / "keep"
    marker.write_text("keep")
    result = run_installer(
        None, "--agent", agent, f"--{agent}-home", str(home), "--skills-only"
    )
    assert result.returncode == 0, result.stderr
    assert marker.read_text() == "keep"
    assert (home / "skills/calibration").resolve() == (
        REPOSITORY_ROOT / "skills/calibration"
    )


def test_all_clients_preflight_before_mutation(tmp_path: Path) -> None:
    codex, grok, pi = (tmp_path / name for name in ("codex", "grok", "pi"))
    (pi / "skills/teach").mkdir(parents=True)
    args = (
        "--agent",
        "all",
        "--codex-home",
        str(codex),
        "--grok-home",
        str(grok),
        "--pi-home",
        str(pi),
    )
    before = snapshot_tree(tmp_path)
    result = run_installer(None, *args)
    assert result.returncode != 0
    assert snapshot_tree(tmp_path) == before
    (pi / "skills/teach").rmdir()
    before = snapshot_tree(tmp_path)
    assert run_installer(None, *args, "--dry-run").returncode == 0
    assert snapshot_tree(tmp_path) == before
    result = run_installer(None, *args)
    assert result.returncode == 0, result.stderr
    for home in (codex, grok, pi):
        assert_standard_installed(REPOSITORY_ROOT, home)


@pytest.mark.parametrize(
    "text",
    [
        "<!-- calibration:begin -->\nunfinished\n",
        "<!-- calibration:end -->\n",
        "<!-- calibration:begin -->\n<!-- calibration:end -->\n"
        "<!-- calibration:begin -->\n<!-- calibration:end -->\n",
    ],
)
def test_malformed_managed_blocks_fail_without_writes(
    tmp_path: Path, text: str
) -> None:
    home = tmp_path / "pi"
    home.mkdir()
    (home / "AGENTS.md").write_text(text)
    before = snapshot_tree(home)
    result = run_installer(None, "--agent", "pi", "--pi-home", str(home))
    assert result.returncode != 0
    assert snapshot_tree(home) == before


def test_pi_environment_home_and_mise_independence(tmp_path: Path) -> None:
    home = tmp_path / "custom-pi"
    result = run_installer(
        None,
        "--agent",
        "pi",
        "--skills-only",
        env_updates={"PI_CODING_AGENT_DIR": str(home)},
    )
    assert result.returncode == 0, result.stderr
    assert (home / "skills/calibration").is_symlink()
    assert not (home / "AGENTS.md").exists()


@pytest.mark.parametrize(
    "args",
    [
        ("--agent", "unknown"),
        ("--agent",),
        ("--agent", "pi", "--profile", "unknown"),
        ("--pi-home", "relative"),
        ("--grok-home", ""),
    ],
)
def test_multi_client_invalid_arguments(tmp_path: Path, args: tuple[str, ...]) -> None:
    result = run_installer(
        tmp_path / "unused",
        *args,
        env_updates={
            "HOME": str(tmp_path / "home"),
            "PI_CODING_AGENT_DIR": str(tmp_path / "pi"),
        },
    )
    assert result.returncode == 2
    assert not (tmp_path / "unused").exists()


def test_overlapping_agent_homes_rejected(tmp_path: Path) -> None:
    home = tmp_path / "agents"
    result = run_installer(
        home, "--agent", "codex", "pi", "--pi-home", str(home / "pi")
    )
    assert result.returncode == 2
    assert not home.exists()


@pytest.mark.parametrize("relative", ["pi", "pi/skills"])
def test_later_nondirectory_target_fails_before_installing_earlier_client(
    tmp_path: Path, relative: str
) -> None:
    obstruction = tmp_path / relative
    obstruction.parent.mkdir(parents=True, exist_ok=True)
    obstruction.write_text("keep")
    before = snapshot_tree(tmp_path)
    result = run_installer(
        tmp_path / "codex",
        "--agent",
        "codex",
        "pi",
        "--pi-home",
        str(tmp_path / "pi"),
    )
    assert result.returncode != 0
    assert snapshot_tree(tmp_path) == before


def test_managed_block_preserves_backslashes_in_rendered_paths(tmp_path: Path) -> None:
    home = tmp_path / "pi"
    home.mkdir()
    (home / "AGENTS.md").write_text("Keep user guidance.\n")
    config_root = tmp_path / "config\\test"
    result = run_installer(
        None,
        "--agent",
        "pi",
        "--pi-home",
        str(home),
        env_updates={"XDG_CONFIG_HOME": str(config_root)},
    )
    assert result.returncode == 0, result.stderr
    assert (
        str(config_root / "calibration/AGENTS.md") in (home / "AGENTS.md").read_text()
    )


@pytest.mark.parametrize("agent", ["grok", "pi"])
@pytest.mark.parametrize("dry_run", [False, True])
@pytest.mark.parametrize("skills_only", [False, True])
def test_selected_client_home_does_not_require_codex_defaults(
    tmp_path: Path, agent: str, dry_run: bool, skills_only: bool
) -> None:
    home = tmp_path / agent
    arguments = ["--agent", agent, f"--{agent}-home", str(home)]
    if dry_run:
        arguments.append("--dry-run")
    if skills_only:
        arguments.append("--skills-only")
    before = snapshot_tree(tmp_path)

    result = run_installer(
        None,
        *arguments,
        env_updates={"XDG_CONFIG_HOME": str(tmp_path / "config")},
        unset_env=("HOME", "CODEX_HOME", "PI_CODING_AGENT_DIR"),
    )

    assert result.returncode == 0, result.stderr
    if dry_run:
        assert snapshot_tree(tmp_path) == before
    else:
        for name in (*MANAGED_SKILLS, *MANAGED_THIRDPARTY_SKILLS):
            assert (home / "skills" / name).is_symlink()
        if skills_only:
            assert not (home / "AGENTS.md").exists()
        else:
            assert_standard_installed(REPOSITORY_ROOT, home)


def test_pi_environment_home_does_not_require_codex_or_home(tmp_path: Path) -> None:
    home = tmp_path / "pi"
    result = run_installer(
        None,
        "--agent",
        "pi",
        env_updates={
            "PI_CODING_AGENT_DIR": str(home),
            "XDG_CONFIG_HOME": str(tmp_path / "config"),
        },
        unset_env=("HOME", "CODEX_HOME"),
    )
    assert result.returncode == 0, result.stderr
    assert_standard_installed(REPOSITORY_ROOT, home)


@pytest.mark.parametrize("agent,label", [("grok", "Grok"), ("pi", "Pi")])
def test_missing_selected_client_home_is_controlled_zero_write_failure(
    tmp_path: Path, agent: str, label: str
) -> None:
    marker = tmp_path / "marker"
    marker.write_text("preserve\n")
    before = snapshot_tree(tmp_path)
    result = run_installer(
        None,
        "--agent",
        agent,
        env_updates={"XDG_CONFIG_HOME": str(tmp_path / "config")},
        unset_env=("HOME", "CODEX_HOME", "PI_CODING_AGENT_DIR"),
    )
    assert result.returncode == 2
    assert f"Cannot derive default {label} home" in result.stderr
    assert "unbound variable" not in result.stderr
    assert snapshot_tree(tmp_path) == before


@pytest.mark.parametrize("profile", ["ao-worker", "unknown"])
def test_removed_or_unknown_profile_fails_without_writes(
    tmp_path: Path, profile: str
) -> None:
    home = tmp_path / "existing-home"
    home.mkdir()
    (home / "AGENTS.md").write_text("preserve instructions\n")
    before = snapshot_tree(home)
    result = run_installer(home, "--profile", profile, "--force")
    assert result.returncode == 2
    assert f"Unknown profile: {profile}" in result.stderr
    assert snapshot_tree(home) == before
    absent = tmp_path / "new-home"
    result = run_installer(absent, "--profile", profile)
    assert result.returncode == 2
    assert not absent.exists()


def test_standard_install_is_idempotent(tmp_path: Path) -> None:
    home = tmp_path / "home"
    first = run_installer(home)
    assert first.returncode == 0, first.stderr
    before = snapshot_tree(home)
    second = run_installer(home)
    assert second.returncode == 0, second.stderr
    assert "AGENTS.md already current" in second.stdout
    assert snapshot_tree(home) == before
