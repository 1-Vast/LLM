"""E007: are the cross-context order reversals reproducible, and do they concentrate
on particular drug pairs or particular cell pairs?

Pre-registered in PROTOCOL_E007.md. Reads only PAIR_SCREEN.csv.

T1 reproducibility: two independent plate pairings of the same cell pair
    (file1_A vs file1_B) and (file2_A vs file2_B). A stable reversal appears in both.
T2 concentration: per drug pair, how many of its cell pairs reverse; per cell pair,
    how many of its drug pairs reverse. Overdispersion relative to binomial.
T3 calibrated null: regenerate data under the shared-order model with the measured
    noise (the parametric null validated against the same-cell control in E006d),
    run it through the identical pipeline, and compare.
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
GAPS = (0.10, 0.15)
PAIRS_PER_CELLPAIR = 1000
N_NULL = 200
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load_layouts():
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
    groups = {}
    for f, s in meta.items():
        groups.setdefault((s["iteration"], s["h"]), {}).setdefault(s["cell"], []).append(f)

    def vec(fname: str, units: list[str]) -> np.ndarray:
        sub = df[(df["file"] == fname) & (~df["failed_qc"]) & df["y"].notna() & (~df["anchor"])]
        return sub.drop_duplicates("Well").set_index("Well")["y"].reindex(units).to_numpy(dtype=float)

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


def pair_flags(Y: np.ndarray, iu, ju, floor: float):
    """For a (n_cells, n_units) matrix, return sign matrix and readability mask per cell pair."""
    S = np.sign(Y[:, iu] - Y[:, ju])
    gap = np.abs(Y[:, iu] - Y[:, ju])
    return S, gap


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    df, layouts = load_layouts()
    rng = np.random.default_rng(SEED)

    res = {"kind": "reversal_reproducibility_and_concentration",
           "input_sha256": sha256(CSV),
           "settings": {"gaps": list(GAPS), "pairs_per_cellpair": PAIRS_PER_CELLPAIR,
                        "N_null": N_NULL, "seed": SEED},
           "audit": {"layouts": len(layouts),
                     "cells_per_layout": {f"{L['iteration']}/{L['hash']}": len(L["cells"]) for L in layouts},
                     "sampled_unitpairs_per_layout": {f"{L['iteration']}/{L['hash']}": int(L["iu"].size) for L in layouts}},
           "by_gap": {}}

    for floor in GAPS:
        t1_rows, dpair_rows, cpair_rows = [], [], []
        for L in layouts:
            cells, V, iu, ju = L["cells"], L["V"], L["iu"], L["ju"]
            Y = np.vstack([np.nanmean(np.vstack(V[c]), axis=0) for c in cells])
            S, gap = pair_flags(Y, iu, ju, floor)

            # ---- T1: independent plate pairings ----
            for a in range(len(cells)):
                for b in range(a + 1, len(cells)):
                    if len(V[cells[a]]) < 2 or len(V[cells[b]]) < 2:
                        continue
                    S1, g1 = pair_flags(np.vstack([V[cells[a]][0], V[cells[b]][0]]), iu, ju, floor)
                    S2, g2 = pair_flags(np.vstack([V[cells[a]][1], V[cells[b]][1]]), iu, ju, floor)
                    ok = (g1[0] >= floor) & (g1[1] >= floor) & (g2[0] >= floor) & (g2[1] >= floor) \
                        & np.isfinite(g1[0]) & np.isfinite(g1[1]) & np.isfinite(g2[0]) & np.isfinite(g2[1])
                    if ok.sum() < 50:
                        continue
                    rev1 = S1[0] != S1[1]
                    rev2 = S2[0] != S2[1]
                    t1_rows.append({"layout": f"{L['iteration']}/{L['hash']}",
                                    "cells": f"{cells[a]}|{cells[b]}", "n_pairs": int(ok.sum()),
                                    "rev1": int((rev1 & ok).sum()), "rev2": int((rev2 & ok).sum()),
                                    "both_rev": int((rev1 & rev2 & ok).sum())})

            # ---- T2: concentration ----
            rev_mat = np.zeros((0, iu.size), dtype=bool)
            ok_mat = np.zeros((0, iu.size), dtype=bool)
            rv, okv = [], []
            for a in range(len(cells)):
                for b in range(a + 1, len(cells)):
                    ok = (gap[a] >= floor) & (gap[b] >= floor) & np.isfinite(gap[a]) & np.isfinite(gap[b])
                    rv.append((S[a] != S[b]) & ok)
                    okv.append(ok)
                    if ok.sum() >= 50:
                        cpair_rows.append({"layout": f"{L['iteration']}/{L['hash']}",
                                           "cells": f"{cells[a]}|{cells[b]}",
                                           "n_pairs": int(ok.sum()), "n_reversing": int(((S[a] != S[b]) & ok).sum())})
            if rv:
                rev_mat = np.vstack(rv)
                ok_mat = np.vstack(okv)
                n_rev = rev_mat.sum(axis=0)
                n_ok = ok_mat.sum(axis=0)
                good = n_ok >= 2
                for pi in np.where(good)[0]:
                    dpair_rows.append({"layout": f"{L['iteration']}/{L['hash']}",
                                       "unit_i": L["units"][iu[pi]], "unit_j": L["units"][ju[pi]],
                                       "n_cellpairs": int(n_ok[pi]), "n_reversing_cellpairs": int(n_rev[pi])})

        t1 = pd.DataFrame(t1_rows)
        dd = pd.DataFrame(dpair_rows)
        cc = pd.DataFrame(cpair_rows)

        n = int(t1["n_pairs"].sum())
        r1 = float(t1["rev1"].sum() / n)
        r2 = float(t1["rev2"].sum() / n)
        overlap = float(t1["both_rev"].sum() / n)
        block = {"n_pairs": n, "n_cellpairs": int(len(t1)),
                 "rate_pairing_A": r1, "rate_pairing_B": r2, "overlap_rate": overlap,
                 "expected_if_independent": r1 * r2,
                 "independence_ratio": (overlap / (r1 * r2)) if r1 * r2 > 0 else None}

        def disp(frame, kcol, ncol):
            fr = frame.dropna()
            if len(fr) < 10:
                return None
            k = fr[kcol].to_numpy(float)
            nn = fr[ncol].to_numpy(float)
            p = k.sum() / nn.sum()
            obs_var = float(np.var(k, ddof=1))
            bin_var = float(np.mean(nn * p * (1 - p)))
            icc = (obs_var - bin_var) / (obs_var + (np.mean(nn) - 1) * bin_var + 1e-12)
            return {"n": int(len(fr)), "mean_k": float(k.mean()), "mean_n": float(nn.mean()),
                    "p_pooled": float(p), "obs_var": obs_var, "binomial_var": bin_var,
                    "variance_ratio": (obs_var / bin_var) if bin_var > 0 else None,
                    "icc_moment": float(icc)}

        # ---- T3: calibrated shared-order null through the same pipeline ----
        null_rates = []
        for _ in range(N_NULL):
            rev_tot, ok_tot = 0, 0
            for L in layouts:
                cells, V, iu, ju = L["cells"], L["V"], L["iu"], L["ju"]
                prof = np.vstack([np.nanmean(np.vstack(V[c]), axis=0) for c in cells])
                if len(V[cells[0]]) >= 2:
                    d0 = V[cells[0]][0] - V[cells[0]][1]
                    sig = float(np.nanstd(d0, ddof=1) / math.sqrt(2.0))
                else:
                    sig = 0.035
                Yn = prof + rng.normal(0.0, sig / math.sqrt(2.0), prof.shape)
                Sn, gn = pair_flags(Yn, iu, ju, floor)
                for a in range(len(cells)):
                    for b in range(a + 1, len(cells)):
                        ok = (gn[a] >= floor) & (gn[b] >= floor) & np.isfinite(gn[a]) & np.isfinite(gn[b])
                        if ok.sum() < 50:
                            continue
                        rev_tot += int(((Sn[a] != Sn[b]) & ok).sum())
                        ok_tot += int(ok.sum())
            null_rates.append(rev_tot / ok_tot if ok_tot else float("nan"))
        block["dispersion_drugpair"] = disp(dd, "n_reversing_cellpairs", "n_cellpairs")
        block["dispersion_cellpair"] = disp(cc, "n_reversing", "n_pairs")
        block["null_shared_order_reversal_rate"] = {"mean": float(np.nanmean(null_rates)),
                                                    "q025": float(np.nanquantile(null_rates, 0.025)),
                                                    "q975": float(np.nanquantile(null_rates, 0.975))}
        res["by_gap"][str(floor)] = block

    res["files"] = {}
    for rel in ("research/2026-10-27-agent-cell-identifiability-r6/PROTOCOL_E007.md",
                "research/2026-10-27-agent-cell-identifiability-r6/e007_reversal_structure.py",
                str(CSV.relative_to(ROOT))):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E007_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    for floor in GAPS:
        d = res["by_gap"][str(floor)]
        print("gap>=%.2f | pairs=%d cellpairs=%d | rateA=%.4f rateB=%.4f overlap=%.4f indep=%.6f ratio=%.1f" % (
            floor, d["n_pairs"], d["n_cellpairs"], d["rate_pairing_A"], d["rate_pairing_B"],
            d["overlap_rate"], d["expected_if_independent"], d["independence_ratio"] or float("nan")))
        for key in ("dispersion_drugpair", "dispersion_cellpair"):
            if d[key]:
                x = d[key]
                print("   %-22s n=%d mean_k=%.3f mean_n=%.2f p=%.3f var_ratio=%.2f icc=%.3f" % (
                    key, x["n"], x["mean_k"], x["mean_n"], x["p_pooled"], x["variance_ratio"], x["icc_moment"]))
        z = d["null_shared_order_reversal_rate"]
        print("   shared-order null rate: %.4f [%.4f, %.4f]" % (z["mean"], z["q025"], z["q975"]))


if __name__ == "__main__":
    main()
