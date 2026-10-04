"""Uncharged resource cost of the single-agent context, against the charged campaign budget.

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws2_predecision_state/costs.py
- Purpose: the frozen replay charges only purchased combination dose points; the single-agent
  context every world-model and heuristic arm uses is not charged. This script counts, per
  target line, what that context consumed in the source screens (wells / records / plates) and
  what a campaign was charged, using design columns only (no outcome column is read).
- Core points:
  - O'Neil: single-agent rows (drug x concentration) x non-null replicate viabilities in the
    batch the context uses (batch 1, frozen fallback otherwise); campaign = budget experiments x
    16 dose points x 4 replicate wells (README: 64 wells per experiment).
  - ALMANAC: drug-alone records (CONCINDEX1 > 0, no drug 2) per line and the plates they sit on;
    campaign = median-9 dose-point records x budget (wells per record are not published).
  - Days: O'Neil single-agent assay 96 h + plating = 5 days (one round) if run before round 1;
    ALMANAC 3 days per round.
- Interfaces: `python costs.py` -> outputs/costs.json
- Depends on: numpy, pandas; research.certified_discovery (read-only); common.py.
"""
from __future__ import annotations

import math
import zipfile
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

from common import ALMANAC, ONEIL, ROOT, load, write_json
from research.certified_discovery import screens
from research.certified_discovery.xlsx import iter_rows


def oneil() -> dict:
    lib = load(ONEIL)
    rows = iter_rows(screens.ONEIL_SINGLE)
    header = next(rows)
    wells = defaultdict(int)
    points = defaultdict(int)
    for row in rows:
        if not row or row[0] != "1":
            continue
        n = sum(1 for x in row[4:10] if x not in (None, "", "NULL"))
        wells[row[1]] += n
        points[row[1]] += 1
    per_line = []
    for l, name in enumerate(lib.lines):
        n = int((lib.c == l).sum())
        budget = math.ceil(0.1 * n)
        per_line.append({"line": name, "single_agent_wells": wells.get(name, 0), "single_agent_points": points.get(name, 0),
                         "campaign_experiments": budget, "campaign_wells": budget * 64,
                         "campaign_dose_points": int(lib.cost_points[lib.c == l].mean() * budget)})
    sw = np.array([r["single_agent_wells"] for r in per_line], float)
    cw = np.array([r["campaign_wells"] for r in per_line], float)
    return {"per_line": per_line, "single_agent_wells_median": float(np.median(sw)),
            "campaign_wells_median": float(np.median(cw)), "ratio_single_to_campaign_median": float(np.median(sw / cw)),
            "days": {"campaign": 20.0, "single_agent_round_if_before_round1": 5.0},
            "note": "singles are also required by the label's Bliss expectation, so they would be bought anyway; what is "
                    "uncharged is their wells and, if they must precede round 1 to serve as context, one extra 5-day round"}


def almanac() -> dict:
    lib = load(ALMANAC)
    cols = ["NSC1", "NSC2", "CONCINDEX1", "CONCINDEX2", "CONC1", "CELLNAME", "PLATE"]
    with zipfile.ZipFile(screens.ALMANAC_ZIP) as archive, archive.open("ComboDrugGrowth_Nov2017.csv") as handle:
        f = pd.read_csv(handle, usecols=cols, low_memory=False, dtype={"NSC1": "Int64", "NSC2": "Int64", "CELLNAME": "string", "PLATE": "string"})
    f["CELLNAME"] = f["CELLNAME"].str.strip()
    alone = f[(f["CONCINDEX1"] > 0) & ~(f["CONCINDEX2"] > 0) & f["NSC2"].isna()]
    g = alone.groupby("CELLNAME")
    rec = g.size()
    plates = g["PLATE"].nunique()
    distinct = alone.groupby("CELLNAME").apply(lambda x: x[["NSC1", "CONC1"]].drop_duplicates().shape[0])
    per_line = []
    for l, name in enumerate(lib.lines):
        n = int((lib.c == l).sum())
        budget = math.ceil(0.1 * n)
        bought = int(np.median(lib.cost_points[lib.c == l]) * budget)
        per_line.append({"line": name, "drug_alone_records": int(rec.get(name, 0)), "drug_alone_plates": int(plates.get(name, 0)),
                         "distinct_drug_conc": int(distinct.get(name, 0)), "campaign_experiments": budget,
                         "campaign_records_approx": bought})
    r = np.array([p["drug_alone_records"] for p in per_line], float)
    c = np.array([p["campaign_records_approx"] for p in per_line], float)
    d = np.array([p["distinct_drug_conc"] for p in per_line], float)
    return {"per_line": per_line, "drug_alone_records_median": float(np.median(r)),
            "distinct_drug_conc_median": float(np.median(d)), "campaign_records_median": float(np.median(c)),
            "ratio_pooled_singles_to_campaign_median": float(np.median(r / c)),
            "ratio_minimal_singles_to_campaign_median": float(np.median(d / c)),
            "note": "the context pools drug-alone wells from ~all plates of the full screen (median 40 plates per drug x "
                    "line), most of which belong to combinations a 10% campaign never buys; a real campaign would need a "
                    "dedicated single-agent plate set (>= distinct drug x conc records) before round 1 (+3 days)"}


def main() -> int:
    payload = {"purpose": "WS2 uncharged single-agent context cost vs charged campaign budget (design columns only)",
               "oneil": oneil(), "almanac_exploratory": almanac(),
               "state_cost_depmap_expression": {
                   "wells": "one culture per line (not a screen well); not charged anywhere",
                   "waiting": "UNKNOWN for a prospective line: culture expansion plus RNA-seq turnaround (not measured here)",
                   "money": "UNKNOWN (no quoted price in the repository); no net-value claim possible"}}
    write_json("costs.json", payload)
    o, a = payload["oneil"], payload["almanac_exploratory"]
    print("oneil single wells median", o["single_agent_wells_median"], "campaign wells median", o["campaign_wells_median"],
          "ratio", round(o["ratio_single_to_campaign_median"], 3))
    print("almanac pooled singles median", a["drug_alone_records_median"], "distinct", a["distinct_drug_conc_median"],
          "campaign", a["campaign_records_median"], "ratios", round(a["ratio_pooled_singles_to_campaign_median"], 2),
          round(a["ratio_minimal_singles_to_campaign_median"], 3))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
