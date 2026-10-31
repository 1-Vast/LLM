"""Post hoc analyses of the GAT confirmation sets (exploratory; not part of the frozen verdict).

Usage: python posthoc.py DATA_DIR RUN_DIR OUT_JSON
1. Sensitivity to D (directions removed) at K = 20 on both sets.
2. Gain of C1 over B1 by tertile of the query's generic fraction (share of its centred signature energy that lies
   in the top-5 reference directions).
3. Neighbour bias: generic fraction of the 20 raw-cosine neighbours vs the 20 C1 neighbours, relative to the query.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "D:/MAESTRO/src")
sys.path.insert(0, "D:/MAESTRO/research/routes/functional_prediction/2026-10-31-generic-axis-transfer")
from gat_core import generic_directions, knn_transfer, mean_cosine, remove_generic  # noqa: E402
from virtual_cell.transcriptional_transfer import selective_r  # noqa: E402

K = 20
DS = [0, 1, 3, 5, 10, 20]
rng = np.random.default_rng(20261031)


def generic_fraction(sig, dirs):
    """Mean over measured options of |projection on the directions|^2 / |centred signature|^2."""
    out = np.full(len(sig), np.nan)
    num = np.zeros(len(sig))
    cnt = np.zeros(len(sig))
    for o, (mu, V) in enumerate(dirs):
        have = np.isfinite(sig[:, o, 0])
        C = sig[have, o].astype(float) - mu
        tot = (C ** 2).sum(1)
        par = ((C @ V.T) ** 2).sum(1)
        num[have] += np.where(tot > 0, par / np.maximum(tot, 1e-12), 0.0)
        cnt[have] += 1
    ok = cnt > 0
    out[ok] = num[ok] / cnt[ok]
    return out


def top_k(sim, k):
    idx = []
    for s in sim:
        ok = np.isfinite(s)
        idx.append(np.argsort(-np.where(ok, s, -np.inf), kind="stable")[: min(k, int(ok.sum()))])
    return idx


def boot(d):
    d = d[np.isfinite(d)]
    b = rng.choice(d, size=(10000, len(d))).mean(1)
    return [float(d.mean()), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5)), int(len(d))]


def score(P, Y, G, min_lines):
    return np.nan_to_num(np.array([selective_r(p, y, g, min_lines=min_lines) for p, y, g in zip(P, Y, G)]), nan=0.0)


def analyse(blocks, Y, G, act, min_lines, run):
    """blocks: list of (query index array, sig_q, sig_r, Y_r)."""
    n = len(Y)
    preds = {D: np.full(Y.shape, np.nan) for D in DS}
    raw = np.full(Y.shape, np.nan)
    gq = np.full(n, np.nan)
    bias_raw, bias_gen, overlap = np.full(n, np.nan), np.full(n, np.nan), np.full(n, np.nan)
    for qi, Xq, Xr, Yr in blocks:
        for D in DS:
            dirs = generic_directions(Xr, D)
            preds[D][qi] = knn_transfer(mean_cosine(remove_generic(Xq, dirs), remove_generic(Xr, dirs)), Yr, K)
        dirs5 = generic_directions(Xr, 5)
        fq, fr = generic_fraction(Xq, dirs5), generic_fraction(Xr, dirs5)
        gq[qi] = fq
        s_raw = mean_cosine(Xq, Xr)
        s_gen = mean_cosine(remove_generic(Xq, dirs5), remove_generic(Xr, dirs5))
        raw[qi] = knn_transfer(s_raw, Yr, K)
        for j, (a, b) in enumerate(zip(top_k(s_raw, K), top_k(s_gen, K))):
            bias_raw[qi[j]] = np.nanmean(fr[a]) - fq[j]
            bias_gen[qi[j]] = np.nanmean(fr[b]) - fq[j]
            overlap[qi[j]] = len(set(a) & set(b)) / K
    r = {D: score(P, Y, G, min_lines) for D, P in preds.items()}
    r_raw = score(raw, Y, G, min_lines)
    assert np.allclose(r_raw, run["r_B1"]) and np.allclose(r[5], run["r_C1"]), "re-computation differs from the run"
    out = {"D_sensitivity_actives": {f"D{D}": {"mean": float(r[D][act].mean()),
                                               "minus_B0": boot(r[D][act] - run["r_B0"][act]),
                                               "minus_B1": boot(r[D][act] - run["r_B1"][act])} for D in DS}}
    edges = np.nanquantile(gq[act], [1 / 3, 2 / 3])
    tert = np.digitize(gq, edges)
    out["gain_C1_minus_B1_by_query_generic_fraction_tertile_actives"] = {
        f"T{t + 1}": {"fraction_range": [float(np.nanmin(gq[act & (tert == t)])), float(np.nanmax(gq[act & (tert == t)]))],
                      "C1_minus_B1": boot((r[5] - r_raw)[act & (tert == t)])} for t in range(3)}
    out["neighbour_generic_fraction_minus_query_actives"] = {"raw_k20": boot(bias_raw[act]), "C1_k20": boot(bias_gen[act])}
    out["neighbour_overlap_raw_vs_C1_actives"] = boot(overlap[act])
    out["query_generic_fraction_actives_vs_inactives"] = [float(np.nanmean(gq[act])), float(np.nanmean(gq[~act]))]
    return out


def main(data: Path, run_dir: Path, out_json: Path) -> None:
    import pandas as pd
    res = {}
    d = np.load(data / "nci60.npz", allow_pickle=True)
    p = np.load(run_dir / "predictions_nci60.npz", allow_pickle=True)
    m = pd.read_csv(run_dir / "metrics_nci60.csv")
    run = {c: m[c].to_numpy() for c in m.columns if c.startswith("r_")}
    fold = d["fold"]
    blocks = [(np.where(fold == f)[0], d["signature"][fold == f], d["signature"][fold != f], d["profile"][fold != f])
              for f in range(10)]
    res["nci60"] = analyse(blocks, p["observed"], p["generic"], d["active"].astype(bool), 40, run)
    pool = np.load(data / "dev_pool.npz", allow_pickle=True)
    q = np.load(data / "prism24q2.npz", allow_pickle=True)
    p = np.load(run_dir / "predictions_prism24q2.npz", allow_pickle=True)
    m = pd.read_csv(run_dir / "metrics_prism24q2.csv")
    run = {c: m[c].to_numpy() for c in m.columns if c.startswith("r_")}
    col = {ln: i for i, ln in enumerate(pool["line"])}
    Yr = pool["profile"][:, [col[ln] for ln in q["line"]]]
    blocks = [(np.arange(len(q["key"])), q["signature"], pool["signature"], Yr)]
    res["prism24q2"] = analyse(blocks, p["observed"], p["generic"], q["active"].astype(bool), 50, run)
    out_json.write_bytes((json.dumps(res, indent=1) + "\n").encode("utf-8"))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
