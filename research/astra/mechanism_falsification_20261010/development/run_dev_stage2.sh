#!/usr/bin/env bash
# Development stage 2 (engine v2): absolute vs relative scores, energy bins, calibration pools.
set -uo pipefail
PY=/d/anaconda/envs/maestro/python.exe
cd /d/MAESTRO/research/astra/mechanism_falsification_20261010
"$PY" -W ignore dev_run.py v2_abs '{"kcal": "all"}' --budget 4 --policies fixed,falsify > development/v2_abs.log 2>&1 &
"$PY" -W ignore dev_run.py v2_rel '{"kcal": "all", "score": "relative"}' --budget 4 --policies fixed,random,magnitude,falsify > development/v2_rel.log 2>&1 &
"$PY" -W ignore dev_run.py v2_rel_b3 '{"kcal": "all", "score": "relative", "n_bins": 3}' --budget 4 --policies fixed,random,magnitude,falsify > development/v2_rel_b3.log 2>&1 &
"$PY" -W ignore dev_run.py v2_rel_mateless '{"score": "relative"}' --budget 4 --policies fixed,falsify > development/v2_rel_mateless.log 2>&1 &
wait
echo STAGE2_DONE
