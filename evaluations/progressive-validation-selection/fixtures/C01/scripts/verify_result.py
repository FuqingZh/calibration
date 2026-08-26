from pathlib import Path

raise SystemExit(
    0
    if Path("live-canary-contract.txt").read_text(encoding="utf-8")
    == "live-canary-contract-v1\n"
    else 1
)
