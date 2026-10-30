"""E018: do compound pairs sharing an annotated gene target show more cell-to-cell
order instability, once the potency-proximity confound is controlled?

Pre-registered in PROTOCOL_E018.md. Reads PAIR_SCREEN.csv plus the two local MAPKG tables.

Unit = (layout, compound pair). Grid-level reversal rate = over cell pairs, the fraction
of sampled dose-combination pairs (gap >= 0.10 on both sides) whose ordering flips;
mean separation = mean min-gap over the same sampled pairs (the confound control).
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
MERGED = ROOT / "data" / "external" / "mapkg_20261009" / "DRUG_merged_drugs_with_residuals.csv"
DG = ROOT / "data" / "external" / "mapkg_20261009" / "DRUG-GENE_filtered_by_existing_drugs_and_genes.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r18"
ANCHORS = {"high control", "low control"}
FLOOR = 0.10
PAIR_SAMPLE = 300
N_BOOT = 1000
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def build_annotations():
    merged = pd.read_csv(MERGED, low_memory=False)
    merged["Drug Name"] = merged["Drug Name"].astype(str).str.strip()
    name2id = merged.drop_duplicates("Drug Name").set_index("Drug Name")["PubChem ID"].to_dict()
    dg = pd.read_csv(DG, low_memory=False)
    id2genes = {int(d): set(s["Gene ID"].astype(str)) for d, s in dg.groupby("Drug ID")}

    def genes(name: str) -> set:
        pid = name2id.get(name)
        if pid is None or pd.isna(pid):
            return set()
        return id2genes.get(int(pid), set())
    return genes


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    genes_of = build_annotations()

    df = pd.read_csv(CSV, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={df.columns[0]: "row_id"})
    for c in ("Drug 1", "Drug 2", "Cell line", "file", "Well"):
        df[c] = df[c].astype(str).str.strip()
    df["iteration"] = pd.to_numeric(df["Iteration"], errors="coerce")
    df["failed_qc"] = df["Failed QC"].astype(str).str.strip().str.lower().isin(["true", "1"])
    df["y"] = pd.to_numeric(df["Viability"], errors="coerce")
    df["c1"] = pd.to_numeric(df["Conc 1 (uM)"], errors="coerce")
    df["c2"] = pd.to_numeric(df["Conc 2 (uM)"], errors="coerce")
    df["anchor"] = df["Drug 1"].isin(ANCHORS) | df["Drug 2"].isin(ANCHORS)
    df["dmso"] = (df["Drug 1"].str.lower() == "dmso") | (df["Drug 2"].str.lower() == "dmso")
    ok = df[(~df["anchor"]) & (~df["failed_qc"]) & df["y"].notna()]
    meta = {}
    for fname, g in df[~df["anchor"]].groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], g["c1"].round(9), g["Drug 2"], g["c2"].round(9))))
        meta[fname] = {"cell": g["Cell line"].iloc[0],
                       "iteration": int(g["iteration"].iloc[0]) if pd.notna(g["iteration"].iloc[0]) else -1,
                       "h": hashlib.sha1(repr(layout).encode()).hexdigest(),
                       "qc": float(g["failed_qc"].mean())}
    groups = {}
    for f, s in meta.items():
        groups.setdefault((s["iteration"], s["h"]), {}).setdefault(s["cell"], []).append(f)

    rng = np.random.default_rng(SEED)
    rows = []
    for (it, h), cells in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 3:
            continue
        ref = cells[good[0]][0]
        rg = ok[ok["file"] == ref]
        if rg.empty:
            continue
        for (d1, d2) in sorted({(a, b) for a, b in zip(rg["Drug 1"], rg["Drug 2"])}):
            g1, g2 = genes_of(d1), genes_of(d2)
            annotated = bool(g1) and bool(g2)
            shared = bool(g1 & g2) if annotated else False
            sub = rg[(rg["Drug 1"] == d1) & (rg["Drug 2"] == d2)]
            doses1 = sorted(sub["c1"].unique())
            doses2 = sorted(sub["c2"].unique())
            if len(doses1) < 3 or len(doses2) < 3:
                continue
            grid = [(i, j) for i in range(len(doses1)) for j in range(len(doses2))]
            gidx = {g: k for k, g in enumerate(grid)}
            surf = {}
            for c in good:
                arrs = []
                for f in cells[c]:
                    s = ok[(ok["file"] == f) & (ok["Drug 1"] == d1) & (ok["Drug 2"] == d2)]
                    if s.empty:
                        continue
                    a = np.full(len(grid), np.nan)
                    for _, row in s.iterrows():
                        a[gidx[(doses1.index(row["c1"]), doses2.index(row["c2"]))]] = row["y"]
                    if np.isfinite(a).sum() >= 0.8 * len(grid):
                        arrs.append(a)
                if arrs:
                    surf[c] = np.nanmean(np.vstack(arrs), axis=0)
            cells_ok = [c for c in good if c in surf and np.isfinite(surf[c]).all()]
            if len(cells_ok) < 3:
                continue
            nu = len(grid)
            iu, ju = np.triu_indices(nu, 1)
            sel = rng.choice(iu.size, min(PAIR_SAMPLE, iu.size), replace=False)
            iu, ju = iu[sel], ju[sel]
            rev_tot = 0.0
            sep_tot = 0.0
            n_tot = 0
            for a in range(len(cells_ok)):
                for b in range(a + 1, len(cells_ok)):
                    ya, yb = surf[cells_ok[a]], surf[cells_ok[b]]
                    ga = np.abs(ya[iu] - ya[ju])
                    gb = np.abs(yb[iu] - yb[ju])
                    okk = (ga >= FLOOR) & (gb >= FLOOR)
                    if okk.sum() == 0:
                        continue
                    rev_tot += int((np.sign(ya[iu] - ya[ju]) != np.sign(yb[iu] - yb[ju]))[okk].sum())
                    sep_tot += float(np.minimum(ga, gb)[okk].mean()) * int(okk.sum())
                    n_tot += int(okk.sum())
            if n_tot < 200:
                continue
            rows.append({"layout": "%s/%s" % (it, h[:12]), "pair": "%s + %s" % (d1, d2),
                         "annotated": annotated, "shared": shared,
                         "shared_genes": int(len(g1 & g2)) if annotated else 0,
                         "rev_rate": rev_tot / n_tot, "mean_sep": sep_tot / n_tot, "n_pairs": n_tot,
                         "n_cells": len(cells_ok)})

    d = pd.DataFrame(rows)
    ann = d[d["annotated"]].copy()
    res = {"kind": "shared_annotated_gene_target_vs_order_instability",
           "input_sha256": {"PAIR_SCREEN.csv": sha256(CSV), "MAPKG_merged": sha256(MERGED), "MAPKG_drug_gene": sha256(DG)},
           "settings": {"floor": FLOOR, "pair_sample": PAIR_SAMPLE, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"pair_units": int(len(d)), "annotated_units": int(len(ann)),
                     "shared_units": int(ann["shared"].sum()),
                     "disjoint_units": int((~ann["shared"]).sum()),
                     "layouts": int(d["layout"].nunique())},
           "groups": {}, "stratified": {}, "files": {}}

    if len(ann):
        sh = ann[ann["shared"]]
        dj = ann[~ann["shared"]]
        res["groups"] = {
            "shared": {"n": int(len(sh)), "rev_rate": float(sh["rev_rate"].mean()),
                       "mean_sep": float(sh["mean_sep"].mean())},
            "disjoint": {"n": int(len(dj)), "rev_rate": float(dj["rev_rate"].mean()),
                         "mean_sep": float(dj["mean_sep"].mean())}}
        diff = float(sh["rev_rate"].mean() - dj["rev_rate"].mean())
        lays = sorted(ann["layout"].unique())
        rng2 = np.random.default_rng(SEED + 2)
        boots = []
        for _ in range(N_BOOT):
            pick = rng2.choice(lays, size=len(lays), replace=True)
            sel = pd.concat([ann[ann["layout"] == p] for p in pick])
            s2, d2_ = sel[sel["shared"]], sel[~sel["shared"]]
            if len(s2) and len(d2_):
                boots.append(float(s2["rev_rate"].mean() - d2_["rev_rate"].mean()))
        ci = [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))] if boots else None
        res["groups"]["diff_shared_minus_disjoint"] = diff
        res["groups"]["ci95_layout_clustered"] = ci

        # stratified by mean separation quintile
        ann["sep_bin"] = pd.qcut(ann["mean_sep"], 5, labels=False, duplicates="drop")
        strat = []
        for b in range(int(ann["sep_bin"].max()) + 1):
            sub = ann[ann["sep_bin"] == b]
            s2, d2_ = sub[sub["shared"]], sub[~sub["shared"]]
            if len(s2) >= 3 and len(d2_) >= 3:
                strat.append({"bin": b, "n_shared": int(len(s2)), "n_disjoint": int(len(d2_)),
                              "rev_shared": float(s2["rev_rate"].mean()),
                              "rev_disjoint": float(d2_["rev_rate"].mean()),
                              "diff": float(s2["rev_rate"].mean() - d2_["rev_rate"].mean()),
                              "sep_mid": float(sub["mean_sep"].mean())})
        res["stratified"] = strat
        pos = [s for s in strat if s["diff"] > 0]
        w = [s["n_shared"] + s["n_disjoint"] for s in strat]
        wd = float(np.average([s["diff"] for s in strat], weights=w)) if strat else None
        res["stratified_summary"] = {"n_bins": len(strat), "bins_positive": len(pos),
                                     "weighted_diff": wd}
        h038 = bool(diff >= 0.01 and ci and ci[0] > 0)
        h039 = bool(len(strat) >= 4 and len(pos) >= math.ceil(0.8 * len(strat))
                    and wd is not None and wd >= 0.005)
    else:
        h038 = h039 = False
    res["decisions"] = {"H038_shared_target_more_unstable": h038, "H039_survives_separation_strata": h039}
    res["decisions"]["verdict"] = ("shared_target_associated_beyond_proximity" if h038 and h039 else
                                   "associated_but_explained_by_proximity" if h038 else
                                   "no_annotation_level_target_signal")
    res["limits"] = [
        "Annotation-level target sharing is NOT measured engagement, NOT a genetic-perturbation reference, and NOT a mechanism claim.",
        "Interaction types are pooled; inhibitor vs agonist is not distinguished, so two drugs sharing a gene may act oppositely.",
        "Pairs are counted as annotated only if BOTH compounds have a gene annotation; that is a selected subset (297 of 659).",
        "Exploratory: plates were used as scoring endpoints earlier and cross-cell comparisons cross days.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r18/PROTOCOL_E018.md",
                "research/2026-10-27-agent-cell-identifiability-r18/e018_target_sharing.py",
                str(CSV.relative_to(ROOT)), str(MERGED.relative_to(ROOT)), str(DG.relative_to(ROOT))):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E018_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    d.to_csv(OUT / "E018_pairs.csv", index=False)

    a = res["audit"]
    print("pair units=%d annotated=%d shared=%d disjoint=%d layouts=%d" % (
        a["pair_units"], a["annotated_units"], a["shared_units"], a["disjoint_units"], a["layouts"]))
    if res["groups"]:
        g = res["groups"]
        print("shared   n=%d rev=%.4f sep=%.4f" % (g["shared"]["n"], g["shared"]["rev_rate"], g["shared"]["mean_sep"]))
        print("disjoint n=%d rev=%.4f sep=%.4f" % (g["disjoint"]["n"], g["disjoint"]["rev_rate"], g["disjoint"]["mean_sep"]))
        print("diff=%.4f CI=%s" % (g["diff_shared_minus_disjoint"], g["ci95_layout_clustered"]))
    print("stratified:", json.dumps(res.get("stratified_summary"), ensure_ascii=False))
    for s in res["stratified"]:
        print("   bin%d n=%d/%d rev_shared=%.4f rev_disjoint=%.4f diff=%+.4f sep=%.3f" % (
            s["bin"], s["n_shared"], s["n_disjoint"], s["rev_shared"], s["rev_disjoint"], s["diff"], s["sep_mid"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
