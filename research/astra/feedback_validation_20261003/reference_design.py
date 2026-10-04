"""Pre-freeze design check for an independent single-agent reference label on NCI-ALMANAC.

File summary
- Path: research/astra/feedback_validation_20261003/reference_design.py
- Purpose: before the primary protocol is frozen, establish (i) which single-agent records NCI
  used for each combination record's ExpectedGrowth (same plate, or a companion plate of the
  same run), and (ii) how many library experiments could be re-referenced against single-agent
  records from a DIFFERENT run (same screener, different test date). It computes no reference
  label value and no policy outcome; it only reads design columns plus EXPECTEDGROWTH and the
  single-agent PERCENTGROWTH needed to identify NCI's reference provenance.
- Core points:
  - ALMANAC is exposed (opened 2026-10-03T17:58:48 by the certified-discovery run). This check
    is exploratory and recorded as "seen before freeze" in the protocol.
  - NCI's documented rule: E = min(G1, G2) if either is negative, else min(G1,100)*min(G2,100)/100.
- Interfaces: `python -m research.astra.feedback_validation_20261003.reference_design`
  -> receipts/reference_design.json
- Depends on: numpy, pandas.
"""
from __future__ import annotations

import json
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
ZIP = ROOT / "data/external/nci_almanac_2017/ComboDrugGrowth_Nov2017.zip"
OUT = Path(__file__).resolve().parent / "receipts"
COLUMNS = ["SCREENER", "STUDY", "TESTDATE", "PLATE", "NSC1", "CONCINDEX1", "CONC1", "NSC2", "CONCINDEX2",
           "CONC2", "CELLNAME", "PERCENTGROWTH", "EXPECTEDGROWTH"]


def expected_growth(g1: np.ndarray, g2: np.ndarray) -> np.ndarray:
    neg = (g1 < 0) | (g2 < 0)
    return np.where(neg, np.minimum(g1, g2), np.minimum(g1, 100) * np.minimum(g2, 100) / 100.0)


def load_frame() -> pd.DataFrame:
    with zipfile.ZipFile(ZIP) as archive, archive.open("ComboDrugGrowth_Nov2017.csv") as handle:
        frame = pd.read_csv(handle, usecols=COLUMNS, low_memory=False,
                            dtype={"NSC1": "Int64", "NSC2": "Int64", "CELLNAME": "string", "PLATE": "string",
                                   "SCREENER": "string", "STUDY": "string", "TESTDATE": "string"})
    frame["CELLNAME"] = frame["CELLNAME"].str.strip()
    return frame


