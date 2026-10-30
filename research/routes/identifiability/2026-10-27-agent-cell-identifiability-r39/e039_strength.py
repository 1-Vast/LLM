"""E039: hold the task fixed and manipulate prediction strength by changing the feature set.
Does the mix/exploit crossover k move with prediction strength?

Pre-registered in PROTOCOL_E039.md. Three feature sets, same splits, 40 repetitions.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r39"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDA = 1.0
KS = (10, 20, 30, 50, 75, 100, 150, 200)
REPEATS = 40
SEARCH = list(range(0, 20))
EVAL = list(range(20, 40))
N_BOOT = 2000
SEED = 20261027
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY",
       "ANCHOR_TARGET", "LIBRARY_TARGET", METRIC, "Synergy"]


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
            "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
            "a": float(j["a"].mean()), "b": float(j["b"].mean())}


def build_matrix(d, cols):
    levels = [sorted(d[c].astype(str).unique()) for c in cols]
    blocks = []
    for c, lv in zip(cols, levels):
        M = np.zeros((len(d), len(lv)))
        vals = d[c].astype(str).to_numpy()
        for j, v in enumerate(lv):
            M[:, j] = (vals == v).astype(float)
        blocks.append(M)
    return np.hstack(blocks)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d[METRIC] = pd.to_numeric(d[METRIC], errors="coerce")
    d = d[np.isfinite(d[METRIC])].copy()
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["CELL_LINE_NAME"].astype(str) + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    d = d.groupby("key", as_index=False).agg(
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        at=("ANCHOR_TARGET", "first"), lt=("LIBRARY_TARGET", "first"), tissue=("Tissue", "first"),
        synergy=(METRIC, "mean"), syn=("syn", "mean"))
    d["syn"] = d["syn"] > 0.5
    for c in ("ap", "lp", "at", "lt", "tissue"):
        d[c] = d[c].astype(str).fillna("NA")

    feature_sets = {
        "tissue": ["tissue"],
        "pathway": ["tissue", "ap", "lp"],
        "full": ["tissue", "ap", "lp", "at", "lt"],
    }
    mats = {k: build_matrix(d, cols) for k, cols in feature_sets.items()}
    y = d.synergy.to_numpy(float)
    syn = d.syn.to_numpy(bool)

    rng = np.random.default_rng(SEED)
    splits = []
    for rep in range(REPEATS):
        perm = rng.permutation(len(d))
        ntr = int(0.8 * len(d))
        splits.append((perm[:ntr], perm[ntr:]))

    rows = []
    for name, X in mats.items():
        for rep, (tr, pool) in enumerate(splits):
            Xtr, ytr = X[tr], y[tr]
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
            for k in KS:
                for strat, sc in (("exploit", rp), ("mix", mix)):
                    idx = np.argsort(-sc)[:k]
                    rows.append({"features": name, "rep": rep, "k": k, "strategy": strat,
                                 "hit": float(syn[pool][idx].mean())})
            rows.append({"features": name, "rep": rep, "k": 0, "strategy": "rho", "hit": float(rho)})

    r = pd.DataFrame(rows)
    res = {"kind": "prediction_strength_moderates_the_budget_crossover",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"lambda": LAMBDA, "ks": list(KS), "repeats": REPEATS,
                        "search_splits": SEARCH, "eval_splits": EVAL, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(d)), "features": {k: int(v.shape[1]) for k, v in mats.items()},
                     "synergy_rate": float(syn.mean())},
           "by_features": {}, "files": {}}

    for name in feature_sets:
        rhos = r[(r.features == name) & (r.strategy == "rho")]["hit"]
        ent = {"prediction_rho": {"mean": float(rhos.mean()), "median": float(rhos.median())}, "by_k": {}}
        kstar = None
        for k in KS:
            sub = r[(r.features == name) & (r.k == k)]
            m = sub[sub.strategy == "mix"].set_index("rep")["hit"]
            e = sub[sub.strategy == "exploit"].set_index("rep")["hit"]
            s = paired(m[m.index.isin(SEARCH)], e[e.index.isin(SEARCH)], 51)
            v = paired(m[m.index.isin(EVAL)], e[e.index.isin(EVAL)], 52)
            ent["by_k"][str(k)] = {"mix_minus_exploit_all": paired(m, e, 53),
                                   "search": s, "eval": v,
                                   "exploit_hit": float(e.mean()), "mix_hit": float(m.mean())}
            if kstar is None and s and s["ci95"][0] > 0:
                kstar = k
        ent["k_star_search"] = kstar
        if kstar is not None:
            ent["eval_at_k_star"] = ent["by_k"][str(kstar)]["eval"]
        res["by_features"][name] = ent

    rho_t = res["by_features"]["tissue"]["prediction_rho"]["mean"]
    rho_p = res["by_features"]["pathway"]["prediction_rho"]["mean"]
    rho_f = res["by_features"]["full"]["prediction_rho"]["mean"]
    h100 = bool(rho_t < rho_p < rho_f and (rho_f - rho_t) > 0.05)
    kt = res["by_features"]["tissue"]["k_star_search"]
    kf = res["by_features"]["full"]["k_star_search"]
    h101 = bool(kt is not None and kf is not None and kt < kf)
    h102 = bool(kf is None)
    res["decisions"] = {"H100_strength_manipulated": h100, "H101_crossover_moves_with_strength": h101,
                        "H102_no_crossover_when_strong": h102}
    res["decisions"]["verdict"] = ("strength_is_the_moderator" if h100 and (h101 or h102) else
                                   "moderator_not_supported")
    res["limits"] = [
        "One dataset; feature sets also change dimensionality, so strength and dimension are not fully separable.",
        "Retrospective candidate pool; SYNERGY_DELTA_AUC is a model-fitted quantity.",
        "No mechanistic, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r39/PROTOCOL_E039.md",
                "research/2026-10-27-agent-cell-identifiability-r39/e039_strength.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E039_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E039_rows.csv", index=False)

    print("keys=%d features=%s" % (res["audit"]["keys"], res["audit"]["features"]))
    for name, e in res["by_features"].items():
        print("  %-8s rho=%.4f  k*(search)=%s" % (name, e["prediction_rho"]["mean"], e["k_star_search"]))
        for k in KS:
            b = e["by_k"][str(k)]
            s, v = b["search"], b["eval"]
            print("      k=%-3d exploit=%.4f mix=%.4f | search %+.4f [%+.3f,%+.3f]  eval %+.4f [%+.3f,%+.3f]" % (
                k, b["exploit_hit"], b["mix_hit"], s["mean_diff"], s["ci95"][0], s["ci95"][1],
                v["mean_diff"], v["ci95"][0], v["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
