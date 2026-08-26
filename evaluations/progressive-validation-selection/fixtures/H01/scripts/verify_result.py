from pathlib import Path


if "printf 'hello, calibration\\n'" not in Path("README.md").read_text():
    raise SystemExit("README example is not repaired")
