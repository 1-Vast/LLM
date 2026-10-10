#!/usr/bin/env bash
# One-time held-out execution, in protocol order. Every step refuses to run before FREEZE.json.
set -euo pipefail
cd "$(dirname "$0")"
PY=D:/anaconda/envs/maestro/python.exe
HELD="c12.h5ad c20.h5ad c26.h5ad c27.h5ad c31.h5ad"
test -f FREEZE.json
mkdir -p heldout_logs
$PY obs_extract.py --files $HELD --workers 5 --allow-heldout > heldout_logs/obs.log 2>&1
$PY extract_expression.py --files $HELD --workers 5 --allow-heldout --basal-rows 512 > heldout_logs/expression.log 2>&1
set -- $HELD
targets=("$@")
for i in 0 1 2 3 4; do
  t=${targets[$i]}
  p=${targets[$(( (i + 1) % 5 ))]}
  $PY state_forecast.py --target "$t" >> heldout_logs/state.log 2>&1
  $PY state_forecast.py --target "$t" --basal-from "$p" >> heldout_logs/state.log 2>&1
done
$PY llm_arm.py --files $HELD > heldout_logs/llm.log 2>&1
$PY evaluate.py > heldout_logs/evaluate.log 2>&1
$PY verify.py > heldout_logs/verify.log 2>&1
echo done
