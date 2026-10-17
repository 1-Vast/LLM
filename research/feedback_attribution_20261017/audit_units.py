"""Resource units: what one logical action returns and what it would cost to measure.

File summary
- Path: research/feedback_attribution_20261017/audit_units.py
- Purpose: the confirmation counted each (sample, inhibitor) AUC as one "well". This audit maps
  logical action -> returned data -> physical experimental cost, from the release's raw inhibitor
  file (design columns: run, panel, plate, replicate, concentration, QC flag) and the published
  assay description. No response value is read.
- Core points:
  - Dose points, wells and replicates per profile are counted over the 520 x 166 domain.
  - The physical cost table is a mapping with stated assumptions, not a price.
- Interfaces: `python -B audit_units.py` writes COST_UNITS.json.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import HERE, RAW, SOURCE_STUDY, load_domain, sha256, write_json

DESIGN_COLUMNS = ["dbgap_rnaseq_sample", "inhibitor", "run_index", "inhibitor_panel", "plate_num", "replicate",
                  "well_concentration", "time_of_read", "passed_qc"]
SOURCES = {
    "tyner_2018": "Tyner et al., Nature 562:526-531 (2018), PMC6280667, Methods: 7-point 3-fold series "
                  "(10 to 0.0137 uM; 1 to 0.00137 uM for 4 drugs), one well per concentration, 10,000 cells "
                  "per well in 384-well plates, plated within 24 h of collection, 72 h culture, MTS read; "
                  "DMSO vehicle and a positive-control combination on each plate; probit fit on 7 points",
    "bottomly_2022": "Bottomly et al., Cancer Cell 40:850-864 (2022), PMC9378589: same assay as 2018; profiles "
                     "removed when deviance > 2 and AIC > 12; plates removed when >= 4 concentrations have SD > 25",
}


def main() -> None:
    d = load_domain()
    raw = pd.read_csv(RAW, sep="\t", usecols=DESIGN_COLUMNS,
                      dtype={"dbgap_rnaseq_sample": str, "inhibitor": str, "inhibitor_panel": str, "passed_qc": str})
    dom = raw[raw.dbgap_rnaseq_sample.isin(set(d["contexts"])) & raw.inhibitor.isin(set(d["items"]))]
    runs = dom.groupby(["dbgap_rnaseq_sample", "inhibitor", "run_index"])
    doses = runs.well_concentration.nunique()
    wells = runs.size()
    per_pair = dom.groupby(["dbgap_rnaseq_sample", "inhibitor"])
    pair_wells = per_pair.size()
    pair_runs = per_pair.run_index.nunique()
    plates = dom.groupby("dbgap_rnaseq_sample").apply(
        lambda g: g[["run_index", "inhibitor_panel", "plate_num"]].drop_duplicates().shape[0], include_groups=False)
    measured = int(np.isfinite(d["Y"]).sum())
    tor = dom.time_of_read.describe()

    res = json.loads((SOURCE_STUDY / "RESULTS.json").read_text(encoding="utf-8"))
    budget, k = res["frozen"]["budget"], res["frozen"]["k_bridge"]
    dose_points = int(doses.mode().iloc[0])
    out = {
        "status": "DESIGN_AUDIT: no response value read",
        "raw_sha256": sha256(RAW),
        "domain": {"samples": int(len(d["contexts"])), "inhibitors": int(len(d["items"])),
                   "measured_pairs": measured},
        "raw_design": {
            "pairs_with_raw_wells": int(len(pair_wells)),
            "dose_points_per_run": {str(int(k_)): int(v) for k_, v in doses.value_counts().items()},
            "wells_per_run": {str(int(k_)): int(v) for k_, v in wells.value_counts().sort_index().items()},
            "runs_per_pair": {str(int(k_)): int(v) for k_, v in pair_runs.value_counts().sort_index().items()},
            "wells_per_pair_mean": float(pair_wells.mean()),
            "share_of_pairs_with_more_than_one_profile": float((pair_wells > dose_points).mean()),
            "plates_per_sample": {"median": float(plates.median()), "p10": float(plates.quantile(0.1)),
                                  "p90": float(plates.quantile(0.9))},
            "passed_qc_values": sorted(dom.passed_qc.unique().tolist()),
            "passed_qc_note": "the release contains QC-passed wells only, so QC removals are not visible",
            "time_of_read": {"median": float(tor["50%"]), "min": float(tor["min"]), "max": float(tor["max"]),
                             "note": "units and meaning are not documented in the release; not used"},
        },
        "assay_sources": SOURCES,
        "action_mapping": [
            {"logical_action": "historical AUC query (this replay)",
             "returns": "one archived probit AUC summary for a (sample, inhibitor) pair, or nothing if the "
                        "archive has no QC-passed profile",
             "physical_cost": "none at replay time; it stands for one past 7-dose profile"},
            {"logical_action": "single-dose measurement",
             "returns": "viability at one concentration",
             "physical_cost": "1 treatment well per replicate plus shared plate controls; not what the "
                              "replay's AUC endpoint can grade"},
            {"logical_action": "AUC profile measurement",
             "returns": "a 7-point dose-response curve, probit fit and QC",
             "physical_cost": f"{dose_points} treatment wells per replicate, 10,000 cells per well, plus "
                              "plate controls; profiles can fail curve or plate QC"},
            {"logical_action": "second experimental round",
             "returns": "a new batch of profiles chosen from first-round readouts",
             "physical_cost": "a new plate set with its own controls, about 72 h more culture, and "
                              "banked cells; the replay assumes the response state is unchanged between "
                              "rounds, which it cannot test"},
        ],
        "per_arm": {
            "no_bridge (vc0, item, knn)": {"queries": budget, "profiles": budget,
                                           "treatment_wells_one_replicate": budget * dose_points,
                                           "rounds": 1, "culture_days_min": 3},
            "bridged (b_exploit, maestro, b_lookahead, attribution groups B/D/E/F)": {
                "queries": budget, "profiles": budget, "treatment_wells_one_replicate": budget * dose_points,
                "rounds": 2, "culture_days_min": 6,
                "round_split": f"{k} profiles then {budget - k}"},
            "attribution groups A/C (probes counted, not used)": {
                "queries": budget, "profiles": budget, "treatment_wells_one_replicate": budget * dose_points,
                "rounds": 1, "culture_days_min": 3},
        },
        "notes": [
            "Paired comparisons at equal query counts are unaffected; only low-cost claims change.",
            "Cells per sample at one replicate: 16 profiles x 7 wells x 10,000 = 1.12 million, before controls.",
            "API spend (0.28 USD for 520 LLM calls) is a small part of the cost of a bridged campaign.",
            "Basal RNA is pre-treatment, but the replay assumes its analysis is available before the first "
            "selection; turnaround for RNA-seq is not modelled.",
        ],
    }
    write_json(HERE / "COST_UNITS.json", out)
    print(json.dumps(out["raw_design"], indent=1))


if __name__ == "__main__":
    main()
