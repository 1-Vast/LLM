"""ON3-READY budget test: B6 1,000 x 5 folds x B4 (two frozen semantics).

NO ON3 effect analysis: synthetic responses only (same shapes/mask counts as frozen design);
no response values read. Measures wall-clock and decides feeasible B6 semantics/count.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

ROOT = r'D:\MAESTRO'
REF = os.path.join(ROOT, 'research', '2026-10-27-core-module-design', 'oneil_dev', 'on3_refimpl')
sys.path.insert(0, REF)
import refimpl as R  # noqa: E402

OUT = os.path.join(ROOT, 'research', '2026-10-27-core-module-design', 'oneil_dev', 'budget_test')
FOLD_UNITS = [68152, 66743, 66556, 69738, 68899]
FOLD_MASKED = [31767, 30824, 30876, 32400, 31901]
FOLD_CONTEXTS = [372, 368, 369, 372, 371]
TARGET30_UNITS = 340088
N_PAIRS = 703
N_PARTNERS = 37
N_PERM = 1000
BUDGET_SECONDS = 45 * 60


def make_fold(fseed, units, masked_n, contexts, n_perm):
    rng = np.random.default_rng(fseed)
    train_n = TARGET30_UNITS - units
    train_cells = 24
    tr_cell = rng.integers(0, train_cells, train_n)
    tr_pair = rng.integers(0, N_PAIRS, train_n)
    tr_part = rng.integers(0, N_PARTNERS, train_n)
    tr_role = rng.integers(0, 2, train_n)
    tr_y = rng.normal(0, 0.2, train_n)
    train = {"cell_id": tr_cell, "pair_id": tr_pair, "partner_id": tr_part,
             "role_id": tr_role, "y": tr_y}
    # held-out: 6 cells; allocate masked/unmasked per cell
    cells = 6
    per_cell_masked = (masked_n // cells) * np.ones(cells, dtype=int)
    per_cell_masked[: masked_n - per_cell_masked.sum()] += 1
    unmasked_n = units - masked_n
    per_cell_unmasked = (unmasked_n // cells) * np.ones(cells, dtype=int)
    per_cell_unmasked[: unmasked_n - per_cell_unmasked.sum()] += 1
    def build(counts):
        n = int(counts.sum())
        cell = np.repeat(np.arange(cells), counts)
        pair = rng.integers(0, N_PAIRS, n)
        part = rng.integers(0, N_PARTNERS, n)
        role = rng.integers(0, 2, n)
        return {"cell_id": cell, "pair_id": pair, "partner_id": part, "role_id": role,
                "stratum": part * 2 + role, "y": rng.normal(0, 0.2, n)}
    masked_units = build(per_cell_masked)
    unmasked_units = build(per_cell_unmasked)
    return {"train": train, "masked_units": masked_units, "unmasked_units": unmasked_units,
            "masked_y": masked_units["y"], "obs_y": masked_units["y"], "n_perm": n_perm}


def bench_semantics(semantics, n_perm, folds_data):
    """Return timing + null summaries for B6 under given semantics."""
    t0 = time.time()
    t_fit = 0.0
    rho_list = []
    for f, fd in enumerate(folds_data):
        tf = time.time()
        b4 = R.fit_b4(fd["train"], rank=3, lam=0.1, refit_factors=True)
        t_fit += time.time() - tf
        pred_b2 = R.predict_b2(b4["b2"], fd["masked_units"])
        rho_b2 = R.spearman(pred_b2, fd["masked_y"])
        rng = np.random.default_rng(20261130 + f)
        for p in range(n_perm):
            if semantics == "full_refit":
                b4p = R.fit_b4(fd["train"], rank=3, lam=0.1, refit_factors=True)
            else:
                b4p = b4
            perm = dict(fd["unmasked_units"])
            perm["cell_id"] = R._permute_cell_within_strata(perm, rng)
            c, U = R.fit_context_factors(perm, b4p, 0.1)
            pred = R.predict_b4(fd["masked_units"], b4p, c, U)
            rho_list.append(R.spearman(pred, fd["masked_y"]) - rho_b2)
    wall = time.time() - t0
    return {"semantics": semantics, "n_perm_per_fold": n_perm, "folds": len(folds_data),
            "total_perms": n_perm * len(folds_data), "wall_seconds": round(wall, 3),
            "fixed_fit_seconds": round(t_fit, 3),
            "null_delta_rho_mean": float(np.mean(rho_list)),
            "null_delta_rho_q95": float(np.percentile(rho_list, 95))}


def main():
    os.makedirs(OUT, exist_ok=True)
    t_start = time.time()
    pilot_folds = [make_fold(1000 + f, FOLD_UNITS[f], FOLD_MASKED[f], FOLD_CONTEXTS[f], n_perm=20)
                   for f in range(5)]
    pilot = bench_semantics("refit_cu_only", 20, pilot_folds)
    per_perm_pilot = (pilot["wall_seconds"] - pilot["fixed_fit_seconds"]) / (20 * 5)
    est_1000 = per_perm_pilot * 1000 * 5 + 5 * pilot["fixed_fit_seconds"]
    print("pilot refit_cu_only", pilot, "per_perm", per_perm_pilot, "est_1000", est_1000)

    # full S2 (refit_cu_only) full 1,000 x 5 if estimate within 2x budget
    if est_1000 <= 2 * BUDGET_SECONDS:
        full_folds = [make_fold(2000 + f, FOLD_UNITS[f], FOLD_MASKED[f], FOLD_CONTEXTS[f], n_perm=N_PERM)
                      for f in range(5)]
        s2_full = bench_semantics("refit_cu_only", N_PERM, full_folds)
    else:
        s2_full = {"skipped": True, "reason": "estimate > 2x budget", "est_1000": est_1000}

    # full-refit semantics extrapolation: 5 perms/fold (times 5 folds), extrapolate to 1,000
    ff_folds = [make_fold(3000 + f, FOLD_UNITS[f], FOLD_MASKED[f], FOLD_CONTEXTS[f], n_perm=5) for f in range(5)]
    ff = bench_semantics("full_refit", 5, ff_folds)
    ff_per_perm = (ff["wall_seconds"] - ff["fixed_fit_seconds"]) / (5 * 5)
    est_ff_1000 = ff_per_perm * 1000 * 5 + 5 * ff["fixed_fit_seconds"]
    print("full_refit pilot", ff, "per_perm", ff_per_perm, "est_1000", est_ff_1000)

    s2_wall = s2_full.get("wall_seconds")
    feasible_s2 = (s2_wall is not None) and (s2_wall <= BUDGET_SECONDS)
    ff_feasible = est_ff_1000 <= BUDGET_SECONDS
    if feasible_s2:
        frozen = {"semantics": "refit_cu_only", "n_perm": N_PERM, "decision": "freeze refit_cu_only 1000 perms",
                  "wall_seconds_measured": s2_wall}
    elif s2_wall is not None:
        frozen = {"semantics": "refit_cu_only", "n_perm": 500, "decision": "freeze refit_cu_only 500 perms (pre-freeze adjustment)",
                  "wall_seconds_measured_at_1000": s2_wall}
    else:
        frozen = {"semantics": "refit_cu_only", "n_perm": N_PERM, "decision": "needs full measurement",
                  "est_1000": est_1000}
    out = {
        "task": "R199-ON3-READY budget test (synthetic data only; NO response values read)",
        "inputs": {"fold_units": FOLD_UNITS, "fold_masked": FOLD_MASKED, "fold_contexts": FOLD_CONTEXTS,
                   "target30_units": TARGET30_UNITS, "n_pairs": N_PAIRS, "n_partners": N_PARTNERS},
        "pilot_refit_cu_only": pilot,
        "per_perm_refit_cu_only": per_perm_pilot,
        "est_1000x5_refit_cu_only": est_1000,
        "full_1000x5_refit_cu_only": s2_full,
        "full_refit_pilot": ff,
        "per_perm_full_refit": ff_per_perm,
        "est_1000x5_full_refit": est_ff_1000,
        "budget_seconds": BUDGET_SECONDS,
        "feasible_refit_cu_only_1000": feasible_s2,
        "feasible_full_refit_1000": ff_feasible,
        "frozen_b6_semantics": frozen,
        "total_wall_seconds": round(time.time() - t_start, 3),
    }
    with open(os.path.join(OUT, 'budget_test.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write('\n')
    print(json.dumps({"feasible_s2": feasible_s2, "feasible_ff": ff_feasible,
                      "frozen": frozen, "wall": out["total_wall_seconds"]}, indent=1))
    print('wrote', os.path.join(OUT, 'budget_test.json'))


if __name__ == '__main__':
    main()
