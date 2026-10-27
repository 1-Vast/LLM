"""C4: can this dataset separate "drug-combination identity" from "well position" at all?

E008c claims excluding same-row/same-col pairs rules out a well-position artifact. But if
the drug-combination -> well mapping is the same physical plate map in every layout, then
every unit pair is simultaneously a drug pair and a position pair, and NO within-layout
control can separate them. What is needed is the same drug pair appearing at a DIFFERENT
position in a different layout (different plate/day/batch).

Checks:
  A. is a given (drug1,conc1,drug2,conc2) unit always at the same Well across layouts?
  B. how many unit identities are shared between layouts; how many shared units keep the
     same well, how many move?
  C. if some units move, does per-unit reversal involvement replicate across layouts
     (drug-property) or not (batch/position property)?
  D. edge-well enrichment of reversal-prone unit pairs (a shared-layout artefact that the
     same-row/same-col filter cannot touch).
"""
from __future__ import annotations

import hashlib
import json
import re
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
SEED = 20261027


def rc(well):
    m = re.match(r"^([A-Z])(\d+)$", str(well).strip().upper())
    return (ord(m.group(1)) - ord("A"), int(m.group(2)) - 1) if m else (None, None)


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
                       "unit": {w: (d1, float(c1), d2, float(c2)) for w, (d1, c1, d2, c2) in
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
                        "iu": iu[sel], "ju": ju[sel], "Y": Y, "unit": meta[first]["unit"]})
    return layouts