def split(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    both = (frame["CONCINDEX1"] > 0) & (frame["CONCINDEX2"] > 0) & frame["NSC2"].notna()
    alone = (frame["CONCINDEX1"] > 0) & ~(frame["CONCINDEX2"] > 0) & frame["NSC2"].isna()
    combo = frame[both].copy()
    single = frame[alone].copy()
    combo["lo"] = combo[["NSC1", "NSC2"]].min(axis=1)
    combo["hi"] = combo[["NSC1", "NSC2"]].max(axis=1)
    return combo, single


def _lookup(combo: pd.DataFrame, single: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Mean single-agent PERCENTGROWTH for drug 1 and drug 2 of each combination record on `keys`."""
    s = single.groupby(keys + ["CELLNAME", "NSC1", "CONC1"])["PERCENTGROWTH"].mean().rename("PG").reset_index()
    left = s.rename(columns={"PG": "PG1"})
    right = s.rename(columns={"NSC1": "NSC2", "CONC1": "CONC2", "PG": "PG2"})
    out = combo.merge(left, on=keys + ["CELLNAME", "NSC1", "CONC1"], how="left")
    return out.merge(right, on=keys + ["CELLNAME", "NSC2", "CONC2"], how="left")


def main() -> int:
    started = time.time()
    frame = load_frame()
    combo, single = split(frame)
    combo = combo[np.isfinite(combo["EXPECTEDGROWTH"].astype(float))].reset_index(drop=True)
    combo["rid"] = np.arange(len(combo))
    report: dict = {"exposure": "EXPLORATORY: ALMANAC opened 2026-10-03T17:58:48 (certified_discovery vault)",
                    "combination_records_with_expected": int(len(combo)), "single_agent_records": int(len(single))}

    # (i) provenance of NCI's expectation: same plate, else same screener + test date (companion plate)
    plate = _lookup(combo, single, ["PLATE"])
    have_plate = plate["PG1"].notna() & plate["PG2"].notna()
    err_plate = np.abs(expected_growth(plate["PG1"].to_numpy(float), plate["PG2"].to_numpy(float))
                       - plate["EXPECTEDGROWTH"].to_numpy(float))
    same_plate = have_plate.to_numpy() & (err_plate < 0.5)
    date = _lookup(combo, single, ["SCREENER", "TESTDATE"])
    have_date = date["PG1"].notna() & date["PG2"].notna()
    err_date = np.abs(expected_growth(date["PG1"].to_numpy(float), date["PG2"].to_numpy(float))
                      - date["EXPECTEDGROWTH"].to_numpy(float))
    rest = ~same_plate
    report["nci_reference_provenance"] = {
        "same_plate_singles_available": float(have_plate.mean()),
        "reproduced_from_same_plate_within_0.5": float(same_plate.mean()),
        "records_not_same_plate": int(rest.sum()),
        "of_those_same_screener_date_singles_available": float(have_date.to_numpy()[rest].mean()),
        "of_those_reproduced_from_same_screener_date_mean_within_0.5": float((have_date.to_numpy() & (err_date < 0.5))[rest].mean()),
        "of_those_reproduced_within_2.0": float((have_date.to_numpy() & (err_date < 2.0))[rest].mean()),
        "unexplained_share_of_all_records": float((rest & ~(have_date.to_numpy() & (err_date < 2.0))).mean()),
    }

    # (ii) coverage of an independent reference: same screener, a test date different from every
    # test date of the experiment's own combination records (hence also different plates).
    exp_key = ["lo", "hi", "CELLNAME"]
    exp_dates = combo.groupby(exp_key)["TESTDATE"].agg(lambda s: frozenset(s.dropna()))
    single_dates = single.groupby(["SCREENER", "CELLNAME", "NSC1", "CONC1"])["TESTDATE"].agg(
        lambda s: frozenset(s.dropna()))
    sd = single_dates.to_dict()
    rec_dates = exp_dates.reindex(pd.MultiIndex.from_frame(combo[exp_key])).to_numpy()
    cover1 = np.zeros(len(combo), bool)
    cover2 = np.zeros(len(combo), bool)
    n_off = np.zeros(len(combo), int)
    for i, (scr, line, n1, c1, n2, c2) in enumerate(zip(combo["SCREENER"], combo["CELLNAME"], combo["NSC1"],
                                                         combo["CONC1"], combo["NSC2"], combo["CONC2"])):
        own = rec_dates[i]
        d1 = sd.get((scr, line, n1, c1), frozenset()) - own
        d2 = sd.get((scr, line, n2, c2), frozenset()) - own
        cover1[i], cover2[i] = bool(d1), bool(d2)
        n_off[i] = min(len(d1), len(d2))
    both_cov = cover1 & cover2
    combo["covered"] = both_cov
    per_exp = combo.groupby(exp_key)["covered"].agg(["mean", "size"])
    report["independent_reference_coverage"] = {
        "definition": "single-agent records of the same drug, cell line and concentration from the same SCREENER "
                      "on a TESTDATE different from every test date of the experiment's combination records",
        "records_covered": float(both_cov.mean()),
        "off_date_runs_per_record_median": float(np.median(n_off[both_cov])) if both_cov.any() else 0.0,
        "off_date_runs_per_record_p10": float(np.percentile(n_off[both_cov], 10)) if both_cov.any() else 0.0,
        "experiments": int(len(per_exp)),
        "experiments_all_records_covered": float((per_exp["mean"] == 1.0).mean()),
        "experiments_any_record_covered": float((per_exp["mean"] > 0).mean()),
    }
    report["wall_seconds"] = round(time.time() - started, 1)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "reference_design.json"
    path.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
