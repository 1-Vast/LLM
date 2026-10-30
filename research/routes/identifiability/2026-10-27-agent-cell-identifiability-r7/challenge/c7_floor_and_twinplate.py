"""C7: does the transfer survive away from the readability floor?

91% of reversals occur where min(|dY|) < 0.30, i.e. where the two treatments are close.
If AUC(M2) collapses once observations with min-gap < 0.20 / < 0.30 are removed, the
"transferable drug-pair fragility" is a statement about which pairs are ALMOST TIED, not
about substantive reordering of a functional viability ranking.

Also: per-pair propensity replication between the two twin plates (_1 vs _2), which is the
strongest within-batch independent-ish replication this file allows.
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
             "iu": iu[sel], "ju": ju[sel], "Y": Y}
        if with_plates:
            L["V"] = V
        layouts.append(L)
    return layouts


def main():
    layouts = build()
    print("=== pooled AUC(M2) as the near-tie band is removed ===")
    store = []
    for L in layouts:
        cells, Y, iu, ju = L["cells"], L["Y"], L["iu"], L["ju"]
        nc = len(cells)
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
                g_te = np.minimum(gap[a, te], gap[b, te])
                p0 = float(R.mean())
                cnt = np.bincount(P, minlength=iu.size).astype(float)
                rev = np.bincount(P, weights=R, minlength=iu.size)
                rate = (rev + ALPHA * p0) / (cnt + ALPHA)
                store.append((r_te, rate[te], g_te))
    for lo in (0.10, 0.15, 0.20, 0.25, 0.30, 0.40):
        ys, ss, ns = [], [], []
        rev = obs = 0
        for r_te, s_te, g_te in store:
            m = g_te >= lo
            if m.sum() == 0:
                continue
            ys.append(r_te[m]); ss.append(s_te[m]); ns.append(m.sum())
            rev += int(r_te[m].sum()); obs += int(m.sum())
        if not ys:
            continue
        y = np.concatenate(ys); s = np.concatenate(ss)
        print(f"  min-gap >= {lo:.2f}: obs={obs:6d} rev={rev:4d} base={rev/obs:.4f} "
              f"pooled AUC(M2)={auc(y, s):.4f}")

    # ---- twin-plate replication of the per-pair propensity ----
    print("\n=== twin-plate replication of per-pair propensity (plate _1 vs plate _2) ===")
    layouts2 = build(with_plates=True)
    xs, ys = [], []
    for L in layouts2:
        cells, iu, ju, units = L["cells"], L["iu"], L["ju"], L["units"]
        nc = len(cells)
        rep = {}
        for ci, c in enumerate(cells):
            Vc = [v for v in L["V"][c] if np.isfinite(v).any()]
            if len(Vc) < 2:
                continue
            rep[ci] = (Vc[0], Vc[1])
        if len(rep) < 4:
            continue
        idx = sorted(rep)

        def rate_from(which):
            S = np.vstack([np.sign(rep[i][which][iu] - rep[i][which][ju]) for i in idx])
            g = np.vstack([np.abs(rep[i][which][iu] - rep[i][which][ju]) for i in idx])
            ok = (g >= FLOOR) & np.isfinite(g)
            R, P = [], []
            for ii in range(len(idx)):
                for jj in range(ii + 1, len(idx)):
                    m = ok[ii] & ok[jj]
                    if m.sum() == 0:
                        continue
                    R.append((S[ii, m] != S[jj, m]).astype(float))
                    P.append(np.where(m)[0])
            if not R:
                return None, None
            R, P = np.concatenate(R), np.concatenate(P)
            p0 = float(R.mean())
            cnt = np.bincount(P, minlength=iu.size).astype(float)
            rev = np.bincount(P, weights=R, minlength=iu.size)
            return (rev + ALPHA * p0) / (cnt + ALPHA), cnt
        r1, c1_ = rate_from(0)
        r2, c2_ = rate_from(1)
        if r1 is None or r2 is None:
            continue
        m = (c1_ >= 3) & (c2_ >= 3)
        if m.sum() < 10:
            continue
        xs.append(r1[m]); ys.append(r2[m])
    if xs:
        x = np.concatenate(xs); y = np.concatenate(ys)
        print(f"  unit pairs compared: {x.size}")
        print(f"  Pearson r  = {np.corrcoef(x, y)[0,1]:.4f}")
        print(f"  Spearman r = {pd.Series(x).corr(pd.Series(y), method='spearman'):.4f}")
        print(f"  mean rate plate1={x.mean():.4f} plate2={y.mean():.4f}")
        print("  (a low correlation would mean the per-pair propensity does not even reproduce")
        print("   between the twin plates of the same batch, i.e. it is not a stable property)")


if __name__ == "__main__":
    main()
