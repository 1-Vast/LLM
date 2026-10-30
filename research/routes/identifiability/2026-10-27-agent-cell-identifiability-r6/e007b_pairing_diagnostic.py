"""E007b: diagnostics raised by the E007 run.

1. R5 reported a 4.00% cross-cell reversal rate; E007's synchronous pairing gives ~2.6%.
   Hypothesis: the rate depends on WHICH plates are paired. (file1,file1) and (file2,file2)
   are closer in time than (file1,file2). Report all four pairings separately.
2. E007's shared-order null re-added noise on top of already-noisy per-cell means, so its
   null reversal rate (4.07%) was inflated. De-noise the profile (shrinkage) before adding
   noise, and re-check the null reversal rate against the same-cell control.
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
N_NULL = 300
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

    pairtype, samecell = {}, {}
    for L in layouts:
        cells, V, iu, ju = L["cells"], L["V"], L["iu"], L["ju"]
        for a in range(len(cells)):
            for b in range(a + 1, len(cells)):
                ca, cb = cells[a], cells[b]
                if len(V[ca]) < 2 or len(V[cb]) < 2:
                    continue
                for ka in (0, 1):
                    for kb in (0, 1):
                        key = f"cross_{ka + 1}{kb + 1}"
                        rev, ok = flags(V[ca][ka], V[cb][kb], iu, ju)
                        d = pairtype.setdefault(key, {"rev": 0, "pairs": 0})
                        d["rev"] += int(rev.sum())
                        d["pairs"] += int(ok.sum())
        for c in cells:
            if len(V[c]) < 2:
                continue
            rev, ok = flags(V[c][0], V[c][1], iu, ju)
            d = samecell.setdefault("same_12", {"rev": 0, "pairs": 0})
            d["rev"] += int(rev.sum())
            d["pairs"] += int(ok.sum())

    # ---- calibrated null with de-noised profile ----
    def null_rate(n_sim: int) -> list[float]:
        out = []
        for _ in range(n_sim):
            rev_tot = ok_tot = 0
            for L in layouts:
                cells, V, iu, ju = L["cells"], L["V"], L["iu"], L["ju"]
                prof = []
                sig_list = []
                for c in cells:
                    m = np.nanmean(np.vstack(V[c]), axis=0)
                    if len(V[c]) >= 2:
                        d0 = V[c][0] - V[c][1]
                        s_file = float(np.nanstd(d0, ddof=1) / math.sqrt(2.0))
                    else:
                        s_file = 0.035
                    k = len(V[c])
                    lam = math.sqrt(max(0.0, 1.0 - (s_file ** 2 / k) / max(np.nanvar(m), 1e-12)))
                    prof.append(np.nanmean(m) + lam * (m - np.nanmean(m)))
                    sig_list.append(s_file)
                P = np.vstack(prof)
                sig_eff = float(np.nanmean(sig_list)) / math.sqrt(2.0)   # two-plate mean noise
                Yn = P + rng.normal(0.0, sig_eff, P.shape)
                for a in range(len(cells)):
                    for b in range(a + 1, len(cells)):
                        rev, ok = flags(Yn[a], Yn[b], iu, ju)
                        rev_tot += int(rev.sum())
                        ok_tot += int(ok.sum())
            out.append(rev_tot / ok_tot if ok_tot else float("nan"))
        return out

    nr = null_rate(N_NULL)
    res = {
        "kind": "e007_diagnostics_pairing_and_null",
        "input_sha256": sha256(CSV),
        "floor": FLOOR,
        "reversal_rate_by_plate_pairing": {
            k: {"reversals": v["rev"], "pairs": v["pairs"], "rate": v["rev"] / v["pairs"] if v["pairs"] else None}
            for k, v in pairtype.items()},
        "same_cell_control": {
            k: {"reversals": v["rev"], "pairs": v["pairs"], "rate": v["rev"] / v["pairs"] if v["pairs"] else None}
            for k, v in samecell.items()},
        "null_shared_order_denoised": {"mean": float(np.nanmean(nr)), "q025": float(np.nanquantile(nr, 0.025)),
                                       "q975": float(np.nanquantile(nr, 0.975)), "n_sim": N_NULL},
        "files": {},
    }
    # within-cell pairing types are only (1,2); report cross-cell ordered pairings
    p = res["reversal_rate_by_plate_pairing"]
    res["synchronous_vs_asynchronous"] = {
        "synchronous": {k: p[k]["rate"] for k in ("cross_11", "cross_22") if k in p},
        "asynchronous": {k: p[k]["rate"] for k in ("cross_12", "cross_21") if k in p},
    }
    for rel in ("research/2026-10-27-agent-cell-identifiability-r6/e007b_pairing_diagnostic.py",
                str(CSV.relative_to(ROOT))):
        pth = ROOT / rel
        if pth.exists():
            res["files"][rel] = sha256(pth)
    (OUT / "E007B_DIAGNOSTIC.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    print("reversal rate by plate pairing (gap>=%.2f):" % FLOOR)
    for k, v in sorted(p.items()):
        print("   %-10s %7d / %8d = %.4f" % (k, v["reversals"], v["pairs"], v["rate"]))
    for k, v in sorted(res["same_cell_control"].items()):
        print("   %-10s %7d / %8d = %.4f  (same-cell control)" % (k, v["reversals"], v["pairs"], v["rate"]))
    z = res["null_shared_order_denoised"]
    print("de-noised shared-order null reversal rate: %.4f [%.4f, %.4f]" % (z["mean"], z["q025"], z["q975"]))


if __name__ == "__main__":
    main()
