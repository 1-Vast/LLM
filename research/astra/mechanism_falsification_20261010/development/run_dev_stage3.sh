#!/usr/bin/env bash
# Development stage 3: world-model settings from the ranking study (kappa 0.05, tau2 10) with
# set vs episode calibration and energy bins.
set -uo pipefail
PY=/d/anaconda/envs/maestro/python.exe
cd /d/MAESTRO/research/astra/mechanism_falsification_20261010
BASE='"score": "relative", "kcal": "all", "kappa": 0.05, "tau2": 10.0'
"$PY" -W ignore dev_run.py s3_set_b3 "{$BASE, \"n_bins\": 3}" --budget 4 --policies fixed,random,magnitude,falsify > development/s3_set_b3.log 2>&1 &
"$PY" -W ignore dev_run.py s3_ep_b3 "{$BASE, \"n_bins\": 3, \"calib\": \"episode\"}" --budget 4 --policies fixed,falsify > development/s3_ep_b3.log 2>&1 &
"$PY" -W ignore dev_run.py s3_ep_b1 "{$BASE, \"n_bins\": 1, \"calib\": \"episode\"}" --budget 4 --policies falsify > development/s3_ep_b1.log 2>&1 &
wait
echo STAGE3_DONE
