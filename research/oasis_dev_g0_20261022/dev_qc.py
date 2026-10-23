"""Outcome-gated OASIS development export and technical-repeat qualification.

Only this worker sees raw source pages. Optimisation consumes its dev-only export.
Parquet can decode mixed-role pages internally; this is not a security sandbox.
"""
from __future__ import annotations

import os
for variable in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[variable] = "4"

import collections
import hashlib
import json
from pathlib import Path
import platform
import re
import sys
import time

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/oasis_dev_g0"
SOURCE = ROOT / "log/20261021/oasis_source_qualification"
IDENTITY = ROOT / "log/20261021/oasis_identity_qualification"
RESERVATION = ROOT / "log/20261021/oasis_evaluation_contract/RESERVATION_v2.json"
RAW = ["mtt_lumi", "ldh_abs_signal", "ldh_abs_background", "ldh_abs"]
IDCOLS = ["source", "plate", "well", "compound_name", "compound_concentration_um", "library"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")


def compound_id(name):
    return hashlib.sha256(str(name).encode()).hexdigest()[:20]


def well_key(source, plate, well):
    match = re.fullmatch(r"([A-Za-z]+)0*(\d+)", str(well))
    if not match:
        raise ValueError("Invalid physical well")
    return str(source).removeprefix("assayworks_"), str(plate), f"{match[1].upper()}{int(match[2]):02d}"


def authenticate(path, expected):
    if sha(path) != expected:
        raise ValueError(f"Source checksum mismatch: {path.name}")


def scan_allowed(path, names, columns, compound_column):
    """Predicate scan: export rows before any optimiser receives numeric arrays."""
    return pq.read_table(path, columns=columns,
                         filters=[(compound_column, "in", sorted(names))]).to_pandas()


def deduplicate(frame, numeric):
    frame = frame.copy()
    frame["key"] = [well_key(*x) for x in frame[["source", "plate", "well"]].itertuples(index=False, name=None)]
    for _, group in frame.groupby("key", sort=False):
        if len(group) > 1:
            check = ["compound_name", "compound_concentration_um", *numeric]
            if any(group[column].nunique(dropna=False) > 1 for column in check):
                raise ValueError("Conflicting duplicate physical well")
    return frame.drop_duplicates("key").copy()


def plate_controls(frame):
    records = []
    for ident, rows in frame.groupby(["batch", "plate"], sort=True):
        controls = rows[rows["is_dmso"]]
        mt = controls["mtt_lumi"].to_numpy(float)
        ld = controls["ldh_abs"].to_numpy(float)
        med_mt = float(np.median(mt)) if len(mt) else np.nan
        med_ld = float(np.median(ld)) if len(ld) else np.nan
        mad_mt = float(1.4826 * np.median(np.abs(mt - med_mt))) if len(mt) else np.nan
        mad_ld = float(1.4826 * np.median(np.abs(ld - med_ld))) if len(ld) else np.nan
        cv = mad_mt / med_mt if med_mt > 0 else np.nan
        reasons = []
        if len(controls) < 8:
            reasons.append("DMSO_LT_8")
        if not (np.isfinite(mt).all() and med_mt > 0 and np.isfinite(cv) and cv <= .25):
            reasons.append("MT_CONTROL_QC")
        if not (np.isfinite(ld).all() and np.isfinite(mad_ld) and mad_ld > 0):
            reasons.append("LDH_CONTROL_QC")
        count = controls["cell_count"].to_numpy(float)
        finite = np.isfinite(count) & (count >= 0)
        count_center = float(np.median(np.log1p(count[finite]))) if finite.any() else np.nan
        records.append({"batch": ident[0], "plate": ident[1], "dmso_wells": len(controls),
                        "mt_median": med_mt, "mt_robust_cv": cv, "ldh_median": med_ld,
                        "ldh_mad_scale": mad_ld, "count_log_center": count_center,
                        "plate_pass": not reasons, "failure_reasons": "|".join(reasons)})
    return pd.DataFrame(records)


def normalise(frame, controls):
    result = frame.merge(controls, on=["batch", "plate"], validate="many_to_one")
    valid = (result["plate_pass"] & np.isfinite(result[RAW]).all(axis=1)
             & (result["mtt_lumi"] > 0) & np.isfinite(result["cell_count"])
             & (result["cell_count"] >= 0) & np.isfinite(result["count_log_center"]))
    result["observation_pass"] = valid
    result["mt_target"] = np.nan
    result["ldh_target"] = np.nan
    result["count_input"] = np.nan
    result.loc[valid, "mt_target"] = np.log2(result.loc[valid, "mtt_lumi"] / result.loc[valid, "mt_median"])
    result.loc[valid, "ldh_target"] = np.arcsinh((result.loc[valid, "ldh_abs"] - result.loc[valid, "ldh_median"])
                                               / result.loc[valid, "ldh_mad_scale"])
    result.loc[valid, "count_input"] = np.log1p(result.loc[valid, "cell_count"]) - result.loc[valid, "count_log_center"]
    return result


def pairs_for_repeat(frame):
    pairs = []
    for _, rows in frame.groupby(["compound_id", "dose_um"], sort=True):
        rows = rows.sort_values(["batch", "plate", "well"]).drop_duplicates(["batch", "plate"])
        if len(rows) < 2:
            continue
        first, second = rows.iloc[0], rows.iloc[1]
        record = {"compound_id": first["compound_id"], "group_id": first["group_id"],
                  "dose_um": float(first["dose_um"]), "plate_1": first["plate"], "plate_2": second["plate"],
                  "batch_1": first["batch"], "batch_2": second["batch"],
                  "same_batch": first["batch"] == second["batch"], "available_plates": len(rows),
                  "pair_pass": bool(first.get("observation_pass", True) and second.get("observation_pass", True))}
        for endpoint in ("mt", "ldh"):
            record[f"{endpoint}_1"] = float(first[f"{endpoint}_target"])
            record[f"{endpoint}_2"] = float(second[f"{endpoint}_target"])
        pairs.append(record)
    return pd.DataFrame(pairs)


def repeat_summary(pairs, draws=2000):
    total_pairs = len(pairs)
    if not pairs.empty:
        pairs = pairs[pairs["pair_pass"]].reset_index(drop=True)
    if pairs.empty:
        return {"paired_groups": 0, "paired_actions": 0, "identity_pair_actions": total_pairs,
                "qc_failed_pair_actions": total_pairs, "endpoints": {}, "pass": False}
    groups = sorted(pairs["group_id"].unique())
    group_rows = [np.flatnonzero(pairs["group_id"].to_numpy() == x) for x in groups]
    rng = np.random.default_rng(20261022)
    indices = [np.concatenate([group_rows[i] for i in rng.integers(len(groups), size=len(groups))]) for _ in range(draws)]
    report = {"paired_groups": len(groups), "paired_actions": len(pairs),
              "identity_pair_actions": total_pairs, "qc_failed_pair_actions": total_pairs - len(pairs),
              "endpoints": {}, "interval_scope": "Conditional on this screen's observed plates and controls"}
    for endpoint in ("mt", "ldh"):
        values = pairs[[f"{endpoint}_1", f"{endpoint}_2"]].to_numpy(float)
        variance = float(np.var(values))
        if variance <= 0 or any(np.ptp(values[:, i]) == 0 for i in (0, 1)):
            report["endpoints"][endpoint] = {"spearman": None, "group_bootstrap_95": None,
                "squared_repeat_discrepancy_over_variance": None, "pass": False, "reason": "NO_DYNAMIC_RANGE"}
            continue
        correlation = float(spearmanr(values[:, 0], values[:, 1]).statistic)
        samples = np.asarray([spearmanr(values[ix, 0], values[ix, 1]).statistic for ix in indices])
        finite = samples[np.isfinite(samples)]
        interval = np.quantile(finite, [.025, .975]).tolist() if len(finite) else None
        report["endpoints"][endpoint] = {"spearman": correlation if np.isfinite(correlation) else None,
            "group_bootstrap_95": interval, "valid_bootstrap_fraction": len(finite) / draws,
            "squared_repeat_discrepancy_over_variance": float(np.mean(np.diff(values, axis=1)**2) / variance),
            "pass": bool(np.isfinite(correlation) and correlation >= .60 and interval is not None
                         and interval[0] > .50 and len(finite) >= .95 * draws)}
    report["pass"] = len(groups) >= 100 and all(x["pass"] for x in report["endpoints"].values())
    return report


def main():
    start, cpu = time.perf_counter(), time.process_time()
    if (OUT / "DEV_QC.json").exists() or (OUT / "dev_wells.parquet").exists():
        raise RuntimeError("Existing numeric output; replay in a new directory, do not overwrite")
    reservation = load_json(RESERVATION)
    mapping = {x["compound_id"]: x for x in reservation["mapping"]}
    identities = load_json(IDENTITY / "IDENTITY_ROWS.json")
    dev_names = {x["compound_name"] for x in identities if mapping.get(x["compound_id"], {}).get("role") == "dev"}
    names = dev_names | {"DMSO"}
    manifest = load_json(SOURCE / "SOURCE_MANIFEST.json")
    frames = []
    for item in manifest:
        path = ROOT / item["local_path"]
        authenticate(path, item["sha256"])
        frames.append(scan_allowed(path, names, IDCOLS + RAW, "compound_name"))
    frame = deduplicate(pd.concat(frames, ignore_index=True), RAW)
    frame["batch"] = [x[0] for x in frame["key"]]
    frame["well"] = [x[2] for x in frame["key"]]
    frame["compound_id"] = frame["compound_name"].map(compound_id)
    frame["is_dmso"] = frame["compound_name"].eq("DMSO")
    frame["role"] = ["control" if c else mapping[x]["role"] for c, x in zip(frame["is_dmso"], frame["compound_id"])]
    if set(frame["role"]) - {"dev", "control"}:
        raise ValueError("Forbidden outcome role")
    frame["group_id"] = [None if c else mapping[x]["group_id"] for c, x in zip(frame["is_dmso"], frame["compound_id"])]
    frame = frame.rename(columns={"compound_concentration_um": "dose_um"})
    meta_manifest = load_json(IDENTITY / "NEW_SOURCE_MANIFEST.json")
    meta_item = next(x for x in meta_manifest["files"] if x["name"] == "metadata.parquet")
    meta_path = ROOT / meta_item["local_path"]
    authenticate(meta_path, meta_item["sha256"])
    columns = ["Metadata_source", "Metadata_Plate", "Metadata_Well", "Metadata_Compound", "Metadata_Concentration", "Metadata_Count_Cells"]
    meta = scan_allowed(meta_path, names, columns, "Metadata_Compound")
    meta["key"] = [well_key(*x) for x in meta[columns[:3]].itertuples(index=False, name=None)]
    for _, group in meta.groupby("key", sort=False):
        if any(group[c].nunique(dropna=False) > 1 for c in columns[3:]):
            raise ValueError("Conflicting metadata physical well")
    meta = meta.drop_duplicates("key").rename(columns={"Metadata_Count_Cells": "cell_count"})
    frame = frame.merge(meta[["key", "cell_count", "Metadata_Compound", "Metadata_Concentration"]],
                        on="key", how="left", validate="one_to_one")
    joined = frame["Metadata_Compound"].notna()
    if not (frame.loc[joined, "compound_name"].eq(frame.loc[joined, "Metadata_Compound"]).all()
            and frame.loc[joined, "dose_um"].eq(frame.loc[joined, "Metadata_Concentration"]).all()):
        raise ValueError("Raw/count condition identity disagreement")
    controls = plate_controls(frame)
    normalised = normalise(frame, controls)
    dev = normalised[~normalised["is_dmso"]].copy()
    eligible = dev[dev["observation_pass"]].copy()
    eligible["fold"] = [int(hashlib.sha256(("oasis_g0_20261022|" + x).encode()).hexdigest()[:16], 16) % 5
                        for x in eligible["group_id"]]
    pairs = pairs_for_repeat(dev)
    repeats = repeat_summary(pairs)
    coverage = len(eligible) / len(dev)
    report = {"scope": "Dev plus DMSO only; technical repeat, not independent biological replication",
              "dev_labels": int(dev["compound_id"].nunique()), "dev_groups": int(dev["group_id"].nunique()),
              "dev_raw_wells": len(dev), "eligible_dev_wells": len(eligible), "eligible_fraction": coverage,
              "missing_count_wells": int(dev["cell_count"].isna().sum()),
              "plates": len(controls), "failing_plates": int((~controls["plate_pass"]).sum()),
              "failed_observations": int((~dev["observation_pass"]).sum()), "repeat": repeats,
              "g0a_pass": coverage >= .9 and repeats["pass"], "selection_exported": False,
              "reserve_exported": False, "quarantine_exported": False,
              "physical_mixed_page_decode_possible": True,
              "raw_ldh_net_identity_max_abs_difference": float(np.max(np.abs(frame["ldh_abs_signal"] - frame["ldh_abs_background"] - frame["ldh_abs"]))),
              "fold_group_counts": eligible.groupby("fold")["group_id"].nunique().to_dict()}
    controls.to_csv(OUT / "plate_controls.csv", index=False)
    dev.drop(columns=["key"]).to_parquet(OUT / "dev_wells_all_qc.parquet", index=False)
    eligible.drop(columns=["key"]).to_parquet(OUT / "dev_wells.parquet", index=False)
    pairs.to_csv(OUT / "technical_repeat_pairs.csv", index=False)
    save_json(OUT / "DEV_QC.json", report)
    try:
        import psutil
        memory = psutil.Process().memory_info()
        peak = getattr(memory, "peak_wset", None)
    except ImportError:
        peak = None
    save_json(OUT / "QC_RESOURCES.json", {"wall_seconds": time.perf_counter() - start,
        "process_cpu_seconds": time.process_time() - cpu, "peak_working_set_bytes": peak,
        "python": sys.version, "platform": platform.platform(), "numpy": np.__version__, "pandas": pd.__version__,
        "api_calls": 0, "gpu_used": False, "new_download_bytes": 0, "unmetered_web_agent_cost": "unknown"})
    print(json.dumps(report, allow_nan=False))


if __name__ == "__main__":
    main()
