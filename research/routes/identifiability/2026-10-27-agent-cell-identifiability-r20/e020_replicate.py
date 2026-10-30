"""E020: replicate the shared-order rejection on the independent high-diversity design.

Pre-registered in PROTOCOL_E020.md. Reads only PAIR_SCREEN.csv.

Each (layout, cell, file) yields a viability vector over ~351 compound pairs (one well
each). Cross-cell Spearman is computed between different cells of the same layout;
the same-cell ceiling between two files of the same cell; an independence null by
shuffling one cell's vector.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r20"
ANCHORS = {"high control", "low control"}
N_BOOT = 1000
N_NULL = 200
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    if a.size < 10:
        return float("nan")
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    ra -= ra.mean()
    rb -= rb.mean()
    den = math.sqrt(float((ra ** 2).sum()) * float((rb ** 2).sum()))
    return float((ra * rb).sum() / den) if den > 0 else float("nan")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    df = pd.read_csv(CSV, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={df.columns[0]: "row_id"})
    for c in ("Drug 1", "Drug 2", "Cell line", "file", "Well"):
        df[c] = df[c].astype(str).str.strip()
    df["failed_qc"] = df["Failed QC"].astype(str).str.strip().str.lower().isin(["true", "1"])
    df["y"] = pd.to_numeric(df["Viability"], errors="coerce")
    df["c1"] = pd.to_numeric(df["Conc 1 (uM)"], errors="coerce")
    df["c2"] = pd.to_numeric(df["Conc 2 (uM)"], errors="coerce")
    df["anchor"] = df["Drug 1"].isin(ANCHORS) | df["Drug 2"].isin(ANCHORS)
    ok = df[(~df["anchor"]) & (~df["failed_qc"]) & df["y"].notna()]

    meta = {}
    for fname, g in df[~df["anchor"]].groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], g["c1"].round(9), g["Drug 2"], g["c2"].round(9))))
        meta[fname] = {"cell": g["Cell line"].iloc[0],
                       "h": hashlib.sha1(repr(layout).encode()).hexdigest(),
                       "qc": float(g["failed_qc"].mean()),
                       "npairs": int(g.groupby(["Drug 1", "Drug 2"]).ngroups)}
    groups = {}
    for f, s in meta.items():
        groups.setdefault(s["h"], {}).setdefault(s["cell"], []).append(f)

    rng = np.random.default_rng(SEED)
    cross_rows, same_rows, null_rows = [], [], []
    layouts_used = {}
    for h, cells in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 2:
            continue
        if max(meta[f]["npairs"] for c in good for f in cells[c]) < 100:
            continue
        # per-file vectors
        vec = {}
        for c in good:
            for f in cells[c]:
                s = ok[ok["file"] == f]
                v = s.groupby(["Drug 1", "Drug 2"])["y"].mean()
                if len(v) >= 100:
                    vec[(c, f)] = v
        if len(vec) < 2:
            continue
        layouts_used[h[:12]] = {"cells": good, "files": len(vec)}
        # cross-cell: one representative vector per cell (mean of its files)
        per_cell = {}
        for c in good:
            vs = [vec[(c, f)] for f in cells[c] if (c, f) in vec]
            if vs:
                per_cell[c] = pd.concat(vs, axis=1).mean(axis=1)
        cs = sorted(per_cell)
        for i in range(len(cs)):
            for j in range(i + 1, len(cs)):
                a, b = per_cell[cs[i]], per_cell[cs[j]]
                common = a.index.intersection(b.index)
                if len(common) < 100:
                    continue
                av = a.loc[common].to_numpy(float)
                bv = b.loc[common].to_numpy(float)
                r = spearman(av, bv)
                if np.isfinite(r):
                    cross_rows.append({"layout": h[:12], "cell_a": cs[i], "cell_b": cs[j], "rho": r, "n": len(common)})
                sh = rng.permutation(bv)
                rn = spearman(av, sh)
                if np.isfinite(rn):
                    null_rows.append({"layout": h[:12], "rho": rn})
        # same-cell ceiling
        for c in good:
            fs = [f for f in cells[c] if (c, f) in vec]
            if len(fs) >= 2:
                for i in range(len(fs)):
                    for j in range(i + 1, len(fs)):
                        a, b = vec[(c, fs[i])], vec[(c, fs[j])]
                        common = a.index.intersection(b.index)
                        if len(common) < 100:
                            continue
                        r = spearman(a.loc[common].to_numpy(float), b.loc[common].to_numpy(float))
                        if np.isfinite(r):
                            same_rows.append({"layout": h[:12], "cell": c, "rho": r, "n": len(common)})

    cross = pd.DataFrame(cross_rows)
    same = pd.DataFrame(same_rows)
    null = pd.DataFrame(null_rows)
    res = {"kind": "shared_order_replication_on_high_diversity_design",
           "input_sha256": sha256(CSV),
           "settings": {"n_boot": N_BOOT, "n_null": N_NULL, "seed": SEED},
           "audit": {"layouts": len(layouts_used), "cross_cell_pairs": int(len(cross)),
                     "same_cell_pairs": int(len(same)), "null_draws": int(len(null)),
                     "layouts_used": layouts_used},
           "files": {}}

    def boots(vals, groups_, nb=N_BOOT, seed_off=1):
        rng2 = np.random.default_rng(SEED + seed_off)
        lays = sorted(set(groups_))
        out = []
        arr = np.array(vals)
        gi = np.array(groups_)
        for _ in range(nb):
            pick = rng2.choice(lays, size=len(lays), replace=True)
            m = np.isin(gi, pick)
            if m.sum():
                out.append(float(arr[m].mean()))
        return [float(np.quantile(out, 0.025)), float(np.quantile(out, 0.975))] if out else None

    if len(cross):
        res["cross_cell"] = {"n": int(len(cross)), "mean_rho": float(cross["rho"].mean()),
                             "median_rho": float(cross["rho"].median()),
                             "ci95_layout_bootstrap": boots(cross["rho"].to_numpy(float),
                                                            cross["layout"].to_numpy(), seed_off=1),
                             "per_layout_median": {k: float(v) for k, v in cross.groupby("layout")["rho"].median().items()}}
    if len(same):
        res["same_cell_ceiling"] = {"n": int(len(same)), "mean_rho": float(same["rho"].mean()),
                                    "median_rho": float(same["rho"].median()),
                                    "ci95_layout_bootstrap": boots(same["rho"].to_numpy(float),
                                                                   same["layout"].to_numpy(), seed_off=2)}
    if len(null):
        res["independence_null"] = {"n": int(len(null)), "mean_rho": float(null["rho"].mean()),
                                    "median_rho": float(null["rho"].median())}

    # gap: same-cell minus cross-cell, layout-clustered on the layout means
    if len(same) and len(cross):
        lm = same.groupby("layout")["rho"].mean().rename("same").to_frame().join(
            cross.groupby("layout")["rho"].mean().rename("cross"), how="inner")
        gap = (lm["same"] - lm["cross"]).to_numpy()
        res["gap"] = {"n_layouts": int(len(lm)), "mean_gap": float(gap.mean()),
                      "ci95_layout_bootstrap": boots(gap, lm.index.to_numpy(), seed_off=3),
                      "per_layout": {k: float(v) for k, v in (lm["same"] - lm["cross"]).items()},
                      "layout_means": {k: {"same": float(r["same"]), "cross": float(r["cross"])}
                                       for k, r in lm.iterrows()}}
        h043 = bool(res["gap"]["ci95_layout_bootstrap"][0] > 0)
    else:
        h043 = False
    med_cross = res.get("cross_cell", {}).get("median_rho")
    h044 = bool(med_cross is not None and med_cross > 0.30)
    h045 = bool(med_cross is not None and 0.562 <= med_cross <= 0.862)
    res["decisions"] = {"H043_same_cell_exceeds_cross_cell": h043, "H044_cross_cell_not_zero": h044,
                        "H045_magnitude_matches_validation_plates": h045}
    res["decisions"]["verdict"] = ("replicates_on_high_diversity_design" if h043 else
                                   "does_not_replicate")
    res["limits"] = [
        "The ordering here is across different compound pairs at one dose each, not across dose ratios within a grid; same family, different object.",
        "Nine of 21 layouts have a same-cell replicate, so the ceiling rests on those nine.",
        "Functional viability only; no mechanism, no drug selection, no unseen drug.",
        "Exploratory: plates were used as scoring endpoints earlier and cells cross days.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r20/PROTOCOL_E020.md",
                "research/2026-10-27-agent-cell-identifiability-r20/e020_replicate.py",
                str(CSV.relative_to(ROOT))):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E020_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(cross):
        cross.to_csv(OUT / "E020_cross_cell.csv", index=False)
    if len(same):
        same.to_csv(OUT / "E020_same_cell.csv", index=False)

    print("layouts=%d cross_pairs=%d same_pairs=%d null=%d" % (len(layouts_used), len(cross), len(same), len(null)))
    for k in ("cross_cell", "same_cell_ceiling", "independence_null", "gap"):
        if k in res:
            v = {kk: vv for kk, vv in res[k].items() if kk not in ("per_layout_median", "per_layout", "layout_means")}
            print(k, json.dumps(v, ensure_ascii=False))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
