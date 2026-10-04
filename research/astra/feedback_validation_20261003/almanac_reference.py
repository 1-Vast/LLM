"""Exploratory: NCI-ALMANAC labels re-referenced to single agents from a different run.

File summary
- Path: research/astra/feedback_validation_20261003/almanac_reference.py
- Purpose: build a validation label for every NCI-ALMANAC experiment whose Bliss expectation uses
  single-agent records from a DIFFERENT test date of the same screening centre, so that it shares
  no single-agent well with NCI's SCORE (which uses same-plate or same-date companion singles;
  `receipts/reference_design.json`). Combination wells are shared, so this is an independent
  single-agent reference, not an independent biological replicate.
- Core points:
  - EXPLORATORY: ALMANAC was opened 2026-10-03T17:58:48 by the certified-discovery run. Nothing
    here is untouched confirmation.
  - Per combination record: E_off = NCI rule applied to the mean PERCENTGROWTH of off-date singles
    (same screener, cell line, drug and concentration); reference score = E_off - PERCENTGROWTH.
    Experiment label = mean over its records; missing (never imputed) unless every record with a
    finite SCORE has off-date singles for both drugs.
  - Validation call: reference label > 10 (the screen's own threshold). Efficacy: some record of
    the experiment has PERCENTGROWTH <= 50.
- Interfaces: `build_panel(ticket)` -> (Panel, report).
- Depends on: numpy, pandas, `reference_design` (loader and NCI rule), frozen `screens`.
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np
import pandas as pd

from research.certified_discovery.screens import CACHE, load_library, sha256

from .reference_design import ZIP, expected_growth, load_frame, split
from .study import Panel

LIBRARY = CACHE / "almanac_v1.npz"
EFFICACY_GROWTH = 50.0


def build_panel(ticket: dict) -> tuple[Panel, dict]:
    if not ticket or "freeze_sha256" not in ticket:
        raise PermissionError("VAULT_SEALED: build_panel needs an open_vault ticket")
    lib = load_library(LIBRARY)
    frame = load_frame()
    combo, single = split(frame)
    combo = combo[np.isfinite(combo["PERCENTGROWTH"].astype(float))].copy()
    # SCORE is not loaded by load_frame; NCI's SCORE is finite exactly where EXPECTEDGROWTH and
    # PERCENTGROWTH are (SCORE = EXPECTEDGROWTH - PERCENTGROWTH within 0.5 for all records).
    combo = combo[np.isfinite(combo["EXPECTEDGROWTH"].astype(float))].reset_index(drop=True)
    key = ["lo", "hi", "CELLNAME"]
    own_dates = combo.groupby(key)["TESTDATE"].agg(lambda s: frozenset(s.dropna())).to_dict()
    sums: dict = defaultdict(lambda: defaultdict(lambda: [0.0, 0]))
    for scr, line, nsc, conc, date, pg in zip(single["SCREENER"], single["CELLNAME"], single["NSC1"], single["CONC1"],
                                              single["TESTDATE"], single["PERCENTGROWTH"].astype(float)):
        if np.isfinite(pg) and not pd.isna(date):      # undated singles cannot be shown to be off-date
            cell = sums[(scr, line, nsc, conc)][date]
            cell[0] += pg
            cell[1] += 1
    totals = {k: (sum(v[0] for v in d.values()), sum(v[1] for v in d.values())) for k, d in sums.items()}

    def off_mean(scr, line, nsc, conc, dates):
        k = (scr, line, nsc, conc)
        if k not in totals:
            return np.nan
        s, n = totals[k]
        for d in dates:
            if d in sums[k]:
                s -= sums[k][d][0]
                n -= sums[k][d][1]
        return s / n if n > 0 else np.nan

    g1 = np.empty(len(combo))
    g2 = np.empty(len(combo))
    for i, (scr, line, lo, hi, n1, c1, n2, c2) in enumerate(zip(
            combo["SCREENER"], combo["CELLNAME"], combo["lo"], combo["hi"], combo["NSC1"], combo["CONC1"],
            combo["NSC2"], combo["CONC2"])):
        dates = own_dates[(lo, hi, line)]
        g1[i] = off_mean(scr, line, n1, c1, dates)
        g2[i] = off_mean(scr, line, n2, c2, dates)
    pg = combo["PERCENTGROWTH"].to_numpy(float)
    ref = expected_growth(g1, g2) - pg
    combo["ref"] = ref
    combo["covered"] = np.isfinite(ref)
    per = combo.groupby(key).agg(ref=("ref", "mean"), covered=("covered", "all"), min_growth=("PERCENTGROWTH", "min"),
                                 n=("ref", "size")).reset_index()
    per.loc[~per["covered"], "ref"] = np.nan
    nsc_index = {int(x): i for i, x in enumerate(lib.provenance["nsc"])}
    line_index = {name: i for i, name in enumerate(lib.lines)}
    lookup = {(nsc_index[int(lo)], nsc_index[int(hi)], line_index[line]): (r, mg)
              for lo, hi, line, r, mg in zip(per["lo"], per["hi"], per["CELLNAME"], per["ref"], per["min_growth"])
              if int(lo) in nsc_index and int(hi) in nsc_index and line in line_index}
    valid_y = np.full(len(lib), np.nan)
    min_growth = np.full(len(lib), np.nan)
    for i, (a, b, c) in enumerate(zip(lib.a, lib.b, lib.c)):
        hit = lookup.get((int(a), int(b), int(c)))
        if hit is not None:
            valid_y[i], min_growth[i] = hit
    missing = ~np.isfinite(valid_y)
    panel = Panel("almanac2017_offdate_reference", "ALMANAC", lib, lib.y > lib.threshold,
                  np.where(missing, False, valid_y > lib.threshold), valid_y,
                  np.nan_to_num(min_growth, nan=np.inf) <= EFFICACY_GROWTH, missing)
    report = {"exposure": "EXPLORATORY (ALMANAC opened 2026-10-03T17:58:48)", "data_sha256": sha256(ZIP),
              "undated_single_records_skipped": int(single["TESTDATE"].isna().sum()),
              "library_sha256": sha256(LIBRARY), "experiments": int(len(lib)),
              "reference_missing": int(missing.sum()), "reference_missing_share": float(missing.mean()),
              "screen_hits": int(panel.screen_hit.sum()), "reference_hits": int(panel.valid_hit.sum()),
              "both": int((panel.screen_hit & panel.valid_hit).sum())}
    return panel, report
