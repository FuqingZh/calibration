from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import NotRequired, TypedDict, cast

from scripts.validate_skills import _installer_skills

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = (
    REPOSITORY_ROOT
    / "thirdparty/import-manifests/progressive-validation-selection.json"
)
REQUIRED_SOURCE_FIELDS = {
    "name",
    "role",
    "source_repo",
    "source_path",
    "source_ref",
    "checked_ref",
    "license_spdx",
    "license_source_path",
    "local_license_path",
    "local_treatment",
    "source_blob_sha256",
}
POLICIES = {
    "coding-protocol": "vendored+patched+shared",
    "verification-before-completion": "method-adapted-not-vendored",
    "designing-workflow-skills": "method-reference-not-vendored",
}
ROLES = {
    "coding-protocol": "Direct Runtime Base",
    "verification-before-completion": "Validation Algorithm",
    "designing-workflow-skills": "Progressive-Disclosure Structure",
}
LENCX_IMPORTED_PATHS = {
    (
        "skills/coding-protocol/SKILL.md",
        "thirdparty/skills/coding-protocol/SKILL.md",
    ),
    (
        "skills/coding-protocol/references/rule-rationale.md",
        "thirdparty/skills/coding-protocol/references/rule-rationale.md",
    ),
    (
        "skills/coding-protocol/references/verification.md",
        "thirdparty/skills/coding-protocol/references/verification.md",
    ),
    ("LICENSE", "thirdparty/skills/coding-protocol/LICENSE"),
}


class ImportedFile(TypedDict):
    upstream_path: str
    upstream_git_blob: str
    upstream_sha256: str
    local_path: str
    local_sha256: str


class Source(TypedDict):
    name: str
    role: str
    source_repo: str
    source_path: str
    source_ref: str
    checked_ref: str
    license_spdx: str
    license_source_path: str
    local_license_path: str | None
    local_treatment: str
    source_blob_sha256: str
    source_notice_paths: NotRequired[list[str]]
    imported_files: NotRequired[list[ImportedFile]]
    local_derivative_path: NotRequired[str]
    local_derivative_sha256: NotRequired[str]
    removal_ref: NotRequired[str]
    independent_expression_review: NotRequired[str]


class Manifest(TypedDict):
    schema_version: int
    checked_at: str
    sources: list[Source]


def manifest() -> Manifest:
    return cast(Manifest, json.loads(MANIFEST_PATH.read_text(encoding="utf-8")))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_manifest_schema_policies_and_license_paths() -> None:
    data = manifest()
    assert data["schema_version"] == 1
    assert isinstance(data["checked_at"], str)
    sources = data["sources"]
    assert isinstance(sources, list)
    by_name = {source["name"]: source for source in sources}
    assert set(by_name) == set(POLICIES)

    for name, policy in POLICIES.items():
        source = by_name[name]
        assert set(source) >= REQUIRED_SOURCE_FIELDS
        assert source["role"] == ROLES[name]
        assert source["local_treatment"] == policy
        assert len(source["source_blob_sha256"]) == 64
        assert all(char in "0123456789abcdef" for char in source["source_blob_sha256"])
        local_license_path = source["local_license_path"]
        if local_license_path is not None:
            assert (REPOSITORY_ROOT / local_license_path).is_file()

    gonka = by_name["verification-before-completion"]
    trail = by_name["designing-workflow-skills"]
    assert "source_notice_paths" in gonka
    assert gonka["source_notice_paths"] == []
    assert trail["local_license_path"] is None
    assert "removal_ref" in trail
    assert trail["removal_ref"] == ("1256982d4d925a0acfe11e26c2253c32052c6247")


