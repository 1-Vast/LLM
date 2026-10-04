"""ALMANAC coupling check: do SCORE's single-agent inputs coincide with our context records?

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws2_predecision_state/almanac_coupling.py
- Purpose: NCI's SCORE = ExpectedGrowth - PercentGrowth, with ExpectedGrowth computed from the
  single drugs' PercentGrowth "tested alone at the same concentration" (ALMANAC_DataFields.txt).
  The frozen builder's context (mono_mean, mono_top, expected) averages drug-alone records
  (CONCINDEX1 > 0, no drug 2). This script checks, record by record, whether ExpectedGrowth is
  reproduced from the drug-alone records on the SAME plate at the same concentration (i.e. the
  label and the context share wells), how many plates each drug-alone (drug, line) mean pools,
  and the screen dates (TESTDATE) for the timing gate.
- Core points:
  - EXPOSED data (opened once for the confirmatory run at 17:58:48). This is exploratory. The
    raw zip is read directly (pandas) and NOT through `screens.open_vault`, because that call
    appends to research/certified_discovery/protocol/vault_log.jsonl, outside WS2's write scope.
    The access is recorded in outputs/almanac_access_receipt.json instead.
  - Reads no column the frozen builder did not already read except EXPECTEDGROWTH, TESTDATE,
    STUDY (documentation-level fields needed for the coupling and timing questions).
- Interfaces: `python almanac_coupling.py` -> outputs/almanac_coupling.json
- Depends on: numpy, pandas; common.py.
"""
from __future__ import annotations

import time
import zipfile

import numpy as np
import pandas as pd

from common import ALMANAC, ROOT, load, sha256_file, write_json

ZIP = ROOT / "data/external/nci_almanac_2017/ComboDrugGrowth_Nov2017.zip"
COLUMNS = ["SCREENER", "STUDY", "TESTDATE", "PLATE", "NSC1", "CONCINDEX1", "CONC1", "NSC2", "CONCINDEX2", "CONC2",
           "PERCENTGROWTH", "EXPECTEDGROWTH", "SCORE", "CELLNAME"]


def expected_growth(g1: np.ndarray, g2: np.ndarray) -> np.ndarray:
    """NCI's documented rule (ALMANAC_DataFields.txt)."""
    neg = (g1 < 0) | (g2 < 0)
    return np.where(neg, np.minimum(g1, g2), np.minimum(g1, 100) * np.minimum(g2, 100) / 100.0)


