"""Direct mono wells, plate-local controls, target exclusion, sparse dose support."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from research.astra.functional_data_20261007.acquire import EXPECTED, HERE, RAW, ROOT
from research.astra.drylab_followup_20261007.reproduce import load_replay
from research.astra.drylab_followup_20261007.tier_a import dose_vectors

COLS = ["BARCODE", "POSITION", "SANGER_MODEL_ID", "CELL_ID", "DATE_CREATED", "RESEARCH_PROJECT",
        "ASSAY", "DURATION", "SEEDING_DENSITY", "TAG", "DRUG_ID", "CONC", "INTENSITY"]
META = ["BARCODE", "sidm", "cell_id", "event", "tissue", "project", "assay", "seed_to_read_days", "seeding_density"]
DESIGN_SOURCE = ROOT / "data/external/gdsc_combinations/jaaks2022_figshare/original_screen_all_tissues_fitted.csv"


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def plate_mono(frame, tissue):
    """No combo well is normalized or exported by this extractor."""
    f = frame.copy()
    for name in ["SANGER_MODEL_ID", "CELL_ID", "DATE_CREATED", "RESEARCH_PROJECT", "ASSAY", "DURATION", "SEEDING_DENSITY"]:
        if f[name].isna().any() or f[name].nunique(dropna=False) != 1:
            return None, {"reason": "nonunique_or_missing_plate_metadata", "field": name}
    if f.groupby("POSITION").INTENSITY.nunique(dropna=False).gt(1).any():
        return None, {"reason": "inconsistent_same_well_intensity"}
    def controls(tag):
        return f[f.TAG.eq(tag)].drop_duplicates("POSITION").INTENSITY.to_numpy(float)
    blank, nc = controls("B"), controls("NC-1")
    if len(blank) < 3 or len(nc) < 3 or not np.isfinite(np.concatenate([blank, nc])).all():
        return None, {"reason": "missing_or_nonfinite_controls"}
    bm, nm = float(blank.mean()), float(nc.mean())
    if nm <= 0 or nm <= bm:
        return None, {"reason": "invalid_normalization_denominator"}
    cv = float(nc.std(ddof=1) / nm)
    zfactor = float(1 - 3 * (nc.std(ddof=1) + blank.std(ddof=1)) / (nm - bm))
    if cv > .18 or zfactor < .3:
        return None, {"reason": "plate_control_qc", "nc_cv": cv, "zfactor": zfactor}
    single = f[f.TAG.str.fullmatch(r"A\d+-S|L\d+-D\d+-S", na=False)].copy()
    single = single.drop_duplicates(["POSITION", "DRUG_ID", "CONC", "TAG", "INTENSITY"])
    ambiguous = single.POSITION.duplicated(keep=False) | single.DRUG_ID.str.contains("|", regex=False, na=False)
    bad_identity = single.DRUG_ID.isna() | single.CONC.isna()
    omitted = int((ambiguous | bad_identity).sum())
    single = single[~(ambiguous | bad_identity)].copy()
    single["dose_uM"] = pd.to_numeric(single.CONC, errors="coerce")
    single["viability"] = (pd.to_numeric(single.INTENSITY, errors="coerce") - bm) / (nm - bm)
    finite = np.isfinite(single[["dose_uM", "viability"]]).all(axis=1) & single.dose_uM.gt(0)
    omitted += int((~finite).sum())
    single = single[finite].copy()
    single["role"] = np.where(single.TAG.str.startswith("A"), "anchor", "library")
    z = single.groupby(["DRUG_ID", "role", "dose_uM"], as_index=False).agg(
        viability=("viability", "mean"), well_sd=("viability", "std"), wells=("POSITION", "nunique"))
    z = z.rename(columns={"DRUG_ID": "drug_id"})
    metadata = {"BARCODE": str(f.BARCODE.iloc[0]), "sidm": str(f.SANGER_MODEL_ID.iloc[0]),
                "cell_id": str(f.CELL_ID.iloc[0]), "event": str(f.DATE_CREATED.iloc[0]),
                "tissue": tissue, "project": str(f.RESEARCH_PROJECT.iloc[0]),
                "assay": str(f.ASSAY.iloc[0]), "seed_to_read_days": int(float(f.DURATION.iloc[0])),
                "seeding_density": float(f.SEEDING_DENSITY.iloc[0])}
    for k, v in metadata.items():
        z[k] = v
    z["nc_cv"], z["zfactor"] = cv, zfactor
    return z[META + ["drug_id", "role", "dose_uM", "viability", "well_sd", "wells", "nc_cv", "zfactor"]], {
        "reason": "PASS", "omitted_ambiguous_or_invalid_rows": omitted, "single_wells": int(single.POSITION.nunique())}


def summarize_curves(points):
    records = []
    keys = ["sidm", "cell_id", "event", "tissue", "assay", "seed_to_read_days", "seeding_density", "drug_id", "role"]
    # Average technical plates in an event before independent-cell summaries.
    event = points.groupby(keys + ["dose_uM"], as_index=False).agg(
        viability=("viability", "mean"), plates=("BARCODE", "nunique"), wells=("wells", "sum"))
    for key, g in event.groupby(keys):
        g = g.sort_values("dose_uM")
        dose, y = g.dose_uM.to_numpy(), g.viability.to_numpy()
        area = float(np.trapezoid(y, np.log2(dose)) / np.log2(dose[-1] / dose[0])) if len(g) >= 3 else None
        slope = float((y[-1] - y[-2]) / np.log2(dose[-1] / dose[-2])) if len(g) >= 2 else None
        records.append(dict(zip(keys, key), n_doses=len(g), min_dose_uM=dose[0], max_dose_uM=dose[-1],
                            top_viability=y[-1], observed_range_area=area, top_adjacent_change=slope,
                            monotone_violations=int((np.diff(y) > .1).sum()),
                            outside_zero_one=int(((y < 0) | (y > 1)).sum()), plates=int(g.plates.max())))
    return event, pd.DataFrame(records)


def interpolate_observed(doses, values, requested):
    order = np.argsort(doses)
    x, y = np.asarray(doses, float)[order], np.asarray(values, float)[order]
    if not len(x) or not np.isfinite(x).all() or not np.isfinite(y).all() or requested <= 0:
        return None
    exact = np.flatnonzero(np.isclose(x, requested, rtol=1e-8, atol=0))
    if len(exact):
        return float(y[exact[0]]), "exact_observed"
    if len(x) < 2 or requested < x[0] or requested > x[-1]:
        return None
    return float(np.interp(np.log2(requested), np.log2(x), y)), "bracketed_log_interpolation"


def candidate_features(menu, event):
    # Role remains exact; do not replace a fixed-dose anchor with a library curve.
    lookup = {}
    supported = event[event.assay.eq("Glo") & event.seed_to_read_days.eq(4)]
    for (tissue, drug, role), g in supported.groupby(["tissue", "drug_id", "role"]):
        curves = []
        for sidm, cells in g.groupby("sidm"):
            per = cells.groupby("dose_uM").viability.mean().sort_index()
            curves.append((sidm, per.index.to_numpy(float), per.to_numpy(float)))
        lookup[(tissue, drug, role)] = curves
    cache = {}
    def response(tissue, drug, role, dose, relaxed):
        key = (tissue, drug, role, dose, relaxed)
        if key not in cache:
            values, interpolated = [], 0
            for cell, x, y in lookup.get((tissue, drug, role), []):
                found = interpolate_observed(x, y, dose)
                if found and (relaxed or found[1] == "exact_observed"):
                    values.append(found[0]); interpolated += found[1] != "exact_observed"
            cache[key] = (float(np.median(values)), len(values), interpolated) if len(values) >= 5 else (np.nan, len(values), interpolated)
        return cache[key]
    rows = []
    for row in menu.itertuples(index=False):
        components, dose_options = dose_vectors(row.ANCHOR_ID, str(row.anchor_set))
        if len(components) != 1 or "|" in row.LIBRARY_ID:
            rows.append({"composite": True, "exact_eligible": False, "relaxed_eligible": False})
            continue
        rec = {"composite": False}
        low, high = min(z[0] for z in dose_options), max(z[0] for z in dose_options)
        for mode, relaxed in [("exact", False), ("relaxed", True)]:
            for name, drug, role, dose in [("anchor_low", row.ANCHOR_ID, "anchor", low),
                                           ("anchor_high", row.ANCHOR_ID, "anchor", high),
                                           ("library_top", row.LIBRARY_ID, "library", float(row.LIBRARY_CONC))]:
                y, n, ni = response(row.Tissue, drug, role, dose, relaxed)
                rec[f"{mode}_{name}_viability"] = y
                rec[f"{mode}_{name}_cells"] = n
                rec[f"{mode}_{name}_interpolated_cells"] = ni
            rec[f"{mode}_eligible"] = bool(np.isfinite([rec[f"{mode}_{k}_viability"] for k in ["anchor_low", "anchor_high", "library_top"]]).all())
        rows.append(rec)
    return pd.DataFrame(rows, index=menu.index)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "data")
    args = parser.parse_args()
    out = args.output
    out.mkdir(exist_ok=False)
    start = time.perf_counter()
    frozen = json.loads((HERE / "PROTOCOL_FREEZE.json").read_text())
    assert hashlib.sha256((HERE / "PROTOCOL.json").read_bytes()).hexdigest() == frozen["sha256"]
    assert hashlib.sha256(RAW.read_bytes()).hexdigest() == EXPECTED
    replay = load_replay()
    _, _, menu = replay.load_data()
    target = set(menu.SIDM)
    design = pd.read_csv(DESIGN_SOURCE, usecols=["BARCODE", "SIDM", "Tissue"], dtype=str).drop_duplicates()
    assert not design.BARCODE.duplicated().any(), "nonunique_plate_identity"
    plate_identity = design.set_index("BARCODE")[["SIDM", "Tissue"]].to_dict("index")
    parts, qc, seen = [], [], set()
    audit = {"raw_rows_streamed": 0, "target_plates_excluded_before_normalization": 0}
    def process(frame):
        # Plate-contiguous stream permits bounded RAM; reject cross-chunk reappearance.
        for barcode, f in frame.groupby("BARCODE", sort=False):
            if barcode in seen:
                raise ValueError("noncontiguous_plate_source")
            seen.add(barcode)
            if f.SANGER_MODEL_ID.isin(target).any():
                audit["target_plates_excluded_before_normalization"] += 1
                qc.append({"BARCODE": barcode, "reason": "TARGET_EXCLUDED"})
                continue
            identity = plate_identity.get(barcode)
            if identity is None or set(f.SANGER_MODEL_ID.dropna()) != {identity["SIDM"]}:
                qc.append({"BARCODE": barcode, "reason": "plate_identity_missing_or_mismatch"})
                continue
            z, report = plate_mono(f, identity["Tissue"])
            qc.append({"BARCODE": barcode, **report})
            if z is not None and len(z):
                parts.append(z)
    with zipfile.ZipFile(RAW) as archive:
        member = archive.namelist()[0]
        with archive.open(member) as handle:
            carry = pd.DataFrame()
            for chunk in pd.read_csv(handle, usecols=COLS, dtype={k: str for k in COLS if k != "INTENSITY"}, chunksize=250000):
                audit["raw_rows_streamed"] += len(chunk)
                frame = pd.concat([carry, chunk], ignore_index=True)
                last = frame.BARCODE.iloc[-1]
                process(frame[frame.BARCODE.ne(last)])
                carry = frame[frame.BARCODE.eq(last)].copy()
            if len(carry):
                process(carry)
    points = pd.concat(parts, ignore_index=True)
    assert not set(points.sidm) & target
    points.to_csv(out / "mono_plate_points.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    event, curves = summarize_curves(points)
    event.to_csv(out / "mono_event_points.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    curves.to_csv(out / "mono_curves.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    pd.DataFrame(qc).to_csv(out / "plate_qualification.csv", index=False)
    features = candidate_features(menu, event)
    pd.concat([menu[replay.KEY + ["role", "pair"]], features], axis=1).to_csv(out / "candidate_features.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    prior = pd.read_csv(ROOT / "research/astra/drylab_followup_20261007/tier_a_run2/public_features.csv.gz")
    boundary = set()
    for _, g in menu.groupby(["SIDM", "role"]):
        n = math.floor(.7 * math.ceil(.2 * len(g)))
        indices = g.index[replay.ordering(g, g.prior_control_score)[max(0, n - 5):n + 5]]
        boundary.update(indices)
    gaps = features.loc[sorted(boundary)]
    audit.update(plates_seen=len(seen), qc_reason_counts=pd.DataFrame(qc).reason.value_counts().to_dict(),
                 mono_plate_points=len(points), mono_event_points=len(event), curve_records=len(curves),
                 history_cells=int(points.sidm.nunique()), compounds=int(points.drug_id.nunique()),
                 library_curves_with_three_or_more_doses=int((curves.role.eq("library") & curves.n_doses.ge(3)).sum()),
                 target_excluded_sidms=sorted(target), raw_source_sha256=EXPECTED, source_member=member,
                 design_metadata_sha256=hashlib.sha256(DESIGN_SOURCE.read_bytes()).hexdigest(),
                 exact_feature_eligible=int(features.exact_eligible.sum()), relaxed_feature_eligible=int(features.relaxed_eligible.sum()),
                 previous_dose_support_eligible=int(prior.eligible.sum()),
                 newly_supported_from_previous=int((features.relaxed_eligible & ~prior.eligible).sum()),
                 missing_boundary_before=int((~prior.loc[sorted(boundary), "eligible"]).sum()),
                 missing_boundary_after=int((~gaps.relaxed_eligible).sum()),
                 wall_seconds=time.perf_counter() - start,
                 meaning="Reference mono viability, never target culture state, fitted pharmacological Emax, synergy, or mechanism probability")
    dump(out / "qualification.json", audit)
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
