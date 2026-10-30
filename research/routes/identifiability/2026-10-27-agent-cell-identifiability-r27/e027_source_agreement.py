"""E027: can agreement among the SOURCE cells predict how well transfer will work,
before any data from the target cell exists?

Pre-registered in PROTOCOL_E027.md. Reads only PAIR_SCREEN.csv.
This is the non-circular version of R26's H063 (which needed the target's own data).
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r27"
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
        if len(good) < 3:
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
        if len(cs) < 3:
            continue
        for c in cs:
            others = [x for x in cs if x != c]
            idx = per_cell[c].index
            src = [per_cell[o].reindex(idx) for o in others]
            M = np.vstack([s.to_numpy(float) for s in src])
            if not np.isfinite(M).all():
                continue
            mu = M.mean(axis=0)
            y = per_cell[c].to_numpy(float)
            # source agreement: pairwise Spearman among source vectors
            ags = []
            for a, b in combinations(range(len(others)), 2):
                ags.append(spearman(M[a], M[b]))
            ags = [a for a in ags if np.isfinite(a)]
            if not ags:
                continue
            rows.append({"layout": h[:12], "cell": c, "n_sources": len(others), "n_pairs": len(y),
                         "source_agreement": float(np.mean(ags)),
                         "transfer_rho": spearman(mu, y),
                         "transfer_p10": p_at_k(mu, y)})

    d = pd.DataFrame(rows)
    res = {"kind": "source_agreement_as_a_pre_computable_scope_condition",
           "input_sha256": sha256(CSV),
           "settings": {"top": TOP, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"units": int(len(d)), "layouts": int(d["layout"].nunique()) if len(d) else 0,
                     "sources_2": int((d["n_sources"] == 2).sum()) if len(d) else 0,
                     "sources_3": int((d["n_sources"] == 3).sum()) if len(d) else 0},
           "files": {}}

    def bsum(v, seed_off):
        v = np.asarray(v, float)
        v = v[np.isfinite(v)]
        if not len(v):
            return None
        rng = np.random.default_rng(SEED + seed_off)
        boots = [float(np.mean(rng.choice(v, size=len(v), replace=True))) for _ in range(N_BOOT)]
        return {"n": int(len(v)), "mean": float(v.mean()), "median": float(np.median(v)),
                "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}

    if len(d) >= 6:
        res["descriptives"] = {
            "source_agreement": bsum(d["source_agreement"], 61),
            "transfer_rho": bsum(d["transfer_rho"], 62),
            "transfer_p10": bsum(d["transfer_p10"], 63)}
        rho_rho = spearman(d["source_agreement"], d["transfer_rho"])
        rho_p10 = spearman(d["source_agreement"], d["transfer_p10"])
        rng = np.random.default_rng(SEED + 64)
        boots_rho, boots_p10 = [], []
        lay = d["layout"].to_numpy()
        uniq = sorted(set(lay))
        for _ in range(N_BOOT):
            pick = rng.choice(uniq, size=len(uniq), replace=True)
            sel = np.concatenate([np.where(lay == p)[0] for p in pick])
            boots_rho.append(spearman(d["source_agreement"].to_numpy()[sel], d["transfer_rho"].to_numpy()[sel]))
            boots_p10.append(spearman(d["source_agreement"].to_numpy()[sel], d["transfer_p10"].to_numpy()[sel]))
        boots_rho = [b for b in boots_rho if np.isfinite(b)]
        boots_p10 = [b for b in boots_p10 if np.isfinite(b)]
        res["association"] = {
            "with_transfer_rho": {"spearman": rho_rho,
                                  "ci95": [float(np.quantile(boots_rho, 0.025)), float(np.quantile(boots_rho, 0.975))] if boots_rho else None},
            "with_transfer_p10": {"spearman": rho_p10,
                                  "ci95": [float(np.quantile(boots_p10, 0.025)), float(np.quantile(boots_p10, 0.975))] if boots_p10 else None}}
        two = d[d["n_sources"] == 2]["transfer_p10"]
        three = d[d["n_sources"] == 3]["transfer_p10"]
        res["by_source_count"] = {"p10_2sources": float(two.mean()) if len(two) else None,
                                  "p10_3sources": float(three.mean()) if len(three) else None,
                                  "n2": int(len(two)), "n3": int(len(three))}
        a1 = res["association"]["with_transfer_rho"]
        a2 = res["association"]["with_transfer_p10"]
        h064 = bool(a1["spearman"] > 0.20 and a1["ci95"] and a1["ci95"][0] > 0)
        h065 = bool(a2["spearman"] > 0.20 and a2["ci95"] and a2["ci95"][0] > 0)
        diff = None
        if len(two) and len(three):
            diff = float(two.mean() - three.mean())
        h066 = False
        res["source_count_diff_p10"] = diff
    else:
        h064 = h065 = h066 = False
    res["decisions"] = {"H064_source_agreement_predicts_rho": h064,
                        "H065_source_agreement_predicts_p10": h065,
                        "H066_fewer_sources_worse": h066}
    res["decisions"]["verdict"] = ("source_agreement_is_a_usable_pre_condition" if (h064 or h065)
                                   else "no_pre_computable_condition_from_sources_alone")
    res["limits"] = [
        "Source sets have only 2-3 cells, so the source-agreement estimate is itself noisy; results are stratified by source count.",
        "Ranking quality only, NOT regret-based decision value; R9's stop condition is untouched.",
        "Unseen combination, not unseen drug; no dose dimension.",
        "Functional viability only; exploratory.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r27/PROTOCOL_E027.md",
                "research/2026-10-27-agent-cell-identifiability-r27/e027_source_agreement.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E027_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(d):
        d.to_csv(OUT / "E027_units.csv", index=False)

    print("units=%d layouts=%d (2 sources=%d, 3 sources=%d)" % (
        len(d), res["audit"]["layouts"], res["audit"]["sources_2"], res["audit"]["sources_3"]))
    for k in ("descriptives", "association", "by_source_count"):
        if k in res:
            print(k, json.dumps(res[k], ensure_ascii=False))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