def main() -> int:
    started = time.time()
    receipt = {"opened_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "file": str(ZIP.relative_to(ROOT)),
               "sha256": sha256_file(ZIP), "columns_read": COLUMNS,
               "purpose": "WS2 exploratory coupling/timing check on exposed ALMANAC (not confirmatory)",
               "vault_log_not_written": "open_vault would append outside WS2 write scope; recorded here instead"}
    write_json("almanac_access_receipt.json", receipt)
    with zipfile.ZipFile(ZIP) as archive, archive.open("ComboDrugGrowth_Nov2017.csv") as handle:
        f = pd.read_csv(handle, usecols=COLUMNS, low_memory=False, dtype={"NSC1": "Int64", "NSC2": "Int64",
                                                                           "CELLNAME": "string", "PLATE": "string"})
    f["CELLNAME"] = f["CELLNAME"].str.strip()
    both = (f["CONCINDEX1"] > 0) & (f["CONCINDEX2"] > 0) & f["NSC2"].notna()
    alone = (f["CONCINDEX1"] > 0) & ~(f["CONCINDEX2"] > 0) & f["NSC2"].isna()
    combo = f[both].copy()
    single = f[alone].copy()
    # single-agent lookup on the same plate, same drug, same concentration
    key = ["PLATE", "CELLNAME", "NSC1", "CONC1"]
    s = single.groupby(key)["PERCENTGROWTH"].agg(["mean", "size"]).reset_index()
    s.columns = ["PLATE", "CELLNAME", "NSC", "CONC", "PG", "n"]
    m = combo.merge(s.rename(columns={"NSC": "NSC1", "CONC": "CONC1", "PG": "PG1", "n": "n1"}), on=["PLATE", "CELLNAME", "NSC1", "CONC1"], how="left")
    m = m.merge(s.rename(columns={"NSC": "NSC2", "CONC": "CONC2", "PG": "PG2", "n": "n2"}), on=["PLATE", "CELLNAME", "NSC2", "CONC2"], how="left")
    have = m["PG1"].notna() & m["PG2"].notna() & m["EXPECTEDGROWTH"].notna()
    recon = expected_growth(m.loc[have, "PG1"].to_numpy(float), m.loc[have, "PG2"].to_numpy(float))
    err = np.abs(recon - m.loc[have, "EXPECTEDGROWTH"].to_numpy(float))
    score_check = np.abs(m["EXPECTEDGROWTH"] - m["PERCENTGROWTH"] - m["SCORE"]).dropna()
    # how many plates feed one (drug, line) context mean
    plates_per_drug_line = single.groupby(["NSC1", "CELLNAME"])["PLATE"].nunique()
    combos_per_plate = combo.groupby("PLATE").apply(lambda g: g[["NSC1", "NSC2"]].drop_duplicates().shape[0])
    # share of an experiment's own-plate single records in the (drug, line) context pool
    own_share = []
    pool = single.groupby(["NSC1", "CELLNAME"]).size()
    exp_plates = combo.assign(lo=combo[["NSC1", "NSC2"]].min(axis=1), hi=combo[["NSC1", "NSC2"]].max(axis=1))
    exp_plates = exp_plates.groupby(["lo", "hi", "CELLNAME"])["PLATE"].unique()
    single_by = single.groupby(["NSC1", "CELLNAME", "PLATE"]).size()
    sample = exp_plates.sample(n=min(5000, len(exp_plates)), random_state=20261003)
    for (lo, hi, line), plates in sample.items():
        for drug in (lo, hi):
            total = pool.get((drug, line), 0)
            own = sum(single_by.get((drug, line, p), 0) for p in plates)
            if total:
                own_share.append(own / total)
    dates = pd.to_datetime(f["TESTDATE"], errors="coerce")
    by_screener = f.assign(d=dates).groupby("SCREENER")["d"].agg(["min", "max"]).astype(str).to_dict("index")
    # within-line correlation of the frozen `expected` feature and the label (from the cache)
    lib = load(ALMANAC)
    payload = {
        "purpose": "ALMANAC label/context coupling (exploratory; data exposed)",
        "access_receipt": receipt,
        "records": int(len(f)), "combination_records": int(both.sum()), "single_agent_records": int(alone.sum()),
        "expectedgrowth_reproduced_from_same_plate_singles": {
            "combination_records_with_both_same_plate_singles": int(have.sum()),
            "share_of_combination_records": float(have.mean()),
            "exact_within_0.01": float((err < 0.01).mean()), "within_0.5": float((err < 0.5).mean()),
            "median_abs_error": float(np.median(err)), "p99_abs_error": float(np.percentile(err, 99)),
            "same_plate_single_records_per_drug_conc_median": float(np.nanmedian(np.r_[m.loc[have, "n1"], m.loc[have, "n2"]])),
        },
        "score_equals_expected_minus_percentgrowth_within_0.5": float((score_check < 0.5).mean()),
        "plates_per_drug_line_context_pool": {"median": float(plates_per_drug_line.median()),
                                              "min": int(plates_per_drug_line.min()), "max": int(plates_per_drug_line.max())},
        "distinct_pairs_per_plate": {"median": float(combos_per_plate.median()), "max": int(combos_per_plate.max())},
        "own_plate_share_of_context_pool": {"median": float(np.median(own_share)), "mean": float(np.mean(own_share)),
                                            "p90": float(np.percentile(own_share, 90)), "n_drug_experiment": len(own_share)},
        "testdate_range_by_screener": by_screener,
        "testdate_overall": [str(dates.min()), str(dates.max())],
        "cache_library_sha256": sha256_file(ALMANAC), "cache_lines": len(lib.lines),
        "wall_seconds": round(time.time() - started, 1),
    }
    path = write_json("almanac_coupling.json", payload)
    print(path)
    print({k: v for k, v in payload.items() if k not in ("access_receipt",)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
