"""Design census only. Explicit allowlist; no response columns loaded."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRISM = ROOT / "data/external/prism_19q4/raw"
PAIR = ROOT / "research/eight_directions_20261026/evidence_audit/raw/PAIR_SCREEN.csv"


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def distribution(series):
    return {str(k): int(v) for k, v in series.value_counts().sort_index().items()}


def main():
    names = [
        "primary-screen-replicate-collapsed-treatment-info.csv",
        "primary-screen-cell-line-info.csv",
        "secondary-screen-replicate-treatment-info.csv",
        "secondary-screen-cell-line-info.csv",
        "secondary-screen-pooling-info.csv",
        "primary-screen-readme.txt", "secondary-screen-readme.txt",
    ]
    files = [PRISM / name for name in names] + [PAIR, HERE / "PROTOCOL.md", Path(__file__)]
    assert all(p.is_file() for p in files)
    assert all(not any(x in str(p).lower() for x in ["sealed", "vault", "reserve", "holdout"]) for p in files)
    primary = pd.read_csv(files[0], low_memory=False)
    pcells = pd.read_csv(files[1])
    secondary = pd.read_csv(files[2], low_memory=False)
    scells = pd.read_csv(files[3])
    pooling = pd.read_csv(files[4])
    readme = files[6].read_text(encoding="utf-8")
    assert "Technical redos for 147" in readme
    assert "Run ComBat for each treatment condition" in readme
    assert primary.column_name.is_unique and secondary.column_name.is_unique
    p = primary[primary.screen_id.eq("HTS") & primary.dose.eq(2.5)].copy()
    s = secondary[secondary.perturbation_type.eq("experimental_treatment")].copy()
    sg = s.groupby(["screen_id", "broad_id", "dose"], dropna=False).agg(
        detections=("detection_plate", "nunique"), compound_plates=("compound_plate", "nunique"),
        rows=("column_name", "size"), names=("name", "nunique"),
    )
    common = set(p.name.dropna().astype(str)) & set(s[s.dose.eq(2.5)].name.dropna().astype(str))
    exact_batches = set(p.broad_id.dropna()) & set(s[s.dose.eq(2.5)].broad_id.dropna())
    strict_p = pcells[pcells.passed_str_profiling.eq(True)]
    strict_s = scells[scells.passed_str_profiling.eq(True)]
    common_cells = set(strict_p.depmap_id.dropna()) & set(strict_s.depmap_id.dropna())
    assert len(common_cells) <= min(len(strict_p), len(strict_s))
    prism = {
        "primary_HTS_2_5_rows": len(p), "primary_HTS_2_5_drug_names": int(p.name.nunique()),
        "primary_STR_cell_metadata": int(strict_p.depmap_id.nunique()),
        "secondary_STR_cell_metadata": int(strict_s.depmap_id.nunique()),
        "shared_STR_cell_ids_nominal_not_measured_pairs": len(common_cells),
        "secondary_screen_rows": distribution(s.screen_id),
        "secondary_dose_unique_count": int(s.dose.nunique()),
        "secondary_dose_range_uM": [float(s.dose.min()), float(s.dose.max())],
        "primary_secondary_exact_2_5_common_names": len(common),
        "primary_secondary_exact_2_5_common_full_batch_ids": len(exact_batches),
        "secondary_condition_detection_plate_count": distribution(sg.detections),
        "secondary_condition_compound_plate_count": distribution(sg.compound_plates),
        "secondary_pool_screen_counts": distribution(pooling.screen_id),
        "MTS010_status": "technical_redo_147_per_original_readme_not_independent_biological_confirmation",
        "processing_risk": "replicate logfold change already ComBat corrected per treatment across pool-replicate batches; fold-pure preprocessing not certified",
        "limits": ["Metadata overlap does not certify finite matched response observations.",
                   "Same dose does not certify matched culture, exposure, assay or biological independence.",
                   "moa/target are annotations, not engagement or genetic perturbation measurements."],
    }
    columns = ["Well", "Cell line", "Drug 1", "Drug 2", "Conc 1 (uM)", "Conc 2 (uM)",
               "Failed QC", "Iteration", "file", "Plate"]
    raw = pd.read_csv(PAIR, usecols=columns, low_memory=False)
    assert "Viability" not in raw and "Raw count" not in raw
    d = raw[raw["Failed QC"].eq(False)].copy()
    missing = {str(k): int(v) for k, v in d[columns].isna().sum().items()}
    structural = [c for c in columns if c not in ["Conc 1 (uM)", "Conc 2 (uM)"]]
    assert not d[structural].isna().any().any(), "Missing structural keys."
    d["cell"] = d["Cell line"]
    # Missing control doses remain an explicit missing token, never imputed as 0 uM.
    left = list(zip(d["Drug 1"].astype(str), d["Conc 1 (uM)"].astype(str)))
    right = list(zip(d["Drug 2"].astype(str), d["Conc 2 (uM)"].astype(str)))
    pairs = [tuple(sorted([a, b])) for a, b in zip(left, right)]
    d["pair"] = [json.dumps(pair, separators=(",", ":")) for pair in pairs]
    controls = {"dmso", "high control", "low control"}
    combo = d[~d["Drug 1"].isin(controls) & ~d["Drug 2"].isin(controls)
              & d["Drug 1"].ne(d["Drug 2"])].copy()
    assert not combo[["Conc 1 (uM)", "Conc 2 (uM)"]].isna().any().any(), "Unknown drug dose."
    groups = combo.groupby(["cell", "Iteration", "pair"]).agg(
        wells=("Well", "size"), files=("file", "nunique"), plates=("Plate", "nunique"))
    pair_cells = combo.groupby("pair").cell.nunique()
    # Published prospective random validation is a distinct acquisition stage.
    # Verify its design separation explicitly; do not pool it into adaptation.
    training = combo[combo.Iteration.astype(str).isin([str(i) for i in range(1, 16)])]
    terminal = combo[combo.Iteration.eq("validation (random, round 15)")]
    train_keys = set(zip(training.cell, training.pair))
    terminal_keys = set(zip(terminal.cell, terminal.pair))
    overlap = sorted(train_keys & terminal_keys)
    pd.DataFrame(overlap, columns=["cell", "unordered_drug_dose_pair"]).to_csv(
        HERE / "validation_overlap_keys.csv", index=False)
    train_drugs = set(training["Drug 1"]) | set(training["Drug 2"])
    terminal_drugs = set(terminal["Drug 1"]) | set(terminal["Drug 2"])
    physical = d.groupby(["cell", "Iteration", "file", "Plate"]).agg(
        wells=("Well", "size"), unique_conditions=("pair", "nunique"))
    assert not physical.empty and not groups.empty
    census = {
        "raw_rows": len(raw), "QC_pass_rows": len(d), "QC_failed_rows": len(raw) - len(d),
        "missing_design_field_counts": missing,
        "cell_labels": sorted(d.cell.unique().tolist()),
        "unordered_combo_conditions_by_cell_iteration": len(groups),
        "unordered_drug_dose_pairs": int(combo.pair.nunique()),
        "cells_per_pair_distribution": distribution(pair_cells),
        "condition_file_count_distribution": distribution(groups.files),
        "condition_well_count_distribution": distribution(groups.wells),
        "observed_plate_groups": len(physical),
        "unique_conditions_per_observed_plate_quantiles": {
            str(q): float(v) for q, v in physical.unique_conditions.quantile([0, .25, .5, .75, 1]).items()},
        "condition_multi_file_count": int((groups.files >= 2).sum()),
        "stage_rows": distribution(d.Iteration.astype(str)),
        "random_validation": {
            "QC_combo_rows": len(terminal), "unique_cell_drug_dose_pair_keys": len(terminal_keys),
            "overlap_with_rounds_1_15": len(train_keys & terminal_keys),
            "distinct_validation_keys_after_overlap_exclusion": len(terminal_keys - train_keys),
            "cell_labels": sorted(terminal.cell.unique().tolist()),
            "new_cell_labels_vs_rounds_1_15": sorted(set(terminal.cell) - set(training.cell)),
            "new_drug_labels_vs_rounds_1_15": sorted(terminal_drugs - train_drugs),
            "status": "published_random_validation_design_checked_no_response_values_used",
            "limits": "same-source separate stage, not independent biological task or proof of unseen-cell/drug transfer; source exposure remains",
        },
        "duplicate_physical_well_keys": int(d.duplicated(["cell", "Iteration", "file", "Plate", "Well"]).sum()),
        "replicate_status": "file/plate/well alone do not identify independent culture batches",
        "action_status": "observed plate groups are accounting units, not validated purchasable menu; one archived label is not costed as one physical experiment",
        "limits": ["MG63 and MG-63 remain separate until authenticated.",
                   "Loaded columns lack exposure/time, engagement, genetic-perturbation or independent-endpoint linkage.",
                   "Iteration is a screen round; random splitting does not create independent endpoint or culture."],
    }
    result = {
        "experiment": "E001_metadata_qualification", "response_columns_loaded": False,
        "runtime": {"executable": sys.executable, "python": sys.version, "numpy": np.__version__, "pandas": pd.__version__},
        "inputs": {str(p.relative_to(ROOT)): {"bytes": p.stat().st_size, "sha256": sha(p)} for p in files},
        "prism": prism, "batchie": census,
        "gate": {
            "drug_context_crossing": "observed_design_metadata_not_complete_finite_endpoint_matrix",
            "orthogonal_target_reference": "not_qualified_for_matched_units",
            "independent_functional_endpoint": "not_qualified_for_matched_units",
            "independent_replicate_mapping": "not_qualified_from_loaded_metadata",
            "decision": "STOP_MECHANISTIC_MAIN_EXPERIMENT_AT_QUALIFICATION_GATE",
            "scientific_status": "unavailable_identification_evidence_not_refuted_biology",
            "baseline_model_and_policy_experiments": "NOT_RUN_gate_failed",
            "gain_confidence_interval": None, "CI_reason": "deterministic_census_no_gain_estimation",
            "meta_learning_RSI_promotion": "NOT_ADMITTED",
        },
    }
    (HERE / "qualification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"runtime": result["runtime"], "prism": prism, "batchie": census, "gate": result["gate"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
