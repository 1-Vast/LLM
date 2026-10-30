"""Compare already frozen outputs; no raw-source access, fitting or replay."""
import csv
import hashlib
import json
import math
from pathlib import Path

root = Path(__file__).resolve().parent
verify = root / "verifier"
freeze = json.loads((verify / "verification_freeze.json").read_text(encoding="utf-8"))
assert freeze["primary_code_or_outputs_read"] is False
assert freeze["comparison_performed"] is False
for name, expected in freeze["artifacts_sha256"].items():
    assert hashlib.sha256((verify / name).read_bytes()).hexdigest() == expected, name
primary = json.loads((root / "primary_result.json").read_text(encoding="utf-8"))
independent = json.loads((verify / "verification_result.json").read_text(encoding="utf-8"))
execution = json.loads((root / "execution_receipt.json").read_text(encoding="utf-8"))
outer = json.loads((root / "primary_outer_execution.json").read_text(encoding="utf-8"))
v_execution = json.loads((verify / "execution_receipt.json").read_text(encoding="utf-8"))
v_outer = json.loads((verify / "launch_receipt.json").read_text(encoding="utf-8"))
assert execution["state"] == "complete" and outer["returncode"] == 0
assert independent["errors"] == [] and v_execution["resource_checks_passed"]
assert independent["bootstrap_completed"] == 500
assert primary["count_values_accessed"] == independent["count_access_attempts"] == 2380
cells = list(primary["point"])
assert cells == [p["cell"] for p in independent["point"]["plates"]]
differences = {"Delta": abs(primary["Delta"] - independent["point"]["Delta"]),
               "q05": abs(primary["stability_q05_q95"][0] - independent["quantile_05"]),
               "q95": abs(primary["stability_q05_q95"][1] - independent["quantile_95"]),
               "positive_fraction": abs(primary["bootstrap_positive_fraction"] - independent["fraction_positive"])}
prediction_errors = []
for cell, vp in zip(cells, independent["point"]["plates"]):
    pp = primary["point"][cell]
    differences["D_" + cell] = abs(pp["D"] - vp["D"])
    assert pp["train_mean"] == vp["training_mean"]
    assert pp["validation_mean"] == vp["validation_mean"]
    for i, model in enumerate(["baseline", "curvature"]):
        for p, v in zip(pp["predictions"][i], vp[model]["prediction_raw"]):
            prediction_errors.append(abs(p - v) / max(1, abs(p)))
with (verify / "bootstrap_scores.csv").open(encoding="utf-8", newline="") as handle:
    draws = list(csv.DictReader(handle))
assert len(draws) == 500
bootstrap_diffs, plate_diffs = [], []
for b, row in enumerate(draws):
    assert int(row["draw"]) == b and row["status"] == "COMPLETE"
    bootstrap_diffs.append(abs(primary["bootstrap_Delta"][b] - float(row["Delta"])))
    for c, cell in enumerate(cells):
        plate_diffs.append(abs(primary["bootstrap_D_by_plate"][b][c] - float(row["D_" + cell])))
differences["max_bootstrap_Delta"] = max(bootstrap_diffs)
differences["max_bootstrap_plate_D"] = max(plate_diffs)
assert all(math.isfinite(x) for x in list(differences.values()) + prediction_errors)
maximum_score_difference = max(differences.values())
maximum_prediction_error = max(prediction_errors)
comparison = {"scope": "separate implementations of one frozen conditional comparison; arithmetic only",
              "frozen_verifier_manifest_sha256": hashlib.sha256((verify / "verification_freeze.json").read_bytes()).hexdigest(),
              "primary_result_sha256": hashlib.sha256((root / "primary_result.json").read_bytes()).hexdigest(),
              "verification_result_sha256": freeze["artifacts_sha256"]["verification_result.json"],
              "absolute_score_tolerance": 1e-9, "relative_prediction_tolerance": 1e-7,
              "absolute_differences": differences,
              "max_absolute_score_difference": maximum_score_difference,
              "max_relative_original_prediction_difference": maximum_prediction_error,
              "outcome_labels_agree": primary["status"] == independent["outcome"],
              "within_declared_numerical_tolerances": maximum_score_difference <= 1e-9 and maximum_prediction_error <= 1e-7,
              "new_raw_source_accesses": 0, "new_model_fits": 0}
(root / "numeric_comparison.json").write_text(json.dumps(comparison, indent=2, allow_nan=False) + "\n", encoding="utf-8")
print(json.dumps(comparison, indent=2))
