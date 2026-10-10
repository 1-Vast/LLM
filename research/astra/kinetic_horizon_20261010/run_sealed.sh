#!/usr/bin/env bash
# One-time sealed run of block K (after FREEZE.json). The Tahoe zero-shot PRISM tier stays sealed.
set -euo pipefail
PY=/d/anaconda/envs/maestro/python.exe
D=/d/MAESTRO/research/astra/kinetic_horizon_20261010
test -f "$D/FREEZE.json"
"$PY" -W ignore "$D/prism_extract.py" confirmation --allow-sealed
"$PY" -W ignore "$D/prism_extract.py" mix_sealed --allow-sealed
for u in A_treated_sealed C_treated D_treated; do "$PY" "$D/mixseq_extract.py" "$u" --allow-sealed; done
"$PY" "$D/evaluate.py"
"$PY" "$D/verify.py"
