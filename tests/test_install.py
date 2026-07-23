from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MANAGED_SKILLS = ("calibration", "retrospect", "writing-code-docs")
MANAGED_THIRDPARTY_SKILLS = (
    "brainstorming",
    "grilling",
    "writing-great-skills",
)


def run_installer(
    repository_root: Path,
    codex_home: Path,
    *arguments: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(repository_root / "install.sh"), *arguments],
        cwd=repository_root,
        env={**os.environ, "CODEX_HOME": str(codex_home)},
        check=False,
        capture_output=True,
        text=True,
    )


def assert_installed(repository_root: Path, codex_home: Path) -> None:
    agents = (codex_home / "AGENTS.md").read_text(encoding="utf-8")
    assert str(repository_root) in agents

    for name in MANAGED_SKILLS:
        assert (codex_home / "skills" / name).readlink() == (
            repository_root / "skills" / name
        )
    for name in MANAGED_THIRDPARTY_SKILLS:
        assert (codex_home / "skills" / name).readlink() == (
            repository_root / "thirdparty/skills" / name
        )


def test_dry_run_does_not_write_codex_home(tmp_path: Path) -> None:
    codex_home = tmp_path / "codex-home"

    result = run_installer(REPOSITORY_ROOT, codex_home, "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "[dry-run]" in result.stdout
    assert not codex_home.exists()


def test_fresh_install_and_reinstall_are_idempotent(tmp_path: Path) -> None:
    codex_home = tmp_path / "codex-home"

    first = run_installer(REPOSITORY_ROOT, codex_home)
    second = run_installer(REPOSITORY_ROOT, codex_home)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert "AGENTS.md already current" in second.stdout
    assert_installed(REPOSITORY_ROOT, codex_home)
    assert list(tmp_path.glob("codex-home/AGENTS.md.bak.*")) == []


def test_existing_skill_requires_force_and_is_preserved_on_failure(
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "codex-home"
    conflict = codex_home / "skills/calibration"
    conflict.mkdir(parents=True)
    marker = conflict / "user-content"
    marker.write_text("keep", encoding="utf-8")

    refused = run_installer(REPOSITORY_ROOT, codex_home)

    assert refused.returncode == 1
    assert "Refusing to replace existing skill path without --force" in refused.stderr
    assert marker.read_text(encoding="utf-8") == "keep"

    forced = run_installer(REPOSITORY_ROOT, codex_home, "--force")

    assert forced.returncode == 0, forced.stderr
    assert_installed(REPOSITORY_ROOT, codex_home)


@pytest.mark.parametrize("no_backup", [False, True])
def test_agents_backup_policy(tmp_path: Path, no_backup: bool) -> None:
    codex_home = tmp_path / ("without-backup" if no_backup else "with-backup")
    codex_home.mkdir()
    agents = codex_home / "AGENTS.md"
    agents.write_text("user content\n", encoding="utf-8")
    arguments = ("--no-backup",) if no_backup else ()

    result = run_installer(REPOSITORY_ROOT, codex_home, *arguments)

    assert result.returncode == 0, result.stderr
    backups = list(codex_home.glob("AGENTS.md.bak.*"))
    assert len(backups) == (0 if no_backup else 1)
    if backups:
        assert backups[0].read_text(encoding="utf-8") == "user content\n"


def test_retired_paths_are_removed_only_when_owned_or_forced(tmp_path: Path) -> None:
    codex_home = tmp_path / "codex-home"
    skills = codex_home / "skills"
    skills.mkdir(parents=True)
    owned = skills / "writing-docstrings"
    owned.symlink_to(REPOSITORY_ROOT / "skills/writing-docstrings")
    foreign = skills / "global-defaults"
    foreign.symlink_to(tmp_path / "foreign-skill")
    unmanaged = skills / "grill-me"
    unmanaged.mkdir()

    normal = run_installer(REPOSITORY_ROOT, codex_home)

    assert normal.returncode == 0, normal.stderr
    assert not owned.exists() and not owned.is_symlink()
    assert foreign.is_symlink()
    assert unmanaged.is_dir()

    forced = run_installer(REPOSITORY_ROOT, codex_home, "--force")

    assert forced.returncode == 0, forced.stderr
    assert foreign.is_symlink()
    assert not unmanaged.exists()


def test_repository_path_with_spaces_is_supported(tmp_path: Path) -> None:
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

    result = run_installer(repository_root, codex_home)

    assert result.returncode == 0, result.stderr
    assert_installed(repository_root, codex_home)
