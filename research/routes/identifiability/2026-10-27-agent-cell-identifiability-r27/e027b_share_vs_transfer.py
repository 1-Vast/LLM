"""E027b: the descriptive version that IS computable - does the potency share of a cell pair
explain how well one cell predicts the other? (25 cell pairs from the same design as E026)

Also reports the structural fact that blocks the non-circular version: source agreement needs
>=3 cells per layout and only 2 layouts have that, giving 4 units.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r27"
E026 = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r26" / "E026_cell_pairs.csv"
ANCHORS = {"high control", "low control"}
TOP = 10
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
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    a, b = a[m], b[m]
    if len(a) < 8:
        return float("nan")
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    ra -= ra.mean()
    rb -= rb.mean()
    den = math.sqrt(float((ra ** 2).sum()) * float((rb ** 2).sum()))
    return float((ra * rb).sum() / den) if den > 0 else float("nan")


def p_at_k(pred, truth, k=TOP):
    n = len(pred)
    kk = min(k, n - 1)
    return len(set(np.argsort(pred)[:kk]) & set(np.argsort(truth)[:kk])) / kk


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    e26 = pd.read_csv(E026)
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

    rows = []
    for h, cells in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 2:
            continue
        if max(meta[f]["npairs"] for c in good for f in cells[c]) < 100:
            continue
        per_cell = {}
        for c in good:
            vs = []
            for f in cells[c]:
                s = ok[ok["file"] == f]
                v = s.groupby(["Drug 1", "Drug 2"])["y"].mean()
                if len(v) >= 100:
                    vs.append(v)
            if vs:
                per_cell[c] = pd.concat(vs, axis=1).mean(axis=1).dropna()
        cs = sorted(per_cell)
        for a, b in [(x, y) for i, x in enumerate(cs) for y in cs[i + 1:]]:
            va, vb = per_cell[a], per_cell[b]
            common = va.index.intersection(vb.index)
            if len(common) < 100:
                continue
            ya = va.loc[common].to_numpy(float)
            yb = vb.loc[common].to_numpy(float)
            rows.append({"layout": h[:12], "cell_a": a, "cell_b": b, "n": len(common),
                         "cross_rho": spearman(ya, yb),
                         "cross_p10": p_at_k(yb, ya),
                         "cross_p10_rev": p_at_k(ya, yb)})
    d = pd.DataFrame(rows)
    merged = e26.merge(d, on=["layout", "cell_a", "cell_b"], how="inner")

    res = {"kind": "potency_share_versus_transfer_quality",
           "input_sha256": sha256(CSV), "settings": {"top": TOP, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"cell_pairs_with_both": int(len(merged)),
                     "non_circular_units_available": 4,
                     "why_only_4": "source agreement needs >=3 cells per layout; only 2 layouts have that"},
           "files": {}}

    if len(merged) >= 8:
        for col in ("main_share_loo", "cross_rho"):
            res[f"{col}_summary"] = {"mean": float(merged[col].mean()),
                                     "median": float(merged[col].median())}
        r1 = spearman(merged["main_share_loo"], merged["cross_rho"])
        r2 = spearman(merged["main_share_loo"], merged["cross_p10"])
        rng = np.random.default_rng(SEED + 71)
        lay = merged["layout"].to_numpy()
        uniq = sorted(set(lay))
        b1, b2 = [], []
        for _ in range(N_BOOT):
            pick = rng.choice(uniq, size=len(uniq), replace=True)
            sel = np.concatenate([np.where(lay == p)[0] for p in pick])
            b1.append(spearman(merged["main_share_loo"].to_numpy()[sel], merged["cross_rho"].to_numpy()[sel]))
            b2.append(spearman(merged["main_share_loo"].to_numpy()[sel], merged["cross_p10"].to_numpy()[sel]))
        b1 = [x for x in b1 if np.isfinite(x)]
        b2 = [x for x in b2 if np.isfinite(x)]
        res["association"] = {
            "with_cross_rho": {"spearman": r1, "ci95": [float(np.quantile(b1, 0.025)), float(np.quantile(b1, 0.975))] if b1 else None},
            "with_cross_p10": {"spearman": r2, "ci95": [float(np.quantile(b2, 0.025)), float(np.quantile(b2, 0.975))] if b2 else None}}
        a1 = res["association"]["with_cross_rho"]
        a2 = res["association"]["with_cross_p10"]
        h063 = bool(a1["spearman"] > 0.20 and a1["ci95"] and a1["ci95"][0] > 0)
        h063b = bool(a2["spearman"] > 0.20 and a2["ci95"] and a2["ci95"][0] > 0)
    else:
        h063 = h063b = False
    res["decisions"] = {
        "H063_potency_share_explains_transfer_rho": h063,
        "H063b_potency_share_explains_transfer_p10": h063b,
        "H064_non_circular_source_agreement": None,
        "H064_status": "UNTESTABLE here: source agreement requires >=3 cells per layout, and only 2 layouts have 3 cells (4 units). Recorded as untestable, NOT as a negative."}
    res["decisions"]["verdict"] = (
        "potency_share_explains_transfer" if (h063 or h063b) else
        "potency_share_does_not_explain_transfer")
    res["circularity_note"] = ("main_share needs the target cell's own data, so this association is explanatory, "
                               "not a pre-computable scope condition for a new cell")
    res["limits"] = [
        "Descriptive and circular for the purpose of predicting a NEW cell: main_share uses both cells' data.",
        "25 cell pairs from 21 layouts; the cluster bootstrap has few clusters.",
        "Ranking quality only, not regret-based decision value.",
        "Unseen combination, not unseen drug; no dose dimension.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r27/PROTOCOL_E027.md",
                "research/2026-10-27-agent-cell-identifiability-r27/e027b_share_vs_transfer.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E027B_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    merged.to_csv(OUT / "E027B_merged.csv", index=False)

    print("merged cell pairs=%d (non-circular units available: 4)" % len(merged))
    if "association" in res:
        print("association:", json.dumps(res["association"], ensure_ascii=False))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
