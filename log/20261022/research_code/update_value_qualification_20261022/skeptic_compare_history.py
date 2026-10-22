"""Compare independently reconstructed values with root's already-frozen audit."""
import json
from pathlib import Path

from skeptic_history_audit import ARMS, LOG, sha

root_path = LOG.parent / "HISTORICAL_CHOICE_AUDIT.json"
own_path = LOG / "HISTORICAL_INDEPENDENT_RECOMPUTE.json"
root = json.loads(root_path.read_text(encoding="utf-8"))
own = json.loads(own_path.read_text(encoding="utf-8"))
checks = []


def compare(name, a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        checks.append({"name": name + "/keys", "passed": set(a) == set(b)})
        for key in sorted(set(a) & set(b)):
            compare(name + "/" + key, a[key], b[key])
    elif isinstance(a, list) and isinstance(b, list):
        checks.append({"name": name + "/length", "passed": len(a) == len(b)})
        for i, (x, y) in enumerate(zip(a, b)):
            compare(f"{name}/{i}", x, y)
    elif isinstance(a, (float, int)) and not isinstance(a, bool) and isinstance(b, (float, int)) and not isinstance(b, bool):
        diff = abs(a - b)
        checks.append({"name": name, "passed": diff <= 1e-12, "absdiff": diff})
    else:
        checks.append({"name": name, "passed": a == b})


mapping = {"campaigns": "complete_campaigns", "differences_R1_minus_ridge": "differences_R1_minus_ridge",
           "strict_both_draws": "strict_non_tie_campaigns", "strict_same_sign": "strict_sign_agreement_count",
           "strict_reversals": "strict_sign_reversals", "strict_agreement_fraction": "strict_sign_agreement_rate",
           "pearson_difference_correlation": "difference_pearson", "historical_practical_scale": "delta_hits_per_complete64",
           "descriptive_both_direction_screen": "descriptive_continuation_pass"}
for key, value in mapping.items():
    compare(key, root[key], own[value])
for key, value in (("symmetric_gain_vs_hindsight_fixed", "gain_vs_hindsight_fixed"),
                   ("symmetric_gain_vs_leave_fold_fixed", "gain_vs_lofo")):
    compare(key, root[key], own["symmetric"][value])
direction_map = {"cross_selected_mean": "chosen_mean", "fixed_evaluation_means": "fixed_means",
    "gain_vs_each_fixed": "gain_vs_each_fixed", "hindsight_evaluation_best_fixed_arm": "hindsight_evaluation_fixed",
    "gain_vs_hindsight_evaluation_best_fixed": "gain_vs_hindsight_fixed", "leave_fold_fixed_mean": "lofo_mean",
    "gain_vs_leave_fold_fixed": "gain_vs_lofo", "selection_ties": "selection_draw_ties",
    "chosen_arms": "choices", "cross_selected_hits": "chosen_values", "leave_fold_fixed_arms": "lofo_choices",
    "leave_fold_fixed_hits": "lofo_values", "same_draw_hindsight_best_mean": "selection_draw_hindsight_best_mean"}
for direction in ("1_to_2", "2_to_1"):
    a, b = root["directions"][direction], own["directions"][direction]
    for key, value in direction_map.items():
        compare(f"{direction}/{key}", a[key], b[value])
    for item in a["per_fold"]:
        fold = str(item["fold"])
        match = b["per_fold"][fold]
        compare(f"{direction}/fold{fold}/campaigns", item["campaigns"], match["campaigns"])
        compare(f"{direction}/fold{fold}/training_means", item["training_means"],
                [match["training_selection_draw_means"][arm] for arm in ARMS])
        compare(f"{direction}/fold{fold}/fixed_arm", item["fixed_arm"], match["fixed_selected_on_other_folds"])
        compare(f"{direction}/fold{fold}/cross_mean", item["cross_selected_mean"], match["chosen_mean"])
        compare(f"{direction}/fold{fold}/fixed_mean", item["fixed_evaluation_mean"],
                match["evaluation_fixed_means"][match["fixed_selected_on_other_folds"]])
for i, (a, b) in enumerate(zip(root["campaigns_metadata"], own["campaigns"])):
    for key in ("fold", "campaign_index", "family_count", "compound_indices"):
        compare(f"metadata/{i}/{key}", a[key], b[key])
    compare(f"metadata/{i}/compounds", a["compounds"], 64)
compare("utilities", root["utilities"], [[r["u1"] for r in own["campaigns"]], [r["u2"] for r in own["campaigns"]]])
for i, (a, b) in enumerate(zip(root["excluded_incomplete"], own["excluded"])):
    for key in ("fold", "campaign_index", "compounds"):
        compare(f"excluded/{i}/{key}", a[key], b[key])
report = {"passed": all(x["passed"] for x in checks), "checks": len(checks),
          "maxdiff": max(x.get("absdiff", 0) for x in checks),
          "mismatches": [x for x in checks if not x["passed"]],
          "source_hashes": {"root_frozen_audit": sha(root_path), "independent_recompute": sha(own_path)},
          "comparison_code_sha256": sha(Path(__file__)), "all_checks": checks}
output = LOG / "HISTORICAL_COMPARISON.json"
if output.exists():
    raise RuntimeError("Refuse to overwrite comparison evidence")
output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: report[k] for k in ("passed", "checks", "maxdiff", "mismatches")}))
raise SystemExit(0 if report["passed"] else 1)
