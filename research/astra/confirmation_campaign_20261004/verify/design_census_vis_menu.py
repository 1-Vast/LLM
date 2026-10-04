"""DESIGN-ONLY: the 19-combination cross-project menu of the Vis 2024 screen, per line and tissue.

File summary
- Path: research/astra/confirmation_campaign_20261004/verify/design_census_vis_menu.py
- Purpose: fix, from design columns only, the candidate menu for the proposed untouched evaluation
  (ordered combinations measured in both GDSC_002 and GDSC_005 drug sets at identical anchor and
  library concentrations), list it, and count per tissue the lines whose menu is complete, the lines
  whose two measurements come from disjoint cell-line batches (CL) for every candidate, and lines with
  replicate plates inside a project (reference/QC lines).
- Interfaces: `python -m research.astra.confirmation_campaign_20261004.verify.design_census_vis_menu`;
  writes verify/design_census_vis_menu.json (refuses to overwrite).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from research.astra.confirmation_campaign_20261004.verify.design_census_vis import load_vis

HERE = Path(__file__).resolve().parent
OUT = HERE / "design_census_vis_menu.json"
PROJECTS = ("GDSC_002", "GDSC_005")


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"REFUSE_OVERWRITE: {OUT}")
    v, meta = load_vis()
    v["project"] = v["RESEARCH_PROJECT"].str[:-2]
    v = v[v["project"].isin(PROJECTS)]
    g = v.groupby(["ANCHOR_ID", "LIBRARY_ID", "project"]).agg(
        conc=("ANCHOR_CONC", lambda s: tuple(sorted(set(s)))), maxc=("maxc", lambda s: tuple(sorted(set(s))))).reset_index()
    combos = []
    excluded = []
    for (a, b), d in g.groupby(["ANCHOR_ID", "LIBRARY_ID"]):
        if d["project"].nunique() < 2:
            continue
        same = d["conc"].nunique() == 1 and d["maxc"].nunique() == 1
        (combos if same else excluded).append((a, b))
    names = v.drop_duplicates(["ANCHOR_ID", "LIBRARY_ID"]).set_index(["ANCHOR_ID", "LIBRARY_ID"])[["ANCHOR_NAME", "LIBRARY_NAME"]]
    cs = set(combos)
    m = v[[k in cs for k in zip(v["ANCHOR_ID"], v["LIBRARY_ID"])]]
    per = m.groupby(["SIDM", "ANCHOR_ID", "LIBRARY_ID", "project"]).agg(
        plates=("BARCODE", "nunique"), cl=("CL", lambda s: frozenset(s)), tissue=("tissue", "first")).reset_index()
    wide = per.pivot_table(index=["SIDM", "ANCHOR_ID", "LIBRARY_ID"], columns="project",
                           values=["plates", "cl"], aggfunc="first")
    ok = wide[("plates", PROJECTS[0])].notna() & wide[("plates", PROJECTS[1])].notna()
    wide = wide[ok]
    disjoint = [len(x & y) == 0 for x, y in zip(wide[("cl", PROJECTS[0])], wide[("cl", PROJECTS[1])])]
    rep_inside = (wide[("plates", PROJECTS[0])] > 1) | (wide[("plates", PROJECTS[1])] > 1)
    t = pd.DataFrame({"SIDM": wide.index.get_level_values(0), "disjoint": disjoint, "rep_inside": rep_inside.to_numpy()})
    tissue = per.drop_duplicates("SIDM").set_index("SIDM")["tissue"]
    line = t.groupby("SIDM").agg(n=("disjoint", "size"), disjoint=("disjoint", "sum"), rep=("rep_inside", "sum"))
    line["tissue"] = tissue.reindex(line.index).to_numpy()
    complete = line[line["n"] == len(combos)]
    r = {"rule": "DESIGN-ONLY (explicit allow list; see design_census_vis.py)", "fitted_tsv_gz_sha256": meta["fitted_tsv_gz_sha256"],
         "projects": list(PROJECTS),
         "menu": [[a, b, names.loc[(a, b), "ANCHOR_NAME"], names.loc[(a, b), "LIBRARY_NAME"]] for a, b in sorted(combos)],
         "menu_size": len(combos),
         "excluded_shared_combos_conc_differs": [[a, b, names.loc[(a, b), "ANCHOR_NAME"], names.loc[(a, b), "LIBRARY_NAME"]]
                                                 for a, b in excluded],
         "lines_with_any": int(len(line)), "lines_complete_menu": int(len(complete)),
         "complete_lines_by_tissue": {k: int(x) for k, x in complete["tissue"].value_counts().items()},
         "complete_lines_all_candidates_disjoint_cl": int((complete["disjoint"] == complete["n"]).sum()),
         "complete_lines_ge10_candidates_disjoint_cl": int((complete["disjoint"] >= 10).sum()),
         "complete_lines_any_candidate_disjoint_cl": int((complete["disjoint"] >= 1).sum()),
         "complete_lines_with_replicate_plates_inside_a_project": int((complete["rep"] > 0).sum()),
         "line_x_candidate_disjoint_cl_share": float(t["disjoint"].mean()),
         "note": "pre-QC design menu; the authors' RMSE QC applied by a frozen builder can remove candidates (outcome-conditioned, reported)"}
    with OUT.open("x", encoding="utf-8") as fh:
        json.dump(r, fh, indent=1, sort_keys=True, default=str)
    print(json.dumps(r, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
