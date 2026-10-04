"""DESIGN-ONLY census of within-screen repeats in the Vis et al. 2024 anchored screen (no outcome parsed).

File summary
- Path: research/astra/confirmation_campaign_20261004/verify/design_census_vis_repeats.py
- Purpose: count, per line, drug set and ordered combination, the repeated plates of the Vis 2024
  pan-cancer anchored screen and how independent they are (different cell-line batch `CL`,
  research project arm A/B, barcode gap), to judge a complete smaller menu with an independent
  second measurement per candidate. Uses the same explicit allow list as design_census_vis.py.
- Interfaces: `python -m research.astra.confirmation_campaign_20261004.verify.design_census_vis_repeats`;
  writes verify/design_census_vis_repeats.json (refuses to overwrite).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from research.astra.confirmation_campaign_20261004.verify.design_census_vis import load_vis

HERE = Path(__file__).resolve().parent
OUT = HERE / "design_census_vis_repeats.json"


def q(s: pd.Series) -> dict:
    return {str(k): float(s.quantile(k)) for k in (0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0)} if len(s) else {}


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"REFUSE_OVERWRITE: {OUT}")
    v, meta = load_vis()
    v["arm"] = v["RESEARCH_PROJECT"].str[-1]
    v["project"] = v["RESEARCH_PROJECT"].str[:-2]
    v["bc"] = pd.to_numeric(v["BARCODE"], errors="coerce")
    r = {"rule": "DESIGN-ONLY (explicit allow list; see design_census_vis.py)", "fitted_tsv_gz_sha256": meta["fitted_tsv_gz_sha256"]}
    plates = v.drop_duplicates("BARCODE")[["BARCODE", "bc", "SIDM", "DRUGSET_ID", "CL", "RESEARCH_PROJECT", "arm",
                                          "project", "tissue"]]
    r["plates"] = int(len(plates))
    r["plates_per_project"] = {k: int(x) for k, x in plates["RESEARCH_PROJECT"].value_counts().items()}
    r["drugsets"] = {str(k): int(x) for k, x in plates["DRUGSET_ID"].value_counts().items()}
    combos_per_ds = v.groupby("DRUGSET_ID").apply(lambda d: d.groupby(["ANCHOR_ID", "LIBRARY_ID"]).ngroups)
    r["ordered_combos_per_drugset"] = {str(k): int(x) for k, x in combos_per_ds.items()}
    ds_project = plates.groupby("DRUGSET_ID")["RESEARCH_PROJECT"].agg(lambda s: sorted(set(s)))
    r["drugset_projects"] = {str(k): x for k, x in ds_project.items()}
    # per line x drug set: plates, CL batches, arms
    lds = plates.groupby(["SIDM", "DRUGSET_ID"]).agg(n=("BARCODE", "size"), cl=("CL", "nunique"),
                                                     arms=("arm", "nunique"), tissue=("tissue", "first"),
                                                     gap=("bc", lambda s: float(np.diff(np.sort(s)).min()) if len(s) > 1 else np.nan))
    r["line_x_drugset"] = int(len(lds))
    r["line_x_drugset_ge2_plates"] = int((lds["n"] >= 2).sum())
    r["line_x_drugset_ge2_cl_batches"] = int((lds["cl"] >= 2).sum())
    r["line_x_drugset_ge2_arms"] = int((lds["arms"] >= 2).sum())
    rep = lds[lds["n"] >= 2]
    r["repeat_min_barcode_gap_quantiles"] = q(rep["gap"].dropna())
    r["repeat_gap_eq1_share"] = float((rep["gap"] == 1).mean()) if len(rep) else None
    # per line: is EVERY drug set of the line repeated with a different CL batch (complete independent repeat)?
    per_line = lds.groupby("SIDM").agg(ds=("n", "size"), ds_rep=("n", lambda s: int((s >= 2).sum())),
                                       ds_rep_cl=("cl", lambda s: int((s >= 2).sum())), tissue=("tissue", "first"))
    full_rep = per_line[per_line["ds_rep"] == per_line["ds"]]
    full_rep_cl = per_line[per_line["ds_rep_cl"] == per_line["ds"]]
    r["lines"] = int(len(per_line))
    r["lines_all_drugsets_ge2_plates"] = int(len(full_rep))
    r["lines_all_drugsets_ge2_cl_batches"] = int(len(full_rep_cl))
    r["lines_ge1_drugset_ge2_cl_batches"] = int((per_line["ds_rep_cl"] >= 1).sum())
    r["lines_all_drugsets_ge2_cl_by_tissue"] = {k: int(x) for k, x in full_rep_cl.groupby("tissue").size().items()}
    # candidate-level: ordered combo x line with >= 2 plates from >= 2 CL batches at the same anchor conc
    u = v.groupby(["SIDM", "ANCHOR_ID", "LIBRARY_ID", "ANCHOR_CONC"]).agg(
        plates=("BARCODE", "nunique"), cl=("CL", "nunique"), maxc=("maxc", "nunique"),
        tissue=("tissue", "first")).reset_index()
    both_conc = u.groupby(["SIDM", "ANCHOR_ID", "LIBRARY_ID"]).agg(
        min_cl=("cl", "min"), min_plates=("plates", "min"), maxc_values=("maxc", "max"), tissue=("tissue", "first")).reset_index()
    r["line_x_combo"] = int(len(both_conc))
    r["line_x_combo_ge2_cl_at_every_conc"] = int((both_conc["min_cl"] >= 2).sum())
    r["line_x_combo_ge2_plates_at_every_conc"] = int((both_conc["min_plates"] >= 2).sum())
    r["line_x_combo_library_conc_changes_across_plates"] = int((both_conc["maxc_values"] > 1).sum())
    cand = both_conc[both_conc["min_cl"] >= 2]
    cpl = cand.groupby("SIDM").size()
    menu = both_conc.groupby("SIDM").size()
    r["independent_repeat_candidates_per_line"] = q(cpl)
    r["lines_with_ge10_independent_repeat_candidates"] = int((cpl >= 10).sum())
    r["lines_with_ge20_independent_repeat_candidates"] = int((cpl >= 20).sum())
    r["lines_with_complete_menu_independent_repeats"] = int(sum(int(cpl.get(s, 0)) == int(menu[s]) for s in menu.index))
    by_t = cand.groupby("tissue")["SIDM"].nunique().sort_values(ascending=False)
    r["lines_with_any_independent_repeat_by_tissue"] = {k: int(x) for k, x in by_t.items()}
    full = [s for s in menu.index if int(cpl.get(s, 0)) == int(menu[s])]
    tissue_of = both_conc.drop_duplicates("SIDM").set_index("SIDM")["tissue"]
    r["complete_menu_lines_by_tissue"] = {k: int(x) for k, x in pd.Series([tissue_of[s] for s in full]).value_counts().items()}
    # arm structure: do A and B arms hold the same drug sets?
    arm_ds = plates.groupby(["project", "arm"])["DRUGSET_ID"].agg(lambda s: sorted(set(s)))
    r["drugsets_by_project_arm"] = {f"{a}|{b}": x for (a, b), x in arm_ds.items()}
    lines_by_arm = plates.groupby(["project", "arm"])["SIDM"].nunique()
    r["lines_by_project_arm"] = {f"{a}|{b}": int(x) for (a, b), x in lines_by_arm.items()}
    with OUT.open("x", encoding="utf-8") as fh:
        json.dump(r, fh, indent=1, sort_keys=True, default=str)
    print(json.dumps(r, indent=1, default=str)[:7000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
