"""SciPlex3 tier-B lineage: frozen episode -> design menu -> physical well -> control -> QC -> protocol reading.

File summary
- Path: research/identifiability_audit/lineage_sciplex3.py
- Purpose: for every (compound, action) of the frozen protocol-v2.1 SciPlex3 tier-B episodes, state
  separately what the *study design* planned, what the *raw release* records cell-by-cell, what the
  *prepared* condition table turned into a reading, and what the *protocol* inferred.
- Core points:
  - Four layers are never collapsed. `design_planned` comes from the frozen `design.py` table
    (obs metadata only). `raw_*` comes from the raw h5ad `obs` cell records. `prep_*` comes from the
    2026-09-26 prepared tables. `protocol_*` comes from the frozen e_data1 replay.
  - A design-planned condition with zero raw cells is `design_only_unverified`, never `not_executed`.
    The script additionally reports whether the same plate carried other compounds at that dose, as
    circumstantial layout evidence; it does not upgrade the label.
  - A planned condition with no usable prepared row carries the protocol's
    `measured_qc_failed` label, which is a protocol convention, not a laboratory receipt.
  - Controls are counted at the (cell line, time, replicate) level the shift was actually taken
    against, from the prepared well table's `is_control` rows.
- Run: python -m research.identifiability_audit.lineage_sciplex3 [--out DIR]
- Interfaces: `obs_cache`, `build`, `main`
- Depends on: h5py, pandas, numpy; research/protocol_v2/design.py; research/dynamic_world_model/common.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "biological_depth"))

TABLES = ROOT / "outputs" / "protocol_v2_1_20260927" / "e_data1" / "tables"
DESIGN = ROOT / "outputs" / "protocol_v2_1_20260927" / "design" / "sciplex3_design.csv"
PREPARED = ROOT / "outputs" / "dynamic_world_model_20260926" / "prepared"
RAW = ROOT / "data" / "raw" / "sciplex3" / "SrivatsanTrapnell2020_sciplex3.h5ad"
LINES = ("A549", "K562", "MCF7")
TIME_H = 24.0
MIN_CELLS = 20
OUT = ROOT / "outputs" / "identifiability_audit_20260930" / "sciplex3_B"

FIELD_BASIS = {
    "design_planned": "protocol-inferred (design.py expansion over raw obs metadata)",
    "raw_cells": "raw record (h5ad obs cell count)",
    "raw_plates": "raw record (h5ad obs plate)",
    "raw_wells": "raw record (h5ad obs well)",
    "raw_replicates": "raw record (h5ad obs replicate)",
    "raw_cells_rep1": "raw record (h5ad obs cell count for the rep1 well)",
    "raw_cells_rep2": "raw record (h5ad obs cell count for the rep2 well)",
    "prep_row": "derived (prepared conditions.csv)",
    "prep_replicates": "derived (prepared conditions.csv)",
    "prep_n_cells_rep1": "derived (prepared conditions.csv)",
    "prep_n_cells_rep2": "derived (prepared conditions.csv)",
    "prep_plate_rep1": "raw-derived (prepared carries obs plate/well)",
    "prep_well_rep1": "raw-derived (prepared carries obs plate/well)",
    "prep_plate_rep2": "raw-derived (prepared carries obs plate/well)",
    "prep_well_rep2": "raw-derived (prepared carries obs plate/well)",
    "qc_rule_passed": "protocol rule (replicates==2 and each rep >= 20 cells)",
    "control_wells_rep1": "derived (prepared wells.csv is_control at line|time|rep1)",
    "control_wells_rep2": "derived (prepared wells.csv is_control at line|time|rep2)",
    "protocol_lifecycle": "protocol label (e_data1 frozen table)",
    "protocol_readout": "protocol label (e_data1 frozen table)",
    "protocol_outcome": "protocol label (e_data1 frozen table)",
    "protocol_detected": "protocol rule (replicate agreement >= vehicle-well null q99)",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


# --------------------------------------------------------------------------------- raw obs cache
def obs_cache(path: Path = RAW, out: Path = OUT) -> pd.DataFrame:
    """The raw `obs` columns the audit needs, cached once as CSV (no matrix values are read)."""
    cached = out / "sciplex3_obs_cache.csv"
    if cached.is_file():
        return pd.read_csv(cached, dtype={"plate": str, "well": str, "replicate": str, "perturbation": str,
                                          "cell_line": str})
    import h5py

    from prepare import obs_column  # research/biological_depth/prepare.py
    out.mkdir(parents=True, exist_ok=True)
    with h5py.File(path, "r") as handle:
        obs = handle["obs"]
        frame = pd.DataFrame({name: obs_column(obs, name) for name in
                              ("cell_line", "perturbation", "dose_value", "time", "replicate", "plate", "well")})
    frame["time"] = frame.time.astype(float)
    frame["dose_value"] = frame.dose_value.astype(float)
    frame["compound"] = frame.perturbation.astype(str).str.strip()
    frame.to_csv(cached, index=False)
    return frame


# --------------------------------------------------------------------------------- loaders
def episode_tables(dataset_tier: str = "sciplex3_B") -> pd.DataFrame:
    """One row per frozen episode: compound, hypotheses, truth, and the per-action outcome table."""
    import gzip

    rows = []
    for path in sorted(TABLES.glob(f"{dataset_tier}_*.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            rows.extend(json.loads(line) for line in handle)
    return pd.DataFrame(rows)


def action_grid(frame: pd.DataFrame) -> pd.DataFrame:
    """(compound, action) rows with the protocol's lifecycle and reading, straight from the tables."""
    records = []
    seen = set()
    for row in frame.itertuples():
        for action, entry in row.outcomes.items():
            key = (row.compound, action)
            if key in seen:
                continue
            seen.add(key)
            line, t, dose = entry["key"]
            records.append({"compound": row.compound, "action": action, "cell_line": line,
                            "time": float(t), "dose": float(dose),
                            "protocol_lifecycle": entry["lifecycle"],
                            "protocol_readout": entry["readout"],
                            "protocol_outcome": entry["outcome"],
                            "in_episodes": True})
    return pd.DataFrame(records).sort_values(["compound", "cell_line", "dose"]).reset_index(drop=True)