def test_lencx_import_hashes_reproduce_exact_local_bytes() -> None:
    source = next(
        item for item in manifest()["sources"] if item["name"] == "coding-protocol"
    )
    assert "imported_files" in source
    imported_files = source["imported_files"]
    assert isinstance(imported_files, list)
    assert {
        (imported["upstream_path"], imported["local_path"])
        for imported in imported_files
    } == LENCX_IMPORTED_PATHS
    assert len(imported_files) == len(LENCX_IMPORTED_PATHS)

    for imported in imported_files:
        path = REPOSITORY_ROOT / imported["local_path"]
        assert path.is_file()
        assert sha256(path) == imported["local_sha256"]
        assert len(imported["upstream_sha256"]) == 64
        assert len(imported["upstream_git_blob"]) == 40

    changed_paths = {
        "thirdparty/skills/coding-protocol/SKILL.md",
        "thirdparty/skills/coding-protocol/references/rule-rationale.md",
    }
    assert all(
        imported["local_sha256"] != imported["upstream_sha256"]
        for imported in imported_files
        if imported["local_path"] in changed_paths
    )
    unchanged_paths = {
        "skills/coding-protocol/references/verification.md",
        source["license_source_path"],
    }
    unchanged = [
        imported
        for imported in imported_files
        if imported["upstream_path"] in unchanged_paths
    ]
    assert len(unchanged) == len(unchanged_paths)
    assert all(
        imported["local_sha256"] == imported["upstream_sha256"]
        for imported in unchanged
    )
    for imported in unchanged:
        blob = subprocess.run(
            ["git", "hash-object", str(REPOSITORY_ROOT / imported["local_path"])],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert blob == imported["upstream_git_blob"]

    license_file = next(
        imported
        for imported in imported_files
        if imported["upstream_path"] == source["license_source_path"]
    )
    assert license_file["local_path"] == source["local_license_path"]

    assert source["source_blob_sha256"] == (
        "cb62f9878a21491202867663bf9dc442e061be698a8adb196f481a01f668ff7f"
    )
    assert source["source_blob_sha256"] != sha256(
        REPOSITORY_ROOT / "thirdparty/skills/coding-protocol/SKILL.md"
    )


def test_gonkagate_derivative_and_trail_method_boundary_are_recorded() -> None:
    by_name = {source["name"]: source for source in manifest()["sources"]}
    gonka = by_name["verification-before-completion"]
    assert "local_derivative_path" in gonka
    assert "local_derivative_sha256" in gonka
    derivative = REPOSITORY_ROOT / gonka["local_derivative_path"]
    text = derivative.read_text(encoding="utf-8")
    assert sha256(derivative) == gonka["local_derivative_sha256"]
    assert "Apache-2.0 derivative notice" in text
    assert "461578373f9c3a8eae3037504f659e0f3e0cc7cd" in text
    assert "Local modifications:" in text
    assert "Node, TypeScript" in text

    trail = by_name["designing-workflow-skills"]
    assert trail["local_license_path"] is None
    assert len(trail["source_blob_sha256"]) == 64
    assert "independent_expression_review" in trail
    assert "independently expressed" in trail["independent_expression_review"]


def test_sources_tsv_matches_manifest_exact_policies() -> None:
    with (REPOSITORY_ROOT / "thirdparty/sources.tsv").open(
        encoding="utf-8", newline=""
    ) as source_file:
        rows = {row["name"]: row for row in csv.DictReader(source_file, delimiter="\t")}

    for name, policy in POLICIES.items():
        assert rows[name]["local_policy"] == policy

    assert rows["coding-protocol"]["imported_ref"] == (
        "b848e124111be50a795cc961558247e7751825e2"
    )
    assert rows["verification-before-completion"]["upstream_ref_checked"] == (
        "461578373f9c3a8eae3037504f659e0f3e0cc7cd"
    )
    assert rows["designing-workflow-skills"]["upstream_ref_checked"] == (
        "293fb74c3151cceda32a85a545fe8acd67f8f5c6"
    )
    assert "remains inert" in rows["coding-protocol"]["notes"]
    assert (
        "installer-managed nor implicitly invoked" in rows["coding-protocol"]["notes"]
    )
    assert "current local derivative" in rows["verification-before-completion"]["notes"]
    assert (
        "planned local derivative"
        not in rows["verification-before-completion"]["notes"]
    )


def test_inert_coding_protocol_is_explicit_only_and_not_installer_managed() -> None:
    metadata = (
        REPOSITORY_ROOT / "thirdparty/skills/coding-protocol/agents/openai.yaml"
    ).read_text(encoding="utf-8")
    assert "allow_implicit_invocation: false" in metadata

    errors: list[str] = []
    active_skills = _installer_skills(REPOSITORY_ROOT, errors)
    assert errors == []
    assert REPOSITORY_ROOT / "thirdparty/skills/coding-protocol" not in active_skills
