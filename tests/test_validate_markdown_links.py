from __future__ import annotations

import runpy
import sys
from pathlib import Path
from typing import cast

import pytest

from scripts.validate_markdown_links import (
    _link_path,
    discover_markdown_files,
    main,
    validate_markdown_links,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_repository_markdown_links_pass() -> None:
    assert validate_markdown_links(REPOSITORY_ROOT) == []


def test_discovers_root_files_and_nested_markdown(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Readme\n", encoding="utf-8")
    (tmp_path / "docs/nested").mkdir(parents=True)
    nested = tmp_path / "docs/nested/page.md"
    nested.write_text("# Page\n", encoding="utf-8")

    assert discover_markdown_files(tmp_path) == [tmp_path / "README.md", nested]


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        ("https://example.com/page", None),
        ("mailto:person@example.com", None),
        ("#section", None),
        ("<page%20name.md>", "page name.md"),
        ('page.md "title"', "page.md"),
    ],
)
def test_link_path_classification(target: str, expected: str | None) -> None:
    assert _link_path(target) == expected


def test_reports_missing_absolute_and_escaping_links(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "source.md").write_text(
        "[missing](missing.md)\n[absolute](/tmp/file.md)\n[escape](../../outside.md)\n",
        encoding="utf-8",
    )

    errors = validate_markdown_links(tmp_path)

    assert len(errors) == 3
    assert any("missing Markdown link target" in error for error in errors)
    assert any("absolute Markdown link" in error for error in errors)
    assert any("Markdown link escapes repository" in error for error in errors)


def test_main_reports_success_and_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "README.md").write_text("# Readme\n", encoding="utf-8")
    assert main(["--root", str(tmp_path)]) == 0
    assert "Validated 1 Markdown files." in capsys.readouterr().out

    (tmp_path / "README.md").write_text("[missing](missing.md)\n", encoding="utf-8")
    assert main(["--root", str(tmp_path)]) == 1
    captured = capsys.readouterr()
    assert "ERROR:" in captured.err
    assert "Markdown link validation failed with 1 error(s)." in captured.err


def test_script_entrypoint_exits_with_main_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "README.md").write_text("# Readme\n", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["validate_markdown_links.py", "--root", str(tmp_path)],
    )
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(
            str(REPOSITORY_ROOT / "scripts/validate_markdown_links.py"),
            run_name="__main__",
        )
    assert cast(int, exc_info.value.code) == 0
