"""E019: retest the target-overlap effect on all high-diversity layouts that have >=2
QC-passing cells, and add a gene-label permutation null.

Pre-registered in PROTOCOL_E019.md. Reads PAIR_SCREEN.csv plus the two local MAPKG tables.

Per layout: units = compound pairs (one well each); adjacency A[i,j] = gene sets overlap.
For each cell pair, sampled well pairs give a reversal vector and a min-gap vector.
Observed diff = mean reversal(shared) - mean reversal(disjoint annotated).
Permutation null: shuffle the compound -> gene-set mapping inside the layout (permuting
rows/cols of A), keeping set sizes and empty positions, then recompute the diff.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r19"
ANCHORS = {"high control", "low control"}
FLOOR = 0.10
PAIRS_PER_CELLPAIR = 4000
N_PERM = 500
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
            return frozenset()
        return frozenset(id2genes.get(int(pid), set()))
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
                       "qc": float(g["failed_qc"].mean()), "nrows": len(g)}
    groups = {}
    for f, s in meta.items():
        groups.setdefault(s["h"], {}).setdefault(s["cell"], []).append(f)

    rng = np.random.default_rng(SEED)
    per_layout = []
    used_cells = {}
    for h, cells in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 2:
            continue
        ref = max((f for c in good for f in cells[c]), key=lambda f: int((ok["file"] == f).sum()))
        rg = ok[ok["file"] == ref]
        if rg.groupby(["Drug 1", "Drug 2"]).ngroups < 100:
            continue
        units = sorted({(a, b) for a, b in zip(rg["Drug 1"], rg["Drug 2"])})
        idx = {u: k for k, u in enumerate(units)}
        gsets = [genes_of(a) | genes_of(b) for a, b in units]
        annotated = np.array([len(s) > 0 for s in gsets])
        n = len(units)
        A = np.zeros((n, n), dtype=bool)
        for i in range(n):
            if not annotated[i]:
                continue
            gi = gsets[i]
            for j in range(i + 1, n):
                if annotated[j] and (gi & gsets[j]):
                    A[i, j] = A[j, i] = True
        # per-cell values
        surf = {}
        for c in good:
            vals = {}
            for f in cells[c]:
                s = ok[ok["file"] == f]
                for _, r in s.iterrows():
                    u = (r["Drug 1"], r["Drug 2"])
                    if u in idx:
                        vals.setdefault(u, []).append(r["y"])
            surf[c] = {u: float(np.mean(v)) for u, v in vals.items() if len(v)}
        cells_ok = [c for c in good if len(surf[c]) >= 100]
        if len(cells_ok) < 2:
            continue
        rev_all, shar_all, ann_all, sep_all, I_all_l, J_all_l = [], [], [], [], [], []
        for a in range(len(cells_ok)):
            for b in range(a + 1, len(cells_ok)):
                common = [u for u in units if u in surf[cells_ok[a]] and u in surf[cells_ok[b]]]
                if len(common) < 100:
                    continue
                ia = np.array([idx[u] for u in common])
                ya = np.array([surf[cells_ok[a]][u] for u in common])
                yb = np.array([surf[cells_ok[b]][u] for u in common])
                iu, ju = np.triu_indices(len(common), 1)
                if iu.size > PAIRS_PER_CELLPAIR:
                    s_ = rng.choice(iu.size, PAIRS_PER_CELLPAIR, replace=False)
                    iu, ju = iu[s_], ju[s_]
                ga = np.abs(ya[iu] - ya[ju])
                gb = np.abs(yb[iu] - yb[ju])
                okk = (ga >= FLOOR) & (gb >= FLOOR)
                if okk.sum() < 100:
                    continue
                I = ia[iu[okk]]
                J = ia[ju[okk]]
                rev = (np.sign(ya[iu] - ya[ju]) != np.sign(yb[iu] - yb[ju]))[okk]
                sep = np.minimum(ga, gb)[okk]
                ann = annotated[I] & annotated[J]
                rev_all.append(rev)
                shar_all.append(A[I, J])
                ann_all.append(ann)
                sep_all.append(sep)
                I_all_l.append(I)
                J_all_l.append(J)
        if not rev_all:
            continue
        rev = np.concatenate(rev_all)
        shar = np.concatenate(shar_all)
        ann = np.concatenate(ann_all)
        sep = np.concatenate(sep_all)
        I_all = np.concatenate(I_all_l)
        J_all = np.concatenate(J_all_l)
        m_s = shar
        m_d = ann & (~shar)
        if m_s.sum() < 50 or m_d.sum() < 50:
            continue
        obs = float(rev[m_s].mean() - rev[m_d].mean())
        per_layout.append({"layout": h[:12], "n_cells": len(cells_ok), "obs_diff": obs,
                           "rev_shared": float(rev[m_s].mean()), "rev_disjoint": float(rev[m_d].mean()),
                           "n_shared": int(m_s.sum()), "n_disjoint": int(m_d.sum()),
                           "sep_shared": float(sep[m_s].mean()), "sep_disjoint": float(sep[m_d].mean()),
                           "state": {"rev": rev, "shar": shar, "ann": ann, "sep": sep, "A": A,
                                     "annotated": annotated, "I": I_all, "J": J_all}})
        used_cells[h[:12]] = cells_ok

    # ---- permutation null: shuffle compound -> gene-set mapping within each layout ----
    perm_diffs = []
    rng2 = np.random.default_rng(SEED + 1)
    for _ in range(N_PERM):
        vals = []
        for L in per_layout:
            st = L["state"]
            A, ann, I, J, rev = st["A"], st["annotated"], st["I"], st["J"], st["rev"]
            idxs = np.where(ann)[0]
            perm = idxs.copy()
            rng2.shuffle(perm)
            Ap = np.zeros_like(A)
            Ap[np.ix_(idxs, idxs)] = A[np.ix_(perm, perm)]
            shar_p = Ap[I, J]
            both = ann[I] & ann[J]
            m_s = shar_p & both
            m_d = both & (~shar_p)
            if m_s.sum() < 50 or m_d.sum() < 50:
                continue
            vals.append(float(rev[m_s].mean() - rev[m_d].mean()))
        if vals:
            perm_diffs.append(float(np.mean(vals)))

    res = {"kind": "target_overlap_effect_21_layouts_with_permutation_null",
           "input_sha256": {"PAIR_SCREEN.csv": sha256(CSV), "MAPKG_merged": sha256(MERGED), "MAPKG_drug_gene": sha256(DG)},
           "settings": {"floor": FLOOR, "pairs_per_cellpair": PAIRS_PER_CELLPAIR, "n_perm": N_PERM,
                        "n_boot": N_BOOT, "seed": SEED},
           "audit": {"layouts_used": len(per_layout),
                     "layouts_with_3_cells": sum(1 for L in per_layout if L["n_cells"] >= 3),
                     "layouts_with_2_cells": sum(1 for L in per_layout if L["n_cells"] == 2),
                     "cells_per_layout": used_cells},
           "per_layout": [{k: v for k, v in L.items() if k != "state"} for L in per_layout],
           "files": {}}

    if per_layout:
        obs = float(np.mean([L["obs_diff"] for L in per_layout]))
        diffs = [L["obs_diff"] for L in per_layout]
        rng3 = np.random.default_rng(SEED + 2)
        boots = []
        for _ in range(N_BOOT):
            pick = rng3.choice(len(diffs), size=len(diffs), replace=True)
            boots.append(float(np.mean([diffs[i] for i in pick])))
        ci = [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]
        res["observed"] = {"mean_diff": obs, "ci95_layout_bootstrap": ci,
                           "n_layouts": len(diffs),
                           "frac_layouts_positive": float(np.mean([d > 0 for d in diffs])),
                           "rev_shared_pooled": float(np.average([L["rev_shared"] for L in per_layout],
                                                                 weights=[L["n_shared"] for L in per_layout])),
                           "rev_disjoint_pooled": float(np.average([L["rev_disjoint"] for L in per_layout],
                                                                   weights=[L["n_disjoint"] for L in per_layout])),
                           "sep_diff_pooled": float(np.average([L["sep_shared"] - L["sep_disjoint"] for L in per_layout],
                                                               weights=[L["n_shared"] + L["n_disjoint"] for L in per_layout]))}
    # ---- decisions ----
    if per_layout:
        obs_mean = res["observed"]["mean_diff"]
        ci = res["observed"]["ci95_layout_bootstrap"]
        res["permutation_null"] = {
            "n_perm": len(perm_diffs),
            "mean": float(np.mean(perm_diffs)) if perm_diffs else None,
            "q025": float(np.quantile(perm_diffs, 0.025)) if perm_diffs else None,
            "q975": float(np.quantile(perm_diffs, 0.975)) if perm_diffs else None,
            "p_one_sided": float((np.sum(np.array(perm_diffs) >= obs_mean) + 1) / (len(perm_diffs) + 1)) if perm_diffs else None,
        }
        h040 = bool(obs_mean >= 0.01 and ci[0] > 0)
        h041 = bool(res["permutation_null"]["q975"] is not None and obs_mean > res["permutation_null"]["q975"])
        h042 = bool(res["observed"]["frac_layouts_positive"] >= 0.70)
    else:
        h040 = h041 = h042 = False
    res["decisions"] = {"H040_effect_holds_over_21_layouts": h040, "H041_beats_gene_label_permutation": h041,
                        "H042_direction_consistent": h042}
    res["decisions"]["verdict"] = (
        "target_overlap_effect_survives_permutation" if h040 and h041 else
        "effect_present_but_indistinguishable_from_annotation_permutation" if h040 else
        "effect_does_not_hold_at_21_layouts")
    res["limits"] = [
        "Annotation-level overlap only; NOT engagement, NOT genetic perturbation, NOT mechanism.",
        "Two-cell layouts contribute a single cell pair each, so their reversal estimates are noisier; per-layout values are reported.",
        "Interaction types are pooled; shared genes may be acted on in opposite directions.",
        "Exploratory: plates were used as scoring endpoints earlier and cross-cell comparisons cross days.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r19/PROTOCOL_E019.md",
                "research/2026-10-27-agent-cell-identifiability-r19/e019_retest.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E019_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    print("layouts used=%d (3-cell=%d, 2-cell=%d)" % (len(per_layout),
                                                      sum(1 for L in per_layout if L["n_cells"] >= 3),
                                                      sum(1 for L in per_layout if L["n_cells"] == 2)))
    if per_layout:
        o = res["observed"]
        print("pooled rev shared=%.4f disjoint=%.4f | mean per-layout diff=%+.4f CI=%s | frac layouts positive=%.2f | sep diff=%+.4f" % (
            o["rev_shared_pooled"], o["rev_disjoint_pooled"], o["mean_diff"],
            ["%.4f" % x for x in o["ci95_layout_bootstrap"]], o["frac_layouts_positive"], o["sep_diff_pooled"]))
        for L in per_layout[:8]:
            print("   %-13s cells=%d obs=%+.4f n_shared=%d n_disjoint=%d" % (
                L["layout"], L["n_cells"], L["obs_diff"], L["n_shared"], L["n_disjoint"]))


if __name__ == "__main__":
    main()
