"""E021: cross-plate same-cell replication on the high-diversity design.

Pre-registered in PROTOCOL_E021.md. Reads only PAIR_SCREEN.csv.

For every pair of layouts that share a cell line and at least 20 compound pairs, compute:
  - cross-plate same-cell Spearman over the shared compound pairs;
  - a same-plate ceiling (two files of that cell within one layout);
  - a cross-cell control over the same compound pairs (another cell of layout A).
"""

from __future__ import annotations

import hashlib
import json
import math
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
CSV = ROOT / "research" / "eight_directions_20261026" / "evidence_audit" / "raw" / "PAIR_SCREEN.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r21"
ANCHORS = {"high control", "low control"}
MIN_SHARED = 20
N_BOOT = 1000
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def spearman(a, b) -> float:
    if len(a) < 8:
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

    # per (layout, cell, file) viability vector over compound pairs
    vec = {}
    layouts = {}
    for h, cells in groups.items():
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 2:
            continue
        if max(meta[f]["npairs"] for c in good for f in cells[c]) < 100:
            continue
        layouts[h[:12]] = {}
        for c in good:
            for f in cells[c]:
                s = ok[ok["file"] == f]
                v = s.groupby(["Drug 1", "Drug 2"])["y"].mean()
                if len(v) >= 100:
                    vec[(h[:12], c, f)] = v
                    layouts[h[:12]].setdefault(c, []).append(f)

    rows = []
    for a, b in combinations(sorted(layouts), 2):
        shared_cells = set(layouts[a]) & set(layouts[b])
        if not shared_cells:
            continue
        for c in sorted(shared_cells):
            va = pd.concat([vec[(a, c, f)] for f in layouts[a][c] if (a, c, f) in vec], axis=1).mean(axis=1)
            vb = pd.concat([vec[(b, c, f)] for f in layouts[b][c] if (b, c, f) in vec], axis=1).mean(axis=1)
            common = va.index.intersection(vb.index)
            if len(common) < MIN_SHARED:
                continue
            x, y = va.loc[common].to_numpy(float), vb.loc[common].to_numpy(float)
            r_cross_plate = spearman(x, y)
            # same-plate ceiling on layout a (two files of that cell)
            ceiling = np.nan
            fs = [f for f in layouts[a][c] if (a, c, f) in vec]
            if len(fs) >= 2:
                v1, v2 = vec[(a, c, fs[0])], vec[(a, c, fs[1])]
                cm = v1.index.intersection(v2.index).intersection(common)
                if len(cm) >= 8:
                    ceiling = spearman(v1.loc[cm].to_numpy(float), v2.loc[cm].to_numpy(float))
            # cross-cell control on the same compound pairs, from layout a
            cross_cell = np.nan
            for c2 in layouts[a]:
                if c2 == c:
                    continue
                v2 = pd.concat([vec[(a, c2, f)] for f in layouts[a][c2] if (a, c2, f) in vec],
                               axis=1).mean(axis=1)
                cm = v2.index.intersection(common)
                if len(cm) >= 8:
                    cross_cell = spearman(va.loc[cm].to_numpy(float), v2.loc[cm].to_numpy(float))
                    break
            rows.append({"layout_a": a, "layout_b": b, "cell": c, "n_shared": int(len(common)),
                         "cross_plate": r_cross_plate, "same_plate_ceiling": ceiling,
                         "cross_cell": cross_cell})
    d = pd.DataFrame(rows)
    res = {"kind": "cross_plate_same_cell_replication",
           "input_sha256": sha256(CSV),
           "settings": {"min_shared": MIN_SHARED, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"layout_pairs_with_shared_cell": int(len(d)),
                     "layouts": int(pd.unique(d[["layout_a", "layout_b"]].values.ravel()).size) if len(d) else 0,
                     "median_shared_pairs": float(d["n_shared"].median()) if len(d) else None},
           "comparisons": rows, "files": {}}

    def summarize(col):
        v = d[col].dropna().to_numpy(float)
        if not len(v):
            return None
        rng = np.random.default_rng(SEED + 11)
        boots = [float(np.mean(rng.choice(v, size=len(v), replace=True))) for _ in range(N_BOOT)]
        return {"n": int(len(v)), "mean": float(v.mean()), "median": float(np.median(v)),
                "ci95_bootstrap": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}

    if len(d):
        res["summary"] = {k: summarize(k) for k in ("cross_plate", "same_plate_ceiling", "cross_cell")}
        # paired differences
        for name, (x, y) in {"ceiling_minus_cross_plate": ("same_plate_ceiling", "cross_plate"),
                             "cross_plate_minus_cross_cell": ("cross_plate", "cross_cell")}.items():
            m = d[[x, y]].dropna()
            if len(m) >= 3:
                dif = (m[x] - m[y]).to_numpy(float)
                rng = np.random.default_rng(SEED + 12)
                boots = [float(np.mean(rng.choice(dif, size=len(dif), replace=True))) for _ in range(N_BOOT)]
                res[name] = {"n": int(len(dif)), "mean": float(dif.mean()),
                             "ci95_bootstrap": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}
        s = res["summary"]
        h046 = bool(s["cross_plate"] and s["cross_plate"]["median"] > 0.50
                    and s["cross_plate"]["ci95_bootstrap"][0] > 0.30)
        h047 = bool(res.get("ceiling_minus_cross_plate") and res["ceiling_minus_cross_plate"]["ci95_bootstrap"][1] < 0)
        h048 = bool(res.get("cross_plate_minus_cross_cell") and res["cross_plate_minus_cross_cell"]["ci95_bootstrap"][0] > 0)
    else:
        h046 = h047 = h048 = False
    res["decisions"] = {"H046_cross_plate_reproduces": h046, "H047_plate_below_file_ceiling": h047,
                        "H048_cell_is_a_bigger_source_than_plate": h048}
    res["decisions"]["verdict"] = ("variance_hierarchy_file_lt_plate_lt_cell" if h047 and h048 else
                                   "replication_weak_reweight_cross_cell_claims" if not h046 else
                                   "mixed")
    res["limits"] = [
        "Each comparison uses only 21-43 shared compound pairs, so individual correlations are noisy; per-comparison values are reported.",
        "Cross-plate here means two different plate layouts that happen to share a cell and some compound pairs; the plate/batch identity differs, but so may the compound library composition.",
        "The high-diversity design has no dose dimension; the unit is one compound pair at one dose.",
        "Functional viability only; exploratory.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r21/PROTOCOL_E021.md",
                "research/2026-10-27-agent-cell-identifiability-r21/e021_cross_plate.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E021_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(d):
        d.to_csv(OUT / "E021_comparisons.csv", index=False)

    print("comparisons=%d" % len(d))
    for r in rows:
        print("   %s vs %s | %-12s n=%2d cross_plate=%+.3f ceiling=%+.3f cross_cell=%+.3f" % (
            r["layout_a"], r["layout_b"], r["cell"], r["n_shared"],
            r["cross_plate"], r["same_plate_ceiling"] if np.isfinite(r["same_plate_ceiling"]) else float("nan"),
            r["cross_cell"] if np.isfinite(r["cross_cell"]) else float("nan")))
    for k in ("summary", "ceiling_minus_cross_plate", "cross_plate_minus_cross_cell"):
        if k in res:
            print(k, json.dumps(res[k], ensure_ascii=False))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
