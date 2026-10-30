"""E042: drive prediction strength toward zero by permuting pathway labels across drugs,
then test whether the mix advantage exists only in an intermediate band.

Pre-registered in PROTOCOL_E042.md. Dimension stays at 41 throughout.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r42"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDA = 1.0
KS = (10, 20, 30, 50, 75, 100, 150, 200)
FRACS = (0.0, 0.25, 0.50, 0.75, 1.00)
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


def build(df, ap_map, lp_map, ap_levels, lp_levels, tissue_levels):
    blocks = []
    vals = df["tissue"].to_numpy()
    M = np.zeros((len(df), len(tissue_levels)))
    for j, v in enumerate(tissue_levels):
        M[:, j] = (vals == v).astype(float)
    blocks.append(M)
    for col, mapping, levels in (("ap", ap_map, ap_levels), ("lp", lp_map, lp_levels)):
        vals = df[col].map(mapping).to_numpy()
        M = np.zeros((len(df), len(levels)))
        for j, v in enumerate(levels):
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
        a=("ANCHOR_NAME", "first"), l=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"), tissue=("Tissue", "first"),
        synergy=(METRIC, "mean"), syn=("syn", "mean"))
    d["syn"] = d["syn"] > 0.5
    for c in ("ap", "lp", "tissue"):
        d[c] = d[c].astype(str).fillna("NA")

    ap_levels = sorted(d["ap"].unique())
    lp_levels = sorted(d["lp"].unique())
    ti_levels = sorted(d["tissue"].unique())

    # drug -> pathway maps (the permutation must act on DRUGS, not on level names:
    # permuting level names is only a column permutation and leaves ridge unchanged)
    # a drug appearing only as a library agent has no anchor pathway, so permute the two
    # roles separately: anchor labels among anchor drugs, library labels among library drugs
    ua = d.drop_duplicates("a")[["a", "ap"]].copy()
    ua["a"] = ua["a"].astype(str)
    drug_ap = dict(zip(ua["a"], ua["ap"]))
    anchor_drugs = sorted(drug_ap)
    ul = d.drop_duplicates("l")[["l", "lp"]].copy()
    ul["l"] = ul["l"].astype(str)
    drug_lp = dict(zip(ul["l"], ul["lp"]))
    library_drugs = sorted(drug_lp)
    y = d.synergy.to_numpy(float)
    syn = d.syn.to_numpy(bool)

    rng = np.random.default_rng(SEED)
    splits = []
    for _ in range(REPEATS):
        perm = rng.permutation(len(d))
        tr = perm[: int(0.8 * len(d))]
        pool = perm[int(0.8 * len(d)):]
        splits.append((tr, pool))

    rows = []
    for frac in FRACS:
        for rep, (tr, pool) in enumerate(splits):
            cur_ap = dict(drug_ap)
            cur_lp = dict(drug_lp)
            if frac > 0:
                ka = max(1, int(round(frac * len(anchor_drugs))))
                pa = [anchor_drugs[i] for i in rng.choice(len(anchor_drugs), size=ka, replace=False)]
                va = [cur_ap[g] for g in pa]
                rng.shuffle(va)
                for g, a in zip(pa, va):
                    cur_ap[g] = a
                kl = max(1, int(round(frac * len(library_drugs))))
                pl = [library_drugs[i] for i in rng.choice(len(library_drugs), size=kl, replace=False)]
                vl = [cur_lp[g] for g in pl]
                rng.shuffle(vl)
                for g, l in zip(pl, vl):
                    cur_lp[g] = l
            dd = d.copy()
            dd["ap"] = dd["a"].astype(str).map(cur_ap)
            dd["lp"] = dd["l"].astype(str).map(cur_lp)
            X = build(dd, {v: v for v in ap_levels}, {v: v for v in lp_levels}, ap_levels, lp_levels, ti_levels)
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
            for kk in KS:
                for strat, sc in (("exploit", rp), ("mix", mix)):
                    idx = np.argsort(-sc)[:kk]
                    rows.append({"frac": frac, "rep": rep, "k": kk, "strategy": strat,
                                 "hit": float(syn[pool][idx].mean())})
            rows.append({"frac": frac, "rep": rep, "k": 0, "strategy": "rho", "hit": float(rho)})

    r = pd.DataFrame(rows)
    res = {"kind": "pathway_label_permutation_strength_sweep",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"lambda": LAMBDA, "ks": list(KS), "fracs": list(FRACS),
                        "repeats": REPEATS, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(d)), "features": len(ap_levels) + len(lp_levels) + len(ti_levels),
                     "synergy_rate": float(syn.mean())},
           "by_frac": {}, "files": {}}

    for frac in FRACS:
        sub_all = r[r.frac == frac]
        rhos = sub_all[sub_all.strategy == "rho"]["hit"]
        ent = {"prediction_rho": {"mean": float(rhos.mean()), "median": float(rhos.median())}, "by_k": {}}
        sig = []
        for kk in KS:
            sub = sub_all[sub_all.k == kk]
            m = sub[sub.strategy == "mix"].set_index("rep")["hit"]
            e = sub[sub.strategy == "exploit"].set_index("rep")["hit"]
            s = paired(m[m.index.isin(SEARCH)], e[e.index.isin(SEARCH)], 71)
            v = paired(m[m.index.isin(EVAL)], e[e.index.isin(EVAL)], 72)
            ent["by_k"][str(kk)] = {"search": s, "eval": v,
                                    "exploit_hit": float(e.mean()), "mix_hit": float(m.mean())}
            if s and v and s["ci95"][0] > 0 and v["ci95"][0] > 0:
                sig.append(kk)
        ent["ks_with_both_halves_positive"] = sig
        res["by_frac"][str(frac)] = ent

    keys = [str(f) for f in FRACS]
    rhos = {k: res["by_frac"][k]["prediction_rho"]["mean"] for k in keys}
    h109 = bool(all(rhos[keys[i]] >= rhos[keys[i + 1]] - 1e-9 for i in range(len(keys) - 1))
                and rhos[keys[-1]] < 0.05 and (rhos[keys[0]] - rhos[keys[-1]]) > 0.25)
    mid = keys[1:-1]
    mid_any = any(len(res["by_frac"][k]["ks_with_both_halves_positive"]) > 0 for k in mid)
    end_none = (len(res["by_frac"][keys[0]]["ks_with_both_halves_positive"]) == 0
                and len(res["by_frac"][keys[-1]]["ks_with_both_halves_positive"]) == 0)
    h110 = bool(mid_any and end_none)
    strong = res["by_frac"][keys[0]]
    h111 = bool(all((strong["by_k"][str(kk)]["eval"]["mean_diff"] <= 0)
                    or (strong["by_k"][str(kk)]["eval"]["ci95"][0] <= 0 <= strong["by_k"][str(kk)]["eval"]["ci95"][1])
                    for kk in KS))
    res["decisions"] = {"H109_strength_swept_to_zero": h109, "H110_intermediate_band": h110,
                        "H111_strong_end_exploit_not_worse": h111}
    res["decisions"]["verdict"] = ("intermediate_band_confirmed" if h110 else
                                   "band_not_confirmed")
    res["limits"] = [
        "Single dataset; permutation touches pathway labels only, not drug or cell identity.",
        "Retrospective candidate pool; SYNERGY_DELTA_AUC is a model-fitted quantity.",
        "No mechanistic, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r42/PROTOCOL_E042.md",
                "research/2026-10-27-agent-cell-identifiability-r42/e042_permute_labels.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E042_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E042_rows.csv", index=False)

    print("keys=%d features=%d" % (res["audit"]["keys"], res["audit"]["features"]))
    for f in FRACS:
        e = res["by_frac"][str(f)]
        print("  frac=%.2f rho=%.4f | ks both-halves-positive: %s" % (
            f, e["prediction_rho"]["mean"], e["ks_with_both_halves_positive"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
