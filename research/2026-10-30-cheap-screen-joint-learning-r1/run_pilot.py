"""Frozen E001 fluorescence-readout analysis; no author code is executed."""
from pathlib import Path
from collections import defaultdict
import csv
import hashlib
import json
import sys
import time

import numpy as np

ROOT = Path(__file__).parent
FILES = {"E3CA": "BxPC3", "E3CB": "BxPC3", "E3DA": "AsPC1", "E3DB": "AsPC1"}
STIMULI = ["None", "IFNG", "TNFA", "IFNG_TNFA"]
DRUGS = ["Momelotinib", "BMS-345541", "Salirasib", "Trametinib", "Taselisib"]
MODE = sys.argv[1]
assert MODE in ("controls", "evaluate")
started, cpu_started = time.monotonic(), time.process_time()


def read_wells(preparation, controls_only):
    path = ROOT / "evidence" / f"cxcl9_raw_{preparation}.body"
    groups = defaultdict(list)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            assert row["Cell line"] == FILES[preparation]
            drug = row["Inhibitors"]
            if controls_only and drug != "None":
                continue  # No numeric conversion of drug outcomes at this stage.
            assert drug in ["None"] + DRUGS
            stimulus, well = row["Cytokines"], row["Condition"]
            assert stimulus in STIMULI and well in ("Sample1", "Sample2")
            value = float(row["Fluorescent intensity (PE)"])
            assert np.isfinite(value), "Nonfinite PE value; no implicit cleaning."
            groups[(drug, stimulus, well)].append(value)
    expected = 8 if controls_only else 48
    assert len(groups) == expected, (preparation, len(groups))
    records, means = [], {}
    for (drug, stimulus, well), values in sorted(groups.items()):
        data = np.asarray(values, dtype=float)
        q1, q3 = np.quantile(data, [0.25, 0.75], method="linear")
        lo, hi = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
        kept = data[(data >= lo) & (data <= hi)]
        assert len(kept)
        means[(drug, stimulus, well)] = float(kept.mean())
        records.append({"drug": drug, "stimulus": stimulus, "technical_well": well,
                        "events": len(data), "retained": len(kept), "mfi": float(kept.mean())})
    return means, records, hashlib.sha256(path.read_bytes()).hexdigest()


def values(means, drug, stimulus):
    return [means[(drug, stimulus, w)] for w in ("Sample1", "Sample2")]


def control_record(means):
    well_values = [values(means, "None", s) for s in STIMULI]
    b, g, t, gt = [float(np.mean(v)) for v in well_values]
    d = [min(well_values[1]) - max(well_values[0]), max(well_values[1]) - min(well_values[0])]
    n = [min(well_values[3]) - max(well_values[2]), max(well_values[3]) - min(well_values[2])]
    eligible = d[0] > 0 and n[0] > 0 and gt - b > 0
    ratios = [x / y for x in n for y in d] if eligible else []
    return {"eligible": eligible, "means": dict(zip(STIMULI, [b, g, t, gt])),
            "D0": g - b, "N0": gt - t, "S0": gt - b, "I0": gt - g - t + b,
            "D_envelope": d, "N_envelope": n,
            "kappa": (gt - t) / (g - b) if eligible else None,
            "kappa_envelope": [min(ratios), max(ratios)] if eligible else None}


result = {"protocol_sha256": hashlib.sha256((ROOT / "protocol_v1_1.md").read_bytes()).hexdigest(),
          "mode": MODE, "numpy_version": np.__version__, "preparations": {}, "targets": []}
if MODE == "evaluate":
    assert (ROOT / "review" / "execution_decision.json").is_file(), "Missing reviewed execution decision."
    decision = json.loads((ROOT / "review" / "execution_decision.json").read_text(encoding="utf-8"))
    assert decision["target_evaluation_authorized"] and decision["protocol_sha256"] == result["protocol_sha256"]
    checkpoint = json.loads((ROOT / "controls_only.json").read_text(encoding="utf-8"))
for prep in FILES:
    means, records, source_sha = read_wells(prep, controls_only=(MODE == "controls"))
    controls = control_record(means)
    if MODE == "evaluate":
        assert source_sha == checkpoint["preparations"][prep]["source_sha256"]
        assert controls == checkpoint["preparations"][prep]["controls"]
    result["preparations"][prep] = {"cell": FILES[prep], "source_sha256": source_sha,
                                    "controls": controls, "well_records": records}
    if MODE == "controls" or not controls["eligible"]:
        continue
    c, k, scale = controls["means"], controls["kappa"], controls["S0"]
    for drug in DRUGS:
        w = [values(means, drug, s) for s in STIMULI]
        b, g, t, gt = [float(np.mean(v)) for v in w]
        predictions = {"gain": t + k * (g - b), "additive": g + t - b,
                       "constant_interaction": g + t - b + controls["I0"], "no_drug_control": c["IFNG_TNFA"]}
        delta = [min(w[1]) - max(w[0]), max(w[1]) - min(w[0])]
        products = [a * b1 for a in controls["kappa_envelope"] for b1 in delta]
        interval = [min(w[2]) + min(products), max(w[2]) + max(products)]
        observed_interval = [min(w[3]), max(w[3])]
        result["targets"].append({"preparation": prep, "cell": FILES[prep], "drug": drug,
                                  "calibration_means": [b, g, t], "observed": gt, "scale": scale,
                                  "predictions": predictions,
                                  "normalized_signed_errors": {m: (p - gt) / scale for m, p in predictions.items()},
                                  "normalized_absolute_errors": {m: abs(p - gt) / scale for m, p in predictions.items()},
                                  "gain_prediction_technical_envelope": interval,
                                  "observed_technical_envelope": observed_interval,
                                  "technical_envelope_overlap": max(interval[0], observed_interval[0]) <= min(interval[1], observed_interval[1]),
                                  "gain_minus_constant_normalized": (predictions["gain"] - predictions["constant_interaction"]) / scale})
if MODE == "evaluate":
    result["mae_by_preparation"] = {
        p: {m: float(np.mean([r["normalized_absolute_errors"][m] for r in result["targets"] if r["preparation"] == p]))
            for m in ["gain", "additive", "constant_interaction", "no_drug_control"]}
        for p in FILES if result["preparations"][p]["controls"]["eligible"]}
result.update(seconds=time.monotonic() - started, cpu_seconds=time.process_time() - cpu_started)
filename = "controls_only.json" if MODE == "controls" else "pilot_result.json"
destination = ROOT / filename
assert not destination.exists(), "Do not overwrite scientific results."
destination.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
print(json.dumps({"output": str(destination), "mode": MODE,
                  "eligible": {p: r["controls"]["eligible"] for p, r in result["preparations"].items()},
                  "targets": len(result["targets"]), "seconds": result["seconds"], "cpu_seconds": result["cpu_seconds"]}))
