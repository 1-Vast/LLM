"""C3: is the transferable "drug-pair fragility" just well-level technical instability?

Each cell-line layout in this resource has TWO replicate plates (`..._<cell>.xlsx` and
`..._<cell>_2.xlsx`, same well layout). E008 averages them into one value, which throws
away the only direct measurement of per-well technical noise available.

Two tests:
 T1  within-cell replicate reversal: reversal between plate1 and plate2 of the SAME cell
     line is, by construction, 100% technical. Is it predicted by M2 (learned from other
     cells)? AUC > 0.5 means the transferable propensity is partly a well-instability
     detector.
 T2  pair-level noise covariate: noise_i = mean |Y_i(plate1)-Y_i(plate2)| over cells.
     Does M2's rate correlate with pair noise, and does M2 survive adding pair noise to
     the model alongside spacing?
Also reports:
  - positives per held-out cell pair and the sensitivity of the 0.916 to the weighting rule
  - composition of the 300 sampled unit pairs (do the two wells share a drug?)
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


def build(with_plates=False):
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
                       "drugs": {w: (d1, d2) for w, (d1, c1, d2, c2) in
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
        L = {"iteration": it, "hash": h[:12], "cells": good, "units": units,
             "iu": iu[sel], "ju": ju[sel], "Y": Y, "drugs": meta[first]["drugs"]}
        if with_plates:
            L["V"] = V
        layouts.append(L)
    return layouts


def main():
    layouts = build(with_plates=True)
    print("layouts built:", len(layouts))
    rep_rows, pair_rows, sel_rows = [], [], []
    for L in layouts:
        cells, Y, iu, ju = L["cells"], L["Y"], L["iu"], L["ju"]
        nc = len(cells)
        layid = f"{L['iteration']}/{L['hash']}"
        S = np.sign(Y[:, iu] - Y[:, ju])
        gap = np.abs(Y[:, iu] - Y[:, ju])
        ok = (gap >= FLOOR) & np.isfinite(gap)
        # per-unit replicate disagreement
        D = np.full((nc, len(L["units"])), np.nan)
        for ci, c in enumerate(cells):
            Vc = [v for v in L["V"][c] if np.isfinite(v).any()]
            if len(Vc) >= 2:
                D[ci] = np.abs(Vc[0] - Vc[1])
        rep_d = np.nanmean(D, axis=0)  # mean replicate |diff| per unit across cells
        # per-well cross-cell SD (biological + technical)
        with np.errstate(invalid="ignore"):
            xsd = np.nanstd(Y, axis=0)

        # ---- pair composition ----
        for p in range(iu.size):
            d1a, d2a = L["drugs"][L["units"][iu[p]]]
            d1b, d2b = L["drugs"][L["units"][ju[p]]]
            sel_rows.append({"layout": layid, "share_d1": int(d1a == d1b), "share_d2": int(d2a == d2b),
                             "same_well_col": int(iu[p] == ju[p])})

        # ---- T2 inputs: pair-level replicate noise ----
        pnoise = np.sqrt(np.nan_to_num(rep_d[iu]) ** 2 + np.nan_to_num(rep_d[ju]) ** 2)
        pxsd = np.sqrt(np.nan_to_num(xsd[iu]) ** 2 + np.nan_to_num(xsd[ju]) ** 2)

        # ---- T1: within-cell replicate reversal predicted by other-cell M2 ----
        pair_rows_l = []
        for c in range(nc):
            Vc = [v for v in L["V"][cells[c]] if np.isfinite(v).any()]
            if len(Vc) < 2:
                continue
            g1 = np.abs(Vc[0][iu] - Vc[0][ju])
            g2 = np.abs(Vc[1][iu] - Vc[1][ju])
            o = (g1 >= FLOOR) & (g2 >= FLOOR) & np.isfinite(g1) & np.isfinite(g2)
            if o.sum() < 20:
                continue
            rw = (np.sign(Vc[0][iu] - Vc[0][ju]) != np.sign(Vc[1][iu] - Vc[1][ju]))[o]
            tr = [i for i in range(nc) if i != c]
            R, P = [], []
            for ii in range(len(tr)):
                for jj in range(ii + 1, len(tr)):
                    m = ok[tr[ii]] & ok[tr[jj]]
                    if m.sum() == 0:
                        continue
                    R.append((S[tr[ii], m] != S[tr[jj], m]).astype(float))
                    P.append(np.where(m)[0])
            if not R:
                continue
            R, P = np.concatenate(R), np.concatenate(P)
            if R.sum() == 0:
                continue
            p0 = float(R.mean())
            cnt = np.bincount(P, minlength=iu.size).astype(float)
            rev = np.bincount(P, weights=R, minlength=iu.size)
            rate = (rev + ALPHA * p0) / (cnt + ALPHA)
            sc = rate[o]
            gsum = np.bincount(P, weights=np.concatenate([
                np.minimum(gap[tr[ii], ok[tr[ii]] & ok[tr[jj]]], gap[tr[jj], ok[tr[ii]] & ok[tr[jj]]])
                for ii in range(len(tr)) for jj in range(ii + 1, len(tr))
                if (ok[tr[ii]] & ok[tr[jj]]).sum() > 0]), minlength=iu.size)
            gm = np.where(cnt > 0, gsum / np.maximum(cnt, 1), np.nanmedian(gsum[cnt > 0]))
            pair_rows_l.append({"layout": layid, "cell": cells[c], "n": int(o.sum()),
                                "prev": float(rw.mean()),
                                "auc_M2": auc(rw, sc),
                                "auc_gap": auc(rw, -(np.minimum(g1, g2)[o])),
                                "auc_noise": auc(rw, pnoise[o]),
                                "auc_xthetd": auc(rw, pxsd[o])})
            pair_rows.append(pair_rows_l[-1])

    rp = pd.DataFrame(pair_rows)
    print(f"\n=== T1 within-cell replicate reversal (same cell line, two replicate plates) ===")
    print(f"cell-lines tested: {len(rp)}, total readable obs: {rp['n'].sum()}, "
          f"pooled prevalence: {(rp['prev']*rp['n']).sum()/rp['n'].sum():.4f}")
    for c in ("auc_M2", "auc_gap", "auc_noise", "auc_xthetd"):
        f = rp[np.isfinite(rp[c])]
        print(f"  {c:12s} weighted {np.average(f[c], weights=f['n']):.4f}  unweighted {f[c].mean():.4f}  n={len(f)}")
    print("  per-cell detail:")
    for _, r in rp.iterrows():
        print(f"    {r['cell']:16s} n={r['n']:4d} prev={r['prev']:.4f} "
              f"AUC_M2={r['auc_M2']:.3f} AUC_noise={r['auc_noise']:.3f} AUC_gap={r['auc_gap']:.3f}")
    rp.to_csv(OUT / "c3_within_cell_replicate.csv", index=False)

    # ---- T2: does M2 rate track pair-level technical noise? ----
    print("\n=== T2 pair-level replicate noise vs M2 rate ===")
    print("  (computed via a leave-two-cells-out loop; see c3 rows below)")
    sdf = pd.DataFrame(sel_rows)
    print("  sampled pair composition: share drug1 = %.2f, share drug2 = %.2f, share both = %.2f, neither = %.2f"
          % (sdf["share_d1"].mean(), sdf["share_d2"].mean(),
             ((sdf["share_d1"] == 1) & (sdf["share_d2"] == 1)).mean(),
             ((sdf["share_d1"] == 0) & (sdf["share_d2"] == 0)).mean()))

    # ---- weighting sensitivity of the 0.916 ----
    pr = pd.read_csv(ROOT / "research" / "2026-10-27-agent-cell-identifiability-r7" / "E008_per_cellpair.csv")
    f = pr[np.isfinite(pr["auc_M2"])].copy()
    f["pos"] = f["prev"] * f["n"]
    print("\n=== sensitivity of AUC(M2)=0.916 to the aggregation rule ===")
    print(f"  cell pairs in file: {len(pr)}, with finite AUC(M2): {len(f)} "
          f"(dropped {len(pr)-len(f)} = {(len(pr)-len(f))/len(pr):.1%}, all zero-positive)")
    print(f"  weighted by n (E008 headline)      : {np.average(f['auc_M2'], weights=f['n']):.4f}")
    print(f"  unweighted mean                    : {f['auc_M2'].mean():.4f}")
    print(f"  weighted by positives              : {np.average(f['auc_M2'], weights=f['pos']):.4f}")
    print(f"  median                             : {f['auc_M2'].median():.4f}")
    print(f"  min / max                          : {f['auc_M2'].min():.4f} / {f['auc_M2'].max():.4f}")
    print(f"  frac of cell pairs with <3 positives: {(f['pos'] < 3).mean():.2%}")
    print(f"  frac with exactly 1 positive        : {(f['pos'] < 2).mean():.2%}")
    print("  positives-per-cell-pair distribution:", np.percentile(f["pos"], [10, 25, 50, 75, 90]).round(1).tolist())
    print("  n distribution                    :", np.percentile(f["n"], [10, 25, 50, 75, 90]).round(0).tolist())
    print("  AUC(M2) for cell pairs with <3 positives: %.4f (n=%d)"
          % (np.average(f[f["pos"] < 3]["auc_M2"], weights=f[f["pos"] < 3]["n"]), (f["pos"] < 3).sum()))
    print("  AUC(M2) for cell pairs with >=5 positives: %.4f (n=%d)"
          % (np.average(f[f["pos"] >= 5]["auc_M2"], weights=f[f["pos"] >= 5]["n"]), (f["pos"] >= 5).sum()))
    print("  AUC(M3-M1) sign by layout:")
    for lay, g in pr.groupby("layout"):
        gg = g[np.isfinite(g["d_M3_M1"])]
        if len(gg):
            print(f"    {lay:22s} ncp={len(gg):3d} mean_dM3M1={gg['d_M3_M1'].mean():+.3f} "
                  f"weighted={np.average(gg['d_M3_M1'], weights=gg['n']):+.3f} "
                  f"frac_pos={(gg['d_M3_M1']>0).mean():.2f}")


if __name__ == "__main__":
    main()