def main():
    layouts = build()
    ids = [f"{L['iteration']}/{L['hash']}" for L in layouts]

    # ---------- A/B: drug identity vs well ----------
    print("=== A. is a unit's Well fixed across layouts? ===")
    unit_well = defaultdict(set)
    unit_lay = defaultdict(set)
    for L, lid in zip(layouts, ids):
        for w in L["units"]:
            unit_well[L["unit"][w]].add(w)
            unit_lay[L["unit"][w]].add(lid)
    shared = {k: v for k, v in unit_lay.items() if len(v) > 1}
    print(f"  distinct unit identities (drug1,conc1,drug2,conc2): {len(unit_well)}")
    print(f"  unit identities present in >1 layout: {len(shared)}")
    nmoved = sum(1 for k in shared if len(unit_well[k]) > 1)
    print(f"  of those, units that appear at a DIFFERENT well: {nmoved} "
          f"({100*nmoved/max(len(shared),1):.1f}%)")
    print(f"  units at >1 well: {sum(1 for k,v in unit_well.items() if len(v)>1)} / {len(unit_well)}")
    # pairwise layout overlap on unit identity
    print("\n  pairwise layout overlap (unit identities) and whether wells coincide:")
    for i in range(len(layouts)):
        for j in range(i + 1, len(layouts)):
            si = {layouts[i]["unit"][w]: w for w in layouts[i]["units"]}
            sj = {layouts[j]["unit"][w]: w for w in layouts[j]["units"]}
            common = set(si) & set(sj)
            if not common:
                continue
            samew = sum(1 for k in common if si[k] == sj[k])
            print(f"    {ids[i]} vs {ids[j]}: shared_units={len(common):3d} same_well={samew:3d}")

    # ---------- D: edge enrichment ----------
    print("\n=== D. edge-well enrichment of reversal-prone unit pairs ===")
    rows = []
    for L, lid in zip(layouts, ids):
        cells, Y, iu, ju = L["cells"], L["Y"], L["iu"], L["ju"]
        nc = len(cells)
        S = np.sign(Y[:, iu] - Y[:, ju])
        gap = np.abs(Y[:, iu] - Y[:, ju])
        ok = (gap >= FLOOR) & np.isfinite(gap)
        rev = np.zeros(iu.size)
        t = np.zeros(iu.size)
        for a in range(nc):
            for b in range(a + 1, nc):
                m = ok[a] & ok[b]
                rev[m] += (S[a, m] != S[b, m])
                t[m] += 1
        for p in range(iu.size):
            if t[p] < 3:
                continue
            (r0, c0) = rc(L["units"][iu[p]])
            (r1, c1) = rc(L["units"][ju[p]])
            # plate is 384-well: rows A-P (0..15), cols 1-24 (0..23)
            edge_i = int(r0 in (0, 15) or c0 in (0, 23))
            edge_j = int(r1 in (0, 15) or c1 in (0, 23))
            rows.append({"layout": lid, "rate": rev[p] / t[p], "n": t[p],
                         "edge_any": max(edge_i, edge_j), "edge_both": int(edge_i and edge_j),
                         "edge_none": int(edge_i == 0 and edge_j == 0),
                         "r0": r0, "c0": c0, "r1": r1, "c1": c1})
    er = pd.DataFrame(rows)
    print(f"  unit pairs (>=3 obs): {len(er)}")
    for k in ("edge_any", "edge_both", "edge_none"):
        g = er[er[k] == 1]
        print(f"  {k:10s} n={len(g):4d} ({100*len(g)/len(er):5.1f}%) mean_rate={g['rate'].mean():.4f}")
    hi = er[er["rate"] > 0]
    print(f"  ever-reversing pairs: {len(hi)}  edge_any_frac={hi['edge_any'].mean():.3f} "
          f"(all pairs {er['edge_any'].mean():.3f})")
    print(f"  reversal mass share in edge-involving pairs: "
          f"{(hi[hi.edge_any==1]['rate']*hi[hi.edge_any==1]['n']).sum()/ (hi['rate']*hi['n']).sum():.3f}")

    # ---------- C: cross-layout replication of per-unit reversal involvement ----------
    print("\n=== C. does per-unit reversal involvement replicate across layouts? ===")
    # per-unit involvement: of the sampled pairs containing unit u, what fraction ever reversed
    per_unit = {}
    for L, lid in zip(layouts, ids):
        cells, Y, iu, ju = L["cells"], L["Y"], L["iu"], L["ju"]
        nc = len(cells)
        S = np.sign(Y[:, iu] - Y[:, ju])
        gap = np.abs(Y[:, iu] - Y[:, ju])
        ok = (gap >= FLOOR) & np.isfinite(gap)
        rev = np.zeros(iu.size); t = np.zeros(iu.size)
        for a in range(nc):
            for b in range(a + 1, nc):
                m = ok[a] & ok[b]
                rev[m] += (S[a, m] != S[b, m]); t[m] += 1
        inv = defaultdict(lambda: [0.0, 0.0])
        for p in range(iu.size):
            if t[p] < 3:
                continue
            for k in (iu[p], ju[p]):
                u = L["unit"][L["units"][k]]
                inv[u][0] += rev[p] / t[p]
                inv[u][1] += 1
        per_unit[lid] = {k: v[0] / v[1] for k, v in inv.items() if v[1] >= 3}
    pairs = []
    for i in range(len(layouts)):
        for j in range(i + 1, len(layouts)):
            a, b = per_unit[ids[i]], per_unit[ids[j]]
            common = set(a) & set(b)
            if len(common) < 8:
                continue
            x = np.array([a[k] for k in common]); y = np.array([b[k] for k in common])
            same_well = sum(1 for k in common if True)  # placeholder
            pairs.append({"A": ids[i], "B": ids[j], "n": len(common),
                          "spearman": float(pd.Series(x).corr(pd.Series(y), method="spearman")),
                          "pearson": float(np.corrcoef(x, y)[0, 1]),
                          "meanA": float(x.mean()), "meanB": float(y.mean())})
    pdf = pd.DataFrame(pairs)
    print(pdf.to_string(index=False) if len(pdf) else "  no layout pair shares >=8 unit identities")
    if len(pdf):
        print(f"\n  median cross-layout Spearman of per-unit reversal involvement: {pdf['spearman'].median():.3f}")
    er.to_csv(OUT / "c4_edge_per_pair.csv", index=False)


if __name__ == "__main__":
    main()
