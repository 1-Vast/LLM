"""Phase 0 metadata-only qualification of assay edges for MAESTRO-FAR (PROPOSED thresholds: >=300 perturbations, >=8 MoA groups).

Reads treatment/cell metadata and L1000 sig_info only. No outcome matrix is opened. Writes EDGES.json.
Edge PRISM-L1000: compound key = first 13 chars of Broad id; cell key = normalised name. Structure identity unverified.
Edges JUMP and DepMap-features are only inventoried by directory presence/size.
"""
from __future__ import annotations
import json, re
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
EXT = HERE.parents[1] / "data" / "external"
norm = lambda s: re.sub(r"[^A-Z0-9]", "", str(s).upper())


def size(p):
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) if p.exists() else 0


def main():
    tr = pd.read_csv(EXT / "prism_19q4/raw/primary-screen-replicate-collapsed-treatment-info.csv", usecols=["broad_id", "moa", "name"])
    tr["cmp"] = tr.broad_id.astype(str).str[:13]
    sig = pd.read_csv(EXT / "lincs_l1000_gse92742/GSE92742_Broad_LINCS_sig_info.txt.gz", sep="\t", usecols=["pert_id", "pert_type", "cell_id"])
    sig = sig[sig.pert_type == "trt_cp"]
    cl = pd.read_csv(EXT / "prism_19q4/raw/primary-screen-cell-line-info.csv", usecols=["ccle_name", "primary_tissue"]).dropna(subset=["ccle_name"])
    pc = {norm(x.split("_")[0]): t for x, t in zip(cl.ccle_name, cl.primary_tissue)}
    sig = sig[sig.cell_id.map(norm).isin(pc)]
    both = set(tr.cmp) & set(sig.pert_id)
    t = tr[tr.cmp.isin(both)].drop_duplicates("cmp")
    moa = t.moa.fillna("").astype(str).str.split(",").explode().str.strip()
    moa = moa[moa != ""]
    lines = sig[sig.pert_id.isin(both)].drop_duplicates(["pert_id", "cell_id"]).groupby(sig.cell_id.map(norm)).size()
    big = lines[lines >= 300].index
    out = {"scope": "metadata only", "status": "OBSERVED (labels)",
           "prism_l1000": {"unique_overlap_compounds": len(both), "compounds_with_moa_label": int(t.moa.notna().sum()),
                           "distinct_moa_labels": int(moa.nunique()), "moa_labels_with_>=5_compounds": int((moa.value_counts() >= 5).sum()),
                           "lines_with_>=300_overlap_compounds": int(len(big)), "lines_>=300": {k: int(lines[k]) for k in big},
                           "tissues_among_lines_>=300": sorted({pc[k] for k in big if k in pc}),
                           "qualifies_on_proposed_counts": bool(len(both) >= 300 and moa.nunique() >= 8)},
           "jump": {"dir_bytes": size(EXT / "jump_target"), "usable": False, "reason": "data/external/jump_target is empty locally; no precomputed profiles"},
           "depmap_features": {"dir_bytes": size(EXT / "depmap_19q4"), "role": "features/dependency evidence for PRISM lines, not an outcome assay edge"},
           "caveats": ["counts qualify identity overlap only; endpoint (5-day viability vs 6/24 h transcription), dose and time mismatch remain",
                       "earlier blocks N/P/Q used this intersection and sealed GSE70138: any use is development, not confirmation"]}
    (HERE / "EDGES.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return out

if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
