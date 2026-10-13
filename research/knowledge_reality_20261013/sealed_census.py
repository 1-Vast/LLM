"""Metadata-only census of the sealed confirmation tier: PRISM Repurposing Public 24Q2 (REP.1M).

File summary
- Path: research/knowledge_reality_20261013/sealed_census.py
- Purpose: fix, before any 24Q2 response value is downloaded, which compounds and lines the
  confirmatory test may use, and the knowledge snapshot each compound gets.
- Core points:
  - Source: Figshare article 25917643 (CC BY 4.0, published 2024-05-31).
    - Only the metadata files are read: README, compound list, treatment and cell-line metadata.
      Their MD5s match Figshare's.
    - The response matrix (`Repurposing_Public_24Q2_Extended_Primary_Data_Matrix.csv`, 72.5 MB,
      MD5 042b15d3...) has not been downloaded. Downloading it needs the owner's authorisation.
  - Eligible compounds are REP.1M compounds absent from PRISM 19Q4 (primary or secondary) by
    Broad core, stripped name and InChIKey connectivity.
    - Each needs a structure in the Repurposing Hub sample file dated 2020-03-24, which predates
      the outcome release by four years.
    - REP.300 compounds are newer, are not in that snapshot, and are not eligible.
  - Knowledge snapshots per compound:
    - `hub2020`: targets and MoA from `repurposing_drugs_20200324.txt`. This is the primary,
      time-matched snapshot.
    - `mapkg2026`: MAP-KG edges matched by structure. It postdates the outcomes and is a
      sensitivity analysis only.
  - Lines:
    - `panel`: 24Q2 lines also in the 19Q4 panel and in CCLE 19Q4 expression. This is the primary
      stratum.
    - `new_context`: 24Q2 lines outside the 19Q4 panel with CCLE expression, reported separately.
  - Overlap: REP.1M compounds refused because they are in 19Q4 are listed with their 19Q4 cores
    in sealed_overlap.csv. Their two releases' profiles give the cross-batch replication ceiling.
- Output: SEALED_CENSUS.json, sealed_compounds.csv and sealed_overlap.csv in this folder.
"""
from __future__ import annotations

import hashlib
import re

import pandas as pd

from sources import (CCLE_EXPRESSION, HERE, HUB, PRISM_LINES, PRISM_SECONDARY_TREATMENTS, PRISM_TREATMENTS, ROOT,
                     connectivity, hub_relation, sha256, strip_name, write_json)

META = ROOT / "tmp/knowledge_reality_20261013/sealed_metadata"
HUB_SAMPLES = ROOT / "data/external/lincs_l1000_gse92742/repurposing_samples_20200324.txt"
FIGSHARE = {"article": 25917643, "licence": "CC BY 4.0", "published": "2024-05-31",
            "metadata_md5": {"README.txt": "bdc45ca3187df4dcf991ab9e26008558",
                             "Repurposing_Public_24Q2_Cell_Line_Meta_Data.csv": "da769165afe40ac83888bcc6dac0932a",
                             "Repurposing_Public_24Q2_Extended_Primary_Compound_List.csv": "cdb450d96507a290defeb455b0d616a4",
                             "Repurposing_Public_24Q2_Readme.txt": "4b630e332a4148e44aec3c1b0f6e4808",
                             "Repurposing_Public_24Q2_Treatment_Meta_Data.csv": "ab143170aa2134f13485670e26056d23"},
            "sealed_outcome_file": {"name": "Repurposing_Public_24Q2_Extended_Primary_Data_Matrix.csv", "file_id": 46630984,
                                    "bytes": 72456953, "md5": "042b15d3ebcc138a80a571b9286451ae",
                                    "url": "https://ndownloader.figshare.com/files/46630984"}}


