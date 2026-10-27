"""C1: structural audit of E008. Read-only on PAIR_SCREEN.csv.

Replicates E008 build() exactly, then reports:
  - layouts, cells/layout, plates(pseudo-replicates)/cell, cell overlap across layouts
  - how many distinct unit pairs ever reverse, rev-count distribution
  - effective sample size vs the 21,278 "observations" used for lift
  - the zero-positive cell pairs that are dropped from the weighted-mean AUC
  - what E008C silently dropped (its len(tr)<3 gate needs nc>=5)
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
SEED = 20261027


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
        nu = len(units)
        iu, ju = np.triu_indices(nu, 1)
        sel = rng.choice(iu.size, min(PAIRS_PER_LAYOUT, iu.size), replace=False)
        Y = np.vstack([np.nanmean(np.vstack(V[c]), axis=0) for c in good])
        layouts.append({"iteration": it, "hash": h[:12], "cells": good, "units": units,
                        "iu": iu[sel], "ju": ju[sel], "Y": Y,
                        "nfiles": {c: len(cells[c]) for c in good}})
    return df, meta, layouts


def main():
    df, meta, layouts = build()
    print("n layouts =", len(layouts))
    print("total files (plates) =", len(meta), " unique cells =", len({m['cell'] for m in meta.values()}))
    allcells = []
    rows = []
    for L in layouts:
        nc = len(L["cells"])
        allcells += L["cells"]
        rows.append({"layout": f"{L['iteration']}/{L['hash']}", "ncells": nc,
                     "nunits": len(L["units"]), "npairs": L["iu"].size,
                     "files_per_cell": sorted(L["nfiles"].values()),
                     "cells": ",".join(L["cells"])})
        print(f"  {L['iteration']}/{L['hash']}: cells={nc} units={len(L['units'])} "
              f"pairs={L['iu'].size} files/cell={sorted(L['nfiles'].values())}")
        print(f"    {', '.join(L['cells'])}")
    print("\ncell occurrences across layouts:", len(allcells), "distinct:", len(set(allcells)))
    from collections import Counter
    c = Counter(allcells)
    print("cells appearing in >1 layout:", {k: v for k, v in c.items() if v > 1})

    # ---- reversal concentration: how many distinct unit pairs ever reverse? ----
    print("\n=== per-layout reversal concentration (all cell pairs, floor 0.10) ===")
    tot = []
    for L in layouts:
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
        live = t > 0
        n_rev_pairs = int((rev[live] > 0).sum())
        print(f"  {L['iteration']}/{L['hash']}: cellpairs={nc*(nc-1)//2} live_unitpairs={live.sum()} "
              f"unitpairs_ever_reversing={n_rev_pairs} ({100*n_rev_pairs/max(live.sum(),1):.1f}%) "
              f"total_rev={int(rev.sum())} total_obs={int(t.sum())} "
              f"top5pairs_share_of_rev={100*np.sort(rev)[-5:].sum()/max(rev.sum(),1):.0f}%")
        tot.append({"layout": f"{L['iteration']}/{L['hash']}", "nc": nc, "files": L["nfiles"],
                    "live": int(live.sum()), "ever_rev": n_rev_pairs, "rev": int(rev.sum()),
                    "obs": int(t.sum())})
    print("\naggregate: live unit pairs =", sum(t["live"] for t in tot),
          " ever-reversing =", sum(t["ever_rev"] for t in tot),
          " total reversals =", sum(t["rev"] for t in tot),
          " total obs =", sum(t["obs"] for t in tot))
    print("NOTE: 'ever_rev' counts per layout; a unit pair is layout-specific.")

    # ---- E008C gate: nc >= 5 ----
    n_c_ge5 = sum(1 for L in layouts if len(L["cells"]) >= 5)
    print(f"\nlayouts with ncells>=5 (E008C's implied gate) = {n_c_ge5} / {len(layouts)}")
    print("layouts dropped by E008C gate:", [f"{L['iteration']}/{L['hash']}" for L in layouts if len(L["cells"]) < 5])

    (OUT / "c1_structure.json").write_text(json.dumps(
        {"layouts": [{"layout": r["layout"], "ncells": r["ncells"], "files_per_cell": r["files_per_cell"]} for r in rows],
         "reversal_concentration": tot}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
