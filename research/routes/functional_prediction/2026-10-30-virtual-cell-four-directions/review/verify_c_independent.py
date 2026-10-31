"""Independent arithmetic implementation of frozen C1 / C1 v1.1.

Reads the original HTS001 file and the two protocols only. Never imports the
primary census or reads its outputs. Running this file is a descriptive
recalculation, not a new experiment or biological replication.
"""

import bisect
import csv
import hashlib
import itertools
import json
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

import numpy as np


REVIEW = Path(__file__).resolve().parent
EPISODE = REVIEW.parent
SOURCE = Path(
    r"D:\MAESTRO\research\routes\functional_prediction\2026-10-29-functional-joint-discovery"
    r"\sources\root\hts001_raw.body"
)
EXPECTED_SHA256 = "e6ff575664705d6021d98e1dad41751c87d86a425a3794f7e2a7e3b12468d617"
MARGIN = 0.25


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def needed_count(value):
    """Validate only counts used by an endpoint's bracketing frames."""
    if value.strip() in {"", "NA"}:
        return None, "missing_count"
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None, "nonnumeric_count"
    if not np.isfinite(parsed):
        return None, "nonfinite_count"
    if parsed <= 0:
        return None, "nonpositive_count"
    return parsed, ""


def interpolate(frames, target):
    """Linear interpolation of counts, using frames strictly before 72 h."""
    earlier = [(t, value) for t, value in frames if t < 72.0]
    times = [t for t, _ in earlier]
    insertion = bisect.bisect_left(times, target)
    if insertion < len(times) and times[insertion] == target:
        needed = [earlier[insertion]]
    elif insertion == 0 or insertion == len(times):
        return None, f"t{int(target)}_unbracketed_before_72h", None, None
    else:
        needed = earlier[insertion - 1:insertion + 1]
    counts = []
    for _, raw in needed:
        parsed, reason = needed_count(raw)
        if reason:
            return None, f"t{int(target)}_{reason}", needed[0][0], needed[-1][0]
        counts.append(parsed)
    if len(needed) == 1:
        value = counts[0]
    else:
        weight = (target - needed[0][0]) / (needed[1][0] - needed[0][0])
        value = counts[0] + weight * (counts[1] - counts[0])
    return float(value), "", needed[0][0], needed[-1][0]


def dose_text(dose):
    return str(dose.normalize())


def mean(values):
    return float(np.mean(values))


