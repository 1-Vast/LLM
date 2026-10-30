"""E007c: the null that E007 should have used.

E007's T3 generated each cell from its OWN observed profile, which preserves that cell's
observed rank order (including any discordance), so its "null" reversal rate (3.83%)
merely copied the data (observed 3.96%). That null cannot test a shared order.

Here the shared order is forced: units are ordered by their average rank across cells,
each cell keeps its own sorted (de-noised) value spacing along that order, and noise is
added at the measured level. Two independent noisy copies are drawn per cell, which gives
both a same-cell null (compare the two copies of one cell) and a cross-cell null
(compare copy 1 of one cell with copy 1 of another).

The same-cell null is the calibration check: it must reproduce the observed same-cell
reversal rate (0.28%). Only if it does is the cross-cell comparison meaningful.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r6"
ANCHORS = {"high control", "low control"}
FLOOR = 0.10
PAIRS_PER_CELLPAIR = 1500
N_SIM = 200
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


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
        sel = rng.choice(iu.size, min(PAIRS_PER_CELLPAIR, iu.size), replace=False)
        layouts.append({"iteration": it, "hash": h[:12], "cells": good, "units": units, "V": V,
                        "iu": iu[sel], "ju": ju[sel]})
    return df, layouts


def flags(xa, xb, iu, ju, floor=FLOOR):
    ga = np.abs(xa[iu] - xa[ju])
    gb = np.abs(xb[iu] - xb[ju])
    ok = (ga >= floor) & (gb >= floor) & np.isfinite(ga) & np.isfinite(gb)
    rev = (np.sign(xa[iu] - xa[ju]) != np.sign(xb[iu] - xb[ju])) & ok
    return rev, ok


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    df, layouts = build()
    rng = np.random.default_rng(SEED)

    # precompute per-layout: shared rank order, per-cell sorted de-noised profile, file noise
    prep = []
    for L in layouts:
        cells, V = L["cells"], L["V"]
        nu = len(L["units"])
        Y = np.vstack([np.nanmean(np.vstack(V[c]), axis=0) for c in cells])
        # average rank across cells (nan-aware)
        ranks = np.vstack([pd.Series(row).rank().to_numpy() for row in Y])
        R = np.nanmean(ranks, axis=0)
        order = np.argsort(R)                       # positions ordered by shared rank
        prof, sig = [], []
        for ci, c in enumerate(cells):
            v = np.sort(Y[ci][~np.isnan(Y[ci])])
            if v.size < nu:
                v = np.interp(np.linspace(0, 1, nu), np.linspace(0, 1, v.size), v)
            s_file = float(np.nanstd(V[c][0] - V[c][1], ddof=1) / math.sqrt(2.0)) if len(V[c]) >= 2 else 0.035
            lam = math.sqrt(max(0.0, 1.0 - (s_file ** 2) / max(np.var(v), 1e-12)))
            placed = np.empty(nu)
            placed[order] = v.mean() + lam * (v - v.mean())
            prof.append(placed)
            sig.append(s_file)
        prep.append({"L": L, "P": np.vstack(prof), "sig": np.asarray(sig)})

    same_rev = same_ok = cross_rev = cross_ok = 0
    sim_same, sim_cross = [], []
    for _ in range(N_SIM):
        s_rev = s_ok = c_rev = c_ok = 0
        for item in prep:
            L, P, sig = item["L"], item["P"], item["sig"]
            cells, iu, ju = L["cells"], L["iu"], L["ju"]
            # two independent noisy copies per cell
            C1 = P + rng.normal(0.0, sig[:, None], P.shape)
            C2 = P + rng.normal(0.0, sig[:, None], P.shape)
            # same-cell null
            for a in range(len(cells)):
                rev, ok = flags(C1[a], C2[a], iu, ju)
                s_rev += int(rev.sum())
                s_ok += int(ok.sum())
            # cross-cell null
            for a in range(len(cells)):
                for b in range(a + 1, len(cells)):
                    rev, ok = flags(C1[a], C1[b], iu, ju)
                    c_rev += int(rev.sum())
                    c_ok += int(ok.sum())
        sim_same.append(s_rev / s_ok if s_ok else float("nan"))
        sim_cross.append(c_rev / c_ok if c_ok else float("nan"))

    res = {
        "kind": "shared_order_null_with_forced_common_rank",
        "input_sha256": sha256(CSV), "floor": FLOOR, "n_sim": N_SIM, "seed": SEED,
        "null_same_cell_reversal_rate": {"mean": float(np.nanmean(sim_same)),
                                         "q025": float(np.nanquantile(sim_same, 0.025)),
                                         "q975": float(np.nanquantile(sim_same, 0.975))},
        "null_cross_cell_reversal_rate": {"mean": float(np.nanmean(sim_cross)),
                                          "q025": float(np.nanquantile(sim_cross, 0.025)),
                                          "q975": float(np.nanquantile(sim_cross, 0.975))},
        "observed": {"same_cell": 0.0028, "cross_cell": 0.0396,
                     "source": "E007B_DIAGNOSTIC.json (same_12 109/38905; cross_11 4400/111167; cross_12/21/22 within 0.0387-0.0407)"},
        "files": {},
    }
    for rel in ("research/2026-10-27-agent-cell-identifiability-r6/e007c_shared_order_null.py",
                str(CSV.relative_to(ROOT))):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E007C_SHARED_ORDER_NULL.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    print("null (forced shared rank) same-cell reversal rate: %.5f [%.5f, %.5f]  vs observed 0.00280" % (
        res["null_same_cell_reversal_rate"]["mean"], res["null_same_cell_reversal_rate"]["q025"],
        res["null_same_cell_reversal_rate"]["q975"]))
    print("null (forced shared rank) cross-cell reversal rate: %.5f [%.5f, %.5f]  vs observed 0.03960" % (
        res["null_cross_cell_reversal_rate"]["mean"], res["null_cross_cell_reversal_rate"]["q025"],
        res["null_cross_cell_reversal_rate"]["q975"]))


if __name__ == "__main__":
    main()
