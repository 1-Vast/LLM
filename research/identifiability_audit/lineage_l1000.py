"""L1000 tier-LT lineage: frozen episode -> design menu -> inst_info well -> signature -> control -> QC.

File summary
- Path: research/identifiability_audit/lineage_l1000.py
- Purpose: for every (pert_id, action) of the frozen protocol-v2.1 L1000 tier-LT episodes, join the
  study design, the aggregated `conditions.json` entry, the physical `inst_info` wells, the Level 5
  signature records and the vehicle controls, and report what each layer can and cannot establish.
- Core points:
  - A `conditions.json` entry is an aggregate over `inst_info` wells: it is expanded here to
    `inst_id`, `rna_plate` and `rna_well`, and the expansion is checked against the entry's own
    `n_wells` / `n_plates` counts.
  - A Level 5 signature is an aggregated replicate-consensus record, not a physical measurement.
    Signature counts and instance counts are reported side by side and are never summed.
  - `qc` in the prepared table is a metadata rule (>=2 wells, >=2 plates, >=1 usable signature,
    finite cached profile); it is not a laboratory receipt.
  - Detection is Broad's own replicate statistic (`distil_cc_q75`) against a DMSO vehicle null of
    the same line and time; the null here is described, not re-fitted.
  - A count disagreement between the cache and `inst_info` is classified: `resolved` when a
    duplicated (rna_plate, rna_well) slot explains it, otherwise `unresolved_source_linkage`.
- Run: python -m research.identifiability_audit.lineage_l1000 [--out DIR]
- Interfaces: `build`, `main`
- Depends on: pandas, numpy; research/protocol_v2/design.py; research/sequence_audit/lincs_prepare.py
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "outputs" / "protocol_v2_1_20260927" / "e_data1" / "tables"
DESIGN = ROOT / "outputs" / "protocol_v2_1_20260927" / "design" / "l1000_design.csv"
DATA = ROOT / "data" / "external" / "lincs_l1000_phase1"
PREPARED = ROOT / "outputs" / "sequence_audit_20260926" / "l1000" / "prepared"
LINES = ("A549", "MCF7", "PC3", "VCAP")
TIMES = (6.0, 24.0)
DOSE_NM = 10000.0
OUT = ROOT / "outputs" / "identifiability_audit_20260930" / "l1000_LT"

FIELD_BASIS = {
    "design_planned": "protocol-inferred (design.py: at least one plated well in conditions.json)",
    "cache_entry": "derived (subset48/conditions.json aggregate over inst_info wells)",
    "cache_n_wells": "derived (conditions.json aggregate count)",
    "cache_n_plates": "derived (conditions.json aggregate count)",
    "inst_rows": "raw record (GSE92742 inst_info rows: one RNA well each)",
    "inst_plates": "raw record (inst_info rna_plate)",
    "inst_wells": "raw record (inst_info rna_well)",
    "inst_distinct_well_slots": "raw record (distinct inst_info rna_plate + rna_well)",
    "signatures": "raw record (GSE92742 sig_info Level 5 aggregates; not physical units)",
    "signature_nsample": "raw record (sig_metrics distil_nsample)",
    "cc_q75": "raw record (sig_metrics distil_cc_q75, replicate-consensus statistic)",
    "vehicle_signatures": "raw record (ctl_vehicle signatures at the same line and time)",
    "vehicle_inst_rows": "raw record (ctl_vehicle inst_info wells at the same line and time)",
    "prep_qc": "protocol rule (>=2 wells, >=2 plates, >=1 usable signature, finite cached profile)",
    "prep_detected": "protocol rule (cc_q75 >= max(0.10, vehicle-null 0.99 quantile))",
    "protocol_lifecycle": "protocol label (e_data1 frozen table)",
    "protocol_readout": "protocol label (e_data1 frozen table)",
    "protocol_outcome": "protocol label (e_data1 frozen table)",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def _episodes(prefix: str = "l1000_LT") -> pd.DataFrame:
    rows = []
    for path in sorted(TABLES.glob(f"{prefix}_*.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            rows.extend(json.loads(line) for line in handle)
    return pd.DataFrame(rows)


def _instances() -> pd.DataFrame:
    frame = pd.read_csv(DATA / "GSE92742_Broad_LINCS_inst_info.txt.gz", sep="\t", dtype=str)
    frame["pert_dose"] = pd.to_numeric(frame.pert_dose, errors="coerce")
    frame["pert_time"] = pd.to_numeric(frame.pert_time, errors="coerce")
    return frame[(frame.pert_type == "trt_cp") & (frame.pert_dose == 10.0)
                 & (frame.pert_time.isin(TIMES)) & (frame.cell_id.isin(LINES))]


def _signatures() -> pd.DataFrame:
    info = pd.read_csv(DATA / "GSE92742_Broad_LINCS_sig_info.txt.gz", sep="\t", dtype=str)
    metrics = pd.read_csv(DATA / "GSE92742_Broad_LINCS_sig_metrics.txt.gz", sep="\t", dtype=str)
    sig = info.merge(metrics[["sig_id", "distil_cc_q75", "distil_nsample", "distil_ss", "tas"]], on="sig_id",
                     how="left")
    sig["time"] = pd.to_numeric(sig.pert_itime.str.split().str[0], errors="coerce")
    sig["cc"] = pd.to_numeric(sig.distil_cc_q75, errors="coerce")
    sig["n"] = pd.to_numeric(sig.distil_nsample, errors="coerce")
    sig["batch"] = sig.sig_id.str.split("_").str[0]
    return sig


def build(out: Path = OUT) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    episodes = _episodes()
    grid: dict[tuple, dict] = {}
    for row in episodes.itertuples():
        for action, entry in row.outcomes.items():
            if (row.compound, action) in grid:
                continue
            line, t, dose = entry["key"]
            grid[(row.compound, action)] = {"compound": row.compound, "action": action, "cell_line": line,
                                            "time": float(t), "dose": float(dose),
                                            "protocol_lifecycle": entry["lifecycle"],
                                            "protocol_readout": entry["readout"],
                                            "protocol_outcome": entry["outcome"]}

    design = pd.read_csv(DESIGN)
    planned = {(r.compound, (r.cell_line, float(r.time), float(r.dose))) for r in design.itertuples()}

    cache = pd.DataFrame(json.loads((DATA / "subset48/conditions.json").read_text(encoding="utf-8")))
    cache["time"] = cache.time_h.astype(float)
    cache_index = {(r.pert_id, (r.cell_id, float(r.time), 10000.0)): r for r in cache.itertuples()
                   if r.cell_id in LINES and float(r.time) in TIMES and float(r.dose_um) == 10.0}

    inst = _instances()
    inst_groups = {}
    for (pert, cell, time), part in inst.groupby(["pert_id", "cell_id", "pert_time"]):
        inst_groups[(pert, (cell, float(time), DOSE_NM))] = part

    sig = _signatures()
    treated_sig = sig[(sig.pert_type == "trt_cp") & (sig.pert_idose == "10 \u00b5M") & (sig.time.isin(TIMES))
                      & (sig.cell_id.isin(LINES))]
    sig_groups = {}
    for (pert, cell, time), part in treated_sig.groupby(["pert_id", "cell_id", "time"]):
        sig_groups[(pert, (cell, float(time), DOSE_NM))] = part
    vehicle_sig = sig[(sig.pert_type == "ctl_vehicle") & (sig.time.isin(TIMES)) & (sig.cell_id.isin(LINES))]
    vehicle_counts = vehicle_sig.groupby(["cell_id", "time"]).size().to_dict()
    vehicle_inst = pd.read_csv(DATA / "GSE92742_Broad_LINCS_inst_info.txt.gz", sep="\t", dtype=str,
                               usecols=["pert_type", "pert_time", "cell_id"])
    vehicle_inst["pert_time"] = pd.to_numeric(vehicle_inst.pert_time, errors="coerce")
    vehicle_inst = vehicle_inst[(vehicle_inst.pert_type == "ctl_vehicle")
                                & (vehicle_inst.pert_time.isin(TIMES)) & (vehicle_inst.cell_id.isin(LINES))]
    vehicle_wells = vehicle_inst.groupby(["cell_id", "pert_time"]).size().to_dict()

    prepared = pd.read_csv(PREPARED / "conditions.csv")
    prep_index = {(r.compound, (r.cell_line, float(r.time), float(r.dose))): r for r in prepared.itertuples()}

    records = []
    for (compound, action), base in sorted(grid.items()):
        key = (base["cell_line"], base["time"], DOSE_NM)
        entry = cache_index.get((compound, key))
        part = inst_groups.get((compound, key))
        sigs = sig_groups.get((compound, key))
        prep = prep_index.get((compound, key))
        inst_rows = 0 if part is None else int(len(part))
        inst_plates = 0 if part is None else int(part.rna_plate.nunique())
        n_sig = 0 if sigs is None else int(len(sigs))
        usable = 0 if sigs is None else int(((sigs.n >= 2) & (sigs.cc > -600)).sum())
        cc = float(np.nanmedian(sigs.cc.to_numpy(dtype=float))) if sigs is not None and len(sigs) else float("nan")
        nsample = float(np.nanmedian(sigs.n.to_numpy(dtype=float))) if sigs is not None and len(sigs) else float("nan")
        records.append({
            **base,
            "design_planned": (compound, key) in planned,
            "cache_entry": entry is not None,
            "cache_n_wells": int(entry.n_wells) if entry is not None else 0,
            "cache_n_plates": int(entry.n_plates) if entry is not None else 0,
            "cache_batches": "|".join(entry.batches) if entry is not None else "",
            "inst_rows": inst_rows,
            "inst_plates": inst_plates,
            "inst_wells": 0 if part is None else int(part.rna_well.nunique()),
            "inst_ids": "|".join(sorted(part.inst_id)[:8]) if part is not None else "",
            "inst_plate_names": "|".join(sorted(set(part.rna_plate))) if part is not None else "",
            "inst_well_names": "|".join(sorted(set(part.rna_well))) if part is not None else "",
            "inst_distinct_well_slots": 0 if part is None else int(part[["rna_plate", "rna_well"]]
                                                                   .drop_duplicates().shape[0]),
            "signatures": n_sig,
            "signatures_usable": usable,
            "signature_nsample": nsample,
            "cc_q75": cc,
            "vehicle_signatures": int(vehicle_counts.get((base["cell_line"], base["time"]), 0)),
            "vehicle_inst_rows": int(vehicle_wells.get((base["cell_line"], base["time"]), 0)),
            "prep_row": prep is not None,
            "prep_qc": bool(prep.qc) if prep is not None else False,
            "prep_detected": bool(prep.detected) if prep is not None else False,
            "prep_n_wells": int(prep.n_wells) if prep is not None else 0,
            "prep_n_plates": int(prep.n_plates) if prep is not None else 0,
            "prep_plates": str(prep.plates) if prep is not None else "",
        })
    frame = pd.DataFrame(records)
    frame["cache_expansion_agrees"] = frame.cache_n_wells == frame.inst_rows
    frame["cache_plate_agrees"] = frame.cache_n_plates == frame.inst_plates
    frame["cache_vs_distinct_slots_agrees"] = frame.cache_n_wells == frame.inst_distinct_well_slots
    frame["duplicate_well_slots"] = frame.inst_rows - frame.inst_distinct_well_slots

    def status(r) -> str:
        if not r.design_planned:
            return "not_planned"
        if r.protocol_lifecycle == "measured_valid":
            return "result_valid"
        if r.protocol_lifecycle == "measured_qc_failed":
            return "qc_failed_protocol_label"
        if r.inst_rows == 0:
            return "design_only_unverified"
        return "planned_no_protocol_row"

    frame["status"] = frame.apply(status, axis=1)
    frame["control_missing"] = frame.vehicle_signatures == 0
    frame.to_csv(out / "action_source.csv", index=False)

    reasons = []
    for r in frame.itertuples():
        if r.status == "result_valid" and r.cache_expansion_agrees:
            continue
        if r.status == "result_valid" and not r.cache_expansion_agrees:
            reasons.append({"compound": r.compound, "action": r.action,
                            "reason": "cache_instance_count_disagreement",
                            "linkage": ("resolved_duplicate_well_slot" if r.duplicate_well_slots > 0
                                        and r.cache_vs_distinct_slots_agrees
                                        else "unresolved_source_linkage"),
                            "detail": f"conditions.json n_wells={r.cache_n_wells} inst_info rows={r.inst_rows} "
                                      f"distinct plate+well slots={r.inst_distinct_well_slots} "
                                      f"duplicate slots={r.duplicate_well_slots}",
                            "resolvable_by": "re-derive the subset48 cache from the current inst_info",
                            "evidence_level": "raw records disagree; the condition's well count is not "
                                              "uniquely determined by the local files"})
            continue
        if r.status == "qc_failed_protocol_label":
            detail = (f"inst_rows={r.inst_rows} inst_plates={r.inst_plates} signatures={r.signatures} "
                      f"usable_signatures={r.signatures_usable} prep_n_wells={r.prep_n_wells} "
                      f"prep_n_plates={r.prep_n_plates} cc_q75={r.cc_q75}")
            causes = []
            if r.prep_n_wells < 2:
                causes.append("fewer_than_two_wells")
            if r.prep_n_plates < 2:
                causes.append("fewer_than_two_plates")
            if r.signatures_usable < 1:
                causes.append("no_signature_with_at_least_two_replicates")
            reasons.append({"compound": r.compound, "action": r.action,
                            "reason": "prepared_qc_rule_failed:" + "|".join(causes or ["cached_profile_not_finite"]),
                            "linkage": "resolved",
                            "detail": detail,
                            "resolvable_by": "inst_info well list and Broad signature metrics (both local)",
                            "evidence_level": "metadata QC rule; no laboratory receipt"})
        elif r.status == "design_only_unverified":
            reasons.append({"compound": r.compound, "action": r.action, "reason": "design_planned_no_instance",
                            "linkage": "unresolved_source_linkage",
                            "detail": f"cache_n_wells={r.cache_n_wells} inst_rows=0",
                            "resolvable_by": "inst_info / plate layout record",
                            "evidence_level": "design-only; absence of an inst_info row is not an execution receipt"})
        else:
            reasons.append({"compound": r.compound, "action": r.action, "reason": r.status,
                            "linkage": "unresolved_source_linkage", "detail": "",
                            "resolvable_by": "", "evidence_level": "unknown"})
    pd.DataFrame(reasons).to_csv(out / "unlinked_reasons.csv", index=False)

    per_action = []
    for action, group in frame.groupby("action"):
        per_action.append({
            "action": action, "compounds": int(len(group)),
            "planned": int(group.design_planned.sum()),
            "inst_rows": int(group.inst_rows.sum()),
            "distinct_rna_plates": len({p for value in group.inst_plate_names for p in str(value).split("|") if p}),
            "signatures": int(group.signatures.sum()),
            "result_valid": int((group.status == "result_valid").sum()),
            "qc_failed_protocol_label": int((group.status == "qc_failed_protocol_label").sum()),
            "design_only_unverified": int((group.status == "design_only_unverified").sum()),
            "control_missing": int(group.control_missing.sum()),
            "unknown_or_other": int(group.status.isin(("not_planned", "planned_no_protocol_row")).sum()),
            "readings_eliminating": int(group.protocol_outcome.isin(("eliminate_a", "eliminate_b")).sum()),
            "readings_undetected": int((group.protocol_outcome == "undetected").sum()),
            "readings_ambiguous": int((group.protocol_outcome == "ambiguous").sum()),
            "cache_expansion_disagreements": int((~group.cache_expansion_agrees).sum()),
            "cache_plate_disagreements": int((~group.cache_plate_agrees).sum()),
            "median_wells_per_condition": float(group.inst_rows.median()),
        })
    per_action = pd.DataFrame(per_action)
    per_action.to_csv(out / "action_summary.csv", index=False)

    unresolved = int(sum(1 for r in reasons if r.get("linkage") == "unresolved_source_linkage"))
    resolved = len(reasons) - unresolved
    summary = {
        "dataset_tier": "l1000:LT",
        "episodes": int(len(episodes)),
        "episode_compounds": int(episodes.compound.nunique()),
        "actions": int(frame.action.nunique()),
        "grid_rows": int(len(frame)),
        "status_counts": frame.status.value_counts().to_dict(),
        "control_missing_rows": int(frame.control_missing.sum()),
        "readings": frame.protocol_outcome.value_counts().to_dict(),
        "cache_expansion_disagreements_total": int((~frame.cache_expansion_agrees).sum()),
        "cache_plate_disagreements_total": int((~frame.cache_plate_agrees).sum()),
        "source_linkage": {"unresolved_source_linkage": unresolved, "resolved": resolved,
                           "note": "an unresolved row means the local files disagree on how many physical "
                                   "wells a condition has and the audit did not settle it"},
        "aggregate_warning": ("a Level 5 signature is an aggregated replicate-consensus record; "
                              "signatures are never counted as physical units and are never added to inst_rows"),
        "biological_units": {"physical_unit": "inst_info RNA well (rna_plate + rna_well)",
                             "replicate_unit": "distinct RNA plate of the same pert_id x cell x time x dose",
                             "unit_used_for_uncertainty": "InChIKey connectivity block (compounds.csv `identity`)",
                             "unit_count": int(episodes.drop_duplicates(["compound"]).shape[0])},
        "field_basis": FIELD_BASIS,
        "inputs": {
            "inst_info": {"path": "data/external/lincs_l1000_phase1/GSE92742_Broad_LINCS_inst_info.txt.gz",
                          "sha256": _sha256(DATA / "GSE92742_Broad_LINCS_inst_info.txt.gz")},
            "sig_info": {"path": "data/external/lincs_l1000_phase1/GSE92742_Broad_LINCS_sig_info.txt.gz",
                         "sha256": _sha256(DATA / "GSE92742_Broad_LINCS_sig_info.txt.gz")},
            "sig_metrics": {"path": "data/external/lincs_l1000_phase1/GSE92742_Broad_LINCS_sig_metrics.txt.gz",
                            "sha256": _sha256(DATA / "GSE92742_Broad_LINCS_sig_metrics.txt.gz")},
            "conditions_json": {"path": "data/external/lincs_l1000_phase1/subset48/conditions.json",
                                "sha256": _sha256(DATA / "subset48" / "conditions.json")},
            "design_table": {"path": "outputs/protocol_v2_1_20260927/design/l1000_design.csv",
                             "sha256": _sha256(DESIGN)},
            "prepared_conditions": {"path": "outputs/sequence_audit_20260926/l1000/prepared/conditions.csv",
                                    "sha256": _sha256(PREPARED / "conditions.csv")},
            "e_data1_tables": {"path": "outputs/protocol_v2_1_20260927/e_data1/tables/l1000_LT_*.jsonl.gz",
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
