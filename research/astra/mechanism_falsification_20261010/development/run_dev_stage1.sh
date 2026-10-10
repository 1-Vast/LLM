#!/usr/bin/env bash
# Development stage 1 (open tier): baseline and the knowledge-calibration choice.
set -euo pipefail
PY=/d/anaconda/envs/maestro/python.exe
cd /d/MAESTRO/research/astra/mechanism_falsification_20261010
"$PY" dev_run.py baseline '{}' --budget 4 --policies fixed,random,magnitude,falsify > development/baseline.log 2>&1 &
"$PY" dev_run.py kcal_small '{"kcal": "small"}' --budget 4 --policies fixed,falsify > development/kcal_small.log 2>&1 &
"$PY" dev_run.py kcal_all '{"kcal": "all"}' --budget 4 --policies fixed,falsify > development/kcal_all.log 2>&1 &
wait
echo STAGE1_DONE
