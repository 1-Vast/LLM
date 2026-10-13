"""Leakage audit of the development split and the knowledge snapshot (reads no response value).

File summary
- Path: research/knowledge_reality_20261013/leakage.py
- Purpose: state, with counts, how the development split and the knowledge edges could leak
  outcome information, and which of those risks the design removes.
- Checks:
  1. Structural aliases: no InChIKey connectivity block spans two folds.
  2. Name aliases: different structures with one stripped name, such as stereoisomers or salts
     recorded as different parents, across folds.
  3. Mechanism overlap: per fold, the share of annotated test compounds whose MoA string or T0
     target gene also occurs in training. This says how unseen the held-out families are.
  4. Provenance classifier: the most frequent relation texts per provenance class, for review,
     and the edges removed as outcome-proximal.
  5. Outcome-derived curated knowledge: Hub annotations known to come from cell-line
     sensitivity screens, found by keyword. A mechanical check cannot find all of them.
  6. Dates: the knowledge snapshot relative to the outcome release.
- Output: LEAKAGE.json in this folder.
"""
from __future__ import annotations

from collections import Counter

import numpy as np
import pandas as pd

from sources import CACHE, HERE, strip_name, write_json

# Annotations whose mechanism was established from cell-line sensitivity patterns (outcome-derived),
# as reported in the PRISM 2020 paper and earlier CTRP work. Keyword match on name, MoA or target.
OUTCOME_DERIVED_KEYWORDS = {
    "SLFN12": "velcrin PDE3A-SLFN12 killing, found from CTRP sensitivity",
    "DCAF15": "aryl sulfonamide degraders, mechanism resolved via sensitivity/resistance screens",
    "DNMDP": "velcrin found in a cell-line viability screen",
    "tepoxalin": "ABCB1-dependent killing reported from PRISM itself",
    "disulfiram": "MT1 / metallothionein-linked killing reported from PRISM itself",
    "vanadium": "SLC26A2-dependent killing reported from PRISM itself",
}


def main() -> None:
    comp = pd.read_csv(HERE / "compounds.csv")
    edges = pd.read_csv(CACHE / "edges.csv")
    info = pd.read_csv(HERE.parents[1] / "data/external/prism_19q4/raw/primary-screen-replicate-collapsed-treatment-info.csv")
    info["core"] = info["broad_id"].str[:13]
    names = info.groupby("core")["name"].first()
    moa = info.groupby("core")["moa"].apply(lambda s: {x.strip() for v in s.dropna() for x in str(v).split(",") if x.strip()})
    target = info.groupby("core")["target"].apply(lambda s: {x.strip() for v in s.dropna() for x in str(v).split(",") if x.strip()})

    folds_per_unit = comp.groupby("unit")["fold"].nunique()
    comp["sname"] = comp["core"].map(names).map(strip_name)
    name_folds = comp.groupby("sname").agg(units=("unit", "nunique"), folds=("fold", "nunique"))
    name_aliases = name_folds[(name_folds["units"] > 1) & (name_folds["folds"] > 1)]

    t0 = edges[edges["provenance"].isin(["curated_hub", "curated_mechanism", "binding_aggregate", "assay_biochemical"])]
    t0_genes = t0.groupby("core")["gene"].apply(set).to_dict()
    overlap = {}
    for f in range(5):
        test = comp[comp["fold"] == f]["core"]
        train = comp[comp["fold"] != f]["core"]
        train_moa = set().union(*[moa.get(c, set()) for c in train])
        train_genes = set().union(*[t0_genes.get(c, set()) for c in train])
        annotated = [c for c in test if t0_genes.get(c) or moa.get(c)]
        share_moa = np.mean([bool(moa.get(c, set()) & train_moa) for c in annotated])
        share_gene = np.mean([bool(t0_genes.get(c, set()) & train_genes) for c in annotated])
        share_any = np.mean([bool(moa.get(c, set()) & train_moa) or bool(t0_genes.get(c, set()) & train_genes) for c in annotated])
        overlap[str(f)] = {"annotated_test": len(annotated), "shares_moa_with_training": float(share_moa),
                           "shares_t0_gene_with_training": float(share_gene), "shares_either": float(share_any)}

    texts = {}
    for prov, grp in edges.groupby("provenance"):
        texts[prov] = [[t, int(n)] for t, n in Counter(grp["evidence"].astype(str)).most_common(8)]

    flagged = {}
    for core in comp["core"]:
        blob = " ".join([str(names.get(core, "")), " ".join(moa.get(core, set())), " ".join(target.get(core, set()))]).lower()
        for k, why in OUTCOME_DERIVED_KEYWORDS.items():
            if k.lower() in blob:
                flagged.setdefault(core, []).append(why)

    write_json(HERE / "LEAKAGE.json", {
        "reads": "metadata and knowledge only; no response value",
        "structural_alias_units_spanning_folds": int((folds_per_unit > 1).sum()),
        "name_alias_groups_spanning_folds": int(len(name_aliases)),
        "name_alias_examples": name_aliases.head(10).index.tolist(),
        "mechanism_overlap_with_training": overlap,
        "provenance_top_texts": texts,
        "outcome_derived_curated_flags": {"compounds": len(flagged), "examples": dict(list(flagged.items())[:12]),
                                          "note": "keyword screen only; most outcome-derived annotations cannot be found mechanically"},
        "dates": {"prism_19q4_release": "2019-12 (Figshare); paper Corsello et al. Nat Cancer 2020-02",
                  "hub_annotation_snapshot": "PRISM treatment-info columns ship with the 19Q4 release; the separate Hub file is dated 2020-03-24",
                  "mapkg_snapshot": "2026 (Feng et al., Nat Mach Intell 2026); postdates every outcome used here",
                  "consequence": "no per-edge date exists, so a time-matched control is impossible on 19Q4; the sealed 24Q2 "
                                 "design can contrast a knowledge snapshot that predates the outcome release with one that postdates it"},
        "removed": {"metabolic_relations": "substrate, reactant, cofactor and carrier edges are not target relations",
                    "outcome_proximal": "cell growth, proliferation, viability and death readouts (58 edges among PRISM compounds)",
                    "t1_only": "cell-based target engagement (969 edges) is used only in the labelled T1 sensitivity arm"},
    })
    print("structural aliases spanning folds:", int((folds_per_unit > 1).sum()), "name aliases spanning folds:", len(name_aliases))
    print(overlap)
    print("flagged:", len(flagged))


if __name__ == "__main__":
    main()
