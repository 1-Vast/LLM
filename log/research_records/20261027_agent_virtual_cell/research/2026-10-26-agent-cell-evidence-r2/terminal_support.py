"""Endpoint design census; no response or QC eligibility used."""
from pathlib import Path
import json
import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE.parents[1] / "research/eight_directions_20261026/evidence_audit/raw/PAIR_SCREEN.csv"
COLS = ["Cell line", "Iteration", "Drug 1", "Drug 2", "Conc 1 (uM)", "Conc 2 (uM)", "file"]
TUMOR = ["A673", "MSKEWS-33838", "MSKEWS-66647", "SKNEP", "TC-71"]
NORMAL = ["BJ", "RPE"]


def main():
    raw = pd.read_csv(RAW, usecols=COLS, low_memory=False)
    controls = {"dmso", "high control", "low control"}
    raw = raw[~raw["Drug 1"].isin(controls) & ~raw["Drug 2"].isin(controls)
              & raw["Drug 1"].ne(raw["Drug 2"])].copy()
    raw["key"] = [tuple(sorted(((a, float(da)), (b, float(db))))) for a, b, da, db in
                  raw[["Drug 1", "Drug 2", "Conc 1 (uM)", "Conc 2 (uM)"]].itertuples(index=False, name=None)]
    source_keys = set(raw.loc[pd.to_numeric(raw.Iteration, errors="coerce").between(1, 10), "key"])
    results = {}
    for stage in ["validation (random, round 15)", "validation (ews hits, round 15)"]:
        frame = raw[raw.Iteration.eq(stage)]
        sets = {cell: set(g.key) for cell, g in frame.groupby("Cell line")}
        normal_common = sets.get("BJ", set()) & sets.get("RPE", set())
        all_shared = normal_common.copy()
        for cell in TUMOR:
            all_shared &= sets.get(cell, set())
        pairwise = {cell: {normal: len(sets.get(cell, set()) & sets.get(normal, set()))
                           for normal in NORMAL} for cell in TUMOR}
        files = frame.groupby(["Cell line", "key"]).file.nunique()
        results[stage] = {"raw_combo_rows": len(frame), "cell_labels": sorted(sets),
                          "unique_keys_per_cell": {c: len(v) for c, v in sets.items()},
                          "tumor_normal_exact_dose_pair_intersections": pairwise,
                          "both_normals_common_keys": len(normal_common),
                          "all_five_tumors_and_both_normals_common_keys": len(all_shared),
                          "common_keys_with_both_doses_in_source_levels_0_1_or_1": sum(all(dose in [.1, 1.] for _, dose in key) for key in all_shared),
                          "common_exact_pair_and_doses_previously_seen_in_source": len(all_shared & source_keys),
                          "files_per_cell_condition_distribution": {str(k): int(v) for k, v in files.value_counts().sort_index().items()}}
    result = {"response_columns_loaded": False, "QC_used_for_eligibility": False,
              "stages": results,
              "limits": ["Raw label/dose identities, no alias or stock normalization.",
                         "Stage dose coverage does not prove culture independence, efficacy or decision value.",
                         "EWS hit stage is a selected candidate panel, not a random population or prospective fresh test."]}
    (HERE / "terminal_support.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
