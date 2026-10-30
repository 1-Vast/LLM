"""E087: a DISCRIMINATING test on BATCHIE.

R86's raw-viability test saturated. Here the potency component is removed by fitting a two-way
additive model on training cells and asking the predictors to rank the held-out cell's
ADDITIVITY RESIDUALS. Marginals have no information about that residual by construction, so
this is the arena where the annotation model should win if it can.

Pre-registered in PROTOCOL_E082.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r87"
ANCHORS = {"high control", "low control"}
K = 20
REPEATS = 20
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


def fit_additive(Y, cells, drugs):
    """Y: pairs x cells matrix. Returns predicted Yhat of the same shape (two-way additive)."""
    n_pairs, n_cells = Y.shape
    rows = []
    ys = []
    for j in range(n_cells):
        for i in range(n_pairs):
            v = Y[i, j]
            if not np.isfinite(v):
                continue
            d1, d2 = drugs[i]
            rows.append((j, d1, d2))
            ys.append(v)
    ys = np.asarray(ys, float)
    cell_lv = {c: k for k, c in enumerate(sorted(set(r[0] for r in rows)))}
    drug_lv = {d: k for k, d in enumerate(sorted({d for r in rows for d in (r[1], r[2])}))}
    X = np.zeros((len(rows), 1 + len(cell_lv) + len(drug_lv)))
    X[:, 0] = 1.0
    for t, (j, d1, d2) in enumerate(rows):
        X[t, 1 + cell_lv[j]] += 1.0
        X[t, 1 + len(cell_lv) + drug_lv[d1]] += 1.0
        X[t, 1 + len(cell_lv) + drug_lv[d2]] += 1.0
    beta, *_ = np.linalg.lstsq(X, ys, rcond=None)
    Yhat = np.zeros_like(Y)
    for j in range(n_cells):
        for i in range(n_pairs):
            d1, d2 = drugs[i]
            row = np.zeros(1 + len(cell_lv) + len(drug_lv))
            row[0] = 1.0
            row[1 + cell_lv[j]] = 1.0
            row[1 + len(cell_lv) + drug_lv[d1]] += 1.0
            row[1 + len(cell_lv) + drug_lv[d2]] += 1.0
            Yhat[i, j] = row @ beta
    return Yhat


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    df = pd.read_csv(CSV, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    for c in ("Drug 1", "Drug 2", "Cell line", "file", "Well"):
        df[c] = df[c].astype(str).str.strip()
    df["failed_qc"] = df["Failed QC"].astype(str).str.strip().str.lower().isin(["true", "1"])
    df["y"] = pd.to_numeric(df["Viability"], errors="coerce")
    df["anchor"] = df["Drug 1"].isin(ANCHORS) | df["Drug 2"].isin(ANCHORS)
    ok = df[(~df["anchor"]) & (~df["failed_qc"]) & df["y"].notna()].copy()

    genes = {}
    ap = ROOT / "data" / "external" / "mapkg_20261009" / "DRUG-GENE_filtered_by_existing_drugs_and_genes.csv"
    dmp = ROOT / "data" / "external" / "mapkg_20261009" / "DRUG_merged_drugs_with_residuals.csv"
    if ap.exists() and dmp.exists():
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
        per = {}
        for c in good:
            vs = []
            for f in cells[c]:
                s = ok[ok["file"] == f]
                v = s.groupby(["Drug 1", "Drug 2"])["y"].mean()
                if len(v) >= 100:
                    vs.append(v)
            if vs:
                per[c] = pd.concat(vs, axis=1).mean(axis=1).dropna()
        if len(per) < 4:
            continue
        allc = sorted(per)
        pairs = [p for p in per[allc[0]].index if all(p in per[c].index for c in allc)]
        if len(pairs) < 150:
            continue
        Y = np.column_stack([per[c].loc[pairs].to_numpy(float) for c in allc])
        drugs = [(p[0], p[1]) for p in pairs]
        Yhat = fit_additive(Y, allc, drugs)
        R = Y - Yhat

        gl = sorted({g for p in drugs for d in p if d in genes for g in genes[d]})
        if len(gl) < 5:
            continue
        gidx = {g: i for i, g in enumerate(gl)}
        X = np.zeros((len(pairs), len(gl)))
        for i, (d1, d2) in enumerate(drugs):
            for d in (d1, d2):
                for g in genes.get(d, ()):
                    if g in gidx:
                        X[i, gidx[g]] += 1.0
        if (X.sum(axis=1) > 0).mean() < 0.7:
            continue

        for _ in range(REPEATS):
            held = int(rng.integers(0, len(allc)))
            tr = [j for j in range(len(allc)) if j != held]
            r_tr = np.nanmean(R[:, tr], axis=1)
            r_held = R[:, held]
            finite = np.isfinite(r_tr) & np.isfinite(r_held)
            if finite.sum() < 150:
                continue
            model = RidgeCV(alphas=(0.1, 1.0, 10.0, 100.0))
            pred = cross_val_predict(model, X[finite], r_tr[finite], cv=KFold(5, shuffle=True, random_state=SEED))
            ss_res = float(np.sum((r_tr[finite] - pred) ** 2))
            ss_tot = float(np.sum((r_tr[finite] - r_tr[finite].mean()) ** 2))
            cv_r2.append(1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan)

            model.fit(X[finite], r_tr[finite])
            r_hat = model.predict(X)
            hit = (r_held <= np.nanquantile(r_held, 0.25)).astype(float)
            order_g = np.argsort(np.where(finite, r_hat, np.inf))[:K]     # LOW residual = synergistic
            rand_idx = rng.choice(np.where(finite)[0], size=K, replace=False)
            rows.append({"layout": h[:12], "cell": allc[held],
                         "gene": float(np.nanmean(hit[order_g])),
                         "random": float(np.nanmean(hit[rand_idx])),
                         "base": float(np.nanmean(hit)), "n": int(finite.sum())})

    r = pd.DataFrame(rows)
    res = {"kind": "BATCHIE_additivity_residual_discriminating_test",
           "input_sha256": sha256(CSV),
           "settings": {"k": K, "repeats": REPEATS, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"units": int(len(r)), "cells": int(r["cell"].nunique()) if len(r) else 0,
                     "mean_cv_r2_of_residual_model": float(np.nanmean(cv_r2)) if cv_r2 else None},
           "summary": {}, "files": {}}
    if len(r) >= 5:
        res["summary"] = {"n": int(len(r)),
                          "gene": float(r["gene"].mean()), "random": float(r["random"].mean()),
                          "base": float(r["base"].mean()),
                          "gene_minus_random": paired(r["gene"], r["random"], 14001)}
    s = res["summary"]
    h221 = bool(s and s["gene_minus_random"]["ci95"][0] > 0)
    h222 = bool(s and s["gene_minus_random"]["ci95"][0] <= 0)
    h223 = bool(res["audit"]["mean_cv_r2_of_residual_model"] is not None
                and res["audit"]["mean_cv_r2_of_residual_model"] > 0)
    res["decisions"] = {"H221_annotation_predicts_residual": h221,
                        "H222_annotation_cannot_predict_residual": h222,
                        "H223_residual_has_learnable_signal": h223}
    res["decisions"]["verdict"] = (
        "not_interpretable_residual_is_noise" if not h223 else
        "annotation_model_WINS_on_the_residual_arena" if h221 else
        "annotation_model_also_loses_the_residual_arena")
    res["limits"] = [
        "The residual task is noisy: one cell, a single concentration grid.",
        "If H223 fails the round says nothing about the annotation model.",
        "Marginals are blind to this residual by construction, so a win here would not rehabilitate them either.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r87/PROTOCOL_E082.md",
                "research/2026-10-27-agent-cell-identifiability-r87/e087_residual_arena.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E087_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E087_rows.csv", index=False)

    print("units=%d cells=%d mean_cv_r2=%.4f" % (
        len(r), res["audit"]["cells"], res["audit"]["mean_cv_r2_of_residual_model"] or float("nan")))
    if s:
        print("  base=%.4f random=%.4f gene=%.4f" % (s["base"], s["random"], s["gene"]))
        c = s["gene_minus_random"]
        print("  gene - random = %+.4f [%+.4f,%+.4f]" % (c["mean_diff"], c["ci95"][0], c["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