def md5(path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as s:
        for b in iter(lambda: s.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> None:
    for name, digest in FIGSHARE["metadata_md5"].items():
        if md5(META / name) != digest:
            raise SystemExit(f"METADATA_DIGEST_MISMATCH: {name}")
    cl = pd.read_csv(META / "Repurposing_Public_24Q2_Extended_Primary_Compound_List.csv")
    cl["core"] = cl["IDs"].str.replace("BRD:", "", regex=False).str[:13]
    rep1m = cl[cl["screen"] == "REP.1M"]
    p19 = pd.concat([pd.read_csv(PRISM_TREATMENTS)[["broad_id", "name", "smiles"]],
                     pd.read_csv(PRISM_SECONDARY_TREATMENTS)[["broad_id", "name", "smiles"]]])
    p19["core"] = p19["broad_id"].str[:13]
    old_cores = set(p19["core"])
    old_names = set(p19["name"].map(strip_name))
    name_cores: dict = {}
    for c, n in zip(p19["core"], p19["name"].map(strip_name)):
        name_cores.setdefault(n, set()).add(c)
    conn_cores: dict = {}
    for c, s in zip(p19["core"], p19["smiles"]):
        k = connectivity(s) if isinstance(s, str) else None
        if k:
            conn_cores.setdefault(k, set()).add(c)
    old_conn = set(conn_cores)
    samples = pd.read_csv(HUB_SAMPLES, sep="\t", comment="!")
    samples["core"] = samples["broad_id"].str[:13]
    # Hub 2020 structures are CXSMILES; the stereo block after " |" contains commas, so strip it first.
    smiles = samples.dropna(subset=["smiles"]).groupby("core")["smiles"].first().map(lambda x: str(x).split(" |")[0].strip())
    hub = pd.read_csv(HUB, sep="\t", comment="!")
    hub_by_name = hub.assign(key=hub["pert_iname"].map(strip_name)).set_index("key")
    names_by_core = samples.groupby("core")["pert_iname"].first()

    rows, refused, overlap = [], {}, []
    for core, grp in rep1m.groupby("core"):
        name = str(grp["Drug.Name"].iloc[0])
        why = None
        if core in old_cores:
            why = "IN_19Q4_BY_CORE"
        elif strip_name(name) in old_names:
            why = "IN_19Q4_BY_NAME"
        elif core not in smiles.index:
            why = "NO_HUB2020_STRUCTURE"
        conn = connectivity(smiles[core]) if why is None else None
        if why is None and conn is None:
            why = "STRUCTURE_UNPARSABLE"
        if why is None and conn in old_conn:
            why = "IN_19Q4_BY_CONNECTIVITY"
        if why:
            refused[why] = refused.get(why, 0) + 1
            match = {"IN_19Q4_BY_CORE": {core}, "IN_19Q4_BY_NAME": name_cores.get(strip_name(name), set()),
                     "IN_19Q4_BY_CONNECTIVITY": conn_cores.get(conn, set())}.get(why)
            if match:
                overlap.append({"core": core, "name": name, "how": why, "cores_19q4": ";".join(sorted(match))})
            continue
        hub_name = strip_name(names_by_core.get(core, name))
        h = hub_by_name.loc[[hub_name]].iloc[0] if hub_name in hub_by_name.index else None
        targets = "" if h is None or pd.isna(h["target"]) else ", ".join(sorted(t.strip() for t in str(h["target"]).split("|")))
        moa = "" if h is None or pd.isna(h["moa"]) else ", ".join(sorted(m.strip() for m in str(h["moa"]).split("|")))
        rows.append({"core": core, "name": name, "smiles": smiles[core], "conn": conn, "hub2020_target": targets,
                     "hub2020_moa": moa, "hub2020_relation": hub_relation(moa),
                     "file24_target": "" if pd.isna(grp["repurposing_target"].iloc[0]) else grp["repurposing_target"].iloc[0],
                     "file24_moa": "" if pd.isna(grp["MOA"].iloc[0]) else grp["MOA"].iloc[0]})
    eligible = pd.DataFrame(rows)
    alias = eligible.groupby("conn")["core"].nunique()
    cm = pd.read_csv(META / "Repurposing_Public_24Q2_Cell_Line_Meta_Data.csv")
    lines24 = set(cm["depmap_id"])
    lines19 = set(pd.read_csv(PRISM_LINES)["depmap_id"])
    ccle = set(pd.read_csv(CCLE_EXPRESSION, usecols=[0]).iloc[:, 0])
    panel = sorted(lines24 & lines19 & ccle)
    new_context = sorted((lines24 - lines19) & ccle)
    eligible.to_csv(HERE / "sealed_compounds.csv", index=False, lineterminator="\n")
    pd.DataFrame(overlap).to_csv(HERE / "sealed_overlap.csv", index=False, lineterminator="\n")
    write_json(HERE / "SEALED_CENSUS.json", {
        "reads": "24Q2 metadata only; no 24Q2 response value has been downloaded",
        "figshare": FIGSHARE,
        "local_inputs": {"hub_drugs_20200324": sha256(HUB), "hub_samples_20200324": sha256(HUB_SAMPLES)},
        "rep1m_compounds": int(rep1m["core"].nunique()),
        "refused": refused,
        "overlap_with_19q4": len(overlap),
        "eligible_compounds": int(len(eligible)),
        "eligible_connectivity_groups": int(len(alias)),
        "eligible_with_hub2020_target": int((eligible["hub2020_target"] != "").sum()),
        "eligible_with_hub2020_moa": int((eligible["hub2020_moa"] != "").sum()),
        "annotation_agreement_2020_vs_2024_target": float((eligible["hub2020_target"].str.replace(" ", "") ==
                                                            eligible["file24_target"].astype(str).str.replace(" ", "")).mean()),
        "lines": {"24q2_total": len(lines24), "panel_with_ccle": len(panel), "new_context_with_ccle": len(new_context)},
        "panel_lines": panel, "new_context_lines": new_context,
    })
    print(len(eligible), refused, len(panel), len(new_context))


if __name__ == "__main__":
    main()
