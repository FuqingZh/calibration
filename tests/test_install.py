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
    codex_home: Path | None,
    *arguments: str,
    env_updates: dict[str, str] | None = None,
    repository_root: Path = REPOSITORY_ROOT,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if codex_home is None:
        env.pop("CODEX_HOME", None)
    else:
        env["CODEX_HOME"] = str(codex_home)
    if env_updates:
        env.update(env_updates)
    return subprocess.run(
        ["bash", str(repository_root / "install.sh"), *arguments],
        cwd=repository_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


def assert_first_party_installed(repository_root: Path, codex_home: Path) -> str:
    agents = (codex_home / "AGENTS.md").read_text(encoding="utf-8")
    assert str(repository_root) in agents
    for name in MANAGED_SKILLS:
        assert (codex_home / "skills" / name).readlink() == (
            repository_root / "skills" / name
        )
    return agents


def assert_standard_installed(repository_root: Path, codex_home: Path) -> str:
    agents = assert_first_party_installed(repository_root, codex_home)
    for name in MANAGED_THIRDPARTY_SKILLS:
        assert (codex_home / "skills" / name).readlink() == (
            repository_root / "thirdparty/skills" / name
        )
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


@pytest.mark.parametrize("profile", ["standard", "ao-worker"])
def test_dry_runs_do_not_write_target_home(tmp_path: Path, profile: str) -> None:
    codex_home = tmp_path / profile
    arguments = ["--profile", profile, "--dry-run"]
    if profile == "ao-worker":
        arguments.extend(["--codex-home", str(codex_home)])

    result = run_installer(codex_home, *arguments)

    assert result.returncode == 0, result.stderr
    assert "[dry-run]" in result.stdout
    assert not codex_home.exists()


def test_ao_worker_requires_explicit_safe_cli_home_before_writes(
    tmp_path: Path,
) -> None:
    env_home = tmp_path / "environment-home"
    cases = (
        ("--profile", "ao-worker"),
        ("--profile", "ao-worker", "--codex-home"),
        ("--profile", "ao-worker", "--codex-home", ""),
        ("--profile", "ao-worker", "--codex-home", "/"),
        ("--profile", "unknown", "--codex-home", str(tmp_path / "other")),
    )

    for arguments in cases:
        result = run_installer(env_home, *arguments)
        assert result.returncode == 2
        assert not env_home.exists()


def test_ao_worker_uses_explicit_second_home_and_cli_precedence(
    tmp_path: Path,
) -> None:
    environment_home = tmp_path / "environment"
    worker_home = tmp_path / "worker home"
    xdg_root = tmp_path / "config root"

    result = run_installer(
        environment_home,
        "--profile",
        "ao-worker",
        "--codex-home",
        str(worker_home),
        env_updates={"XDG_CONFIG_HOME": str(xdg_root)},
    )

    assert result.returncode == 0, result.stderr
    assert not environment_home.exists()
    agents = assert_first_party_installed(REPOSITORY_ROOT, worker_home)
    assert str(xdg_root / "calibration/AGENTS.md") in agents
    for name in MANAGED_THIRDPARTY_SKILLS:
        assert not (worker_home / "skills" / name).exists()


def test_private_profile_absence_does_not_block_install(tmp_path: Path) -> None:
    worker_home = tmp_path / "worker"
    config_root = tmp_path / "missing-config"

    result = run_installer(
        None,
        "--profile",
        "ao-worker",
        "--codex-home",
        str(worker_home),
        env_updates={"XDG_CONFIG_HOME": str(config_root)},
    )

    assert result.returncode == 0, result.stderr
    agents = assert_first_party_installed(REPOSITORY_ROOT, worker_home)
    assert "if that file exists" in " ".join(agents.split())
    assert not config_root.exists()


def test_profiles_are_idempotent_and_convert_safely(tmp_path: Path) -> None:
    codex_home = tmp_path / "codex-home"
    foreign_target = tmp_path / "foreign"

    first_standard = run_installer(codex_home)
    second_standard = run_installer(codex_home, "--profile", "standard")
    assert first_standard.returncode == second_standard.returncode == 0
    assert "AGENTS.md already current" in second_standard.stdout

    owned = codex_home / "skills" / MANAGED_THIRDPARTY_SKILLS[0]
    owned.unlink()
    owned.symlink_to(foreign_target)
    worker = run_installer(
        None,
        "--profile",
        "ao-worker",
        "--codex-home",
        str(codex_home),
    )
    second_worker = run_installer(
        None,
        "--profile",
        "ao-worker",
        "--codex-home",
        str(codex_home),
    )
    assert worker.returncode == second_worker.returncode == 0
    assert owned.is_symlink() and owned.readlink() == foreign_target
    for name in MANAGED_THIRDPARTY_SKILLS[1:]:
        assert not (codex_home / "skills" / name).exists()

    standard_again = run_installer(codex_home, "--profile", "standard")
    assert standard_again.returncode == 0, standard_again.stderr
    assert_standard_installed(REPOSITORY_ROOT, codex_home)


def test_ao_worker_preserves_unowned_codex_state_byte_exactly(
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "worker"
    markers = {
        "config.toml": b"model = 'private'\n",
        "auth.json": b'{"token":"private"}\n',
        "Apps/marker.bin": b"\x00apps\xff",
        "Plugins/marker.bin": b"\x00plugins\xff",
        "MCP/marker.bin": b"\x00mcp\xff",
    }
    for relative, content in markers.items():
        path = codex_home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    result = run_installer(
        None,
        "--profile",
        "ao-worker",
        "--codex-home",
        str(codex_home),
    )

    assert result.returncode == 0, result.stderr
    for relative, content in markers.items():
        assert (codex_home / relative).read_bytes() == content


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
