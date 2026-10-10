#!/usr/bin/env bash
# Development stage 5: agent knowledge as analogies (vs shuffled analogies and a generic prototype).
set -uo pipefail
PY=/d/anaconda/envs/maestro/python.exe
cd /d/MAESTRO/research/astra/mechanism_falsification_20261010
BASE='"score": "relative", "kcal": "all", "kappa": 0.05, "tau2": 10.0, "n_bins": 3'
run() { "$PY" -W ignore dev_run.py "$1" "{$BASE$2}" --budget 4 --policies fixed,random > "development/$1.log" 2>&1; }
run s5_analogy ', "knowledge": "analogy"' &
run s5_analogy_perm ', "knowledge": "analogy_permuted"' &
run s5_generic ', "knowledge": "generic"' &
wait
echo STAGE5_DONE
