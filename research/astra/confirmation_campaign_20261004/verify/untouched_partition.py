"""DESIGN-ONLY proposed H/E line partition for an untouched Vis 2024 cross-run confirmation evaluation.

File summary
- Path: research/astra/confirmation_campaign_20261004/verify/untouched_partition.py
- Purpose: a proposal only (the parent decides and freezes). From design columns of the Vis 2024
  fitted file (explicit allow list) and of the exposed Jaaks release: eligible lines = lines with the
  complete 19-combination cross-project menu (design_census_vis_menu.json) in tissues with >= 10 such
  lines; every line that appears in the Jaaks 2022 release goes to H (history only: its Jaaks
  measurements of the same combinations were seen by earlier studies and C*/fp* were selected on Jaaks
  lines); the other lines of each tissue are permuted with numpy default_rng([20261004, 99, tissue
  rank]) and the first min(floor(n_t / 2), n_non_jaaks) go to E, the rest to H.
- Interfaces: `python -m research.astra.confirmation_campaign_20261004.verify.untouched_partition`;
  writes verify/untouched_partition_proposal.json (refuses to overwrite).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from research.astra.confirmation_campaign_20261004.verify.design_census_vis import JAAKS, load_vis

HERE = Path(__file__).resolve().parent
OUT = HERE / "untouched_partition_proposal.json"
MENU = HERE / "design_census_vis_menu.json"
PROJECTS = ("GDSC_002", "GDSC_005")
MIN_LINES = 10
SEED = 20261004


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"REFUSE_OVERWRITE: {OUT}")
    menu = json.loads(MENU.read_text(encoding="utf-8"))
    combos = {(a, b) for a, b, _, _ in menu["menu"]}
    v, meta = load_vis()
    v["project"] = v["RESEARCH_PROJECT"].str[:-2]
    v = v[v["project"].isin(PROJECTS) & pd.Series([k in combos for k in zip(v["ANCHOR_ID"], v["LIBRARY_ID"])], index=v.index)]
    cover = v.groupby(["SIDM", "ANCHOR_ID", "LIBRARY_ID"])["project"].nunique()
    full = cover[cover == 2].groupby(level="SIDM").size()
    complete = sorted(full[full == len(combos)].index)
    tissue = v.drop_duplicates("SIDM").set_index("SIDM")["tissue"]
    cl = v.groupby(["SIDM", "project"])["CL"].agg(lambda s: frozenset(s)).unstack("project")
    disjoint_cl = {s: len(cl.loc[s, PROJECTS[0]] & cl.loc[s, PROJECTS[1]]) == 0 for s in complete}
    jaaks_lines = set(pd.read_csv(JAAKS, usecols=["SIDM"], dtype=str)["SIDM"].str.strip())
    by_t: dict[str, list] = {}
    for s in complete:
        by_t.setdefault(tissue[s], []).append(s)
    eligible = sorted(t for t, ls in by_t.items() if len(ls) >= MIN_LINES)
    split, counts = {}, {}
    for rank, t in enumerate(eligible):
        ls = sorted(by_t[t])
        jl = [s for s in ls if s in jaaks_lines]
        other = [s for s in ls if s not in jaaks_lines]
        perm = np.random.default_rng([SEED, 99, rank]).permutation(len(other))
        k = min(len(ls) // 2, len(other))
        e = sorted(other[i] for i in perm[:k])
        h = sorted(set(ls) - set(e))
        split[t] = {"E": e, "H": h, "H_jaaks_lines": sorted(jl)}
        counts[t] = {"lines": len(ls), "E": len(e), "H": len(h), "H_jaaks": len(jl),
                     "E_disjoint_cl": int(sum(disjoint_cl[s] for s in e))}
    tot = {k: int(sum(c[k] for c in counts.values())) for k in ("lines", "E", "H", "H_jaaks", "E_disjoint_cl")}
    r = {"status": "PROPOSAL (design-only; not frozen; no outcome of the Vis release has been read)",
         "fitted_tsv_gz_sha256": meta["fitted_tsv_gz_sha256"], "menu_size": len(combos), "min_lines_per_tissue": MIN_LINES,
         "rule": __doc__.split("- Purpose:")[1].split("- Interfaces")[0].strip(),
         "complete_lines_all_tissues": len(complete), "eligible_tissues": eligible,
         "excluded_tissues": {t: len(ls) for t, ls in by_t.items() if t not in eligible},
         "counts": counts, "totals": tot, "split": split}
    with OUT.open("x", encoding="utf-8") as fh:
        json.dump(r, fh, indent=1, sort_keys=True)
    print(json.dumps({k: r[k] for k in ("complete_lines_all_tissues", "excluded_tissues", "counts", "totals")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
