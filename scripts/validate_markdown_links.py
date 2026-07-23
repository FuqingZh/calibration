#!/usr/bin/env python3
"""Validate first-party Markdown links that resolve inside the repository."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


MARKDOWN_ROOTS = (
    Path("README.md"),
    Path("AGENTS.md"),
    Path("docs"),
    Path("references"),
    Path("skills"),
    Path("codex"),
)
MARKDOWN_LINK_PATTERN = re.compile(r"(?<!!)\[[^]]*]\(([^)]+)\)")


def discover_markdown_files(root: Path) -> list[Path]:
    """Return all first-party Markdown files covered by the repository gate."""
    files: list[Path] = []
    for relative in MARKDOWN_ROOTS:
        path = root / relative
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(path.rglob("*.md"))
    return sorted(files)


def _link_path(target: str) -> str | None:
    raw_target = target.strip().split(maxsplit=1)[0].strip("<>")
    split = urlsplit(unquote(raw_target))
    if split.scheme or split.netloc or not split.path:
        return None
    return split.path


def validate_markdown_links(root: Path) -> list[str]:
    """Return broken or nonportable first-party Markdown link errors."""
    root = root.resolve()
    errors: list[str] = []
    for source in discover_markdown_files(root):
        text = source.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK_PATTERN.finditer(text):
            target = match.group(1)
            link_path = _link_path(target)
            if link_path is None:
                continue
            relative = Path(link_path)
            if relative.is_absolute():
                errors.append(f"{source}: absolute Markdown link {target!r}")
                continue
            resolved = (source.parent / relative).resolve()
            try:
                resolved.relative_to(root)
            except ValueError:
                errors.append(f"{source}: Markdown link escapes repository {target!r}")
                continue
            if not resolved.exists():
                errors.append(f"{source}: missing Markdown link target {target!r}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the validator's repository)",
    )
    args = parser.parse_args(argv)
    errors = validate_markdown_links(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(
            f"Markdown link validation failed with {len(errors)} error(s).",
            file=sys.stderr,
        )
        return 1
    print(
        f"Validated {len(discover_markdown_files(args.root.resolve()))} Markdown files."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
