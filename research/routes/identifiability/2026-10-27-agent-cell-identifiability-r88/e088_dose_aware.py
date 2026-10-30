"""E088: R87's null result may have been a modelling failure.

R87 averaged over doses, discarding BATCHIE's dose structure, so its additive null was almost
certainly underfitted. Here each (pair, dose) well is a row and the null model gives every drug
its own intercept AND log-dose slope (a crude Loewe-type additivity). The same gate applies:
the residual must be learnable before any comparison counts.

Pre-registered in PROTOCOL_E083.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import KFold, cross_val_predict

ROOT = Path(r"D:\MAESTRO")
CSV = ROOT / "research" / "eight_directions_20261026" / "evidence_audit" / "raw" / "PAIR_SCREEN.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r88"
ANCHORS = {"high control", "low control"}
K = 20
REPEATS = 12
N_BOOT = 2000
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def paired(a, b, off):
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    if len(j) < 3:
        return None
    dif = (j["a"] - j["b"]).to_numpy(float)
    rng = np.random.default_rng(SEED + off)
    boots = [float(np.mean(rng.choice(dif, size=len(dif), replace=True))) for _ in range(N_BOOT)]
    return {"n": int(len(dif)), "mean_diff": float(dif.mean()),
            "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}


def design(d1, d2, c1, c2, drug_lv):
    """Dose-aware additive design: per-drug intercept and log-dose slope for both sides."""
    n = len(d1)
    nd = len(drug_lv)
    X = np.zeros((n, 2 * nd + 2 * nd))
    lc1 = np.log10(np.clip(c1, 1e-9, None))
    lc2 = np.log10(np.clip(c2, 1e-9, None))
    for t in range(n):
        i1 = drug_lv[d1[t]]
        i2 = drug_lv[d2[t]]
        X[t, i1] = 1.0
        X[t, nd + i2] = 1.0
        X[t, 2 * nd + i1] = lc1[t]
        X[t, 3 * nd + i2] = lc2[t]
    return X


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    df = pd.read_csv(CSV, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    for c in ("Drug 1", "Drug 2", "Cell line", "file", "Well"):
        df[c] = df[c].astype(str).str.strip()
    df["failed_qc"] = df["Failed QC"].astype(str).str.strip().str.lower().isin(["true", "1"])
    df["y"] = pd.to_numeric(df["Viability"], errors="coerce")
    df["c1"] = pd.to_numeric(df["Conc 1 (uM)"], errors="coerce")
    df["c2"] = pd.to_numeric(df["Conc 2 (uM)"], errors="coerce")
    df["anchor"] = df["Drug 1"].isin(ANCHORS) | df["Drug 2"].isin(ANCHORS)
    ok = df[(~df["anchor"]) & (~df["failed_qc"]) & df["y"].notna()
            & df["c1"].notna() & df["c2"].notna()].copy()

    genes = {}
    ap = ROOT / "data" / "external" / "mapkg_20261009" / "DRUG-GENE_filtered_by_existing_drugs_and_genes.csv"
    dmp = ROOT / "data" / "external" / "mapkg_20261009" / "DRUG_merged_drugs_with_residuals.csv"
    dmap = pd.read_csv(dmp, low_memory=False)
    gdf = pd.read_csv(ap, low_memory=False)
    n2i = dict(zip(dmap["Drug Name"].astype(str).str.strip(), dmap["PubChem ID"]))
    i2g = gdf.groupby("Drug ID")["Gene ID"].apply(lambda s: frozenset(s)).to_dict()
    for nm, pid in n2i.items():
        if pid in i2g:
            genes[nm] = i2g[pid]

    meta = {}
    for fname, g in df[~df["anchor"]].groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], g["Drug 2"])))
        meta[fname] = {"cell": g["Cell line"].iloc[0],
                       "h": hashlib.sha1(repr(layout).encode()).hexdigest(),
                       "qc": float(g["failed_qc"].mean())}
    groups = {}
    for f, s in meta.items():
        groups.setdefault(s["h"], {}).setdefault(s["cell"], []).append(f)

    rng = np.random.default_rng(SEED)
    rows = []
    cv_r2 = []
    for h, cells in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 4:
            continue
        frames = {c: ok[ok["file"].isin(cells[c])] for c in good}
        drugs = sorted({d for f in frames.values() for d in list(f["Drug 1"]) + list(f["Drug 2"])})
        drug_lv = {d: i for i, d in enumerate(drugs)}
        per_cell = {}
        for c in good:
            f = frames[c]
            Xc = design(f["Drug 1"].tolist(), f["Drug 2"].tolist(), f["c1"].to_numpy(), f["c2"].to_numpy(), drug_lv)
            per_cell[c] = (Xc, f["y"].to_numpy(float),
                           list(zip(f["Drug 1"], f["Drug 2"])), f)
        gl = sorted({g for d in drugs if d in genes for g in genes[d]})
        if len(gl) < 5:
            continue
        gidx = {g: i for i, g in enumerate(gl)}

        for _ in range(REPEATS):
            held = good[int(rng.integers(0, len(good)))]
            tr_cells = [c for c in good if c != held]
            Xtr = np.vstack([per_cell[c][0] for c in tr_cells])
            ytr = np.concatenate([per_cell[c][1] for c in tr_cells])
            cell_id = np.concatenate([[i] * len(per_cell[c][1]) for i, c in enumerate(tr_cells)])
            # add cell intercepts
            C = np.zeros((len(cell_id), len(tr_cells)))
            C[np.arange(len(cell_id)), cell_id] = 1.0
            Xtr_full = np.hstack([Xtr, C])

            Xh, yh, pairh, fh = per_cell[held]
            Ch = np.zeros((len(yh), len(tr_cells)))
            Xh_full = np.hstack([Xh, Ch])

            m = RidgeCV(alphas=(1.0, 10.0, 100.0, 1000.0))
            pred_tr = cross_val_predict(m, Xtr_full, ytr, cv=KFold(5, shuffle=True, random_state=SEED))
            ss_res = float(np.sum((ytr - pred_tr) ** 2))
            ss_tot = float(np.sum((ytr - ytr.mean()) ** 2))
            cv_r2.append(1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan)

            m.fit(Xtr_full, ytr)
            r_tr = ytr - m.predict(Xtr_full)
            r_held = yh - m.predict(Xh_full)

            # gene features per well
            def gfeat(pairs):
                G = np.zeros((len(pairs), len(gl)))
                for i, (d1, d2) in enumerate(pairs):
                    for d in (d1, d2):
                        for g in genes.get(d, ()):
                            if g in gidx:
                                G[i, gidx[g]] += 1.0
                return G
            pairs_tr = [p for c in tr_cells for p in per_cell[c][2]]
            Gtr = gfeat(pairs_tr)
            Gh = gfeat(pairh)
            keep = Gtr.sum(axis=1) > 0
            if keep.sum() < 500 or (Gh.sum(axis=1) > 0).mean() < 0.7:
                continue
            gm = RidgeCV(alphas=(1.0, 10.0, 100.0, 1000.0))
            gm.fit(Gtr[keep], r_tr[keep])
            r_hat = gm.predict(Gh)

            # aggregate predicted residual per pair (mean over its dose wells) and score
            pair_scores = {}
            for i, p in enumerate(pairh):
                pair_scores.setdefault(p, []).append(r_hat[i])
            agg = {p: float(np.mean(v)) for p, v in pair_scores.items()}
            true_res = {}
            for i, p in enumerate(pairh):
                true_res.setdefault(p, []).append(r_held[i])
            agg_true = {p: float(np.mean(v)) for p, v in true_res.items()}
            ps = list(agg)
            if len(ps) < 60:
                continue
            tv = np.array([agg_true[p] for p in ps])
            sv = np.array([agg[p] for p in ps])
            hit = (tv <= np.quantile(tv, 0.25)).astype(float)
            top = np.argsort(sv)[:K]
            rnd = rng.choice(len(ps), size=K, replace=False)
            rows.append({"layout": h[:12], "cell": held,
                         "gene": float(hit[top].mean()), "random": float(hit[rnd].mean()),
                         "base": float(hit.mean()), "n_pairs": len(ps)})

    r = pd.DataFrame(rows)
    res = {"kind": "dose_aware_additive_null_on_BATCHIE",
           "input_sha256": sha256(CSV),
           "settings": {"k": K, "repeats": REPEATS, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"units": int(len(r)), "cells": int(r["cell"].nunique()) if len(r) else 0,
                     "mean_cv_r2_of_additive_null": float(np.nanmean(cv_r2)) if cv_r2 else None,
                     "note": "R87's additive null had CV R2 -0.034; this one includes per-drug log-dose slopes"},
           "summary": {}, "files": {}}
    if len(r) >= 5:
        res["summary"] = {"n": int(len(r)),
                          "gene": float(r["gene"].mean()), "random": float(r["random"].mean()),
                          "base": float(r["base"].mean()),
                          "gene_minus_random": paired(r["gene"], r["random"], 15001)}
    s = res["summary"]
    h224 = bool(res["audit"]["mean_cv_r2_of_additive_null"] is not None
                and res["audit"]["mean_cv_r2_of_additive_null"] > 0)
    h225 = bool(s and s["gene_minus_random"]["ci95"][0] > 0)
    h226 = bool(s and s["gene_minus_random"]["ci95"][0] <= 0)
    res["decisions"] = {"H224_residual_now_learnable": h224,
                        "H225_annotation_wins": h225,
                        "H226_annotation_loses": h226}
    res["decisions"]["verdict"] = (
        "still_not_interpretable" if not h224 else
        "annotation_wins_on_dose_aware_residuals" if h225 else
        "annotation_loses_on_dose_aware_residuals")
    res["limits"] = [
        "Each drug has only a few concentration points, so the slope estimates are unstable.",
        "Residuals may still be dominated by well-level noise.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r88/PROTOCOL_E083.md",
                "research/2026-10-27-agent-cell-identifiability-r88/e088_dose_aware.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E088_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E088_rows.csv", index=False)

    print("units=%d cells=%d cv_r2=%.4f" % (
        len(r), res["audit"]["cells"], res["audit"]["mean_cv_r2_of_additive_null"] or float("nan")))
    if s:
        print("  base=%.4f random=%.4f gene=%.4f" % (s["base"], s["random"], s["gene"]))
        c = s["gene_minus_random"]
        print("  gene - random = %+.4f [%+.4f,%+.4f]" % (c["mean_diff"], c["ci95"][0], c["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
