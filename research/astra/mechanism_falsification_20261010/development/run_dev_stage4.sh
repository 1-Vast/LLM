#!/usr/bin/env bash
# Development stage 4: content controls under the chosen world model (non-adaptive designs, set calibration).
set -uo pipefail
PY=/d/anaconda/envs/maestro/python.exe
cd /d/MAESTRO/research/astra/mechanism_falsification_20261010
BASE='"score": "relative", "kcal": "all", "kappa": 0.05, "tau2": 10.0, "n_bins": 3'
run() { "$PY" -W ignore dev_run.py "$1" "{$BASE$2}" --budget 4 --policies fixed,random $3 > "development/$1.log" 2>&1; }
run s4_perm_classes ', "permute_classes": true' "" &
run s4_perm_emh ', "permute_emh": true' "" &
run s4_nolit ', "emh_variant": "nolit"' "" &
wait
run s4_critic ', "emh_variant": "lit_critic"' "" &
run s4_c2_open ', "knowledge_for_unreferenced": false' "" &
run s4_c2_closed '' "--hyp library" &
wait
"$PY" -W ignore dev_identifiability.py s4_identifiability "{$BASE}" > development/s4_identifiability.log 2>&1 &
"$PY" -W ignore dev_revision.py s4_revision "{$BASE}" --budget 4 --agent > development/s4_revision.log 2>&1 &
wait
echo STAGE4_DONE
