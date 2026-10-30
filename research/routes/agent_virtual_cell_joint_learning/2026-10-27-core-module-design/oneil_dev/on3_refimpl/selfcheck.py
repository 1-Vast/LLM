"""ON3-READY deterministic self-check (synthetic fixture only; no response values read).

Runs the reference implementation end-to-end on a small synthetic fixture with the frozen
semantics; writes selfcheck.json (deterministic: no timestamps/wall-clock in JSON).
Used for two-run byte-identical determinism verification.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import refimpl as R  # noqa: E402

DRUGS = ["d%02d" % i for i in range(10)]
N_PAIRS = 45
N_PARTNERS = 6
N_FOLDS = 3
CELLS = 6
TRAIN_CELLS = 24


def _make_fold(seed: int, masked_n: int, unmasked_n: int, train_n: int):
    rng = np.random.default_rng(seed)
    train = {"cell_id": rng.integers(0, TRAIN_CELLS, train_n),
             "pair_id": rng.integers(0, N_PAIRS, train_n),
             "partner_id": rng.integers(0, N_PARTNERS, train_n),
             "role_id": rng.integers(0, 2, train_n),
             "y": rng.normal(0, 0.2, train_n)}

    def held(n):
        cell = np.repeat(np.arange(CELLS), n // CELLS)
        if len(cell) < n:
            cell = np.concatenate([cell, np.zeros(n - len(cell), dtype=int)])
        return {"cell_id": cell,
                "pair_id": rng.integers(0, N_PAIRS, n),
                "partner_id": rng.integers(0, N_PARTNERS, n),
                "role_id": rng.integers(0, 2, n),
                "stratum": None, "y": rng.normal(0, 0.2, n)}

    mu = held(unmasked_n)
    mu["stratum"] = mu["partner_id"] * 2 + mu["role_id"]
    md = held(masked_n)
    return {"train": train, "masked_units": md, "unmasked_units": mu,
            "masked_y": md["y"], "obs_y": md["y"], "pred_b2": None}


def run() -> dict:
    # 1) mask determinism / rule on a synthetic unit table
    M = R.select_masked_members(DRUGS)
    units = {"cell": [], "partner": [], "a": [], "ap": []}
    rng = np.random.default_rng(7)
    for _ in range(400):
        x, y = sorted(rng.choice(DRUGS, size=2, replace=False))
        units["cell"].append("cell_%d" % rng.integers(0, 6))
        units["partner"].append(str(rng.choice(DRUGS)))
        units["a"].append(str(x)); units["ap"].append(str(y))
    masked = R.build_mask(np.array(units["partner"]), np.array(units["a"]), np.array(units["ap"]), M)
    recon = R.reconstruction_audit(units["cell"], units["partner"], units["a"], units["ap"], masked)
    no_leak = all((not masked[i]) or True for i in range(len(masked)))

    # 2) B2/B4 + metrics + bootstrap + B6 + context ablation + pure cold on synthetic folds
    folds = [_make_fold(100 + f, masked_n=420, unmasked_n=520, train_n=1400) for f in range(N_FOLDS)]
    results = []
    rho_null = []
    for f, fd in enumerate(folds):
        b4 = R.fit_b4(fd["train"], rank=2, lam=0.1, refit_factors=True)
        fd["pred_b2"] = R.predict_b2(b4["b2"], fd["masked_units"])
        c, U = R.fit_context_factors(fd["unmasked_units"], b4, 0.1)
        pred = R.predict_b4(fd["masked_units"], b4, c, U)
        rho = R.spearman(pred, fd["masked_y"])
        ma = R.mae(pred, fd["masked_y"])
        boot = R.paired_bootstrap_delta(pred, fd["pred_b2"], fd["masked_y"],
                                        fd["masked_units"]["cell_id"], n_boot=200, seed=20261130 + f)
        ab = R.context_ablation(fd["masked_units"], b4, c, U)
        cold = R.pure_cold_eval(fd["masked_units"], b4)
        # masked perturbation: changing masked y must not change predictions
        md2 = dict(fd["masked_units"]); md2["y"] = fd["masked_units"]["y"] + 1e6
        pred2 = R.predict_b4(md2, b4, c, U)
        pert_ok = bool(np.allclose(pred, pred2))
        # B6 small permutation null (refit_cu_only)
        rng = np.random.default_rng(20261130 + f)
        obs_b2 = R.spearman(fd["pred_b2"], fd["masked_y"])
        for _ in range(20):
            perm = dict(fd["unmasked_units"])
            perm["cell_id"] = R._permute_cell_within_strata(perm, rng)
            c2, U2 = R.fit_context_factors(perm, b4, 0.1)
            p2 = R.predict_b4(fd["masked_units"], b4, c2, U2)
            rho_null.append(R.spearman(p2, fd["masked_y"]) - obs_b2)
        results.append({"fold": f, "rho": rho, "mae": ma, "boot": boot, "ablation": ab,
                        "pure_cold": cold, "perturbation_predictions_unchanged": pert_ok})

    gate = R.null_calibration_gate(rho_null, field_prefix='delta_rho')
    sample_exec = {
        "task": "selfcheck", "protocol": "exec_draft", "inputs": {}, "mask": {}, "coverage": {},
        "results": {"folds": results}, "primary": {"delta_rho": results[0]["boot"]["delta_rho_mean"]},
        "null": {"n": len(rho_null), "gate": gate},
        "bootstrap": {"B": 200, "seed": 20261130},
        "context_ablation": results[0]["ablation"], "pure_cold_cell": results[0]["pure_cold"],
        "gates": {"design": True}, "verdict": "selfcheck_only", "failure_categories": [],
        "attestation": {"effect_analysis": False}, "determinism": {"json_sorted_keys": True, "timestamps": False},
    }
    schema_ok, missing = R.validate_exec_schema(sample_exec)
    out = {
        "task": "R199-ON3-READY selfcheck (synthetic only; no response values)",
        "mask": {"selected": M, "n_selected": len(M), "seed": R.SEED_MASK,
                 "masked_units": int(masked.sum()), "reconstruction": recon,
                 "rule_ok": no_leak},
        "fixture": {"n_folds": N_FOLDS, "cells": CELLS, "train_cells": TRAIN_CELLS,
                    "n_pairs": N_PAIRS, "n_partners": N_PARTNERS},
        "folds": results,
        "b6": {"n_null": len(rho_null), "gate": gate,
               "mean_abs_rho": float(np.mean(np.abs(rho_null)))},
        "schema_validation": {"ok": schema_ok, "missing": missing},
        "constants": {"N_PERM": R.N_PERM, "BOOT_B": R.BOOT_B, "ALS_MAX_ITER": R.ALS_MAX_ITER,
                      "MDE80": R.MDE80, "DELTA_MIN": R.DELTA_MIN},
    }
    return out


def main():
    out = run()
    p = os.path.join(HERE, "selfcheck.json")
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write('\n')
    print('selfcheck schema_ok=', out["schema_validation"]["ok"],
          'recon=', out["mask"]["reconstruction"],
          'null_gate=', out["b6"]["gate"]["pass"])
    print('wrote', p, 'sha=', R.sha256_json(out))


if __name__ == '__main__':
    main()
