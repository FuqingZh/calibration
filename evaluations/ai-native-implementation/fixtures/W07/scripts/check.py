"""Run the fixture's declared type and runtime checks."""

from __future__ import annotations

import os
import subprocess
import sys


def main() -> int:
    """Return the first nonzero result from Pyright or pytest."""
    environment = os.environ.copy()
    python_path = [".", "vendor"]
    if inherited := environment.get("PYTHONPATH"):
        python_path.append(inherited)
    environment["PYTHONPATH"] = os.pathsep.join(python_path)
    for command in (("pyright",), (sys.executable, "-m", "pytest", "-q")):
        result = subprocess.run(command, env=environment, check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
