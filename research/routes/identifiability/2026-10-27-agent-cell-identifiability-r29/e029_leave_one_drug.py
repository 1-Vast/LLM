"""E029: leave-one-drug-out prediction of synergy from target/pathway annotation only.

Pre-registered in PROTOCOL_E029.md. Reads the local Jaaks 2022 GDSC files only.

Features never encode drug identity: anchor pathway one-hot, library pathway one-hot and
tissue one-hot. Ridge with a fixed penalty, grouped by drug (65 folds). Compared against a
constant (training-mean) baseline on the same folds.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
BASE = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare"
ORIG = BASE / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r29"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDA = 1.0
N_BOOT = 1000
SEED = 20261027


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def spearman(a, b) -> float:
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    a, b = a[m], b[m]
    if len(a) < 20 or np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    ra -= ra.mean()
    rb -= rb.mean()
    den = math.sqrt(float((ra ** 2).sum()) * float((rb ** 2).sum()))
    return float((ra * rb).sum() / den) if den > 0 else float("nan")


def auc(y, s) -> float:
    y = np.asarray(y, bool)
    s = np.asarray(s, float)
    if y.all() or (~y).all():
        return float("nan")
    r = pd.Series(s).rank().to_numpy()
    n1, n0 = int(y.sum()), int((~y).sum())
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cols = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME",
            "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", "ANCHOR_TARGET", "LIBRARY_TARGET", METRIC, "Synergy"]
    d = pd.read_csv(ORIG, low_memory=False, usecols=cols)
    d[METRIC] = pd.to_numeric(d[METRIC], errors="coerce")
    d = d[np.isfinite(d[METRIC])].copy()
    for c in ("ANCHOR_PATHWAY", "LIBRARY_PATHWAY", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME"):
        d[c] = d[c].astype(str).fillna("NA")

    drugs = sorted(set(d["ANCHOR_NAME"]) | set(d["LIBRARY_NAME"]))
    paths_a = sorted(d["ANCHOR_PATHWAY"].unique())
    paths_l = sorted(d["LIBRARY_PATHWAY"].unique())
    tissues = sorted(d["Tissue"].unique())

    def design(frame):
        X = np.zeros((len(frame), len(paths_a) + len(paths_l) + len(tissues)))
        for k, v in enumerate(paths_a):
            X[:, k] = (frame["ANCHOR_PATHWAY"] == v).to_numpy(float)
        off = len(paths_a)
        for k, v in enumerate(paths_l):
            X[:, off + k] = (frame["LIBRARY_PATHWAY"] == v).to_numpy(float)
        off2 = off + len(paths_l)
        for k, v in enumerate(tissues):
            X[:, off2 + k] = (frame["Tissue"] == v).to_numpy(float)
        return X

    X = design(d)
    y = d[METRIC].to_numpy(float)
    ybin = d["Synergy"].astype(str).str.lower().isin(["true", "1"]).to_numpy(bool)
    anchor = d["ANCHOR_NAME"].to_numpy()
    library = d["LIBRARY_NAME"].to_numpy()

    rows = []
    for drug in drugs:
        te = (anchor == drug) | (library == drug)
        tr = ~te
        if te.sum() < 50 or tr.sum() < 200:
            continue
        Xtr, ytr = X[tr], y[tr]
        mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
        sd[sd == 0] = 1.0
        Xs = (Xtr - mu) / sd
        Xte = (X[te] - mu) / sd
        A = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
        w = np.linalg.solve(A, Xs.T @ (ytr - ytr.mean()))
        pred = ytr.mean() + Xte @ w
        base = np.full(te.sum(), ytr.mean())
        rows.append({"drug": drug, "n_test": int(te.sum()),
                     "rho_model": spearman(pred, y[te]),
                     "rho_const": spearman(base, y[te]),
                     "auc_model": auc(ybin[te], pred),
                     "auc_const": auc(ybin[te], base),
                     "pred_mean": float(pred.mean()), "true_mean": float(y[te].mean())})

    r = pd.DataFrame(rows)
    res = {"kind": "leave_one_drug_out_synergy_from_pathway_annotation",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"lambda": LAMBDA, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"rows": int(len(d)), "drugs": len(drugs), "folds_used": int(len(r)),
                     "pathways_anchor": len(paths_a), "pathways_library": len(paths_l),
                     "tissues": len(tissues)},
           "per_drug": rows, "files": {}}

    if len(r) >= 10:
        def bsum(v, seed_off):
            v = np.asarray(v, float)
            v = v[np.isfinite(v)]
            if not len(v):
                return None
            rng = np.random.default_rng(SEED + seed_off)
            boots = [float(np.mean(rng.choice(v, size=len(v), replace=True))) for _ in range(N_BOOT)]
            return {"n": int(len(v)), "mean": float(v.mean()), "median": float(np.median(v)),
                    "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}

        dif = (r["rho_model"] - r["rho_const"]).to_numpy(float)
        res["summary"] = {
            "rho_model": bsum(r["rho_model"], 81), "rho_const": bsum(r["rho_const"], 82),
            "rho_diff": bsum(dif, 83),
            "auc_model": bsum(r["auc_model"], 84),
            "frac_drugs_model_better": float(np.nanmean(dif > 0))}
        rm = res["summary"]["rho_model"]
        rd = res["summary"]["rho_diff"]
        am = res["summary"]["auc_model"]
        h070 = bool(rm and rm["median"] >= 0.10 and rd and rd["ci95"][0] > 0)
        h071 = bool(rm and rm["median"] >= 0.20)
        h072 = bool(am and am["median"] >= 0.60)
    else:
        h070 = h071 = h072 = False
    res["decisions"] = {"H070_unseen_drug_predictable": h070, "H071_substantial": h071,
                        "H072_binary_synergy_auc": h072}
    res["decisions"]["verdict"] = ("unseen_drug_transfer_holds" if h070 and h071 else
                                   "weak_but_present" if h070 else
                                   "pathway_annotation_does_not_predict_unseen_drug_synergy")
    res["limits"] = [
        "Features are target/pathway annotation, NOT measured engagement.",
        "Drug identity is hidden, but other drugs sharing the same pathway remain visible; this is annotation-level generalisation.",
        "SYNERGY_DELTA_AUC is a model-fitted quantity; three tissues only.",
        "No mechanistic, clinical or drug-choice claim.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r29/PROTOCOL_E029.md",
                "research/2026-10-27-agent-cell-identifiability-r29/e029_leave_one_drug.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E029_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E029_per_drug.csv", index=False)

    print("rows=%d drugs=%d folds=%d | pathways anchor=%d library=%d tissues=%d" % (
        len(d), len(drugs), len(r), len(paths_a), len(paths_l), len(tissues)))
    for k in ("rho_model", "rho_const", "rho_diff", "auc_model"):
        if "summary" in res and res["summary"].get(k):
            v = res["summary"][k]
            print("  %-11s mean=%.4f median=%.4f CI=[%.4f,%.4f] n=%d" % (
                k, v["mean"], v["median"], v["ci95"][0], v["ci95"][1], v["n"]))
    if "summary" in res:
        print("  frac drugs model better=%.2f" % res["summary"]["frac_drugs_model_better"])
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
