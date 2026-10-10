#!/usr/bin/env bash
# One-time sealed run of block M: freeze, evaluate on the 502 confirmation drugs, verify, receipt.
set -euo pipefail
PY=/d/anaconda/envs/maestro/python.exe
D=/d/MAESTRO/research/astra/mechanism_falsification_20261010
cd "$D"
"$PY" freeze.py
test -f FREEZE.json
"$PY" -u -W ignore evaluate.py
"$PY" -u -W ignore verify.py
"$PY" make_receipt.py
echo SEALED_RUN_DONE
