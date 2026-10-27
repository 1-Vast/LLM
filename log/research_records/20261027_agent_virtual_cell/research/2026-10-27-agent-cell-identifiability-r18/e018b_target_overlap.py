"""E018b: target overlap and order reversal on the 315-pair random-combination plates.

Protocol: PROTOCOL_E018.md + AMENDMENT_009_UNIT_CORRECTION.md.
Unit = well pair (two 2-compound regimens) within a random-combination plate.
Reads PAIR_SCREEN.csv plus the two local MAPKG tables.
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
PAIRS_PER_CELLPAIR = 4000
N_BOOT = 1000
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def annotations():
    merged = pd.read_csv(MERGED, low_memory=False)
    merged["Drug Name"] = merged["Drug Name"].astype(str).str.strip()
    name2id = merged.drop_duplicates("Drug Name").set_index("Drug Name")["PubChem ID"].to_dict()
    dg = pd.read_csv(DG, low_memory=False)
    id2genes = {int(d): set(s["Gene ID"].astype(str)) for d, s in dg.groupby("Drug ID")}

    def g(name):
        pid = name2id.get(name)
        if pid is None or pd.isna(pid):
            return set()
        return id2genes.get(int(pid), set())
    return g


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    genes_of = annotations()

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
                       "qc": float(g["failed_qc"].mean()), "n_wells": len(g)}
    groups = {}
    for f, s in meta.items():
        groups.setdefault(s["h"], {}).setdefault(s["cell"], []).append(f)

    rng = np.random.default_rng(SEED)
    rows = []
    layouts_used = []
    for h, cells in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        it = 0
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 3:
            continue
        # random-combination design: many compound pairs, one well each
        # pick the reference file that carries the most usable non-anchor rows
        cand = [f for c in good for f in cells[c]]
        ref = max(cand, key=lambda f: int((ok["file"] == f).sum()))
        rg = ok[ok["file"] == ref]
        n_pairs = rg.groupby(["Drug 1", "Drug 2"]).ngroups
        if n_pairs < 100:          # only the 315-pair design
            continue
        units = sorted({(a, b) for a, b in zip(rg["Drug 1"], rg["Drug 2"])})
        genes = {(a, b): genes_of(a) | genes_of(b) for a, b in units}
        annotated = {u: bool(genes[u]) for u in units}
        surf = {}
        for c in good:
            vals = {}
            for f in cells[c]:
                s = ok[ok["file"] == f]
                for _, r in s.iterrows():
                    vals.setdefault((r["Drug 1"], r["Drug 2"]), []).append(r["y"])
            surf[c] = {u: float(np.mean(v)) for u, v in vals.items() if u in genes}
        cells_ok = [c for c in good if len(surf[c]) >= 100]
        if len(cells_ok) < 3:
            continue
        layouts_used.append("%s/%s" % (it, h[:12]))
        for a in range(len(cells_ok)):
            for b in range(a + 1, len(cells_ok)):
                ca, cb = cells_ok[a], cells_ok[b]
                common = [u for u in units if u in surf[ca] and u in surf[cb]]
                if len(common) < 100:
                    continue
                ya = np.array([surf[ca][u] for u in common])
                yb = np.array([surf[cb][u] for u in common])
                iu, ju = np.triu_indices(len(common), 1)
                if iu.size > PAIRS_PER_CELLPAIR:
                    sel = rng.choice(iu.size, PAIRS_PER_CELLPAIR, replace=False)
                    iu, ju = iu[sel], ju[sel]
                ga = np.abs(ya[iu] - ya[ju])
                gb = np.abs(yb[iu] - yb[ju])
                okk = (ga >= FLOOR) & (gb >= FLOOR) & np.isfinite(ga) & np.isfinite(gb)
                if okk.sum() < 100:
                    continue
                shared = np.array([bool(genes[common[i]] & genes[common[j]]) and annotated[common[i]]
                                   and annotated[common[j]] for i, j in zip(iu[okk], ju[okk])])
                bothann = np.array([annotated[common[i]] and annotated[common[j]] for i, j in zip(iu[okk], ju[okk])])
                rev = (np.sign(ya[iu] - ya[ju]) != np.sign(yb[iu] - yb[ju]))[okk]
                sep = np.minimum(ga, gb)[okk]
                for label, mask in (("shared", shared), ("disjoint", bothann & (~shared))):
                    if mask.sum() >= 20:
                        rows.append({"layout": "%s/%s" % (it, h[:12]), "group": label,
                                     "rev_rate": float(rev[mask].mean()),
                                     "mean_sep": float(sep[mask].mean()), "n": int(mask.sum())})
                rows.append({"layout": "%s/%s" % (it, h[:12]), "group": "all", "rev_rate": float(rev.mean()),
                             "mean_sep": float(sep.mean()), "n": int(okk.sum())})

    u = pd.DataFrame(rows)
    res = {"kind": "target_overlap_vs_reversal_on_random_combination_plates",
           "input_sha256": {"PAIR_SCREEN.csv": sha256(CSV), "MAPKG_merged": sha256(MERGED), "MAPKG_drug_gene": sha256(DG)},
           "settings": {"floor": FLOOR, "pairs_per_cellpair": PAIRS_PER_CELLPAIR, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"layouts_used": len(set(layouts_used)), "layouts": sorted(set(layouts_used)),
                     "comparison_rows": int(len(u))},
           "groups": {}, "files": {}}

    if len(u):
        agg = {}
        for g_, d_ in u.groupby("group"):
            w = d_["n"]
            agg[g_] = {"rows": int(len(d_)), "n": int(w.sum()),
                       "rev_rate": float(np.average(d_["rev_rate"], weights=w)),
                       "mean_sep": float(np.average(d_["mean_sep"], weights=w))}
        res["groups"] = agg
        # layout-clustered: per-layout shared-minus-disjoint
        per = []
        for lay, d_ in u.groupby("layout"):
            s_ = d_[d_["group"] == "shared"]
            dj = d_[d_["group"] == "disjoint"]
            if len(s_) and len(dj):
                per.append({"layout": lay,
                            "diff": float(np.average(s_["rev_rate"], weights=s_["n"])
                                          - np.average(dj["rev_rate"], weights=dj["n"])),
                            "shared_sep": float(np.average(s_["mean_sep"], weights=s_["n"])),
                            "disjoint_sep": float(np.average(dj["mean_sep"], weights=dj["n"]))})
        res["per_layout"] = per
        lays = [p["layout"] for p in per]
        rng2 = np.random.default_rng(SEED + 4)
        boots = []
        for _ in range(N_BOOT):
            pick = rng2.choice(lays, size=len(lays), replace=True) if lays else []
            vals = [next(p["diff"] for p in per if p["layout"] == q) for q in pick]
            if vals:
                boots.append(float(np.mean(vals)))
        diff = float(np.mean([p["diff"] for p in per])) if per else None
        ci = [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))] if boots else None
        res["shared_minus_disjoint"] = {"point": diff, "ci95": ci, "n_layouts": len(per),
                                        "per_layout_diffs": per}
        h038 = bool(diff is not None and diff >= 0.01 and ci and ci[0] > 0)
    else:
        h038 = False
    # separation confound check
    confound = None
    if len(u):
        s_ = res["groups"].get("shared", {})
        dj = res["groups"].get("disjoint", {})
        if s_ and dj:
            confound = s_["mean_sep"] - dj["mean_sep"]
    res["separation_confound"] = {"shared_minus_disjoint_mean_sep": confound}
    res["decisions"] = {"H038_prime_shared_target_more_unstable": h038,
                        "verdict": ("target_overlap_associated_with_instability" if h038
                                    else "no_annotation_level_target_signal_at_this_power")}
    res["limits"] = [
        "Annotation-level target overlap only; NOT measured engagement, NOT a genetic-perturbation reference, NOT a mechanism claim.",
        "Interaction types are pooled (inhibitor vs agonist not distinguished).",
        "Only two random-combination layouts qualify (three cells each), so the layout-clustered CI rests on two clusters and is fragile.",
        "Reversal here compares two 2-compound regimens, so target overlap is a set overlap, not a two-drug pair.",
        "Exploratory: plates were used as scoring endpoints earlier and cross-cell comparisons cross days.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r18/PROTOCOL_E018.md",
                "research/2026-10-27-agent-cell-identifiability-r18/AMENDMENT_009_UNIT_CORRECTION.md",
                "research/2026-10-27-agent-cell-identifiability-r18/e018b_target_overlap.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E018B_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(u):
        u.to_csv(OUT / "E018B_rows.csv", index=False)

    print("layouts used:", res["audit"]["layouts"])
    print(json.dumps(res["groups"], indent=1, ensure_ascii=False))
    print("shared-disjoint:", json.dumps(res.get("shared_minus_disjoint"), ensure_ascii=False)[:600])
    print("separation confound:", confound)
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
