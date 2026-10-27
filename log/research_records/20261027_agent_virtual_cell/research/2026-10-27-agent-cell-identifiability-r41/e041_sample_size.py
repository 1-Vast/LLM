"""E040: fixed-dimension manipulation of prediction strength via training-label noise.

Pre-registered in PROTOCOL_E040.md. Features are always the 41-dim pathway set; only the
fraction of corrupted training labels varies.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r41"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDA = 1.0
KS = (10, 20, 30, 50, 75, 100, 150, 200)
SIZES = (200, 500, 2000, 8000, 20000, None)  # None = full training set
REPEATS = 40
SEARCH = list(range(0, 20))
EVAL = list(range(20, 40))
N_BOOT = 2000
SEED = 20261027
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", METRIC, "Synergy"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def rank_corr(a, b):
    a = pd.Series(a).rank().to_numpy()
    b = pd.Series(b).rank().to_numpy()
    a = a - a.mean()
    b = b - b.mean()
    den = np.sqrt((a ** 2).sum() * (b ** 2).sum())
    return float((a * b).sum() / den) if den > 0 else np.nan


def paired(a, b, off):
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    if len(j) < 3:
        return None
    dif = (j["a"] - j["b"]).to_numpy(float)
    rng = np.random.default_rng(SEED + off)
    boots = [float(np.mean(rng.choice(dif, size=len(dif), replace=True))) for _ in range(N_BOOT)]
    return {"n": int(len(dif)), "mean_diff": float(dif.mean()),
            "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d[METRIC] = pd.to_numeric(d[METRIC], errors="coerce")
    d = d[np.isfinite(d[METRIC])].copy()
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["CELL_LINE_NAME"].astype(str) + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    d = d.groupby("key", as_index=False).agg(
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"), tissue=("Tissue", "first"),
        synergy=(METRIC, "mean"), syn=("syn", "mean"))
    d["syn"] = d["syn"] > 0.5
    for c in ("ap", "lp", "tissue"):
        d[c] = d[c].astype(str).fillna("NA")

    cols = ["tissue", "ap", "lp"]
    blocks = []
    for c in cols:
        lv = sorted(d[c].unique())
        M = np.zeros((len(d), len(lv)))
        vals = d[c].to_numpy()
        for j, v in enumerate(lv):
            M[:, j] = (vals == v).astype(float)
        blocks.append(M)
    X = np.hstack(blocks)
    y = d.synergy.to_numpy(float)
    syn = d.syn.to_numpy(bool)

    rng = np.random.default_rng(SEED)
    splits = []
    for _ in range(REPEATS):
        perm = rng.permutation(len(d))
        ntr = int(0.8 * len(d))
        splits.append((perm[:ntr], perm[ntr:]))

    rows = []
    for size in SIZES:
        for rep, (tr, pool) in enumerate(splits):
            if size is None or size >= len(tr):
                tr_use = tr
            else:
                tr_use = rng.choice(tr, size=size, replace=False)
            ytr = y[tr_use]
            Xtr = X[tr_use]
            mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
            sd[sd == 0] = 1.0
            Xs = (Xtr - mu) / sd
            Xp = (X[pool] - mu) / sd
            A = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
            Ainv = np.linalg.inv(A)
            w = Ainv @ Xs.T @ (ytr - ytr.mean())
            pred = ytr.mean() + Xp @ w
            var = np.einsum("ij,jk,ik->i", Xp, Ainv, Xp)
            rho = rank_corr(pred, y[pool])
            rp = pd.Series(pred).rank(pct=True).to_numpy()
            rv = pd.Series(var).rank(pct=True).to_numpy()
            mix = rp + rv
            key = "full" if size is None else str(size)
            for k in KS:
                for strat, sc in (("exploit", rp), ("mix", mix)):
                    idx = np.argsort(-sc)[:k]
                    rows.append({"size": key, "rep": rep, "k": k, "strategy": strat,
                                 "hit": float(syn[pool][idx].mean())})
            rows.append({"size": key, "rep": rep, "k": 0, "strategy": "rho", "hit": float(rho)})

    r = pd.DataFrame(rows)
    res = {"kind": "sample_size_prediction_strength_sweep",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"lambda": LAMBDA, "ks": list(KS), "training_sizes": [("full" if s is None else s) for s in SIZES],
                        "repeats": REPEATS, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(d)), "features": int(X.shape[1]),
                     "synergy_rate": float(syn.mean())},
           "by_size": {}, "files": {}}

    for size in SIZES:
        key = "full" if size is None else str(size)
        rhos = r[(r["size"] == key) & (r.strategy == "rho")]["hit"]
        ent = {"prediction_rho": {"mean": float(rhos.mean()), "median": float(rhos.median())}, "by_k": {}}
        sig_both = []
        for k in KS:
            sub = r[(r["size"] == key) & (r.k == k)]
            m = sub[sub.strategy == "mix"].set_index("rep")["hit"]
            e = sub[sub.strategy == "exploit"].set_index("rep")["hit"]
            s = paired(m[m.index.isin(SEARCH)], e[e.index.isin(SEARCH)], 61)
            v = paired(m[m.index.isin(EVAL)], e[e.index.isin(EVAL)], 62)
            ent["by_k"][str(k)] = {"search": s, "eval": v,
                                   "exploit_hit": float(e.mean()), "mix_hit": float(m.mean())}
            if s and v and s["ci95"][0] > 0 and v["ci95"][0] > 0:
                sig_both.append(k)
        ent["ks_with_both_halves_positive"] = sig_both
        ent["max_abs_diff"] = float(max(abs(ent["by_k"][str(k)]["eval"]["mean_diff"]) for k in KS))
        res["by_size"][key] = ent

    keys = ["full" if s is None else str(s) for s in SIZES]
    rhos = {k: res["by_size"][k]["prediction_rho"]["mean"] for k in keys}
    order = [k for k in keys]
    h106 = bool(all(rhos[order[i]] <= rhos[order[i + 1]] + 1e-9 for i in range(len(order) - 1))
                and (rhos[order[-1]] - rhos[order[0]]) > 0.15)
    weakest = order[0]
    strongest = order[-1]
    mid = order[1:-1]
    mid_any = any(len(res["by_size"][k]["ks_with_both_halves_positive"]) > 0 for k in mid)
    weak_none = len(res["by_size"][weakest]["ks_with_both_halves_positive"]) == 0
    strong_any = len(res["by_size"][strongest]["ks_with_both_halves_positive"]) > 0
    h107 = bool(mid_any and weak_none)
    h108 = bool(res["by_size"][weakest]["max_abs_diff"] < 0.01)
    res["decisions"] = {"H106_strength_swept_cleanly": h106, "H107_intermediate_band": h107,
                        "H108_weak_end_no_difference": h108}
    res["decisions"]["verdict"] = (
        "intermediate_band_confirmed" if h106 and h107 else
        "manipulation_failed_again_untested" if not h106 else
        "no_intermediate_band_refuted")
    res["limits"] = [
        "Single dataset, single feature set, single noise mechanism (training-label resampling).",
        "Retrospective candidate pool; SYNERGY_DELTA_AUC is a model-fitted quantity.",
        "No mechanistic, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r40/PROTOCOL_E040.md",
                "research/2026-10-27-agent-cell-identifiability-r40/e040_noise_sweep.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E041_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E041_rows.csv", index=False)

    print("keys=%d features=%d" % (res["audit"]["keys"], res["audit"]["features"]))
    for key in [("full" if s is None else str(s)) for s in SIZES]:
        e = res["by_size"][key]
        print("  size=%-6s rho=%.4f | ks both-halves-positive: %s" % (
            key, e["prediction_rho"]["mean"], e["ks_with_both_halves_positive"]))
        for k in KS:
            b = e["by_k"][str(k)]
            print("      k=%-3d exploit=%.4f mix=%.4f | search %+.4f  eval %+.4f" % (
                k, b["exploit_hit"], b["mix_hit"], b["search"]["mean_diff"], b["eval"]["mean_diff"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