# --------------------------------------------------------------------------------- build
def build(out: Path = OUT) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    episodes = episode_tables()
    grid = action_grid(episodes)
    compounds = sorted(grid.compound.unique())

    design = pd.read_csv(DESIGN)
    planned = {(r.compound, (r.cell_line, float(r.time), float(r.dose))) for r in design.itertuples()}

    conditions = pd.read_csv(PREPARED / "conditions.csv")
    conditions["compound"] = conditions.compound.astype(str).str.strip()
    prep = {(r.compound, (r.cell_line, float(r.time), float(r.dose))): r for r in conditions.itertuples()}

    wells = pd.read_csv(PREPARED / "wells.csv")
    wells["compound"] = wells.compound.astype(str).str.strip()
    controls = wells[wells.is_control]
    control_counts = (controls.groupby(["cell_line", "time", "replicate"]).size().to_dict())

    raw = obs_cache(out=out)
    raw_24 = raw[(raw.time == TIME_H) & (raw.cell_line.isin(LINES))]
    grouped = raw_24.groupby(["cell_line", "compound", "dose_value"])
    raw_cells = grouped.size()
    raw_plate = grouped.plate.apply(lambda s: sorted({str(x) for x in s}))
    raw_well = grouped.well.apply(lambda s: sorted({str(x) for x in s}))
    raw_rep = grouped.replicate.apply(lambda s: sorted({str(x) for x in s}))
    # per-replicate raw cell counts distinguish an absent well from a plated well with few survivors
    by_rep = raw_24.groupby(["cell_line", "compound", "dose_value", "replicate"]).size()
    # circumstantial layout evidence: cells that exist on the same plate at the same line/time/dose
    plate_dose = raw_24.groupby(["cell_line", "plate", "dose_value"]).size()

    def raw_get(key, table, default):
        try:
            return table.loc[key]
        except KeyError:
            return default

    records = []
    for row in grid.itertuples():
        key = (row.cell_line, row.time, row.dose)
        line, dose = row.cell_line, row.dose
        compound = row.compound
        cells = int(raw_get((line, compound, dose), raw_cells, 0))
        plates = raw_get((line, compound, dose), raw_plate, [])
        entry = prep.get((compound, key))
        qc = (int(entry.replicates) == 2 and entry.n_cells_rep1 >= MIN_CELLS and entry.n_cells_rep2 >= MIN_CELLS) \
            if entry is not None else False
        layout = 0
        for plate in plates:
            try:
                layout += int(plate_dose.loc[(line, str(plate), dose)])
            except KeyError:
                pass
        records.append({
            "compound": compound, "action": row.action, "cell_line": line, "time": row.time, "dose": dose,
            "in_episodes": True,
            "design_planned": (compound, key) in planned,
            "raw_cells": cells,
            "raw_plates": "|".join(plates),
            "raw_wells": "|".join(raw_get((line, compound, dose), raw_well, [])),
            "raw_replicates": "|".join(raw_get((line, compound, dose), raw_rep, [])),
            "raw_cells_rep1": int(raw_get((line, compound, dose, "rep1"), by_rep, 0)),
            "raw_cells_rep2": int(raw_get((line, compound, dose, "rep2"), by_rep, 0)),
            "same_plate_cells_at_dose": int(layout),
            "prep_row": entry is not None,
            "prep_replicates": int(entry.replicates) if entry is not None else 0,
            "prep_n_cells_rep1": int(entry.n_cells_rep1) if entry is not None else 0,
            "prep_n_cells_rep2": int(entry.n_cells_rep2) if entry is not None else 0,
            "prep_plate_rep1": str(entry.plate_rep1) if entry is not None else "",
            "prep_well_rep1": str(entry.well_rep1) if entry is not None else "",
            "prep_plate_rep2": str(entry.plate_rep2) if entry is not None else "",
            "prep_well_rep2": str(entry.well_rep2) if entry is not None else "",
            "qc_rule_passed": bool(qc),
            "control_wells_rep1": int(control_counts.get((line, TIME_H, "rep1"), 0)),
            "control_wells_rep2": int(control_counts.get((line, TIME_H, "rep2"), 0)),
            "protocol_lifecycle": row.protocol_lifecycle,
            "protocol_readout": row.protocol_readout,
            "protocol_outcome": row.protocol_outcome,
        })

    frame = pd.DataFrame(records)

    def status(r) -> str:
        if not r.design_planned:
            return "not_planned"
        if r.protocol_lifecycle == "measured_valid":
            return "result_valid"
        if r.protocol_lifecycle == "measured_qc_failed":
            return "qc_failed_protocol_label"
        if r.raw_cells == 0 and not r.prep_row:
            return "design_only_unverified"
        if r.raw_cells > 0 and not r.prep_row:
            return "physical_rows_dropped_before_reading"
        return "planned_no_protocol_row"

    frame["status"] = frame.apply(status, axis=1)
    frame["control_missing"] = (frame.control_wells_rep1 == 0) | (frame.control_wells_rep2 == 0)
    frame["physical_unit"] = frame.prep_row.astype(int)
    frame.to_csv(out / "action_source.csv", index=False)

    # ------------------------------------------------------------------ unlinkable reasons
    reasons = []
    for r in frame.itertuples():
        if r.status == "result_valid":
            continue
        if r.status == "design_only_unverified":
            reasons.append({"compound": r.compound, "action": r.action, "reason": "design_only_no_raw_cells",
                            "detail": f"design planned; h5ad obs has no cell at this compound x line x time x dose; "
                                      f"other compounds on the same plate(s) at this dose: {r.same_plate_cells_at_dose} cells",
                            "resolvable_by": "plate layout / source protocol record",
                            "evidence_level": "protocol-inferred design; absence of a raw row is not an execution receipt"})
        elif r.status == "qc_failed_protocol_label":
            absent = [name for name, value in (("rep1", r.raw_cells_rep1), ("rep2", r.raw_cells_rep2)) if value == 0]
            below = [name for name, value in (("rep1", r.raw_cells_rep1), ("rep2", r.raw_cells_rep2))
                     if 0 < value < MIN_CELLS]
            cause = ("replicate_well_absent_from_raw_obs:" + ",".join(absent) if absent else
                     "replicate_well_below_minimum_cells:" + ",".join(below))
            reasons.append({"compound": r.compound, "action": r.action, "reason": cause,
                            "detail": f"raw_cells_rep1={r.raw_cells_rep1} raw_cells_rep2={r.raw_cells_rep2} "
                                      f"prepared_replicates={r.prep_replicates} plate_rep2={r.prep_plate_rep2} "
                                      f"well_rep2={r.prep_well_rep2}",
                            "resolvable_by": ("a plate-layout record for the absent well" if absent else
                                              "a laboratory QC receipt for the named plate/well"),
                            "evidence_level": ("raw obs records no cell for that replicate well" if absent else
                                               "raw obs records cells, so cell survival is the outcome that "
                                               "dropped the row; the protocol label is a convention, not a receipt")})
        elif r.status == "physical_rows_dropped_before_reading":
            reasons.append({"compound": r.compound, "action": r.action, "reason": "raw_cells_without_prepared_row",
                            "detail": f"raw_cells={r.raw_cells}", "resolvable_by": "prepare.py exclusion ledger",
                            "evidence_level": "raw record present, prepared row absent"})
        elif r.status == "planned_no_protocol_row":
            reasons.append({"compound": r.compound, "action": r.action, "reason": "no_protocol_table_row",
                            "detail": f"raw_cells={r.raw_cells} prep_row={r.prep_row}",
                            "resolvable_by": "e_data1 table re-run", "evidence_level": "unknown"})
        else:
            reasons.append({"compound": r.compound, "action": r.action, "reason": "not_planned",
                            "detail": "", "resolvable_by": "", "evidence_level": "protocol-inferred design"})
    pd.DataFrame(reasons).to_csv(out / "unlinked_reasons.csv", index=False)

    # ------------------------------------------------------------------ per-action summary
    per_action = []
    for action, group in frame.groupby("action"):
        per_action.append({
            "action": action, "compounds": int(len(group)),
            "planned": int(group.design_planned.sum()),
            "raw_cell_records": int((group.raw_cells > 0).sum()),
            "prepared_rows": int(group.prep_row.sum()),
            "result_valid": int((group.status == "result_valid").sum()),
            "qc_failed_protocol_label": int((group.status == "qc_failed_protocol_label").sum()),
            "design_only_unverified": int((group.status == "design_only_unverified").sum()),
            "physical_rows_dropped_before_reading": int((group.status == "physical_rows_dropped_before_reading").sum()),
            "control_missing": int(group.control_missing.sum()),
            "unknown_or_other": int(group.status.isin(("not_planned", "planned_no_protocol_row")).sum()),
            "readings_eliminating": int((group.protocol_outcome.isin(("eliminate_a", "eliminate_b"))).sum()),
            "readings_undetected": int((group.protocol_outcome == "undetected").sum()),
            "readings_ambiguous": int((group.protocol_outcome == "ambiguous").sum()),
            "total_raw_cells": int(group.raw_cells.sum()),
            "distinct_plates": len({p for value in group.prep_plate_rep1 for p in str(value).split("|") if p} |
                                   {p for value in group.prep_plate_rep2 for p in str(value).split("|") if p}),
        })
    per_action = pd.DataFrame(per_action)
    per_action.to_csv(out / "action_summary.csv", index=False)

    summary = {
        "dataset_tier": "sciplex3:B",
        "episodes": int(len(episodes)),
        "episode_compounds": int(episodes.compound.nunique()),
        "actions": int(frame.action.nunique()),
        "grid_rows": int(len(frame)),
        "status_counts": frame.status.value_counts().to_dict(),
        "control_missing_rows": int(frame.control_missing.sum()),
        "readings": frame.protocol_outcome.value_counts().to_dict(),
        "distinct_plates_all_actions": int(per_action.distinct_plates.max()),
        "biological_units": {"unit_used_for_uncertainty": "Murcko scaffold (frozen compounds.csv `skeleton`)",
                             "unit_count": int(episodes.drop_duplicates(["compound"]).shape[0]),
                             "note": "cells and wells are not independent replicates of the compound"},
        "field_basis": FIELD_BASIS,
        "inputs": {
            "raw_h5ad": {"path": str(RAW.relative_to(ROOT)).replace("\\", "/"), "sha256": None,
                         "note": "2.46 GB; only obs columns were read, no matrix values"},
            "design_table": {"path": str(DESIGN.relative_to(ROOT)).replace("\\", "/"), "sha256": _sha256(DESIGN)},
            "prepared_conditions": {"path": "outputs/dynamic_world_model_20260926/prepared/conditions.csv",
                                    "sha256": _sha256(PREPARED / "conditions.csv")},
            "prepared_wells": {"path": "outputs/dynamic_world_model_20260926/prepared/wells.csv",
                               "sha256": _sha256(PREPARED / "wells.csv")},
            "e_data1_tables": {"path": "outputs/protocol_v2_1_20260927/e_data1/tables/sciplex3_B_*.jsonl.gz",
                               "rows": int(len(episodes))},
        },
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=1, default=str), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    summary = build(Path(args.out))
    print(json.dumps({k: v for k, v in summary.items() if k != "field_basis"}, indent=1, default=str))


if __name__ == "__main__":
    main()
