#!/usr/bin/env python3
"""Run the synthetic R worker and stable XLSX consumer."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from xlsx_export import export_workbook


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expression", type=Path, required=True)
    parser.add_argument("--traits", type=Path, required=True)
    parser.add_argument("--modules", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    worker = Path(__file__).with_name("wgcna_worker.R")
    result = subprocess.run(
        [
            "Rscript",
            str(worker),
            str(args.expression),
            str(args.traits),
            str(args.modules),
            str(args.output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        sys.stderr.write(result.stderr)
        return result.returncode
    export_workbook(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
