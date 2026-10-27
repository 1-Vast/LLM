"""C6: three last numbers.

1. Sample arithmetic: E008's 176 cell pairs vs the 136 that produce an AUC vs E008C's
   17,186-observation positional control vs E008B's 21,278. Is the positional control run
   on the same sample as the headline? (No: it is conditioned on >=1 reversal.)
2. Are the reversals near-ties or real rank crossings? Distribution of min(gap) at reversal
   vs non-reversal observations, and AUC(M2) inside the top gap quintile.
3. The cheapest falsification test: a permutation null that PRESERVES per-well flippiness
   and destroys only the pair-level pairing. If AUC survives, the "drug-pair" attribution
   is not identified and the signal is a per-well property.
"""
from __future__ import annotations

import hashlib
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


def auc(y, s):
    y = np.asarray(y, bool)
    if y.all() or (~y).all():
        return float("nan")
    r = pd.Series(s).rank().to_numpy()
    n1, n0 = int(y.sum()), int((~y).sum())
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


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
    pr = pd.read_csv(ROOT / "research" / "2026-10-27-agent-cell-identifiability-r7" / "E008_per_cellpair.csv")
    n_all = int(pr["n"].sum())
    pos_all = float((pr["prev"] * pr["n"]).sum())
    f = pr[np.isfinite(pr["auc_M2"])]
    print("=== 1. sample arithmetic ===")
    print(f"  E008 176 cell pairs : n={n_all} positives={pos_all:.0f} base={pos_all/n_all:.4f}")
    print(f"  E008 136 scored     : n={int(f['n'].sum())} positives={(f['prev']*f['n']).sum():.0f} "
          f"base={(f['prev']*f['n']).sum()/f['n'].sum():.4f}")
    print(f"  E008B               : n=21278 base=0.02848")
    print(f"  E008C 'all'         : n=17186 base=0.03526")
    print(f"  => E008C removed {n_all-17186} obs ({100*(n_all-17186)/n_all:.1f}%) and raised the base rate "
          f"{100*(0.03526/0.02848-1):.0f}% relative, by dropping every zero-positive cell pair")
    print(f"  => the 'positional control' 0.8746 -> 0.8749 is on a DIFFERENT, outcome-conditioned sample "
          f"than the 0.869 pooled headline")

    print("\n=== 2. are reversals near-ties? ===")
    gs, ys = [], []
    for L in layouts:
        cells, Y, iu, ju = L["cells"], L["Y"], L["iu"], L["ju"]
        nc = len(cells)
        S = np.sign(Y[:, iu] - Y[:, ju])
        gap = np.abs(Y[:, iu] - Y[:, ju])
        ok = (gap >= FLOOR) & np.isfinite(gap)
        for a in range(nc):
            for b in range(a + 1, nc):
                m = ok[a] & ok[b]
                if m.sum() == 0:
                    continue
                g_te = np.minimum(gap[a, m], gap[b, m])
                r_te = (S[a, m] != S[b, m]).astype(float)
                gs.append(g_te); ys.append(r_te)
    G, Yv = np.concatenate(gs), np.concatenate(ys)
    print(f"  obs={Yv.size} rev={int(Yv.sum())} base={Yv.mean():.4f}")
    print(f"  min-gap at reversal   : median={np.median(G[Yv==1]):.3f} "
          f"quartiles={np.percentile(G[Yv==1],[25,75]).round(3).tolist()}")
    print(f"  min-gap at non-reversal: median={np.median(G[Yv==0]):.3f} "
          f"quartiles={np.percentile(G[Yv==0],[25,75]).round(3).tolist()}")
    for lo in (0.10, 0.20, 0.30):
        m = G >= lo
        print(f"  rate at min-gap>={lo:.2f}: {Yv[m].mean():.4f} (n={m.sum()}, rev={int(Yv[m].sum())})")

    print("\n=== 3. per-well-preserving permutation null (cheapest falsification) ===")
    rng = np.random.default_rng(SEED + 11)
    obs, null = [], []
    for L in layouts:
        cells, Y, iu, ju = L["cells"], L["Y"], L["iu"], L["ju"]
        nc, nu = len(cells), len(L["units"])
        S = np.sign(Y[:, iu] - Y[:, ju])
        gap = np.abs(Y[:, iu] - Y[:, ju])
        ok = (gap >= FLOOR) & np.isfinite(gap)
        for a in range(nc):
            for b in range(a + 1, nc):
                tr = [i for i in range(nc) if i not in (a, b)]
                R, P = [], []
                for ii in range(len(tr)):
                    for jj in range(ii + 1, len(tr)):
                        x, y_ = tr[ii], tr[jj]
                        m = ok[x] & ok[y_]
                        if m.sum() == 0:
                            continue
                        R.append((S[x, m] != S[y_, m]).astype(float))
                        P.append(np.where(m)[0])
                if not R:
                    continue
                R, P = np.concatenate(R), np.concatenate(P)
                m_te = ok[a] & ok[b]
                if m_te.sum() < 20 or R.sum() == 0:
                    continue
                te = np.where(m_te)[0]
                r_te = (S[a, te] != S[b, te]).astype(float)
                if not (0 < r_te.sum() < r_te.size):
                    continue
                p0 = float(R.mean())
                cnt = np.bincount(P, minlength=iu.size).astype(float)
                rev = np.bincount(P, weights=R, minlength=iu.size)
                rate = (rev + ALPHA * p0) / (cnt + ALPHA)
                obs.append((r_te, rate[te]))
                # well involvement from training observations
                wi = np.bincount(iu[P], weights=R, minlength=nu)
                wc = np.bincount(iu[P], minlength=nu)
                wj = np.bincount(ju[P], weights=R, minlength=nu)
                wd = np.bincount(ju[P], minlength=nu)
                wr = ((wi + wj) + ALPHA * p0) / ((wc + wd) + ALPHA)
                pairw = 0.5 * (wr[iu] + wr[ju])
                # permute the pair rate among pairs with a similar well-level score
                q = pd.qcut(pairw, 8, labels=False, duplicates="drop")
                idx = np.arange(iu.size)
                perm = idx.copy()
                for k in np.unique(q[~pd.isna(q)]):
                    sel = idx[q == k]
                    perm[sel] = rng.permutation(sel)
                null.append((r_te, rate[perm][te]))
    yo = np.concatenate([o[0] for o in obs]); so = np.concatenate([o[1] for o in obs])
    yn = np.concatenate([o[0] for o in null]); sn = np.concatenate([o[1] for o in null])
    print(f"  observed pooled AUC(M2)                     : {auc(yo, so):.4f}")
    print(f"  AUC after permuting pair rates WITHIN bins of the per-well score: {auc(yn, sn):.4f}")
    print("  (if this stays near the observed value, the signal is per-well, not per-pair)")


if __name__ == "__main__":
    main()
