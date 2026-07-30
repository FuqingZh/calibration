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
    root_link = tmp_path / "root-link"
    root_link.symlink_to("/")
    cases = (
        ("--profile", "ao-worker"),
        ("--profile", "ao-worker", "--codex-home"),
        ("--profile", "ao-worker", "--codex-home", ""),
        ("--profile", "ao-worker", "--codex-home", "/"),
        ("--profile", "ao-worker", "--codex-home", "//"),
        ("--profile", "ao-worker", "--codex-home", "/tmp/.."),
        ("--profile", "ao-worker", "--codex-home", "."),
        ("--profile", "ao-worker", "--codex-home", str(root_link)),
        ("--profile", "ao-worker", "--codex-home", str(REPOSITORY_ROOT)),
        (
            "--profile",
            "ao-worker",
            "--codex-home",
            str(REPOSITORY_ROOT / "worker-home"),
        ),
        (
            "--profile",
            "ao-worker",
            "--codex-home",
            str(REPOSITORY_ROOT.parent),
        ),
        ("--profile", "unknown", "--codex-home", str(tmp_path / "other")),
    )

    for arguments in cases:
        result = run_installer(env_home, *arguments)
        assert result.returncode == 2
        assert not env_home.exists()
        assert root_link.is_symlink() and root_link.readlink() == Path("/")


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
    assert worker_home.stat().st_mode & 0o777 == 0o700
    assert (worker_home / "skills").stat().st_mode & 0o777 == 0o700


def test_ao_worker_rejects_broad_existing_home_without_writes(
    tmp_path: Path,
) -> None:
    worker_home = tmp_path / "broad-home"
    worker_home.mkdir(mode=0o755)
    worker_home.chmod(0o755)
    marker = worker_home / "marker"
    marker.write_text("preserve\n", encoding="utf-8")

    result = run_installer(
        None,
        "--profile",
        "ao-worker",
        "--codex-home",
        str(worker_home),
    )

    assert result.returncode == 2
    assert "group or other permissions" in result.stderr
    assert marker.read_text(encoding="utf-8") == "preserve\n"
    assert list(worker_home.iterdir()) == [marker]


def test_ao_worker_rejects_all_symlink_path_forms_without_writes(
    tmp_path: Path,
) -> None:
    target = tmp_path / "private-target"
    target.mkdir(mode=0o700)
    marker = target / "marker"
    marker.write_text("preserve\n", encoding="utf-8")
    link = tmp_path / "worker-link"
    link.symlink_to(target, target_is_directory=True)
    intermediate_target = tmp_path / "intermediate-target"
    nested_home = intermediate_target / "worker"
    nested_home.mkdir(parents=True, mode=0o700)
    nested_home.chmod(0o700)
    nested_marker = nested_home / "marker"
    nested_marker.write_text("nested preserve\n", encoding="utf-8")
    intermediate_link = tmp_path / "intermediate-link"
    intermediate_link.symlink_to(intermediate_target, target_is_directory=True)

    selected_paths = (
        str(link),
        f"{link}/",
        f"{link}/.",
        str(intermediate_link / "worker"),
    )
    for selected in selected_paths:
        result = run_installer(
            None,
            "--profile",
            "ao-worker",
            "--codex-home",
            selected,
        )
        assert result.returncode == 2
        assert "must not traverse a symlink" in result.stderr

    assert link.is_symlink() and link.readlink() == target
    assert intermediate_link.is_symlink()
    assert intermediate_link.readlink() == intermediate_target
    assert marker.read_text(encoding="utf-8") == "preserve\n"
    assert nested_marker.read_text(encoding="utf-8") == "nested preserve\n"
    assert list(target.iterdir()) == [marker]
    assert list(nested_home.iterdir()) == [nested_marker]


def test_ao_worker_rejects_non_directory_home_without_writes(
    tmp_path: Path,
) -> None:
    file_home = tmp_path / "worker-file"
    file_home.write_text("not a directory\n", encoding="utf-8")

    result = run_installer(
        None,
        "--profile",
        "ao-worker",
        "--codex-home",
        str(file_home),
    )

    assert result.returncode == 2
    assert "must be a directory" in result.stderr
    assert file_home.read_text(encoding="utf-8") == "not a directory\n"


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
    codex_home.chmod(0o700)

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

    retired_owned = codex_home / "skills/writing-plans"
    retired_owned.symlink_to(REPOSITORY_ROOT / "thirdparty/skills/writing-plans")
    retired_foreign = codex_home / "skills/darwin-skill"
    retired_foreign.symlink_to(foreign_target)
    worker_again = run_installer(
        None,
        "--profile",
        "ao-worker",
        "--codex-home",
        str(codex_home),
    )
    assert worker_again.returncode == 0, worker_again.stderr
    assert not retired_owned.exists() and not retired_owned.is_symlink()
    assert retired_foreign.is_symlink()

    standard_again = run_installer(codex_home, "--profile", "standard")
    assert standard_again.returncode == 0, standard_again.stderr
    assert_standard_installed(REPOSITORY_ROOT, codex_home)


def test_ao_worker_preserves_unowned_codex_state_byte_exactly(
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
        "ao-worker",
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
        "ao-worker",
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
