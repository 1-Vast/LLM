"""Descriptive within-plate switching census; no biological-replication claims."""
from itertools import combinations, product
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "2026-10-29-functional-joint-discovery/sources/root/hts001_raw.body"
MARGIN = 0.25


def endpoint(group):
    times = group["time"].to_numpy()
    counts = group["cell.count"].to_numpy()
    keep = times < 72
    times, counts = times[keep], counts[keep]
    order = np.argsort(times)
    times, counts = times[order], counts[order]
    if len(np.unique(times)) != len(times):
        return None, "duplicate_time"
    if not len(times) or times.min() > 24 or times.max() < 60:
        return None, "unbracketed_endpoint"
    # Only endpoint-bracketing frames enter the calculation.
    selected = []
    for target in [24, 60]:
        right = int(np.searchsorted(times, target))
        left = right if times[right] == target else right - 1
        if not np.isfinite(counts[[left, right]]).all() or np.any(counts[[left, right]] <= 0):
            return None, "nonpositive_or_nonfinite_bracketing_count"
        selected.append(float(np.interp(target, times[[left, right]], counts[[left, right]])))
    return float(np.log2(selected[1] / selected[0])), None


def main():
    started = time.monotonic()
    target = ROOT / "census_c_result.json"
    if target.exists():
        raise SystemExit("Existing census result: preserve the original execution")
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == "e6ff575664705d6021d98e1dad41751c87d86a425a3794f7e2a7e3b12468d617"
    frame = pd.read_csv(SOURCE)
    wells, excluded = [], []
    keys = ["cell.line", "upid", "well", "drug1", "drug1.conc"]
    for key, group in frame.groupby(keys, sort=True):
        value, reason = endpoint(group)
        row = dict(zip(keys, key))
        if reason:
            excluded.append({**row, "reason": reason})
        else:
            wells.append({**row, "log2_growth": value})
    well_frame = pd.DataFrame(wells)
    controls = well_frame[well_frame.drug1 == "control"].groupby("upid").log2_growth.median()
    well_frame["relative_growth"] = well_frame.log2_growth - well_frame.upid.map(controls)
    assert well_frame.relative_growth.notna().all()
    well_frame.to_csv(ROOT / "census_c_wells.csv", index=False)
    treated = well_frame[well_frame.drug1 != "control"]
    curve_values = {}
    incomplete_conditions = []
    for (cell, drug, dose), group in treated.groupby(["cell.line", "drug1", "drug1.conc"], sort=True):
        assert group.upid.nunique() == 1
        if len(group) != 2:
            incomplete_conditions.append({"cell": cell, "drug": drug, "dose_M": float(dose), "surviving_wells": len(group)})
            continue
        curve_values.setdefault((cell, drug), {})[float(dose)] = group.sort_values("well").relative_growth.to_numpy()
    pairs, witnesses = [], []
    input_pairs_by_background = {}
    for cell, group in frame[frame.drug1 != "control"].groupby("cell.line"):
        grids = {drug: set(part["drug1.conc"]) for drug, part in group.groupby("drug1")}
        input_pairs_by_background[cell] = sum(len(grids[a] & grids[b]) >= 2 for a,b in combinations(sorted(grids),2))
    for cell in sorted(treated["cell.line"].unique()):
        drugs = sorted(drug for c, drug in curve_values if c == cell)
        for first, second in combinations(drugs, 2):
            a, b = curve_values[cell, first], curve_values[cell, second]
            doses = sorted(set(a) & set(b))
            if len(doses) < 2:
                continue
            delta = {dose: float(np.mean(a[dose]) - np.mean(b[dose])) for dose in doses}
            positive = [dose for dose in doses if delta[dose] >= MARGIN]
            negative = [dose for dose in doses if delta[dose] <= -MARGIN]
            stable_positive = [dose for dose in positive if np.all(a[dose]-b[dose] >= MARGIN) and min(a[dose]) > max(b[dose])]
            stable_negative = [dose for dose in negative if np.all(a[dose]-b[dose] <= -MARGIN) and max(a[dose]) < min(b[dose])]
            stable = bool(stable_positive and stable_negative)
            pairs.append({"cell": cell, "first": first, "second": second, "common_doses": len(doses),
                          "mean_flip": bool(positive and negative), "technical_concordant_flip": stable,
                          "minimum_mean_contrast": min(delta.values()), "maximum_mean_contrast": max(delta.values())})
            primary_witness = (min(stable_positive),min(stable_negative)) if stable else None
            for pos, neg in product(positive, negative):
                other_cells = sorted(c for c,d in curve_values if d == first and c != cell)
                available, reproduced, margin_reproduced = 0, 0, 0
                for other in other_cells:
                    aa, bb = curve_values[other,first], curve_values.get((other,second), {})
                    if not {pos,neg} <= set(aa) & set(bb):
                        continue
                    available += 1
                    reproduced += bool(np.mean(aa[pos])-np.mean(bb[pos]) > 0 and np.mean(aa[neg])-np.mean(bb[neg]) < 0)
                    margin_reproduced += bool(np.mean(aa[pos])-np.mean(bb[pos]) >= MARGIN and np.mean(aa[neg])-np.mean(bb[neg]) <= -MARGIN)
                witnesses.append({"cell": cell, "first": first, "second": second,
                                  "positive_dose_M": pos, "negative_dose_M": neg,
                                  "positive_delta": delta[pos], "negative_delta": delta[neg],
                                  "technical_concordant_witness": pos in stable_positive and neg in stable_negative,
                                  "primary_technical_witness": (pos,neg) == primary_witness,
                                  "other_backgrounds_available": available, "other_backgrounds_sign_reproduced": reproduced,
                                  "other_backgrounds_margin_reproduced": margin_reproduced,
                                  "other_backgrounds_sign_fraction": reproduced/available if available else None})
    pair_frame = pd.DataFrame(pairs)
    pair_frame.to_csv(ROOT / "census_c_pairs.csv", index=False)
    pd.DataFrame(witnesses).to_csv(ROOT / "census_c_witnesses.csv", index=False)
    primary = [w for w in witnesses if w["primary_technical_witness"] and w["other_backgrounds_available"]]
    by_background = {}
    for cell, denominator in sorted(input_pairs_by_background.items()):
        part = pair_frame[pair_frame.cell == cell]
        by_background[cell] = {"input_pairs": denominator, "eligible_pairs": len(part), "mean_flips": int(part.mean_flip.sum()),
                               "technical_concordant_flips": int(part.technical_concordant_flip.sum()),
                               "input_wells": int(frame.loc[frame["cell.line"] == cell,"well"].nunique()),
                               "eligible_wells": int((well_frame["cell.line"] == cell).sum()),
                               "excluded_wells": sum(w["cell.line"] == cell for w in excluded)}
    result = {"status": "DESCRIPTIVE_TECHNICAL_CENSUS_ONLY", "input_rows": len(frame),
              "eligible_wells": len(wells), "excluded_wells": excluded,
              "backgrounds": int(treated["cell.line"].nunique()), "drugs": int(treated.drug1.nunique()),
              "eligible_cell_drug_pairs": len(pairs), "mean_flips": int(pair_frame.mean_flip.sum()),
              "technical_concordant_flips": int(pair_frame.technical_concordant_flip.sum()),
              "input_backgrounds": len(input_pairs_by_background), "by_background": by_background,
              "incomplete_surviving_conditions": incomplete_conditions,
              "all_mean_flip_dose_witnesses": len(witnesses),
              "technical_concordant_dose_witnesses": sum(w["technical_concordant_witness"] for w in witnesses),
              "primary_reproduction_pair_units": len(primary),
              "mean_pairwise_other_background_sign_fraction": float(np.mean([w["other_backgrounds_sign_fraction"] for w in primary])) if primary else None,
              "pooled_other_background_sign_fraction": sum(w["other_backgrounds_sign_reproduced"] for w in primary)/sum(w["other_backgrounds_available"] for w in primary) if primary else None,
              "wall_seconds": time.monotonic()-started,
              "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "protocol_sha256": hashlib.sha256((ROOT/"protocol_c_census_v1_1.md").read_bytes()).hexdigest(),
              "limitations": ["one plate per background", "no certified independent culture", "technical wells are not population replicates", "drug pairs reuse the same drugs", "no clinical exposure inference", "not a predictive model comparison"]}
    target.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in ["excluded_wells","incomplete_surviving_conditions"]}, indent=2))


if __name__ == "__main__":
    main()
