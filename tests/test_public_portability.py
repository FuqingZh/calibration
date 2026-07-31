from __future__ import annotations

import csv
import ipaddress
import re
import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
THIRDPARTY_ROOT = Path("thirdparty")
PERSONAL_HOME_PATTERNS = (
    re.compile(rb"/(?:home|Users)/[A-Za-z0-9._-]+"),
    re.compile(rb"/root(?:/|(?=$))"),
    re.compile(rb"[A-Za-z]:[\\/]+Users[\\/]+[A-Za-z0-9._-]+"),
)
IPV4_CANDIDATE = re.compile(rb"(?<![0-9])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9])")
PRIVATE_DEPLOYMENT_NETWORKS = tuple(
    ipaddress.ip_network(network)
    for network in (
        "10." + "0.0.0/8",
        "172." + "16.0.0/12",
        "192." + "168.0.0/16",
    )
)
# Vendored source may retain a private value when provenance requires it. Keep
# each exception exact and reviewable instead of excluding thirdparty wholesale.
THIRDPARTY_PROVENANCE_ALLOWLIST: dict[str, tuple[bytes, ...]] = {}


def tracked_text() -> dict[str, bytes]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
    )
    tracked: dict[str, bytes] = {}
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        relative = raw_path.decode()
        path = REPOSITORY_ROOT / relative
        if not path.is_file():
            continue
        content = path.read_bytes()
        if b"\0" not in content:
            tracked[relative] = content
    return tracked


def private_values(content: bytes) -> set[bytes]:
    values = {
        match.group()
        for pattern in PERSONAL_HOME_PATTERNS
        for match in pattern.finditer(content)
    }
    for match in IPV4_CANDIDATE.finditer(content):
        candidate = match.group()
        try:
            address = ipaddress.ip_address(candidate.decode())
        except ValueError:
            continue
        if any(address in network for network in PRIVATE_DEPLOYMENT_NETWORKS):
            values.add(candidate)
    return values


def portability_violations(tracked: dict[str, bytes], *, thirdparty: bool) -> list[str]:
    violations: list[str] = []
    for relative, content in tracked.items():
        is_thirdparty = Path(relative).is_relative_to(THIRDPARTY_ROOT)
        if is_thirdparty != thirdparty:
            continue
        values = private_values(relative.encode()) | private_values(content)
        allowed = set(THIRDPARTY_PROVENANCE_ALLOWLIST.get(relative, ()))
        unexpected = sorted(value for value in values if value not in allowed)
        if unexpected:
            rendered = ", ".join(repr(value.decode()) for value in unexpected)
            violations.append(f"{relative}: {rendered}")
    return violations


def test_first_party_surfaces_have_no_personal_paths_or_private_ipv4() -> None:
    assert portability_violations(tracked_text(), thirdparty=False) == []


def test_vendored_surfaces_document_private_values_as_provenance() -> None:
    tracked = tracked_text()
    assert portability_violations(tracked, thirdparty=True) == []
    assert set(THIRDPARTY_PROVENANCE_ALLOWLIST) <= set(tracked)
    for relative, allowed in THIRDPARTY_PROVENANCE_ALLOWLIST.items():
        assert set(allowed) <= private_values(tracked[relative])


def test_private_value_detection_is_structural() -> None:
    samples = (
        b"/ho" + b"me/alice/project",
        b"/Us" + b"ers/bob/project",
        b"/ro" + b"ot/project",
        b"C:\\Us" + b"ers\\carol\\project",
        b"10." + b"23.4.5",
        b"172." + b"31.4.5",
        b"192." + b"168.4.5",
    )
    for sample in samples:
        assert private_values(sample)


def test_retired_darwin_source_keeps_immutable_provenance_only() -> None:
    with (REPOSITORY_ROOT / "thirdparty/sources.tsv").open(
        encoding="utf-8", newline=""
    ) as source_file:
        rows = {row["name"]: row for row in csv.DictReader(source_file, delimiter="\t")}

    darwin = rows["darwin-skill"]
    expected_ref = "7c7b7909b630dc3b5cbb91bd4bcb1b10bfb1f894"
    assert darwin["imported_ref"] == expected_ref
    assert darwin["upstream_ref_checked"] == expected_ref
    assert darwin["local_policy"] == "retired-not-vendored"
    assert not (REPOSITORY_ROOT / "thirdparty/skills/darwin-skill").exists()


def test_public_repository_has_no_deployable_ao_artifacts() -> None:
    assert not (REPOSITORY_ROOT / "docs/runbooks/artifacts").exists()
    assert not (REPOSITORY_ROOT / "docs/runbooks/patches").exists()
