from __future__ import annotations

import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = (
    b"/home/" + b"fq" + b"zhang",
    b"fq" + b"zhang",
    b"192." + b"168.30.",
)


def test_tracked_tree_has_no_private_host_tokens() -> None:
    result = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard", "-z"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
    )
    violations: list[str] = []
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        relative = raw_path.decode()
        path = REPOSITORY_ROOT / relative
        if not path.is_file():
            continue
        content = path.read_bytes()
        if any(token in content for token in FORBIDDEN):
            violations.append(relative)

    assert violations == []


def test_public_repository_has_no_deployable_ao_artifacts() -> None:
    assert not (REPOSITORY_ROOT / "docs/runbooks/artifacts").exists()
    assert not (REPOSITORY_ROOT / "docs/runbooks/patches").exists()
