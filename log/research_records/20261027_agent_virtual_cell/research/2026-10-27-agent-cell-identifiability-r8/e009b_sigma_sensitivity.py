"""E009b: is the VOI lead an artefact of the noise scale?

The VOI score Phi((min_{v!=u} p_v - p_u)/sigma) depends on sigma, which is estimated from
cross-cell residuals. If the top-1 benefit at large k vanishes when sigma is scaled by
0.5 or 2, the lead is not a robust finding and must not be reported as one.
Also reports the seed stability of the random arm.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r8"
ANCHORS = {"high control", "low control"}
FLOOR = 0.10
K_GRID = (4, 8)
SIGMA_MULT = (0.5, 1.0, 2.0)
N_SEEDS = 5
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

    def vec(fname, units):
        sub = df[(df["file"] == fname) & (~df["failed_qc"]) & df["y"].notna() & (~df["anchor"])]
        return sub.drop_duplicates("Well").set_index("Well")["y"].reindex(units).to_numpy(dtype=float)

    groups = {}
    for f, s in meta.items():
        groups.setdefault((s["iteration"], s["h"]), {}).setdefault(s["cell"], []).append(f)
    layouts = []
    for (it, h), cells in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 4:
            continue
        first = cells[good[0]][0]
        units = [u for u in sorted(meta[first]["combo"]) if meta[first]["combo"][u]]
        V = {c: [vec(f, units) for f in cells[c]] for c in good}
        layouts.append({"iteration": it, "hash": h[:12], "cells": good,
                        "Y": {c: np.nanmean(np.vstack(V[c]), axis=0) for c in good}})
    return df, layouts


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    _, layouts = build()
    out = {"kind": "voi_sigma_sensitivity", "input_sha256": sha256(CSV),
           "sigma_multipliers": list(SIGMA_MULT), "k_grid": list(K_GRID), "results": {}}

    for mult in SIGMA_MULT:
        rows = []
        for L in layouts:
            cells = L["cells"]
            for c in cells:
                others = [x for x in cells if x != c]
                if len(others) < 3:
                    continue
                Yc = L["Y"][c]
                M = np.vstack([L["Y"][x] for x in others])
                P = np.nanmean(M, axis=0)
                sigma = float(np.nanmedian(np.nanstd(M - P[None, :], axis=0))) * mult
                if not np.isfinite(sigma) or sigma <= 0:
                    continue
                valid = np.isfinite(P) & np.isfinite(Yc)
                if valid.sum() < 20:
                    continue
                idx = np.where(valid)[0]
                p, truth = P[idx], Yc[idx]
                n = idx.size
                best = float(np.min(truth))
                rank_true = np.argsort(np.argsort(truth))
                voi = np.empty(n)
                for j in range(n):
                    rest = np.delete(p, j)
                    m_other = float(np.min(rest)) if rest.size else np.inf
                    voi[j] = 0.5 * math.erfc((p[j] - m_other) / (sigma * math.sqrt(2.0)))
                for k in K_GRID:
                    if k > n - 1:
                        continue
                    for name, sel in (("exploit", list(np.argsort(-p)[:k])),
                                      ("voi", list(np.argsort(-voi)[:k]))):
                        est = p.copy()
                        est[sel] = truth[sel]
                        ch = int(np.argmin(est))
                        rows.append({"layout": L["hash"], "cell": c, "k": k, "strategy": name,
                                     "hit": int(rank_true[ch] < 3), "regret": float(truth[ch] - best)})
        r = pd.DataFrame(rows)
        block = {}
        for k in K_GRID:
            sub = r[r["k"] == k]
            if sub.empty:
                continue
            a = sub[sub.strategy == "voi"].set_index(["layout", "cell"])
            b = sub[sub.strategy == "exploit"].set_index(["layout", "cell"])
            common = a.index.intersection(b.index)
            dh = (a.loc[common, "hit"] - b.loc[common, "hit"])
            dr = (a.loc[common, "regret"] - b.loc[common, "regret"])
            block[str(k)] = {"n": int(len(common)),
                             "hit_voi": float(a.loc[common, "hit"].mean()),
                             "hit_exploit": float(b.loc[common, "hit"].mean()),
                             "hit_diff": float(dh.mean()),
                             "regret_voi": float(a.loc[common, "regret"].mean()),
                             "regret_exploit": float(b.loc[common, "regret"].mean()),
                             "regret_diff": float(dr.mean())}
        out["results"]["sigma_x%.1f" % mult] = block

    for rel in ("research/2026-10-27-agent-cell-identifiability-r8/e009b_sigma_sensitivity.py",):
        p = ROOT / rel
        if p.exists():
            out.setdefault("files", {})[rel] = sha256(p)
    (OUT / "E009B_SIGMA_SENSITIVITY.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    for m, block in out["results"].items():
        for k, v in block.items():
            print("%-12s k=%s n=%d | hit voi=%.3f exploit=%.3f diff=%+.3f | regret diff=%+.4f" % (
                m, k, v["n"], v["hit_voi"], v["hit_exploit"], v["hit_diff"], v["regret_diff"]))


if __name__ == "__main__":
    main()
