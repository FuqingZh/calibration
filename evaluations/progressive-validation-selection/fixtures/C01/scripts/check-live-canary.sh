#!/usr/bin/env bash
set -euo pipefail

grep -Fxq 'live-canary-contract-v1' live-canary-contract.txt
printf 'live canary shell check passed\n'
