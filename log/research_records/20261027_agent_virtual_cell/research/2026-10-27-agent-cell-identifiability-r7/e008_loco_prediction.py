"""E008: does drug-pair reversal propensity transfer to unseen cells?

Pre-registered in PROTOCOL_E008.md. Reads only PAIR_SCREEN.csv.

For every cell pair (A,B) in a layout, all cell pairs involving A or B are removed from
training (leave-two-cells-out), and the reversal indicator of each sampled unit pair is
predicted from
    M0 constant, M1 spacing (logistic on min gap), M2 drug-pair rate (shrunk to M0),
    M3 M2 + spacing.
ROC AUC on the held-out pair; layout-clustered bootstrap for intervals.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r7"
ANCHORS = {"high control", "low control"}
FLOOR = 0.10
PAIRS_PER_LAYOUT = 300
ALPHA_SHRINK = 5.0
N_BOOT = 400
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def auc(y: np.ndarray, s: np.ndarray) -> float:
    """ROC AUC with ties handled by average rank; nan when a class is absent."""
    y = np.asarray(y, bool)
    if y.all() or (~y).all():
        return float("nan")
    r = pd.Series(s).rank().to_numpy()
    n1 = int(y.sum())
    n0 = int((~y).sum())
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def logit_fit(X: np.ndarray, y: np.ndarray, l2: float = 1.0, iters: int = 200):
    """Plain Newton/IRLS logistic regression with an intercept, tiny L2 on slopes."""
    n, d = X.shape
    Xb = np.hstack([np.ones((n, 1)), X])
    w = np.zeros(d + 1)
    for _ in range(iters):
        z = Xb @ w
        p = 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))
        W = np.clip(p * (1 - p), 1e-6, None)
        g = Xb.T @ (y - p)
        H = Xb.T @ (Xb * W[:, None])
        reg = np.zeros_like(H)
        reg[1:, 1:] = l2 * np.eye(d)
        try:
            step = np.linalg.solve(H + reg + 1e-8 * np.eye(d + 1), g)
        except np.linalg.LinAlgError:
            break
        w += step
        if np.max(np.abs(step)) < 1e-8:
            break
    return w


def logit_pred(w: np.ndarray, X: np.ndarray) -> np.ndarray:
    Xb = np.hstack([np.ones((X.shape[0], 1)), X])
    return Xb @ w


def build():
    df = pd.read_csv(CSV, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={df.columns[0]: "row_id"})
    for c in ("Drug 1", "Drug 2", "Cell line", "file", "Well"):
        df[c] = df[c].astype(str).str.strip()
    df["iteration"] = pd.to_numeric(df["Iteration"], errors="coerce")
    df["failed_qc"] = df["Failed QC"].astype(str).str.strip().str.lower().isin(["true", "1"])
    df["y"] = pd.to_numeric(df["Viability"], errors="coerce")
    df["anchor"] = df["Drug 1"].isin(ANCHORS) | df["Drug 2"].isin(ANCHORS)
    df["dmso"] = (df["Drug 1"].str.lower() == "dmso") | (df["Drug 2"].str.lower() == "dmso")
    meta = {}
    for fname, g in df[~df["anchor"]].groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], pd.to_numeric(g["Conc 1 (uM)"]).round(9),
                                  g["Drug 2"], pd.to_numeric(g["Conc 2 (uM)"]).round(9))))
        meta[fname] = {"cell": g["Cell line"].iloc[0],
                       "iteration": int(g["iteration"].iloc[0]) if pd.notna(g["iteration"].iloc[0]) else -1,
                       "h": hashlib.sha1(repr(layout).encode()).hexdigest(),
                       "combo": {w: (str(d1).lower() != "dmso" and str(d2).lower() != "dmso")
                                 for w, (d1, c1, d2, c2) in
                                 {w: (d1, c1, d2, c2) for w, d1, c1, d2, c2 in layout}.items()},
                       "qc": float(g["failed_qc"].mean())}

    def vec(fname: str, units: list[str]) -> np.ndarray:
        sub = df[(df["file"] == fname) & (~df["failed_qc"]) & df["y"].notna() & (~df["anchor"])]
        return sub.drop_duplicates("Well").set_index("Well")["y"].reindex(units).to_numpy(dtype=float)

    groups = {}
    for f, s in meta.items():
        groups.setdefault((s["iteration"], s["h"]), {}).setdefault(s["cell"], []).append(f)
    rng = np.random.default_rng(SEED)
    layouts = []
    for (it, h), cells in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        if len(cells) < 3:
            continue
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 3:
            continue
        first = cells[good[0]][0]
        units = [u for u in sorted(meta[first]["combo"]) if meta[first]["combo"][u]]
        V = {c: [vec(f, units) for f in cells[c]] for c in good}
        nu = len(units)
        iu, ju = np.triu_indices(nu, 1)
        sel = rng.choice(iu.size, min(PAIRS_PER_LAYOUT, iu.size), replace=False)
        Y = np.vstack([np.nanmean(np.vstack(V[c]), axis=0) for c in good])
        layouts.append({"iteration": it, "hash": h[:12], "cells": good, "units": units,
                        "iu": iu[sel], "ju": ju[sel], "Y": Y})
    return df, layouts


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    df, layouts = build()
    rng = np.random.default_rng(SEED)

    # per-layout observation tables
    tables = []
    for L in layouts:
        cells, Y, iu, ju = L["cells"], L["Y"], L["iu"], L["ju"]
        nc = len(cells)
        S = np.sign(Y[:, iu] - Y[:, ju])          # (nc, npairs)
        gap = np.abs(Y[:, iu] - Y[:, ju])
        tables.append({"L": L, "S": S, "gap": gap,
                       "ok": (gap >= FLOOR) & np.isfinite(gap)})

    # held-out predictions
    pred_rows = []
    for t in tables:
        L, S, gap, ok = t["L"], t["S"], t["gap"], t["ok"]
        cells = L["cells"]
        nc = len(cells)
        for a in range(nc):
            for b in range(a + 1, nc):
                tr_mask = np.ones(nc, bool)
                tr_mask[[a, b]] = False
                tr = [i for i in range(nc) if tr_mask[i]]
                # training observations: all pairs within tr
                r_tr, g_tr, p_tr = [], [], []
                for ii in range(len(tr)):
                    for jj in range(ii + 1, len(tr)):
                        x, y_ = tr[ii], tr[jj]
                        m = ok[x] & ok[y_]
                        if m.sum() == 0:
                            continue
                        r_tr.append((S[x, m] != S[y_, m]).astype(float))
                        g_tr.append(np.minimum(gap[x, m], gap[y_, m]))
                        p_tr.append(np.where(m)[0])
                if not r_tr:
                    continue
                R = np.concatenate(r_tr)
                G = np.concatenate(g_tr)
                P = np.concatenate(p_tr)
                m_te = ok[a] & ok[b]
                if m_te.sum() < 20 or R.sum() == 0:
                    continue
                r_te = (S[a, m_te] != S[b, m_te]).astype(float)
                g_te = np.minimum(gap[a, m_te], gap[b, m_te])
                p_te = np.where(m_te)[0]
                p0 = float(R.mean())
                # M2: per-unit-pair shrunk rate from training
                cnt = np.bincount(P, minlength=S.shape[1]).astype(float)
                rev = np.bincount(P, weights=R, minlength=S.shape[1])
                rate = (rev + ALPHA_SHRINK * p0) / (cnt + ALPHA_SHRINK)
                m2_te = rate[p_te]
                # M1 / M3 logistics
                mu_g, sd_g = float(G.mean()), float(G.std() + 1e-9)
                X1 = ((G - mu_g) / sd_g)[:, None]
                w1 = logit_fit(X1, R)
                s1 = logit_pred(w1, ((g_te - mu_g) / sd_g)[:, None])
                cnt_te = cnt[p_te]
                m2z = (m2_te - p0) / (p0 * (1 - p0) + 1e-6)
                rate_obs = rate[P]
                m2z_obs = (rate_obs - p0) / (p0 * (1 - p0) + 1e-6)
                X3 = np.column_stack([((G - mu_g) / sd_g), m2z_obs])
                w3 = logit_fit(X3, R)
                s3 = logit_pred(w3, np.column_stack([((g_te - mu_g) / sd_g), m2z]))
                pred_rows.append({
                    "layout": f"{L['iteration']}/{L['hash']}", "cells": f"{cells[a]}|{cells[b]}",
                    "n": int(m_te.sum()), "prev": float(r_te.mean()),
                    "auc_M0": auc(r_te, np.full(m_te.sum(), 0.5)),
                    "auc_M1": auc(r_te, s1), "auc_M2": auc(r_te, m2_te), "auc_M3": auc(r_te, s3),
                    "mean_train_support": float(cnt_te.mean())})

    pr = pd.DataFrame(pred_rows)
    auc_block = {}
    for name, col in (("M0_constant", "auc_M0"), ("M1_spacing", "auc_M1"),
                      ("M2_drugpair", "auc_M2"), ("M3_both", "auc_M3")):
        ok_rows = np.isfinite(pr[col].to_numpy(dtype=float))
        auc_block[name] = {"weighted_mean": float(np.average(pr.loc[ok_rows, col].to_numpy(dtype=float),
                                                             weights=pr.loc[ok_rows, "n"].to_numpy(dtype=float)))}
    res = {"kind": "leave_two_cells_out_prediction_of_reversal",
           "input_sha256": sha256(CSV),
           "settings": {"floor": FLOOR, "pairs_per_layout": PAIRS_PER_LAYOUT,
                        "alpha_shrink": ALPHA_SHRINK, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"layouts": len(layouts), "heldout_cellpairs": int(len(pr)),
                     "median_pairs_per_heldout": float(pr["n"].median()) if len(pr) else None,
                     "median_prevalence": float(pr["prev"].median()) if len(pr) else None,
                     "median_train_support": float(pr["mean_train_support"].median()) if len(pr) else None},
           "auc": auc_block,
           "differences": {}, "files": {}}

    # differences with layout-clustered bootstrap
    pr["d_M2_M0"] = pr["auc_M2"] - pr["auc_M0"]
    pr["d_M3_M1"] = pr["auc_M3"] - pr["auc_M1"]
    pr["d_M2_M1"] = pr["auc_M2"] - pr["auc_M1"]
    lays = sorted(pr["layout"].unique())

    def boot(col):
        vals = []
        rng2 = np.random.default_rng(SEED + 1)
        for _ in range(N_BOOT):
            pick = rng2.choice(lays, size=len(lays), replace=True)
            sel = pd.concat([pr[pr["layout"] == p] for p in pick])
            sel = sel[np.isfinite(sel[col])]
            if len(sel) >= 5:
                vals.append(float(np.average(sel[col], weights=sel["n"])))
        return [float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))] if vals else None

    for name, col in (("M2_minus_M0", "d_M2_M0"), ("M3_minus_M1", "d_M3_M1"), ("M2_minus_M1", "d_M2_M1")):
        finite = pr[np.isfinite(pr[col])]
        res["differences"][name] = {
            "weighted_mean": float(np.average(finite[col], weights=finite["n"])) if len(finite) else None,
            "ci95_layout_clustered": boot(col),
            "frac_cellpairs_positive": float((finite[col] > 0).mean()) if len(finite) else None,
            "n": int(len(finite))}

    res["decisions"] = {
        "H012a_drugpair_transfers": bool(
            (res["differences"]["M2_minus_M0"]["weighted_mean"] or 0) >= 0.05
            and (res["differences"]["M2_minus_M0"]["ci95_layout_clustered"] or [0, 0])[0] > 0),
        "H012b_not_just_spacing": bool(
            (res["differences"]["M3_minus_M1"]["weighted_mean"] or 0) >= 0.03
            and (res["differences"]["M3_minus_M1"]["ci95_layout_clustered"] or [0, 0])[0] > 0),
    }
    res["decisions"]["verdict"] = (
        "drugpair_fragility_transfers_across_cells" if res["decisions"]["H012a_drugpair_transfers"] and res["decisions"]["H012b_not_just_spacing"]
        else "drugpair_effect_is_spacing_proxy" if res["decisions"]["H012a_drugpair_transfers"]
        else "drugpair_fragility_does_not_transfer")
    res["limits"] = [
        "Reversal of a functional viability ordering, not death rate, mechanism, selectivity or clinical benefit.",
        "Validation plates already used as scoring endpoints by an earlier round; cross-cell comparisons also cross days. Exploratory, not confirmatory.",
        "Drug pairs are layout-specific, so this tests transfer across unseen CELLS, not unseen drugs.",
        "AUC is computed per held-out cell pair on its readable unit pairs; cell pairs are dependent within a layout, and only 9 layouts exist, so intervals are wide by construction.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r7/PROTOCOL_E008.md",
                "research/2026-10-27-agent-cell-identifiability-r7/e008_loco_prediction.py",
                str(CSV.relative_to(ROOT))):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E008_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / "E008_per_cellpair.csv").write_text(pr.to_csv(index=False), encoding="utf-8")

    a = res["auc"]
    print("heldout cell pairs=%d median n=%d prevalence=%.4f support=%.1f" % (
        len(pr), res["audit"]["median_pairs_per_heldout"], res["audit"]["median_prevalence"],
        res["audit"]["median_train_support"]))
    for m in ("M0_constant", "M1_spacing", "M2_drugpair", "M3_both"):
        print("  AUC %-12s %.4f" % (m, a[m]["weighted_mean"]))
    for k, v in res["differences"].items():
        print("  %-14s %+.4f CI=%s frac+=%.2f" % (k, v["weighted_mean"] or float("nan"),
                                                  v["ci95_layout_clustered"], v["frac_cellpairs_positive"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
