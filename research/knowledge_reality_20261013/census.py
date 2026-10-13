"""Metadata-only census and leakage audit: compounds, knowledge edges, families and folds.

File summary
- Path: research/knowledge_reality_20261013/census.py
- Purpose: decide, before any response value is read, which compounds and edges are eligible, how
  compounds group into mechanism families, and which fold each family belongs to.
- Core points:
  - Universe: PRISM 19Q4 primary-screen compounds (Broad core) with a parsable structure.
  - Knowledge: PRISM's Hub columns plus MAP-KG edges matched by structure. Every edge is typed and
    provenance-classed (`sources.py`). Metabolic edges are dropped. Outcome-proximal edges (cell
    growth, proliferation, viability readouts) are counted and removed. Cell-based engagement
    edges are T1 and are kept only for a separately labelled sensitivity analysis.
  - Aliases: cores sharing an InChIKey connectivity block are one compound for splitting.
  - Mechanism families: connected components over shared T0 target genes (any provenance) or
    shared MoA strings. A compound's family therefore holds every compound it shares a target
    with, so a held-out family has no target gene in common with training.
    - The largest component is split by a fixed rule: its compounds are re-grouped by their
      first-listed Hub MoA string. Those test drugs may share a target gene with training;
      `strict_new_target` marks the ones that do not.
  - Folds: five, assigned by a salted hash of the family key.
  - The census also records the exposure history of each source and its licence and date.
- Output: CENSUS.json and census.npz (tmp copy of the edge table) in this folder.
"""
from __future__ import annotations

import hashlib
from collections import Counter

import numpy as np
import pandas as pd

from sources import (CACHE, EDGE_TIER, HERE, OUTCOME_PROXIMAL, PRISM_LFC, PRISM_TREATMENTS, MAPKG_EDGES, MAPKG_DRUGS,
                     HUB, CCLE_EXPRESSION, CCLE_MUTATIONS, connectivity, hub_edges, mapkg_edges, mapkg_identity,
                     sha256, write_json)
import sources

SALT = "knowledge-reality-20261013"
FOLDS = 5

EXPOSURE = {
    "prism_19q4_primary": "exposed: blocks N (421 sealed drugs, opened 2026-10-11), P (975, opened 2026-10-11), "
                          "selective hit triage (all compounds as input, 2026-10-13)",
    "prism_19q4_secondary": "exposed: blocks N/P secondary columns; triage bought 98 secondaries and read all in VC+S",
    "ctrp_v2": "exposed: triage development and test splits opened 2026-10-13",
    "gdsc2": "exposed: mono pretraining (2026-10-05) and GDSC transport (2026-10-02)",
    "lincs_l1000_gse92742_gse70138": "exposed: blocks N, P, Q (GSE70138 sealed tier opened 2026-10-12)",
    "ccle_19q4_expression_mutations": "basal cell state, not an outcome; used as context by triage",
    "repurposing_hub": "knowledge; used by blocks N, P, Q and triage",
    "mapkg_2026": "knowledge; used by block Q (signed edges in the RKT know route)",
}
LICENCES = {
    "prism_19q4": "CC BY 4.0 (DepMap / Figshare release, Dec 2019; Corsello et al., Nat Cancer 2020)",
    "ccle_19q4": "CC BY 4.0 (DepMap 19Q4)",
    "repurposing_hub": "Broad Drug Repurposing Hub: non-commercial use only (file header); file dated 2020-03-24 (after the PRISM 19Q4 release)",
    "mapkg_2026": "research release of Feng et al., Nat Mach Intell 2026; aggregates 14 sources whose own terms "
                  "apply (DrugBank-derived content is CC BY-NC 4.0, ChEMBL CC BY-SA 3.0); research use only",
    "ctrp_v2": "public NCI CTD2 data portal; no stated restriction",
    "gdsc": "Sanger GDSC terms: free for academic research",
}


