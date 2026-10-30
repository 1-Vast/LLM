"""C5: is the "drug-pair" the right unit of analysis, and what kind of pair is it?

Two questions the protocol never asked:
 (a) COMPOSITION: 38% of the sampled unit pairs share BOTH drugs (they are two dose levels
     of the same combination). If the signal lives there, the object is a dose-rank
     crossing, not a "drug-pair ordering".
 (b) LEVEL: the propensity is assigned to a pair of wells. A pair is fragile if either of
     its wells is fragile. Test a per-WELL model (a compound whose viability sign is
     unstable across cell lines) against the per-PAIR model. If the per-well score matches
     M2, the pair is not the unit of the phenomenon.
Also: leave-one-layout-out held-out AUC of M2 (does the number survive dropping a batch?)
"""
from __future__ import annotations

import hashlib
from collections import defaultdict
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
        layouts.append({"iteration": it, "hash": h[:12], "cells": good, "units": units,
                        "iu": iu[sel], "ju": ju[sel], "Y": Y, "drugs": meta[first]["drugs"]})
    return layouts


def main():
    layouts = build()
    rows = []
    for L in layouts:
        cells, Y, iu, ju = L["cells"], L["Y"], L["iu"], L["ju"]
        nc = len(cells)
        layid = f"{L['iteration']}/{L['hash']}"
        S = np.sign(Y[:, iu] - Y[:, ju])
        gap = np.abs(Y[:, iu] - Y[:, ju])
        ok = (gap >= FLOOR) & np.isfinite(gap)
        d1 = np.array([L["drugs"][L["units"][i]][0] for i in iu[0:]])
        # per-pair drug sharing
        share_both = np.array([L["drugs"][L["units"][a]] == L["drugs"][L["units"][b]] for a, b in zip(iu, ju)])
        share_one = np.array([(len({L["drugs"][L["units"][a]][0], L["drugs"][L["units"][b]][0]}) == 1) ^
                              (len({L["drugs"][L["units"][a]][1], L["drugs"][L["units"][b]][1]}) == 1)
                              for a, b in zip(iu, ju)])
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
                p0 = float(R.mean())
                nunit = iu.size
                cnt = np.bincount(P, minlength=nunit).astype(float)
                rev = np.bincount(P, weights=R, minlength=nunit)
                rate = (rev + ALPHA * p0) / (cnt + ALPHA)
                # per-WELL involvement: for unit u, reversal rate of all training obs containing u
                wi = np.bincount(iu[P], weights=R, minlength=len(L["units"]))
                wc = np.bincount(iu[P], minlength=len(L["units"]))
                wi2 = np.bincount(ju[P], weights=R, minlength=len(L["units"]))
                wc2 = np.bincount(ju[P], minlength=len(L["units"]))
                well_rate = ((wi + wi2) + ALPHA * p0) / ((wc + wc2) + ALPHA)
                mwell = 0.5 * (well_rate[iu] + well_rate[ju])
                w1 = logit_fit(zz(G)[:, None], R)
                s1 = logit_pred(w1, zz(g_te)[:, None])
                m2z_obs = (rate[P] - p0) / (p0 * (1 - p0) + 1e-6)
                m2z_te = (rate[te] - p0) / (p0 * (1 - p0) + 1e-6)
                w3 = logit_fit(np.column_stack([zz(G), m2z_obs]), R)
                s3 = logit_pred(w3, np.column_stack([zz(g_te), m2z_te]))
                # pair + well
                wz = (mwell - mwell.mean()) / (mwell.std() + 1e-9)
                w6 = logit_fit(np.column_stack([zz(G), wz[P], m2z_obs]), R)
                s6 = logit_pred(w6, np.column_stack([zz(g_te), wz[te], m2z_te]))
                rows.append({"layout": layid, "cells": f"{cells[a]}|{cells[b]}", "n": int(te.size),
                             "auc_M1": auc(r_te, s1), "auc_M2": auc(r_te, rate[te]),
                             "auc_M3": auc(r_te, s3),
                             "auc_well": auc(r_te, mwell[te]), "auc_well_sp": auc(r_te, s6),
                             "share_both": float(np.mean(share_both[te] < 1)),
                             "pos_both": float(r_te[share_both[te] == 1].sum()),
                             "n_both": float((share_both[te] == 1).sum()),
                             "pos_one": float(r_te[share_both[te] < 1].sum()),
                             "n_one": float((share_both[te] < 1).sum())})
    pr = pd.DataFrame(rows)
    print(f"cell pairs: {len(pr)}")
    print("\n=== model comparison (weighted by n, as in E008) ===")
    for c in ("auc_M1", "auc_M2", "auc_M3", "auc_well", "auc_well_sp"):
        f = pr[np.isfinite(pr[c])]
        print(f"  {c:12s} {np.average(f[c], weights=f['n']):.4f}")
    print("\n  increments:")
    for name, a_, b_ in (("M3-M1 protocol", "auc_M3", "auc_M1"),
                         ("well+spacing - spacing", "auc_well_sp", "auc_M1"),
                         ("pair+spacing - (well+spacing)", "auc_M3", "auc_well_sp"),
                         ("well - constant", "auc_well", "auc_M1")):
        d = pr[a_] - pr[b_]
        f = np.isfinite(d)
        print(f"    {name:34s} {np.average(d[f], weights=pr['n'][f]):+.4f}  frac_pos={(d[f]>0).mean():.2f}")

    print("\n=== composition: pairs sharing BOTH drugs (two dose levels of one combination) ===")
    tot_n = pr["n_both"].sum() + pr["n_one"].sum()
    tot_both = pr["n_both"].sum(); pos_both = pr["pos_both"].sum()
    tot_one = pr["n_one"].sum(); pos_one = pr["pos_one"].sum()
    print(f"  same-combination dose pairs : n={tot_both:.0f} ({100*tot_both/tot_n:.1f}%) "
          f"positives={pos_both:.0f} rate={pos_both/max(tot_both,1):.4f}")
    print(f"  different-combination pairs : n={tot_one:.0f} ({100*tot_one/tot_n:.1f}%) "
          f"positives={pos_one:.0f} rate={pos_one/max(tot_one,1):.4f}")
    print(f"  share of all reversals contributed by same-combination dose pairs: "
          f"{pos_both/max(pos_both+pos_one,1):.3f}")
    pr.to_csv(OUT / "c5_level_and_composition.csv", index=False)


if __name__ == "__main__":
    main()
