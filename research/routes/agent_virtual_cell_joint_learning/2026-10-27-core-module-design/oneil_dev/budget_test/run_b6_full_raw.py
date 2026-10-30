"""ON3-READY.2 raw budget evidence: full B6 refit_cu_only 1,000 x 5 (5,000 real permutations).

Prints a raw progress/stdout log (redirected to budget_test/b6_full_raw.log) and writes
budget_test/b6_full_raw.json with counts, per-fold progress, wall-clock and null summary.
Synthetic shapes = frozen design; NO response values read; NO ON3 effect run.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

ROOT = r'D:\MAESTRO'
REF = os.path.join(ROOT, 'research', '2026-10-27-core-module-design', 'oneil_dev', 'on3_refimpl')
OUT = os.path.join(ROOT, 'research', '2026-10-27-core-module-design', 'oneil_dev', 'budget_test')
sys.path.insert(0, REF)
import refimpl as R  # noqa: E402

FOLD_UNITS = [68152, 66743, 66556, 69738, 68899]
FOLD_MASKED = [31767, 30824, 30876, 32400, 31901]
TARGET30_UNITS = 340088
N_PAIRS = 703
N_PARTNERS = 37
N_PERM = 1000
BUDGET_SECONDS = 45 * 60


def make_fold(fseed, units, masked_n):
    rng = np.random.default_rng(fseed)
    train_n = TARGET30_UNITS - units
    train = {"cell_id": rng.integers(0, 24, train_n), "pair_id": rng.integers(0, N_PAIRS, train_n),
             "partner_id": rng.integers(0, N_PARTNERS, train_n), "role_id": rng.integers(0, 2, train_n),
             "y": rng.normal(0, 0.2, train_n)}
    cells = 6
    per_cell_masked = (masked_n // cells) * np.ones(cells, dtype=int)
    per_cell_masked[: masked_n - per_cell_masked.sum()] += 1
    unmasked_n = units - masked_n
    per_cell_unmasked = (unmasked_n // cells) * np.ones(cells, dtype=int)
    per_cell_unmasked[: unmasked_n - per_cell_unmasked.sum()] += 1

    def held(counts):
        n = int(counts.sum())
        return {"cell_id": np.repeat(np.arange(cells), counts),
                "pair_id": rng.integers(0, N_PAIRS, n), "partner_id": rng.integers(0, N_PARTNERS, n),
                "role_id": rng.integers(0, 2, n), "stratum": rng.integers(0, N_PARTNERS * 2, n),
                "y": rng.normal(0, 0.2, n)}
    md = held(per_cell_masked)
    mu = held(per_cell_unmasked)
    mu["stratum"] = mu["partner_id"] * 2 + mu["role_id"]
    return {"train": train, "masked_units": md, "unmasked_units": mu, "masked_y": md["y"], "obs_y": md["y"]}


def main():
    t_start = time.time()
    print("[b6-raw] command: python -X utf8 budget_test/run_b6_full_raw.py")
    print("[b6-raw] semantics=refit_cu_only: training structure (B2 + B4 pair factors V) fitted ONCE per fold;")
    print("[b6-raw] per permutation only held-out cell c_cell/U_cell re-estimated from permuted NON-masked context.")
    print("[b6-raw] synthetic shapes = frozen design; no response values read.")
    fold_rows = []
    all_drho = []
    total_perms = 0
    for f in range(5):
        t0 = time.time()
        fd = make_fold(1000 + f, FOLD_UNITS[f], FOLD_MASKED[f])
        b4 = R.fit_b4(fd["train"], rank=3, lam=0.1, refit_factors=True)  # fitted ONCE per fold
        pred_b2 = R.predict_b2(b4["b2"], fd["masked_units"])
        rho_b2 = R.spearman(pred_b2, fd["masked_y"])
        rng = np.random.default_rng(20261130 + f)
        rho_list = []
        drho_list = []
        t_fold = time.time()
        for p in range(N_PERM):
            perm = dict(fd["unmasked_units"])
            perm["cell_id"] = R._permute_cell_within_strata(perm, rng)
            c, U = R.fit_context_factors(perm, b4, 0.1)
            pred = R.predict_b4(fd["masked_units"], b4, c, U)
            rho = R.spearman(pred, fd["masked_y"])
            rho_list.append(rho)
            drho_list.append(rho - rho_b2)
            total_perms += 1
            if (p + 1) % 100 == 0:
                print("[b6-raw] fold=%d perm=%d/%d cum_perms=%d elapsed_fold=%.2fs elapsed_total=%.2fs"
                      % (f, p + 1, N_PERM, total_perms, time.time() - t_fold, time.time() - t_start))
        wall = time.time() - t0
        all_drho.extend(drho_list)
        fold_rows.append({"fold": f, "perms": N_PERM, "wall_seconds": round(wall, 3),
                          "train_fit_seconds": round(t_fold - t0, 3),
                          "null_delta_rho_mean": float(np.mean(drho_list)),
                          "null_delta_rho_q95": float(np.percentile(drho_list, 95))})
        print("[b6-raw] fold=%d DONE perms=%d fold_wall=%.2fs cum_total_perms=%d"
              % (f, N_PERM, wall, total_perms))
    wall_total = time.time() - t_start
    all_drho = np.asarray(all_drho)
    out = {
        "task": "R199-ON3-READY.2 full raw B6 budget evidence",
        "command": "python -X utf8 research/2026-10-27-core-module-design/oneil_dev/budget_test/run_b6_full_raw.py",
        "semantics": "refit_cu_only",
        "semantics_assertion": ("training structure fitted once per fold; per permutation only "
                               "held-out c_cell/U_cell re-estimated from permuted non-masked context"),
        "synthetic": True,
        "response_values_read": False,
        "n_perm_per_fold": N_PERM,
        "n_folds": 5,
        "total_real_permutations": total_perms,
        "expected_total_permutations": N_PERM * 5,
        "total_perms_match": bool(total_perms == N_PERM * 5),
        "folds": fold_rows,
        "wall_seconds_measured": round(wall_total, 3),
        "budget_seconds": BUDGET_SECONDS,
        "budget_ok": bool(wall_total <= BUDGET_SECONDS),
        "null_delta_rho_mean": float(all_drho.mean()),
        "null_delta_rho_q95": float(np.percentile(all_drho, 95)),
        "stdout_log_path_rel": "research/2026-10-27-core-module-design/oneil_dev/budget_test/b6_full_raw.log",
    }
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'b6_full_raw.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write('\n')
    print("[b6-raw] FINAL total_real_permutations=%d wall=%.3fs budget<=%ds: %s"
          % (total_perms, wall_total, BUDGET_SECONDS, wall_total <= BUDGET_SECONDS))
    print("[b6-raw] wrote", os.path.join(OUT, 'b6_full_raw.json'))


if __name__ == '__main__':
    main()
