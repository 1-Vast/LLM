"""Cross-check already saved independent outputs; no response access or fitting."""
from pathlib import Path
import hashlib
import json
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT, OTHER = HERE / "g1_run", HERE / "independent_g1"


def read(base, name):
    return json.loads((base / name).read_text(encoding="utf-8"))


root_summary, independent_summary = read(ROOT, "summary.json"), read(OTHER, "summary.json")
predictions = read(ROOT, "predictions.json")
losses = read(ROOT, "losses.json")
actions = read(ROOT, "actions_frozen.json")["actions"]
delta = {(r["condition"], r["policy"]): r for r in read(ROOT, "delta_access_ledger.json")}
pred_error, loss_error, action_checks, delta_checks = [], [], [], []
for row in read(OTHER, "predictions.json"):
    name, policy = row["condition"], row["method"]
    pred_error.extend(np.abs(np.array(predictions[name][policy]) - row["prediction"]).tolist())
    action_checks.append(actions[name][policy] == row["pair_index"])
    delta_checks.append(delta[name, policy]["signed_delta_only"] == row["delta"] and
                        delta[name, policy]["pair"] == [row["q"], row["r"]])
for row in read(OTHER, "per_drug_losses.json"):
    policy = "mean_noquery" if row["method"] == "no_query" else row["method"]
    loss_error.append(abs(losses[row["condition"]][policy] - row["normalized_loss"]))
rl, il = read(ROOT, "loo_selection.json"), read(OTHER, "loo_selection.json")
loo_error = max(float(np.max(np.abs(np.array(rl["raw_mean_losses"][k]) - il["raw_MSE"][policy])))
                for k, policy in enumerate(("B0", "B1")))
ci_error = max(float(np.max(np.abs(np.array(root_summary["comparisons"][b]["stability_interval_95"]) -
                                 independent_summary["comparisons"][b + "_minus_C"]["CI95"])))
               for b in ("B0", "B1"))
draw_identical = (ROOT / "bootstrap_draws.npy").read_bytes() == (OTHER / "bootstrap_shared_draws.npy").read_bytes()
report = {"comparison_scope": "saved independent outputs; no raw CSV, fit or hypothesis rerun",
          "paired_predictions": len(action_checks), "paired_losses": len(loss_error),
          "max_prediction_absolute_difference": max(pred_error), "max_loss_absolute_difference": max(loss_error),
          "max_loo_mean_absolute_difference": loo_error, "max_CI_absolute_difference": ci_error,
          "D_absolute_difference": abs(root_summary["common_D_pre_ridge"] - independent_summary["D"]),
          "all_action_indices_equal": all(action_checks), "all_signed_deltas_and_pairs_equal": all(delta_checks),
          "bootstrap_npy_bytes_identical": draw_identical,
          "bootstrap_sha256": hashlib.sha256((ROOT / "bootstrap_draws.npy").read_bytes()).hexdigest(),
          "both_implementations_H_not_supported": not root_summary["H_G1_supported_in_proxy"] and
                                                 not independent_summary["phenomenon_development_support"],
          "numerical_agreement_tolerance": 1e-10,
          "scientific_inference": "computational consistency only; frozen H remains unsupported/undecided"}
assert len(action_checks) == 144 and len(loss_error) == 192
assert all(action_checks) and all(delta_checks) and draw_identical
assert max(max(pred_error), max(loss_error), loo_error, ci_error, report["D_absolute_difference"]) < 1e-10
output = HERE / "root_independent_comparison.json"
assert not output.exists(), "Preserve first cross-check"
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False))
