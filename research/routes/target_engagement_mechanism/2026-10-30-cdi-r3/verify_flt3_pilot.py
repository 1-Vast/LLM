"""Independent audit of the saved FLT3 exploratory pilot outputs."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


EP = Path(r"D:/MAESTRO/research/2026-10-30-cdi-r3")


def main() -> None:
    summary = json.loads((EP / "flt3_response_pilot.json").read_text(encoding="utf-8"))
    pairs = pd.read_csv(EP / "flt3_pair_cell_dose_observations.csv", low_memory=False)
    contrasts = pd.read_csv(EP / "flt3_context_contrasts.csv", low_memory=False)
    checks = {}
    checks["row_count"] = int(len(pairs))
    checks["pair_count"] = int(pairs["pair_id"].nunique())
    checks["unique_cell_dose_pair_keys"] = int(pairs[["pair_id", "dose", "cell_id"]].drop_duplicates().shape[0])
    checks["all_keys_unique"] = checks["unique_cell_dose_pair_keys"] == len(pairs)
    checks["delta_pKd_constant_within_pair"] = bool((pairs.groupby("pair_id")["delta_pKd"].nunique() <= 1).all())
    checks["positive_column_counts"] = bool((pairs[["n_cols_a", "n_cols_b"]] > 0).all().all())
    checks["unique_cells"] = int(pairs["cell_id"].nunique())
    checks["unique_lineages"] = int(pairs["lineage"].nunique(dropna=True))
    checks["context_contrast_rows"] = int(contrasts["D_high_minus_low"].notna().sum())
    pair_mean = pairs.groupby(["pair_id", "delta_pKd"], as_index=False).agg(mean_delta_y=("delta_y", "mean"))
    rho_mean = spearmanr(pair_mean["delta_pKd"], pair_mean["mean_delta_y"]).statistic
    valid = contrasts.dropna(subset=["D_high_minus_low"])
    rho_d = spearmanr(valid["delta_pKd"], valid["D_high_minus_low"]).statistic
    checks["rho_pair_mean"] = float(rho_mean)
    checks["rho_context_D"] = float(rho_d)
    checks["summary_counts_match"] = (
        checks["row_count"] == summary["pair_cell_dose_rows"]
        and checks["pair_count"] == summary["pair_count"]
        and checks["context_contrast_rows"] == summary["context_contrast_rows_with_high_low"]
    )
    # Numerical re-read only; no claim of independent biological replication.
    assert checks["all_keys_unique"]
    assert checks["delta_pKd_constant_within_pair"]
    assert checks["positive_column_counts"]
    assert checks["summary_counts_match"]
    out = {
        "checks": checks,
        "source_summary": summary,
        "interpretation": "Independent file-level and arithmetic audit only. It does not validate target mediation, exposure matching, biological replication, or Agent benefit.",
    }
    (EP / "flt3_pilot_independent_review.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
