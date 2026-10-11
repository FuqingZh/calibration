"""Run the installer against isolated homes without changing the caller environment."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from tests.support import REPOSITORY_ROOT


def run_installer(
    codex_home: Path | None,
    *arguments: str,
    env_updates: dict[str, str] | None = None,
    unset_env: tuple[str, ...] = (),
    repository_root: Path = REPOSITORY_ROOT,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if codex_home is None:
        env.pop("CODEX_HOME", None)
    else:
        env["CODEX_HOME"] = str(codex_home)
    if env_updates:
        env.update(env_updates)
    for name in unset_env:
        env.pop(name, None)
    return subprocess.run(
        ["bash", str(repository_root / "install.sh"), *arguments],
        cwd=repository_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
