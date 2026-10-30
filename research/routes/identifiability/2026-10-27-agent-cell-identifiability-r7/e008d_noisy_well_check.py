"""E008d: is the transferable propensity just a noisy well?

A unit pair whose wells are measured erratically will flip in every cell, which looks like
a transferable property without being one. The discriminating quantity is the SAME-CELL
reversal rate of that pair (its two replicate files disagreeing), which is pure measurement
instability with no cell difference in it.

  1. Per unit pair: cross-cell reversal rate vs same-cell reversal rate; correlation.
  2. Restrict the prediction to pairs whose same-cell rate is low (stable pairs): does the
     drug-pair propensity still predict reversals out of sample?
  3. Restrict to pairs whose same-cell rate is high (unstable pairs) for contrast.
"""

from __future__ import annotations

import hashlib
import json
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
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


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
        nu = len(units)
        iu, ju = np.triu_indices(nu, 1)
        sel = rng.choice(iu.size, min(PAIRS_PER_LAYOUT, iu.size), replace=False)
        layouts.append({"iteration": it, "hash": h[:12], "cells": good,
                        "V": V, "iu": iu[sel], "ju": ju[sel]})
    return df, layouts


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    _, layouts = build()
    per_pair = []
    auc_by_stratum = {}
    for L in layouts:
        cells, V, iu, ju = L["cells"], L["V"], L["iu"], L["ju"]
        nc = len(cells)
        lay = f"{L['iteration']}/{L['hash']}"
        # per cell: file0 and file1 gaps/signs when available
        G0, G1, S0, S1 = [], [], [], []
        for c in cells:
            if len(V[c]) >= 2:
                G0.append(np.abs(V[c][0][iu] - V[c][0][ju]))
                G1.append(np.abs(V[c][1][iu] - V[c][1][ju]))
                S0.append(np.sign(V[c][0][iu] - V[c][0][ju]))
                S1.append(np.sign(V[c][1][iu] - V[c][1][ju]))
            else:
                G0.append(np.full(iu.size, np.nan))
                G1.append(np.full(iu.size, np.nan))
                S0.append(np.full(iu.size, np.nan))
                S1.append(np.full(iu.size, np.nan))
        G0, G1, S0, S1 = map(np.vstack, (G0, G1, S0, S1))
        # same-cell instability per pair (two files of the same cell, both readable)
        ok_h = (G0 >= FLOOR) & (G1 >= FLOOR) & np.isfinite(G0) & np.isfinite(G1)
        rev_h = ((S0 != S1) & ok_h)
        n_h = ok_h.sum(axis=0)
        k_h = rev_h.sum(axis=0)
        same_rate = np.where(n_h > 0, k_h / np.maximum(n_h, 1), np.nan)
        # cross-cell rate per pair (mean over cells, two files)
        meanY = np.vstack([np.nanmean(np.vstack(V[c]), axis=0) for c in cells])
        gap = np.abs(meanY[:, iu] - meanY[:, ju])
        S = np.sign(meanY[:, iu] - meanY[:, ju])
        ok = (gap >= FLOOR) & np.isfinite(gap)
        kc = np.zeros(iu.size)
        nc_ = np.zeros(iu.size)
        for a in range(nc):
            for b in range(a + 1, nc):
                m = ok[a] & ok[b]
                kc[m] += (S[a, m] != S[b, m])
                nc_[m] += 1
        cross_rate = np.where(nc_ > 0, kc / np.maximum(nc_, 1), np.nan)
        for p in range(iu.size):
            per_pair.append({"layout": lay, "cross_rate": cross_rate[p], "same_cell_rate": same_rate[p],
                             "n_cross": nc_[p], "n_same": n_h[p]})

        # AUC of propensity, restricted by same-cell stability
        for label, selmask in (("all", np.ones(iu.size, bool)),
                               ("stable_pairs", (same_rate <= 0.0) | np.isnan(same_rate)),
                               ("mid_pairs", (same_rate > 0.0) & (same_rate <= 0.1)),
                               ("unstable_pairs", same_rate > 0.1)):
            preds, ys = [], []
            for a in range(nc):
                for b in range(a + 1, nc):
                    tr = [i for i in range(nc) if i not in (a, b)]
                    if len(tr) < 3:
                        continue
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
                    R = np.concatenate(R)
                    P = np.concatenate(P)
                    m_te = ok[a] & ok[b] & selmask
                    if m_te.sum() < 15 or R.sum() == 0:
                        continue
                    if not (0 < (S[a, m_te] != S[b, m_te]).sum() < m_te.sum()):
                        continue
                    p0 = float(R.mean())
                    cnt = np.bincount(P, minlength=iu.size).astype(float)
                    rev = np.bincount(P, weights=R, minlength=iu.size)
                    rate = (rev + ALPHA_SHRINK * p0) / (cnt + ALPHA_SHRINK)
                    te = np.where(m_te)[0]
                    preds.append(rate[te])
                    ys.append((S[a, te] != S[b, te]).astype(float))
            if preds:
                d = auc_by_stratum.setdefault(label, {"p": [], "y": []})
                d["p"].append(np.concatenate(preds))
                d["y"].append(np.concatenate(ys))

    pp = pd.DataFrame(per_pair).dropna(subset=["cross_rate", "same_cell_rate"])
    corr = float(pp[["cross_rate", "same_cell_rate"]].corr(method="spearman").iloc[0, 1]) if len(pp) > 5 else None
    strata = []
    for lo, hi, name in ((0, 0.001, "same_cell_rate==0"), (0.001, 0.05, "(0,0.05]"), (0.05, 0.15, "(0.05,0.15]"),
                         (0.15, 1.01, ">0.15")):
        s = pp[(pp["same_cell_rate"] >= lo) & (pp["same_cell_rate"] < hi)]
        strata.append({"same_cell_band": name, "n_pairs": int(len(s)),
                       "mean_cross_rate": float(s["cross_rate"].mean()) if len(s) else None})
    out = {"kind": "noisy_well_confound_check",
           "input_sha256": sha256(CSV), "floor": FLOOR,
           "spearman_cross_vs_same_cell_rate": corr,
           "n_pairs": int(len(pp)),
           "cross_rate_by_same_cell_band": strata,
           "auc_by_pair_stability": {},
           "note": ("same_cell_rate is the pair's own replicate disagreement - measurement instability "
                    "with no cell difference. If it drives the cross-cell rate, the 'transferable "
                    "propensity' is a noisy-well effect."),
           "files": {}}
    for label, d in auc_by_stratum.items():
        P = np.concatenate(d["p"])
        Y = np.concatenate(d["y"])
        out["auc_by_pair_stability"][label] = {"n": int(Y.size), "baseline": float(Y.mean()), "auc": auc(Y, P)}
    for rel in ("research/2026-10-27-agent-cell-identifiability-r7/e008d_noisy_well_check.py",
                str(CSV.relative_to(ROOT))):
        p = ROOT / rel
        if p.exists():
            out["files"][rel] = sha256(p)
    (OUT / "E008D_NOISY_WELL.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print("n_pairs=%d spearman(cross_rate, same_cell_rate)=%.3f" % (len(pp), corr or float("nan")))
    for s in strata:
        print("  same_cell %-16s n=%5d mean_cross_rate=%.4f" % (s["same_cell_band"], s["n_pairs"],
                                                               s["mean_cross_rate"] or float("nan")))
    for k, v in out["auc_by_pair_stability"].items():
        print("  AUC (%-15s) n=%6d baseline=%.4f AUC=%.4f" % (k, v["n"], v["baseline"], v["auc"]))


if __name__ == "__main__":
    main()
