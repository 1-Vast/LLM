"""C2: does the drug-pair propensity survive a PAIR-LEVEL spacing baseline?

The protocol's spacing baseline M1 uses min(gap_a, gap_b) -- the gap measured on the
single held-out cell pair. That is a noisy, one-draw proxy for how close the pair's two
units sit. M2 (the per-pair reversal rate) is, mechanically, a denoised estimate of
exactly that quantity: a pair whose typical gap is just above the 0.10 floor flips in
some cells and not others, so its training reversal rate is high AND its held-out gap is
usually small.

This script therefore adds the spacing baseline the protocol did not pre-register:
    Mpair  : the pair's mean min(gap) over training observations (pair-level spacing)
and asks
    1. AUC(Mpair) alone vs AUC(M1)=0.828
    2. AUC(M4 = M1 + Mpair) vs AUC(M3 = M1 + M2)
    3. AUC(M5 = M1 + Mpair + M2): does M2 still add anything once pair-level spacing is in?
    4. within-decile-of-pair-gap AUC of M2 (does the propensity rank anything inside a
       spacing stratum?)
Read-only on PAIR_SCREEN.csv.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
CSV = ROOT / "research" / "eight_directions_20261026" / "evidence_audit" / "raw" / "PAIR_SCREEN.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r7" / "challenge"
ANCHORS = {"high control", "low control"}
FLOOR = 0.10
PAIRS_PER_LAYOUT = 300
ALPHA = 5.0
SEED = 20261027
N_BOOT = 400


def auc(y, s):
    y = np.asarray(y, bool)
    if y.all() or (~y).all():
        return float("nan")
    r = pd.Series(s).rank().to_numpy()
    n1, n0 = int(y.sum()), int((~y).sum())
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def logit_fit(X, y, l2=1.0, iters=200):
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


def zz(x):
    return (x - np.mean(x)) / (np.std(x) + 1e-9)


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

    def vec(fname, units):
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
        iu, ju = np.triu_indices(len(units), 1)
        sel = rng.choice(iu.size, min(PAIRS_PER_LAYOUT, iu.size), replace=False)
        Y = np.vstack([np.nanmean(np.vstack(V[c]), axis=0) for c in good])
        layouts.append({"iteration": it, "hash": h[:12], "cells": good, "units": units,
                        "iu": iu[sel], "ju": ju[sel], "Y": Y})
    return layouts


def main():
    layouts = build()
    rows = []
    for L in layouts:
        cells, Y, iu, ju = L["cells"], L["Y"], L["iu"], L["ju"]
        nc = len(cells)
        S = np.sign(Y[:, iu] - Y[:, ju])
        gap = np.abs(Y[:, iu] - Y[:, ju])
        ok = (gap >= FLOOR) & np.isfinite(gap)
        layid = f"{L['iteration']}/{L['hash']}"
        for a in range(nc):
            for b in range(a + 1, nc):
                tr = [i for i in range(nc) if i not in (a, b)]
                R, G, P = [], [], []
                for ii in range(len(tr)):
                    for jj in range(ii + 1, len(tr)):
                        x, y_ = tr[ii], tr[jj]
                        m = ok[x] & ok[y_]
                        if m.sum() == 0:
                            continue
                        R.append((S[x, m] != S[y_, m]).astype(float))
                        G.append(np.minimum(gap[x, m], gap[y_, m]))
                        P.append(np.where(m)[0])
                if not R:
                    continue
                R, G, P = np.concatenate(R), np.concatenate(G), np.concatenate(P)
                m_te = ok[a] & ok[b]
                if m_te.sum() < 20 or R.sum() == 0:
                    continue
                te = np.where(m_te)[0]
                r_te = (S[a, te] != S[b, te]).astype(float)
                g_te = np.minimum(gap[a, te], gap[b, te])
                if 0 < r_te.sum() < r_te.size and r_te.sum() >= 1:
                    pass
                p0 = float(R.mean())
                cnt = np.bincount(P, minlength=iu.size).astype(float)
                rev = np.bincount(P, weights=R, minlength=iu.size)
                rate = (rev + ALPHA * p0) / (cnt + ALPHA)
                gsum = np.bincount(P, weights=G, minlength=iu.size)
                gmean = np.where(cnt > 0, gsum / np.maximum(cnt, 1), np.nan)
                gmean_f = np.where(np.isfinite(gmean), gmean, np.nanmedian(gmean[cnt > 0]))
                mu_g, sd_g = float(G.mean()), float(G.std() + 1e-9)
                X1 = zz(G)[:, None]
                w1 = logit_fit(X1, R)
                s1 = logit_pred(w1, zz(g_te)[:, None])
                pz = zz(gmean_f)
                w4 = logit_fit(np.column_stack([zz(G), pz[P]]), R)
                s4 = logit_pred(w4, np.column_stack([zz(g_te), pz[te]]))
                m2z_obs = (rate[P] - p0) / (p0 * (1 - p0) + 1e-6)
                m2z_te = (rate[te] - p0) / (p0 * (1 - p0) + 1e-6)
                w3 = logit_fit(np.column_stack([zz(G), m2z_obs]), R)
                s3 = logit_pred(w3, np.column_stack([zz(g_te), m2z_te]))
                w5 = logit_fit(np.column_stack([zz(G), pz[P], m2z_obs]), R)
                s5 = logit_pred(w5, np.column_stack([zz(g_te), pz[te], m2z_te]))
                rows.append({"layout": layid, "cells": f"{cells[a]}|{cells[b]}", "nc": nc,
                             "n": int(te.size), "prev": float(r_te.mean()),
                             "auc_M1": auc(r_te, s1), "auc_M2": auc(r_te, rate[te]),
                             "auc_M3": auc(r_te, s3),
                             "auc_Mpair": auc(r_te, -pz[te]),
                             "auc_M4": auc(r_te, s4), "auc_M5": auc(r_te, s5),
                             "pairgap_te": float(np.mean(g_te)),
                             "pairgap_tr": float(np.nanmean(gmean[te]))})
    pr = pd.DataFrame(rows)
    print("cell pairs scored:", len(pr), " layouts:", pr["layout"].nunique())
    print("\n--- weighted-mean AUC (E008 protocol weighting) ---")
    for c in ("auc_M1", "auc_M2", "auc_M3", "auc_Mpair", "auc_M4", "auc_M5"):
        f = pr[np.isfinite(pr[c])]
        print(f"  {c:10s} {np.average(f[c], weights=f['n']):.4f}  (n={len(f)})")

    def boot(col, base):
        d = (pr[col] - pr[base]).to_numpy()
        fin = np.isfinite(d)
        pr2 = pr[fin].copy()
        pr2["d"] = d[fin]
        lays = sorted(pr2["layout"].unique())
        rng = np.random.default_rng(SEED + 1)
        vals = []
        for _ in range(N_BOOT):
            pick = rng.choice(lays, size=len(lays), replace=True)
            sel = pd.concat([pr2[pr2["layout"] == p] for p in pick])
            if len(sel) >= 5:
                vals.append(float(np.average(sel["d"], weights=sel["n"])))
        return [float(np.quantile(vals, .025)), float(np.quantile(vals, .975))] if vals else None

    print("\n--- increments (weighted mean, layout-clustered 95% CI) ---")
    for name, a_, b_ in (("M3 - M1 (protocol H012b)", "auc_M3", "auc_M1"),
                         ("M4 - M1 (pair-gap baseline)", "auc_M4", "auc_M1"),
                         ("M5 - M4 (M2 beyond pair gap)", "auc_M5", "auc_M4"),
                         ("M5 - M1 (M2+pairgap vs spacing)", "auc_M5", "auc_M1"),
                         ("M2 - M1", "auc_M2", "auc_M1")):
        d = float(np.average((pr[a_] - pr[b_])[np.isfinite(pr[a_] - pr[b_])],
                             weights=pr["n"][np.isfinite(pr[a_] - pr[b_])]))
        print(f"  {name:32s} {d:+.4f}  CI={boot(a_, b_)}")

    # ---- within-pair-gap-decile AUC of M2 (does it rank inside a spacing stratum?) ----
    print("\n--- AUC of M2 and Mpair WITHIN deciles of the held-out pair's own gap ---")
    pr["gdec"] = pd.qcut(pr["pairgap_te"], 5, labels=False, duplicates="drop")
    for q, g in pr.groupby("gdec"):
        if len(g) < 4:
            continue
        f = g[np.isfinite(g["auc_M2"])]
        if len(f) < 3:
            continue
        print(f"  quintile {int(q)} (mean pair gap {g['pairgap_te'].mean():.3f}): "
              f"AUC_M2={np.average(f['auc_M2'], weights=f['n']):.4f}  "
              f"AUC_M1={np.average(f[np.isfinite(f['auc_M1'])]['auc_M1'], weights=f[np.isfinite(f['auc_M1'])]['n']):.4f}")

    pr.to_csv(OUT / "c2_pairgap_percellpair.csv", index=False)
    print("\nwrote c2_pairgap_percellpair.csv")


if __name__ == "__main__":
    main()
