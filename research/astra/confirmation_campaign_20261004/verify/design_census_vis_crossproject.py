"""DESIGN-ONLY census: ordered combinations measured in two research projects of the Vis 2024 screen.

File summary
- Path: research/astra/confirmation_campaign_20261004/verify/design_census_vis_crossproject.py
- Purpose: the repeat census showed that drug sets of different projects (GDSC_002, _004, _005) share
  ordered combinations, so most lines measure some combinations twice, on plates of two different
  projects (different drug-set layout and screening run). Count, from design columns only, the
  shared combinations, their project pairs, per-line completeness, anchor/library concentration
  identity, cell-line batch (CL) identity and barcode distance between the two measurements, and
  overlap of these lines/combinations with the exposed Jaaks 2022 release.
- Interfaces: `python -m research.astra.confirmation_campaign_20261004.verify.design_census_vis_crossproject`;
  writes verify/design_census_vis_crossproject.json (refuses to overwrite).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from research.astra.confirmation_campaign_20261004.verify.design_census_vis import JAAKS, JCOLS, load_vis

HERE = Path(__file__).resolve().parent
OUT = HERE / "design_census_vis_crossproject.json"


def q(s) -> dict:
    s = pd.Series(s)
    return {str(k): float(s.quantile(k)) for k in (0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0)} if len(s) else {}


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"REFUSE_OVERWRITE: {OUT}")
    v, meta = load_vis()
    v["project"] = v["RESEARCH_PROJECT"].str[:-2]
    v["bc"] = pd.to_numeric(v["BARCODE"], errors="coerce")
    r = {"rule": "DESIGN-ONLY (explicit allow list; see design_census_vis.py)",
         "fitted_tsv_gz_sha256": meta["fitted_tsv_gz_sha256"]}
    combo_proj = v.groupby(["ANCHOR_ID", "LIBRARY_ID"])["project"].agg(lambda s: tuple(sorted(set(s))))
    shared = combo_proj[combo_proj.map(len) >= 2]
    r["ordered_combos"] = int(len(combo_proj))
    r["ordered_combos_in_ge2_projects"] = int(len(shared))
    r["shared_combo_project_sets"] = {"|".join(k): int(x) for k, x in shared.value_counts().items()}
    names = v.drop_duplicates(["ANCHOR_ID", "LIBRARY_ID"]).set_index(["ANCHOR_ID", "LIBRARY_ID"])[["ANCHOR_NAME", "LIBRARY_NAME"]]
    r["shared_combos"] = [[a, b, names.loc[(a, b), "ANCHOR_NAME"], names.loc[(a, b), "LIBRARY_NAME"], list(p)]
                          for (a, b), p in shared.items()]
    s = v[v.set_index(["ANCHOR_ID", "LIBRARY_ID"]).index.isin(shared.index)]
    # per line x shared combo x project: plates, CL batches, anchor concs
    g = s.groupby(["SIDM", "ANCHOR_ID", "LIBRARY_ID", "project"]).agg(
        plates=("BARCODE", lambda x: tuple(sorted(set(x)))), cl=("CL", lambda x: tuple(sorted(set(x)))),
        conc=("ANCHOR_CONC", lambda x: tuple(sorted(set(x)))), maxc=("maxc", lambda x: tuple(sorted(set(x)))),
        tissue=("tissue", "first")).reset_index()
    per = g.groupby(["SIDM", "ANCHOR_ID", "LIBRARY_ID"]).agg(
        n_proj=("project", "nunique"), cls=("cl", lambda x: [c for t in x for c in t]),
        cl_sets=("cl", list), concs=("conc", list), maxcs=("maxc", list), plates=("plates", list),
        tissue=("tissue", "first")).reset_index()
    two = per[per["n_proj"] >= 2].copy()
    two["same_anchor_concs"] = two["concs"].map(lambda c: all(x == c[0] for x in c))
    two["same_maxc"] = two["maxcs"].map(lambda c: all(x == c[0] for x in c))
    two["disjoint_cl"] = two["cl_sets"].map(lambda c: len(set(c[0]) & set(c[1])) == 0)
    two["shared_cl"] = ~two["disjoint_cl"]
    two["min_bc_gap"] = two["plates"].map(lambda p: float(min(abs(int(a) - int(b)) for a in p[0] for b in p[1])))
    r["line_x_shared_combo_measured_in_2_projects"] = int(len(two))
    r["of_which_same_anchor_concs"] = int(two["same_anchor_concs"].sum())
    r["of_which_same_library_maxc"] = int(two["same_maxc"].sum())
    r["of_which_disjoint_cl_batches"] = int(two["disjoint_cl"].sum())
    r["cross_project_min_barcode_gap_quantiles"] = q(two["min_bc_gap"])
    menu_shared = len(shared)
    perline = two[two["same_anchor_concs"] & two["same_maxc"]].groupby("SIDM").agg(
        n=("ANCHOR_ID", "size"), disjoint=("disjoint_cl", "sum"), tissue=("tissue", "first"))
    r["lines_with_any"] = int(len(perline))
    r["shared_combos_per_line_quantiles"] = q(perline["n"])
    r["lines_with_complete_shared_menu"] = int((perline["n"] == menu_shared).sum())
    r["lines_with_ge15_of_shared_menu"] = int((perline["n"] >= 15).sum())
    r["lines_with_complete_shared_menu_and_disjoint_cl"] = int(((perline["n"] == menu_shared)
                                                                  & (perline["disjoint"] == perline["n"])).sum())
    comp = perline[perline["n"] == menu_shared]
    r["complete_shared_menu_lines_by_tissue"] = {k: int(x) for k, x in comp["tissue"].value_counts().items()}
    r["complete_shared_menu_tissues_with_ge10_lines"] = int((comp["tissue"].value_counts() >= 10).sum())
    # how many measurements per (line, combo, project): replicate plates inside a project
    r["plates_per_line_combo_project_quantiles"] = q(g["plates"].map(len))
    # overlap with Jaaks lines and ordered combinations (exposed release, design columns)
    j = pd.read_csv(JAAKS, usecols=JCOLS, dtype=str, low_memory=False)
    for c in j.columns:
        j[c] = j[c].str.strip()
    jkeys = set(zip(j["SIDM"], j["ANCHOR_ID"], j["LIBRARY_ID"]))
    two["in_jaaks"] = [k in jkeys for k in zip(two["SIDM"], two["ANCHOR_ID"], two["LIBRARY_ID"])]
    r["line_x_shared_combo_also_in_jaaks"] = int(two["in_jaaks"].sum())
    r["lines_also_in_jaaks"] = int(len(set(perline.index) & set(j["SIDM"])))
    with OUT.open("x", encoding="utf-8") as fh:
        json.dump(r, fh, indent=1, sort_keys=True, default=str)
    print(json.dumps(r, indent=1, default=str)[:8000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
