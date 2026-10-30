"""E013: can we know in advance whether a cross-cell dose-grid prediction is trustworthy?

Pre-registered in PROTOCOL_E013.md.

Unit = (layout, compound pair, held-out cell). Label = hit@3 / regret of the cross-cell
mean-surface predictor (R11). Features use ONLY cells other than the held-out one:
argmin agreement among the other cells, normalised gap to runner-up, plateau size,
dynamic range, edge flag, number of other cells.

H023: leave-one-layout-out AUC for hit@3 >= 0.65 and >= best single feature + 0.05.
H024: a coverage >= 30% subgroup at hit@3 >= 0.80.
H025: calibration deviation <= 0.10.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
CSV = ROOT / "research" / "eight_directions_20261026" / "evidence_audit" / "raw" / "PAIR_SCREEN.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r12"
ANCHORS = {"high control", "low control"}
NOISE_UNIT = 0.04
THRESH_GRID = (0.5, 0.6, 0.7, 0.8, 0.9)
N_BOOT = 1000
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"
FEATS = ("argmin_agree", "gap2", "plateau", "dyn_range", "edge", "n_other")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def auc(y, s) -> float:
    y = np.asarray(y, bool)
    if y.all() or (~y).all():
        return float("nan")
    r = pd.Series(s).rank().to_numpy()
    n1, n0 = int(y.sum()), int((~y).sum())
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def logit_fit(X, y, l2=1.0, iters=300):
    n, d = X.shape
    Xb = np.hstack([np.ones((n, 1)), X])
    w = np.zeros(d + 1)
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-np.clip(Xb @ w, -30, 30)))
        W = np.clip(p * (1 - p), 1e-6, None)
        H = Xb.T @ (Xb * W[:, None])
        reg = np.zeros_like(H)
        reg[1:, 1:] = l2 * np.eye(d)
        try:
            step = np.linalg.solve(H + reg + 1e-8 * np.eye(d + 1), Xb.T @ (y - p))
        except np.linalg.LinAlgError:
            break
        w += step
        if np.max(np.abs(step)) < 1e-8:
            break
    return w


def logit_pred(w, X):
    return np.hstack([np.ones((X.shape[0], 1)), X]) @ w


def build_units():
    df = pd.read_csv(CSV, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={df.columns[0]: "row_id"})
    for c in ("Drug 1", "Drug 2", "Cell line", "file", "Well"):
        df[c] = df[c].astype(str).str.strip()
    df["iteration"] = pd.to_numeric(df["Iteration"], errors="coerce")
    df["failed_qc"] = df["Failed QC"].astype(str).str.strip().str.lower().isin(["true", "1"])
    df["y"] = pd.to_numeric(df["Viability"], errors="coerce")
    df["c1"] = pd.to_numeric(df["Conc 1 (uM)"], errors="coerce")
    df["c2"] = pd.to_numeric(df["Conc 2 (uM)"], errors="coerce")
    df["anchor"] = df["Drug 1"].isin(ANCHORS) | df["Drug 2"].isin(ANCHORS)
    df["dmso"] = (df["Drug 1"].str.lower() == "dmso") | (df["Drug 2"].str.lower() == "dmso")
    keep = df[(~df["anchor"]) & (~df["dmso"]) & (~df["failed_qc"]) & df["y"].notna()]
    meta = {}
    for fname, g in df[~df["anchor"]].groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], g["c1"].round(9), g["Drug 2"], g["c2"].round(9))))
        meta[fname] = {"cell": g["Cell line"].iloc[0],
                       "iteration": int(g["iteration"].iloc[0]) if pd.notna(g["iteration"].iloc[0]) else -1,
                       "h": hashlib.sha1(repr(layout).encode()).hexdigest(),
                       "qc": float(g["failed_qc"].mean())}
    groups = {}
    for f, s in meta.items():
        groups.setdefault((s["iteration"], s["h"]), {}).setdefault(s["cell"], []).append(f)

    units = []
    for (it, h), cells in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 3:
            continue
        ref = cells[good[0]][0]
        rg = keep[keep["file"] == ref]
        if rg.empty:
            continue
        for (d1, d2) in sorted({(a, b) for a, b in zip(rg["Drug 1"], rg["Drug 2"])}):
            sub_ref = rg[(rg["Drug 1"] == d1) & (rg["Drug 2"] == d2)]
            doses1 = sorted(sub_ref["c1"].unique())
            doses2 = sorted(sub_ref["c2"].unique())
            if len(doses1) < 3 or len(doses2) < 3:
                continue
            grid = [(i, j) for i in range(len(doses1)) for j in range(len(doses2))]
            gidx = {g: k for k, g in enumerate(grid)}
            surf = {}
            for c in good:
                arrs = []
                for f in cells[c]:
                    sub = keep[(keep["file"] == f) & (keep["Drug 1"] == d1) & (keep["Drug 2"] == d2)]
                    if sub.empty:
                        continue
                    a = np.full(len(grid), np.nan)
                    for _, row in sub.iterrows():
                        a[gidx[(doses1.index(row["c1"]), doses2.index(row["c2"]))]] = row["y"]
                    if np.isfinite(a).sum() >= 0.8 * len(grid):
                        arrs.append(a)
                if arrs:
                    surf[c] = np.nanmean(np.vstack(arrs), axis=0)
            cells_ok = [c for c in good if c in surf and np.isfinite(surf[c]).all()]
            if len(cells_ok) < 3:
                continue
            for c in cells_ok:
                others = [x for x in cells_ok if x != c]
                if len(others) < 2:
                    continue
                units.append({"layout": "%s/%s" % (it, h[:12]), "pair": "%s + %s" % (d1, d2), "cell": c,
                              "truth": surf[c], "others": np.vstack([surf[x] for x in others]),
                              "n1": len(doses1), "n2": len(doses2)})
    return units


def features(u):
    tr, others = u["truth"], u["others"]
    pooled = others.mean(axis=0)
    order = np.argsort(pooled)
    best = pooled[order[0]]
    gap2 = (pooled[order[1]] - best) / (pooled.std() + 1e-9)
    plateau = float(np.mean(pooled <= best + NOISE_UNIT))
    dyn = float(pooled.max() - pooled.min())
    i, j = divmod(int(order[0]), u["n2"])
    edge = float(i in (0, u["n1"] - 1) or j in (0, u["n2"] - 1))
    amins = [int(np.argmin(o)) for o in others]
    agree = float(np.mean([amins[a] == amins[b] for a in range(len(amins)) for b in range(a + 1, len(amins))]))
    return {"argmin_agree": agree, "gap2": float(gap2), "plateau": plateau, "dyn_range": dyn,
            "edge": edge, "n_other": float(len(others))}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    units = build_units()
    rows = []
    for u in units:
        f = features(u)
        pooled = u["others"].mean(axis=0)
        ch = int(np.argmin(pooled))
        truth = u["truth"]
        rank_true = np.argsort(np.argsort(truth))
        f.update({"layout": u["layout"], "pair": u["pair"], "cell": u["cell"],
                  "hit3": int(rank_true[ch] < 3),
                  "regret": float(truth[ch] - truth.min())})
        rows.append(f)
    d = pd.DataFrame(rows)
    X = d[list(FEATS)].to_numpy(float)
    X = (X - X.mean(0)) / (X.std(0) + 1e-9)
    y = d["hit3"].to_numpy(int)

    # leave-one-layout-out CV
    preds = np.full(len(d), np.nan)
    for lay in d["layout"].unique():
        te = (d["layout"] == lay).to_numpy()
        w = logit_fit(X[~te], y[~te])
        preds[te] = 1.0 / (1.0 + np.exp(-np.clip(logit_pred(w, X[te]), -30, 30)))
    auc_cv = auc(y, preds)
    single = {f: auc(y, -X[:, k] if f in ("gap2", "dyn_range", "n_other") else X[:, k])
              for k, f in enumerate(FEATS)}
    best_single = max((v for v in single.values() if np.isfinite(v)), default=float("nan"))

    # bootstrap over layouts
    lays = sorted(d["layout"].unique())
    rng = np.random.default_rng(SEED)
    boots = []
    for _ in range(N_BOOT):
        pick = rng.choice(lays, size=len(lays), replace=True)
        idx = np.concatenate([np.where((d["layout"] == p).to_numpy())[0] for p in pick])
        a = auc(y[idx], preds[idx])
        if np.isfinite(a):
            boots.append(a)
    ci = [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))] if boots else None

    h023 = bool(np.isfinite(auc_cv) and auc_cv >= 0.65 and (auc_cv - best_single) >= 0.05)

    # H024: threshold rule on argmin_agree
    rule = []
    base = float(y.mean())
    for t in THRESH_GRID:
        sel = d["argmin_agree"] >= t
        if sel.sum() == 0:
            continue
        rule.append({"threshold": t, "coverage": float(sel.mean()), "n": int(sel.sum()),
                     "hit3_in_subgroup": float(d.loc[sel, "hit3"].mean()),
                     "regret_in_subgroup": float(d.loc[sel, "regret"].mean()),
                     "lift_over_base": float(d.loc[sel, "hit3"].mean() / base) if base > 0 else None})
    h024 = any(r["hit3_in_subgroup"] >= 0.80 and r["coverage"] >= 0.30 for r in rule)

    # H025: calibration of the CV predictions, 3 bins
    bins = pd.qcut(preds, 3, labels=False, duplicates="drop")
    calib = []
    for b in range(int(bins.max()) + 1):
        m = bins == b
        calib.append({"bin": b, "n": int(m.sum()), "mean_predicted": float(preds[m].mean()),
                      "observed": float(y[m].mean())})
    max_dev = max(abs(c["mean_predicted"] - c["observed"]) for c in calib) if calib else None
    h025 = bool(max_dev is not None and max_dev <= 0.10)

    res = {"kind": "predictability_of_predictability",
           "input_sha256": sha256(CSV), "settings": {"noise_unit": NOISE_UNIT, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"units": int(len(d)), "layouts": int(d["layout"].nunique()),
                     "pairs": int(d.groupby("pair").ngroups), "base_hit3": base},
           "auc": {"logit_loo_layout": auc_cv, "ci95_layout_bootstrap": ci,
                   "single_feature": single, "best_single": best_single},
           "threshold_rule": rule, "calibration": calib,
           "decisions": {"H023_trustworthiness_predictable": h023, "H024_deployable_subgroup": h024,
                         "H025_calibrated": h025},
           "files": {}}
    res["decisions"]["verdict"] = ("trustworthiness_predictable" if h023 and h024 else
                                   "average_only_not_deployable")
    for rel in ("research/2026-10-27-agent-cell-identifiability-r12/PROTOCOL_E013.md",
                "research/2026-10-27-agent-cell-identifiability-r12/e013_confidence.py",
                str(CSV.relative_to(ROOT))):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E013_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    d.to_csv(OUT / "E013_units.csv", index=False)

    print("units=%d layouts=%d pairs=%d base_hit3=%.3f" % (len(d), d["layout"].nunique(),
                                                           d.groupby("pair").ngroups, base))
    print("AUC (LOO layout) = %.3f  CI=%s | best single = %.3f" % (auc_cv, ci, best_single))
    print("single-feature AUCs:", {k: round(v, 3) for k, v in single.items() if np.isfinite(v)})
    for r in rule:
        print("  argmin_agree>=%.1f  cov=%.2f n=%d hit3=%.3f regret=%.4f lift=%.2f" % (
            r["threshold"], r["coverage"], r["n"], r["hit3_in_subgroup"], r["regret_in_subgroup"], r["lift_over_base"]))
    print("calibration:", [(c["bin"], round(c["mean_predicted"], 3), round(c["observed"], 3)) for c in calib])
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
