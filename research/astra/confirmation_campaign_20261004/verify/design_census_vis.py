"""DESIGN-ONLY census of the Vis et al. 2024 pan-cancer anchored screen (no outcome column is parsed).

File summary
- Path: research/astra/confirmation_campaign_20261004/verify/design_census_vis.py
- Purpose: decide from identifier / plate / dose columns only whether the Vis et al. 2024 Cell Rep Med
  5:101687 screen (Europe PMC PMC11384948, Data S1 `pancan_combi_fitted_data_jan21.tsv.gz`) can give
  an untouched verification of Jaaks 2022 screen measurements (same line, same ordered combination,
  same anchor concentration, different plates / scans), and whether it has within-screen repeats or
  both orientations of a pair.
- Core points:
  - An explicit ALLOW list of design columns is parsed with pandas `usecols`; every other column of
    the release (all SYNERGY_*, LIBRARY_* fits, ANCHOR_VIABILITY*, DAY1_*, GROWTH_RATE,
    DOUBLING_TIME, scal, scale) is never parsed.
  - Jaaks design columns (exposed release) and the frozen builder's design-only S/V split
    (`jaaks.split_drugs`) map every overlapping ordered combination to the builder menu role.
- Interfaces: `python -m research.astra.confirmation_campaign_20261004.verify.design_census_vis`;
  writes verify/design_census_vis.json (refuses to overwrite).
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BUNDLE = ROOT / "data/external/vis2024_pancancer_combinations/PMC11384948_SupplementaryFiles.zip"
INNER = "data-code/SupplementalMaterials/pancan_combi_fitted_data_jan21.tsv.gz"
JAAKS = ROOT / "data/external/gdsc_combinations/jaaks2022_figshare/original_screen_all_tissues_fitted.csv"
OUT = HERE / "design_census_vis.json"
ALLOW = ["CELL_LINE_NAME", "CL", "maxc", "drug", "LIBRARY_ID", "BARCODE", "SCAN_ID", "DRUGSET_ID", "CL_SPEC",
         "time_stamp", "RESEARCH_PROJECT", "ANCHOR_ID", "ANCHOR_CONC", "LIBRARY_NAME", "ANCHOR_NAME", "COSMIC_ID",
         "SIDM", "tissue"]
FORBIDDEN = ("synergy", "xmid", "auc", "rmse", "emax", "viability", "day1", "growth", "doubling", "scal", "zscore")
JCOLS = ["BARCODE", "Tissue", "SIDM", "ANCHOR_ID", "ANCHOR_NAME", "ANCHOR_CONC", "LIBRARY_ID", "LIBRARY_NAME",
         "LIBRARY_CONC"]


def guard(cols):
    bad = [c for c in cols if any(h in c.lower() for h in FORBIDDEN)]
    if bad:
        raise SystemExit(f"FORBIDDEN_COLUMN: {bad}")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_vis() -> tuple[pd.DataFrame, dict]:
    guard(ALLOW)
    outer = zipfile.ZipFile(BUNDLE)
    inner_bytes = outer.read("mmc7.zip")
    inner = zipfile.ZipFile(io.BytesIO(inner_bytes))
    raw = inner.read(INNER)
    with gzip.open(io.BytesIO(raw), "rt", encoding="utf-8") as fh:
        header = fh.readline().rstrip("\n").split("\t")
    with gzip.open(io.BytesIO(raw), "rt", encoding="utf-8") as fh:
        v = pd.read_csv(fh, sep="\t", usecols=ALLOW, dtype=str, low_memory=False)
    for c in v.columns:
        v[c] = v[c].str.strip()
    meta = {"bundle_sha256": sha(BUNDLE), "inner_zip_sha256": hashlib.sha256(inner_bytes).hexdigest(),
            "fitted_tsv_gz_sha256": hashlib.sha256(raw).hexdigest(), "header": header, "columns_parsed": ALLOW,
            "columns_never_parsed": [c for c in header if c not in ALLOW]}
    return v, meta


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"REFUSE_OVERWRITE: {OUT}")
    import sys
    sys.path.insert(0, str(ROOT))
    from research.astra.feedback_validation_20261003 import jaaks as builder

    v, meta = load_vis()
    j = pd.read_csv(JAAKS, usecols=JCOLS, dtype=str, low_memory=False)
    for c in j.columns:
        j[c] = j[c].str.strip()
    r = {"rule": "DESIGN-ONLY: explicit allow list; no outcome column of the Vis release parsed", **meta}
    r["vis"] = {"rows": int(len(v)), "lines": int(v["SIDM"].nunique()), "tissues": int(v["tissue"].nunique()),
                "barcodes": int(v["BARCODE"].nunique()), "scan_ids": int(v["SCAN_ID"].nunique()),
                "research_projects": {k: int(x) for k, x in v["RESEARCH_PROJECT"].value_counts().items()},
                "anchors": int(v["ANCHOR_ID"].nunique()), "libraries": int(v["LIBRARY_ID"].nunique()),
                "ordered_combos": int(v.groupby(["ANCHOR_ID", "LIBRARY_ID"]).ngroups),
                "time_stamp_examples": sorted(v["time_stamp"].dropna().unique().tolist())[:5],
                "time_stamp_distinct": int(v["time_stamp"].nunique())}
    # orientation: both (A anchored, B library) and (B anchored, A library)?
    oc = v[["ANCHOR_ID", "LIBRARY_ID"]].drop_duplicates()
    rev = set(zip(oc["LIBRARY_ID"], oc["ANCHOR_ID"]))
    r["vis"]["ordered_combos_with_reverse_present"] = int(sum((a, b) in rev for a, b in zip(oc["ANCHOR_ID"], oc["LIBRARY_ID"])))
    # repeats within Vis per (line, ordered combo, anchor conc)
    per = v.groupby(["SIDM", "ANCHOR_ID", "LIBRARY_ID", "ANCHOR_CONC"]).agg(
        plates=("BARCODE", "nunique"), scans=("SCAN_ID", "nunique"), cl_batches=("CL", "nunique")).reset_index()
    r["vis"]["line_x_combo_x_conc"] = int(len(per))
    r["vis"]["plates_per_unit_quantiles"] = {q: float(per["plates"].quantile(q)) for q in (0.25, 0.5, 0.75, 0.9, 1.0)}
    r["vis"]["units_with_ge2_plates"] = int((per["plates"] >= 2).sum())
    r["vis"]["units_with_ge2_cl_batches"] = int((per["cl_batches"] >= 2).sum())
    perlc = v.groupby(["SIDM", "ANCHOR_ID", "LIBRARY_ID"])["BARCODE"].nunique()
    r["vis"]["line_x_ordered_combo"] = int(perlc.size)
    menu_per_line = perlc.groupby(level="SIDM").size()
    r["vis"]["combos_per_line_quantiles"] = {q: float(menu_per_line.quantile(q)) for q in (0, 0.25, 0.5, 0.75, 1.0)}

    # overlap with Jaaks (exposed): lines, ordered combos (same GDSC ids), anchor concentrations, barcodes
    jl = set(j["SIDM"])
    vl = set(v["SIDM"])
    jb = set(j["BARCODE"])
    vb = set(v["BARCODE"])
    jo = j.groupby(["SIDM", "ANCHOR_ID", "LIBRARY_ID"]).agg(conc=("ANCHOR_CONC", lambda s: set(s)),
                                                           plates=("BARCODE", lambda s: set(s)),
                                                           tissue=("Tissue", "first"))
    vo = v.groupby(["SIDM", "ANCHOR_ID", "LIBRARY_ID"]).agg(conc=("ANCHOR_CONC", lambda s: set(s)),
                                                           plates=("BARCODE", lambda s: set(s)),
                                                           cl=("CL", lambda s: set(s)), tissue=("tissue", "first"))
    both = jo.index.intersection(vo.index)
    rows = []
    for k in both:
        jc, vc = jo.loc[k, "conc"], vo.loc[k, "conc"]
        rows.append({"SIDM": k[0], "ANCHOR_ID": k[1], "LIBRARY_ID": k[2], "tissue": jo.loc[k, "tissue"],
                     "same_conc_any": bool(jc & vc), "same_conc_all": jc == vc,
                     "shared_plates": len(jo.loc[k, "plates"] & vo.loc[k, "plates"]),
                     "vis_plates": len(vo.loc[k, "plates"])})
    ov = pd.DataFrame(rows)
    # same unordered pair but opposite orientation in Jaaks
    jun = set((s, min(a, b), max(a, b)) for s, a, b in jo.index)
    vun = set((s, min(a, b), max(a, b)) for s, a, b in vo.index)
    r["overlap_with_jaaks"] = {
        "jaaks_lines": len(jl), "vis_lines": len(vl), "lines_in_both": len(jl & vl),
        "jaaks_barcodes": len(jb), "vis_barcodes": len(vb), "barcodes_in_both": len(jb & vb),
        "vis_barcode_range": [min(vb, key=lambda x: (len(x), x)), max(vb, key=lambda x: (len(x), x))],
        "jaaks_barcode_range": [min(jb, key=lambda x: (len(x), x)), max(jb, key=lambda x: (len(x), x))],
        "line_x_ordered_combo_in_both": int(len(ov)),
        "line_x_unordered_pair_in_both": int(len(jun & vun)),
        "same_anchor_conc_any": int(ov["same_conc_any"].sum()) if len(ov) else 0,
        "same_anchor_conc_all": int(ov["same_conc_all"].sum()) if len(ov) else 0,
        "with_shared_plates": int((ov["shared_plates"] > 0).sum()) if len(ov) else 0,
        "lines_with_overlap": int(ov["SIDM"].nunique()) if len(ov) else 0,
        "ordered_combos_with_overlap": int(ov.groupby(["ANCHOR_ID", "LIBRARY_ID"]).ngroups) if len(ov) else 0,
        "by_tissue": {k: int(x) for k, x in ov.groupby("tissue").size().items()} if len(ov) else {},
        "per_line_quantiles": ({q: float(ov.groupby("SIDM").size().quantile(q)) for q in (0, 0.25, 0.5, 0.75, 1.0)}
                               if len(ov) else {}),
    }
    # map to the frozen builder's S x V menu orientation (design-only split)
    design = builder._read(builder.RELEASE, builder.DESIGN_COLUMNS)
    role_rows = []
    for tissue, d in design.groupby("Tissue"):
        side = builder.split_drugs(tissue, d)
        sub = ov[ov["tissue"] == tissue] if len(ov) else ov
        for _, x in sub.iterrows():
            sa, sl = side.get(x["ANCHOR_ID"]), side.get(x["LIBRARY_ID"])
            if sa is None or sl is None or sa == sl:
                role = "not_in_SxV_menu"
            else:
                role = "SV_screen_orientation" if sa == "S" else "VS_screen_orientation"
            role_rows.append({"tissue": tissue, "SIDM": x["SIDM"], "role": role, "same_conc_all": x["same_conc_all"]})
    rr = pd.DataFrame(role_rows)
    if len(rr):
        r["overlap_with_jaaks"]["builder_menu_role"] = {k: int(x) for k, x in rr["role"].value_counts().items()}
        inmenu = rr[(rr["role"] != "not_in_SxV_menu") & rr["same_conc_all"]]
        r["overlap_with_jaaks"]["in_menu_same_conc_line_x_combo"] = int(len(inmenu))
        r["overlap_with_jaaks"]["in_menu_same_conc_lines"] = int(inmenu["SIDM"].nunique())
        r["overlap_with_jaaks"]["in_menu_same_conc_per_line_quantiles"] = (
            {q: float(inmenu.groupby("SIDM").size().quantile(q)) for q in (0, 0.25, 0.5, 0.75, 1.0)} if len(inmenu) else {})
        r["overlap_with_jaaks"]["in_menu_same_conc_by_tissue_lines"] = {
            k: int(x) for k, x in inmenu.groupby("tissue")["SIDM"].nunique().items()}
    with OUT.open("x", encoding="utf-8") as fh:
        json.dump(r, fh, indent=1, sort_keys=True, default=str)
    print(json.dumps({k: r[k] for k in ("vis", "overlap_with_jaaks")}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