def main():
    source_hash = sha256(SOURCE)
    if source_hash != EXPECTED_SHA256:
        raise ValueError("HTS001 source SHA256 does not match the frozen protocol")
    trajectories = {}
    rows = 0
    with SOURCE.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        expected_columns = {"drug1", "cell.line", "drug1.conc", "well", "upid", "time", "cell.count", "drug1.units"}
        if set(reader.fieldnames or []) != expected_columns:
            raise ValueError("Unexpected raw HTS001 columns")
        for row in reader:
            rows += 1
            cell, plate, well = row["cell.line"], row["upid"], row["well"]
            if row["drug1.units"] not in {"M", "Molar", "molar", "mol/L", "mol/l"}:
                raise ValueError(f"Unrecognised Molar unit: {row['drug1.units']!r}")
            dose = Decimal(row["drug1.conc"])
            if not dose.is_finite() or dose < 0:
                raise ValueError("Invalid numeric concentration")
            time = float(row["time"])
            if not np.isfinite(time):
                raise ValueError("A frame has no finite time")
            key = cell, plate, well
            identity = row["drug1"], dose
            if key not in trajectories:
                trajectories[key] = {"identity": identity, "frames": []}
            if trajectories[key]["identity"] != identity:
                raise ValueError(f"A well changes treatment identity: {key}")
            trajectories[key]["frames"].append((time, row["cell.count"]))

    cells = sorted({key[0] for key in trajectories})
    plates_by_cell = {cell: sorted({key[1] for key in trajectories if key[0] == cell}) for cell in cells}
    if any(len(plates) != 1 for plates in plates_by_cell.values()):
        raise ValueError("Frozen HTS001 scope requires one plate per background")

    wells = []
    for (cell, plate, well), trajectory in sorted(trajectories.items()):
        frames = sorted(trajectory["frames"])
        if len({t for t, _ in frames}) != len(frames):
            raise ValueError(f"Duplicate time within well: {(cell, plate, well)}")
        n24, reason24, lower24, upper24 = interpolate(frames, 24.0)
        n60, reason60, lower60, upper60 = interpolate(frames, 60.0)
        reasons = [reason for reason in [reason24, reason60] if reason]
        growth = float(np.log2(n60 / n24)) if not reasons else None
        drug, dose = trajectory["identity"]
        wells.append({
            "cell": cell, "plate": plate, "well": well, "drug": drug,
            "dose_molar": dose_text(dose), "input_frames": len(frames),
            "n24": n24, "n60": n60,
            "t24_lower_h": lower24, "t24_upper_h": upper24,
            "t60_lower_h": lower60, "t60_upper_h": upper60,
            "log2_growth": growth, "vehicle_median_log2_growth": None,
            "relative_log2_growth": None, "eligible": False,
            "exclusion_reason": ";".join(reasons),
        })

    vehicle_growth = defaultdict(list)
    for well in wells:
        if well["drug"] == "control" and well["log2_growth"] is not None:
            vehicle_growth[(well["cell"], well["plate"])].append(well["log2_growth"])
    medians = {key: float(np.median(values)) for key, values in vehicle_growth.items()}
    for well in wells:
        reference = medians.get((well["cell"], well["plate"]))
        well["vehicle_median_log2_growth"] = reference
        if well["log2_growth"] is not None:
            if reference is None:
                well["exclusion_reason"] = "no_valid_same_plate_vehicle"
            else:
                well["relative_log2_growth"] = well["log2_growth"] - reference
                well["eligible"] = True

    conditions = defaultdict(list)
    for well in wells:
        if well["drug"] != "control":
            conditions[(well["cell"], well["plate"], well["drug"], Decimal(well["dose_molar"]))].append(well)
    complete = {}
    condition_exclusions = []
    for (cell, plate, drug, dose), members in sorted(conditions.items()):
        ordered = sorted(members, key=lambda item: item["well"])
        if len(ordered) != 2:
            raise ValueError(f"Frozen scope requires two input wells per treatment condition: {(cell, plate, drug, dose)}")
        usable = [member for member in ordered if member["eligible"]]
        if len(usable) == 2:
            complete[(cell, plate, drug, dose)] = [member["relative_log2_growth"] for member in ordered]
        else:
            condition_exclusions.append({
                "cell": cell, "plate": plate, "drug": drug, "dose_molar": dose_text(dose),
                "input_wells": [member["well"] for member in ordered],
                "eligible_wells": [member["well"] for member in usable],
                "reason": "incomplete_two_well_condition" if usable else "no_eligible_well_in_condition",
            })

    # Dose sets are constructed from input conditions, so zero-eligible cells survive.
    input_doses = defaultdict(set)
    for cell, plate, drug, dose in conditions:
        input_doses[(cell, plate, drug)].add(dose)
    pair_records = []
    pair_doses = {}
    primary_witnesses = []
    for cell in cells:
        plate = plates_by_cell[cell][0]
        drugs = sorted({key[2] for key in input_doses if key[:2] == (cell, plate)})
        for drug_a, drug_b in itertools.combinations(drugs, 2):
            shared_input = input_doses[(cell, plate, drug_a)] & input_doses[(cell, plate, drug_b)]
            if len(shared_input) < 2:
                continue
            dose_records = {}
            for dose in sorted(shared_input):
                a = complete.get((cell, plate, drug_a, dose))
                b = complete.get((cell, plate, drug_b, dose))
                if a is None or b is None:
                    continue
                pseudo = [a[index] - b[index] for index in range(2)]
                cross = [x - y for x in a for y in b]
                dose_records[dose] = {
                    "dose_molar": dose_text(dose), "mean_contrast": mean(a) - mean(b),
                    "pseudo_contrasts": pseudo, "all_cross_well_contrasts": cross,
                    "technical_positive": all(value >= MARGIN for value in pseudo) and all(value > 0 for value in cross),
                    "technical_negative": all(value <= -MARGIN for value in pseudo) and all(value < 0 for value in cross),
                }
            eligible = len(dose_records) >= 2
            positive = [dose for dose, result in dose_records.items() if result["mean_contrast"] >= MARGIN] if eligible else []
            negative = [dose for dose, result in dose_records.items() if result["mean_contrast"] <= -MARGIN] if eligible else []
            witnesses = []
            technical_witnesses = []
            for pos, neg in itertools.product(positive, negative):
                concordant = dose_records[pos]["technical_positive"] and dose_records[neg]["technical_negative"]
                witnesses.append({
                    "positive_dose_molar": dose_text(pos), "negative_dose_molar": dose_text(neg),
                    "positive_mean_contrast": dose_records[pos]["mean_contrast"],
                    "negative_mean_contrast": dose_records[neg]["mean_contrast"],
                    "technical_concordant": concordant,
                })
                if concordant:
                    technical_witnesses.append((pos, neg))
            primary = min(technical_witnesses) if technical_witnesses else None
            record = {
                "cell": cell, "plate": plate, "drug_a": drug_a, "drug_b": drug_b,
                "input_shared_doses_molar": [dose_text(dose) for dose in sorted(shared_input)],
                "eligible_shared_doses": len(dose_records), "eligible_pair": eligible,
                "mean_flip": bool(witnesses), "repeat_concordant_flip": bool(technical_witnesses),
                "doses": list(dose_records.values()), "witnesses": witnesses,
                "primary_witness": None if primary is None else {
                    "positive_dose_molar": dose_text(primary[0]), "negative_dose_molar": dose_text(primary[1]),
                },
            }
            pair_records.append(record)
            pair_doses[(cell, drug_a, drug_b)] = dose_records
            if primary is not None:
                primary_witnesses.append((cell, drug_a, drug_b, *primary))

    cross_units = []
    for source_cell, drug_a, drug_b, pos, neg in primary_witnesses:
        targets = []
        for target_cell in cells:
            if target_cell == source_cell:
                continue
            target = pair_doses.get((target_cell, drug_a, drug_b), {})
            available = pos in target and neg in target
            detail = {"cell": target_cell, "available": available}
            if available:
                positive_contrast = target[pos]["mean_contrast"]
                negative_contrast = target[neg]["mean_contrast"]
                detail.update({
                    "positive_mean_contrast": positive_contrast,
                    "negative_mean_contrast": negative_contrast,
                    "sign_reproduced": positive_contrast > 0 and negative_contrast < 0,
                    "margin_reproduced": positive_contrast >= MARGIN and negative_contrast <= -MARGIN,
                })
            else:
                detail["unavailable_reason"] = "no_complete_two_well_measurements_for_both_drugs_at_both_exact_doses"
            targets.append(detail)
        available_targets = [target for target in targets if target["available"]]
        n_available = len(available_targets)
        n_sign = sum(target["sign_reproduced"] for target in available_targets)
        n_margin = sum(target["margin_reproduced"] for target in available_targets)
        cross_units.append({
            "source_cell": source_cell, "drug_a": drug_a, "drug_b": drug_b,
            "positive_dose_molar": dose_text(pos), "negative_dose_molar": dose_text(neg),
            "available_other_backgrounds": n_available,
            "sign_reproduced_backgrounds": n_sign, "margin_reproduced_backgrounds": n_margin,
            "sign_fraction": n_sign / n_available if n_available else None,
            "margin_fraction": n_margin / n_available if n_available else None,
            "targets": targets,
        })
    available_units = [unit for unit in cross_units if unit["available_other_backgrounds"]]
    pooled_available = sum(unit["available_other_backgrounds"] for unit in available_units)
    pooled_sign = sum(unit["sign_reproduced_backgrounds"] for unit in available_units)
    pooled_margin = sum(unit["margin_reproduced_backgrounds"] for unit in available_units)

    backgrounds = []
    for cell in cells:
        cell_wells = [well for well in wells if well["cell"] == cell]
        cell_pairs = [pair for pair in pair_records if pair["cell"] == cell]
        reasons = Counter(reason for well in cell_wells for reason in well["exclusion_reason"].split(";") if reason)
        backgrounds.append({
            "cell": cell, "plates": plates_by_cell[cell], "input_wells": len(cell_wells),
            "eligible_wells": sum(well["eligible"] for well in cell_wells),
            "excluded_wells": sum(not well["eligible"] for well in cell_wells),
            "input_vehicle_wells": sum(well["drug"] == "control" for well in cell_wells),
            "eligible_vehicle_wells": sum(well["drug"] == "control" and well["eligible"] for well in cell_wells),
            "well_exclusion_reasons": dict(sorted(reasons.items())),
            "input_exact_dose_pairs": len(cell_pairs),
            "eligible_exact_dose_pairs": sum(pair["eligible_pair"] for pair in cell_pairs),
            "mean_flip_pairs": sum(pair["mean_flip"] for pair in cell_pairs),
            "repeat_concordant_pairs": sum(pair["repeat_concordant_flip"] for pair in cell_pairs),
        })

    summary = {
        "input_rows": rows, "input_backgrounds": cells, "input_wells": len(wells),
        "eligible_wells": sum(well["eligible"] for well in wells),
        "excluded_wells": sum(not well["eligible"] for well in wells),
        "input_exact_dose_pairs": len(pair_records),
        "eligible_exact_dose_pairs": sum(pair["eligible_pair"] for pair in pair_records),
        "mean_flip_pairs": sum(pair["mean_flip"] for pair in pair_records),
        "repeat_concordant_pairs": sum(pair["repeat_concordant_flip"] for pair in pair_records),
    }
    cross_summary = {
        "source_cell_pair_units": len(cross_units), "units_with_available_other_backgrounds": len(available_units),
        "units_with_no_available_other_background": len(cross_units) - len(available_units),
        "primary_mean_sign_fraction": mean([unit["sign_fraction"] for unit in available_units]) if available_units else None,
        "mean_margin_fraction": mean([unit["margin_fraction"] for unit in available_units]) if available_units else None,
        "pooled_available_opportunities": pooled_available,
        "pooled_sign_reproduced": pooled_sign, "pooled_margin_reproduced": pooled_margin,
        "pooled_sign_fraction": pooled_sign / pooled_available if pooled_available else None,
        "pooled_margin_fraction": pooled_margin / pooled_available if pooled_available else None,
    }
    result = {
        "scope": "Independent arithmetic verification of descriptive census C1 v1.1; no biological replication, fit, threshold search, or primary-output access.",
        "source": {"path": str(SOURCE), "sha256": source_hash},
        "script_sha256": sha256(Path(__file__)),
        "protocol_sha256": {name: sha256(EPISODE / name) for name in ["protocol_c_census.md", "protocol_c_census_v1_1.md"]},
        "criteria": {"time_interval_h": [24, 60], "frames_strictly_before_h": 72, "contrast_margin": MARGIN,
                     "dose_matching": "Exact Decimal numeric equality in Molar", "drug_orientation": "lexicographic drug_a minus drug_b"},
        "summary": summary, "backgrounds": backgrounds,
        "excluded_conditions": condition_exclusions,
        "incomplete_conditions": [condition for condition in condition_exclusions if len(condition["eligible_wells"]) == 1],
        "pairs": pair_records, "cross_background_summary": cross_summary, "cross_background_units": cross_units,
    }
    # Both independent artifacts are saved before any external comparison.
    with (REVIEW / "c_independent_wells.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(wells[0]))
        writer.writeheader()
        writer.writerows(wells)
    (REVIEW / "c_independent_result.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"summary": summary, "cross_background": cross_summary}, sort_keys=True))


if __name__ == "__main__":
    main()
