from __future__ import annotations

from tests.support import REPOSITORY_ROOT

NAMING = REPOSITORY_ROOT / "skills/calibration/references/naming"


def test_naming_entrypoint_preserves_contracts_and_routes_to_sources() -> None:
    guide = " ".join((NAMING / "README.md").read_text(encoding="utf-8").split())
    for boundary in (
        "Read only the source needed",
        "Preserve published compatibility",
        "protocols, overrides, serialization, or framework integration",
        "does not authorize renaming an existing interface",
        "Follow repository conventions and the API being extended",
        "Let configured formatters and linters check mechanical conventions",
        "R projects adopting tidyverse conventions",
        "state the gap",
    ):
        assert boundary in guide
    for source in (
        "https://peps.python.org/pep-0008/#naming-conventions",
        "https://rust-lang.github.io/api-guidelines/naming.html",
        "https://style.tidyverse.org/syntax.html#object-names",
    ):
        assert f"]({source})" in guide


def test_former_naming_paths_are_compatibility_pointers() -> None:
    for name in ("function", "method", "type", "variable", "loop"):
        guide = (NAMING / f"{name}.md").read_text(encoding="utf-8")
        assert "](README.md)" in guide
        assert "| ---" not in guide
    method = (NAMING / "method.md").read_text(encoding="utf-8")
    assert "protocol and override names" in method
    assert "../design/codebase.md" in method
    loop = (NAMING / "loop.md").read_text(encoding="utf-8")
    assert "ignored or unused values" in loop
    assert "No cross-project binder prefix is required" in loop
    branch = (NAMING / "branch.md").read_text(encoding="utf-8")
    assert "branch_and_pr_collaboration/20260602-v1.0.md" in branch
    assert "codex/<type>" not in branch


def test_remaining_specialized_contracts_are_still_routed() -> None:
    guide = (NAMING / "README.md").read_text(encoding="utf-8")
    for name in ("cli", "version", "schema", "artifact"):
        assert f"]({name}.md)" in guide
        assert (NAMING / f"{name}.md").is_file()