def families(cores: list[str], targets: dict, moas: dict) -> dict:
    parent = {c: c for c in cores}

    def find(c):
        while parent[c] != c:
            parent[c] = parent[parent[c]]
            c = parent[c]
        return c

    owner: dict = {}
    for c in cores:
        for token in ["T:" + t for t in sorted(targets.get(c, ()))] + ["M:" + m for m in sorted(moas.get(c, ()))]:
            if token in owner:
                a, b = find(c), find(owner[token])
                if a != b:
                    parent[a] = b
            else:
                owner[token] = c
    return {c: find(c) for c in cores}


def fold_of(key: str) -> int:
    return int(hashlib.sha256(f"{SALT}:{key}".encode()).hexdigest(), 16) % FOLDS


def main() -> None:
    lfc_header = pd.read_csv(PRISM_LFC, nrows=0).columns.tolist()[1:]
    info = pd.read_csv(PRISM_TREATMENTS)
    info = info[info["column_name"].isin(lfc_header)]
    info["core"] = info["broad_id"].str[:13]
    first = info.sort_values(["core", "screen_id"]).groupby("core").first()
    compounds = pd.DataFrame({
        "name": first["name"], "smiles": first["smiles"],
        "moa": info.groupby("core")["moa"].apply(lambda s: ", ".join(sorted({x.strip() for v in s.dropna() for x in str(v).split(",") if x.strip()}))),
        "target": info.groupby("core")["target"].apply(lambda s: ", ".join(sorted({x.strip() for v in s.dropna() for x in str(v).split(",") if x.strip()}))),
    })
    compounds["conn"] = [connectivity(s) if isinstance(s, str) else None for s in compounds["smiles"]]
    parsable = compounds["conn"].notna()

    mapping, how = mapkg_identity(compounds[parsable])
    hub = hub_edges(compounds)
    mk = mapkg_edges(mapping)
    edges = pd.concat([hub, mk], ignore_index=True)
    edges["tier"] = edges["provenance"].map(EDGE_TIER).fillna("none")
    removed_metabolic = int((edges["relation"] == "metabolic").sum())
    removed_outcome = int(edges["provenance"].isin(OUTCOME_PROXIMAL).sum())
    kept = edges[(edges["relation"] != "metabolic") & ~edges["provenance"].isin(OUTCOME_PROXIMAL)]
    kept = kept.drop_duplicates(["core", "gene", "relation", "provenance"])

    expr_genes = {c.split(" (")[0] for c in pd.read_csv(CCLE_EXPRESSION, nrows=0).columns[1:]}
    t0 = kept[kept["tier"] == "T0"]
    t0_targets = t0.groupby("core")["gene"].apply(set).to_dict()
    moas = {c: {m.strip() for m in str(v).split(",") if m.strip()} for c, v in compounds["moa"].items() if str(v).strip()}

    # Aliases: cores sharing a connectivity block are one compound for splitting.
    alias = {k: sorted(v) for k, v in compounds[parsable].groupby("conn").groups.items()}
    alias_groups = {k: v for k, v in alias.items() if len(v) > 1}
    cores = sorted(compounds.index[parsable])
    unit = {c: compounds.at[c, "conn"] for c in cores}
    unit_targets: dict = {}
    unit_moas: dict = {}
    for c in cores:
        unit_targets.setdefault(unit[c], set()).update(t0_targets.get(c, ()))
        unit_moas.setdefault(unit[c], set()).update(moas.get(c, ()))
    units = sorted(set(unit.values()))
    fam = families(units, unit_targets, unit_moas)
    sizes = Counter(fam.values())
    giant = max(sizes, key=sizes.get)
    family = {}
    for u in units:
        if fam[u] == giant:
            key = sorted(unit_moas[u])[0] if unit_moas.get(u) else "T:" + sorted(unit_targets[u])[0]
            family[u] = f"G:{key}"
        else:
            family[u] = f"F:{fam[u]}"
    fold = {u: fold_of(family[u]) for u in units}

    # A drug is strict-new-target when none of its T0 targets is held by a compound in another fold.
    gene_folds: dict = {}
    for u in units:
        for g in unit_targets.get(u, ()):
            gene_folds.setdefault(g, set()).add(fold[u])
    strict = {u: all(gene_folds[g] == {fold[u]} for g in unit_targets.get(u, ())) for u in units}

    rows = []
    for c in cores:
        u = unit[c]
        rows.append({"core": c, "unit": u, "family": family[u], "fold": fold[u], "strict_new_target": bool(strict[u]),
                     "n_t0_targets": len(t0_targets.get(c, ())),
                     "n_t0_targets_in_ccle": len(t0_targets.get(c, set()) & expr_genes),
                     "mapkg_matched": c in mapping})
    table = pd.DataFrame(rows)

    by_prov = kept.groupby("provenance").agg(edges=("gene", "size"), compounds=("core", "nunique"), genes=("gene", "nunique"))
    by_rel = kept.groupby(["provenance", "relation"]).size().unstack(fill_value=0)
    coverage = {
        "compounds_total": int(len(compounds)), "compounds_parsable": int(parsable.sum()),
        "compound_units": len(units), "alias_groups": len(alias_groups),
        "mapkg_match": how,
        "with_t0_target": int((table["n_t0_targets"] > 0).sum()),
        "with_t0_target_in_ccle": int((table["n_t0_targets_in_ccle"] > 0).sum()),
        "with_hub_target": int(hub["core"].nunique()),
        "with_curated_only": int(table["core"].isin(t0[t0["provenance"].isin(["curated_hub", "curated_mechanism"])]["core"]).sum()),
        "with_cell_engagement_t1": int(kept[kept["provenance"] == "assay_cell_engagement"]["core"].nunique()),
    }
    fams = Counter(family.values())
    census = {
        "study": "knowledge_reality_20261013",
        "reads": "metadata and knowledge only; no response value",
        "sources": {name: {"path": str(p.relative_to(sources.ROOT)).replace("\\", "/"), "sha256": sha256(p)}
                    for name, p in {"prism_lfc_header_file": PRISM_LFC, "prism_treatments": PRISM_TREATMENTS,
                                    "mapkg_edges": MAPKG_EDGES, "mapkg_drugs": MAPKG_DRUGS, "hub": HUB,
                                    "ccle_expression": CCLE_EXPRESSION, "ccle_mutations": CCLE_MUTATIONS}.items()},
        "exposure": EXPOSURE, "licences": LICENCES,
        "edges": {
            "raw": int(len(edges)), "removed_metabolic": removed_metabolic,
            "removed_outcome_proximal": removed_outcome, "kept": int(len(kept)),
            "by_provenance": {k: {kk: int(vv) for kk, vv in v.items()} for k, v in by_prov.to_dict("index").items()},
            "by_provenance_relation": {k: {kk: int(vv) for kk, vv in v.items()} for k, v in by_rel.to_dict("index").items()},
            "tier": {k: int(v) for k, v in kept["tier"].value_counts().items()},
        },
        "coverage": coverage,
        "families": {"count": len(fams), "giant_component_units": int(sizes[giant]),
                     "giant_split_into": sum(1 for f in fams if f.startswith("G:")),
                     "largest": [[f, n] for f, n in fams.most_common(8)],
                     "singletons": sum(1 for n in fams.values() if n == 1)},
        "folds": {str(k): {"units": int((table.groupby("unit")["fold"].first() == k).sum()),
                           "with_t0_target": int(((table["fold"] == k) & (table["n_t0_targets"] > 0)).sum()),
                           "strict_new_target_with_target": int(((table["fold"] == k) & table["strict_new_target"] & (table["n_t0_targets"] > 0)).sum())}
                  for k in range(FOLDS)},
        "salt": SALT,
    }
    write_json(HERE / "CENSUS.json", census)
    CACHE.mkdir(parents=True, exist_ok=True)
    kept.to_csv(CACHE / "edges.csv", index=False, lineterminator="\n")
    table.to_csv(HERE / "compounds.csv", index=False, lineterminator="\n")
    print(json_summary(census))


def json_summary(c: dict) -> str:
    import json
    return json.dumps({k: c[k] for k in ("edges", "coverage", "families", "folds")}, indent=1)


if __name__ == "__main__":
    main()
