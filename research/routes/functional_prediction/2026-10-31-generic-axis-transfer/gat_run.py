"""Confirmatory run of the GAT study (once, after the freeze).

Usage: python gat_run.py DATA_DIR OUT_DIR
Reads dev_pool.npz, nci60.npz and prism24q2.npz from DATA_DIR (built by gat_data.py) and writes
predictions_<set>.npz, metrics_<set>.csv and RESULTS.json to OUT_DIR.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, "D:/MAESTRO/src")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gat_core import (generic_directions, knn_transfer, mean_cosine, remove_generic,  # noqa: E402
                      selective_hit_precision, tanimoto)
from virtual_cell.transcriptional_transfer import selective_r  # noqa: E402

D = 5                       # generic directions removed (fixed by the rule in DEV_LOG.md section 8)
K = 20                      # neighbours for B1, B2, C1, L (fixed from development)
SEED = 20261031
ARMS = ["B0", "B1", "B2", "C1", "L"]
FAMILY = {"H1": ("C1", "B0"), "H3": ("C1", "B1")}
CONTEXT = {"C1_vs_B2": ("C1", "B2"), "B1_vs_B0": ("B1", "B0")}
ALPHA = 0.05


def predict(sig_q, sig_r, fp_q, fp_r, Y_r, rng):
    """All arms for one query block against one reference block."""
    raw = mean_cosine(sig_q, sig_r)
    dirs = generic_directions(sig_r, D)
    gen = mean_cosine(remove_generic(sig_q, dirs), remove_generic(sig_r, dirs))
    chem = tanimoto(fp_q, fp_r)
    perm = Y_r[rng.permutation(len(Y_r))]
    return {"B0": knn_transfer(raw, Y_r, 5), "B1": knn_transfer(raw, Y_r, K), "B2": knn_transfer(chem, Y_r, K),
            "C1": knn_transfer(gen, Y_r, K), "L": knn_transfer(gen, perm, K)}


def score(pred, Y, G, sign, min_lines):
    r = {a: np.array([selective_r(p, y, g, min_lines=min_lines) for p, y, g in zip(P, Y, G)]) for a, P in pred.items()}
    h = {a: np.array([selective_hit_precision(p, y, g, sign, min_lines=min_lines) for p, y, g in zip(P, Y, G)])
         for a, P in pred.items()}
    return {a: np.nan_to_num(v, nan=0.0) for a, v in r.items()}, {a: np.nan_to_num(v, nan=0.0) for a, v in h.items()}


def contrast(x, y, rng):
    d = x - y
    boot = rng.choice(d, size=(10000, len(d))).mean(axis=1)
    t = stats.ttest_rel(x, y, alternative="greater")
    return {"mean_difference": float(d.mean()), "ci95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
            "t": float(t.statistic), "p_one_sided": float(t.pvalue), "n": int(len(d))}


def holm(tests):
    order = sorted(tests, key=lambda h: tests[h]["p_one_sided"])
    m, rejecting = len(order), True
    for i, h in enumerate(order):
        rejecting = rejecting and tests[h]["p_one_sided"] <= ALPHA / (m - i)
        tests[h]["holm_reject"] = bool(rejecting)
    return tests


def run_nci(data):
    d = np.load(data / "nci60.npz", allow_pickle=True)
    Y, X, fp, fold = d["profile"], d["signature"], d["fingerprint"], d["fold"]
    pred = {a: np.full(Y.shape, np.nan) for a in ARMS}
    G = np.full(Y.shape, np.nan)
    rng = np.random.default_rng(SEED)
    for f in range(10):
        q, r = fold == f, fold != f
        G[q] = np.nanmean(Y[r], axis=0)
        for a, P in predict(X[q], X[r], fp[q], fp[r], Y[r], rng).items():
            pred[a][q] = P
    return d, Y, G, pred, +1.0, 40


def run_24q2(data):
    pool = np.load(data / "dev_pool.npz", allow_pickle=True)
    d = np.load(data / "prism24q2.npz", allow_pickle=True)
    col = {ln: i for i, ln in enumerate(pool["line"])}
    Y_r = pool["profile"][:, [col[ln] for ln in d["line"]]]
    Y = d["profile"]
    G = np.repeat(np.nanmean(Y_r, axis=0)[None], len(Y), axis=0)
    pred = predict(d["signature"], pool["signature"], d["fingerprint"], pool["fingerprint"], Y_r,
                   np.random.default_rng(SEED))
    return d, Y, G, pred, -1.0, 50


def main(data: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    results = {"D": D, "K": K, "seed": SEED, "arms": ARMS, "sets": {}}
    for name, runner in (("nci60", run_nci), ("prism24q2", run_24q2)):
        d, Y, G, pred, sign, min_lines = runner(data)
        r, h = score(pred, Y, G, sign, min_lines)
        act = d["active"].astype(bool)
        np.savez_compressed(out / f"predictions_{name}.npz", key=d["key"], line=d["line"], observed=Y, generic=G,
                            active=act, **{f"pred_{a}": P for a, P in pred.items()})
        table = pd.DataFrame({"key": d["key"], "active": act, **{f"r_{a}": r[a] for a in ARMS},
                              **{f"hit_{a}": h[a] for a in ARMS}})
        table.to_csv(out / f"metrics_{name}.csv", index=False, lineterminator="\n")
        rng = np.random.default_rng(SEED)
        fam = holm({hn: contrast(r[a][act], r[b][act], rng) for hn, (a, b) in FAMILY.items()})
        ctx = {cn: contrast(r[a][act], r[b][act], rng) for cn, (a, b) in CONTEXT.items()}
        sec = {hn: contrast(h[a][act], h[b][act], rng) for hn, (a, b) in FAMILY.items()}
        results["sets"][name] = {
            "n_queries": int(len(Y)), "n_active": int(act.sum()), "n_lines": int(Y.shape[1]),
            "primary_mean_active": {a: float(r[a][act].mean()) for a in ARMS},
            "primary_mean_all": {a: float(r[a].mean()) for a in ARMS},
            "primary_mean_inactive": {a: float(r[a][~act].mean()) if (~act).any() else None for a in ARMS},
            "hit_precision_active": {a: float(h[a][act].mean()) for a in ARMS} | {"Z": 0.10},
            "zero_arm_primary": 0.0,
            "family": fam, "context": ctx, "secondary_hit_precision": sec,
            "leakage_control": {"mean": float(r["L"][act].mean()),
                                "p_two_sided": float(stats.ttest_1samp(r["L"][act], 0.0).pvalue)},
        }
        leak = results["sets"][name]["leakage_control"]
        leak["valid"] = bool(abs(leak["mean"]) <= 0.03 or leak["p_two_sided"] >= 0.01)
        if name == "prism24q2":
            results["sets"][name]["parsed_treatments"] = int(d["parsed_treatments"])
            results["sets"][name]["dropped_in_pool"] = [str(k) for k in d["dropped_in_pool"]]
    nci, p24 = results["sets"]["nci60"], results["sets"]["prism24q2"]
    valid = nci["leakage_control"]["valid"] and p24["leakage_control"]["valid"]
    verdict = {}
    for hn in FAMILY:
        if not valid:
            verdict[hn] = "INVALID"
        elif nci["family"][hn]["holm_reject"] and p24["family"][hn]["holm_reject"]:
            verdict[hn] = "REPLICATED"
        elif nci["family"][hn]["holm_reject"] and p24["family"][hn]["mean_difference"] > 0:
            verdict[hn] = "CONFIRMED"
        else:
            verdict[hn] = "NOT_CONFIRMED"
    results["verdict"] = verdict
    results["promote_C1"] = bool(verdict["H1"] in {"CONFIRMED", "REPLICATED"}
                                 and p24["family"]["H3"]["mean_difference"] >= 0)
    (out / "RESULTS.json").write_bytes((json.dumps(results, indent=1) + "\n").encode("utf-8"))
    print(json.dumps({"verdict": verdict, "promote_C1": results["promote_C1"]}, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
