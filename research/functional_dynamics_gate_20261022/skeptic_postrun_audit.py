"""Independent non-fit audit of saved HTS001 predictions and frozen choices.

Does not import hts_gate, load the pickle, or read the biological source CSV.
"""
import ast
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("D:/MAESTRO")
BASE = ROOT / "log/20261022/functional_dynamics_gate"
OUT = BASE / "hts_gate"
freeze_path = OUT / "MODEL_FREEZE_BEFORE_TEST_TARGETS.json"
result_path = OUT / "RESULT.json"
frozen = json.loads(freeze_path.read_text(encoding="utf-8"))
result = json.loads(result_path.read_text(encoding="utf-8"))
identity = json.loads((OUT / "IDENTITY_SPLIT_BEFORE_RESPONSES.json").read_text(encoding="utf-8"))
checks = []


def check(name, condition, detail=None):
    checks.append({"name": name, "pass": bool(condition), "detail": detail})


def near(a, b):
    return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)


def metrics(keys, prediction, target):
    # Independent grouping implementation of drug -> background -> dose -> well.
    errors = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for key, pred, observed in zip(keys, prediction, target):
        errors[key[0]][key[1]][key[2]].append(abs(pred - observed))
    by_drug = {}
    for drug, backgrounds in errors.items():
        by_background = []
        for doses in backgrounds.values():
            by_background.append(sum(sum(wells) / len(wells) for wells in doses.values()) / len(doses))
        by_drug[drug] = sum(by_background) / len(by_background)
    return sum(by_drug.values()) / len(by_drug), by_drug


split = result["split"]
all_drugs = sum(split.values(), [])
ordered = sorted(all_drugs, key=lambda drug: hashlib.sha256(
    ("HTS001-functional-gate-v1|" + drug).encode()).hexdigest())
expected_split = {"train": ordered[:8], "validation": ordered[8:11], "test": ordered[11:]}
check("identity_hash_split_and_no_overlap", len(set(all_drugs)) == 14 and split == expected_split
      and split == identity["split"])
check("no_identity_exclusions", identity["excluded"] == [] and identity["eligible"] == 1960)
for relative, expected in frozen["sha256"].items():
    # Source hash retained by root; do not open the raw biological payload here.
    if relative.replace("\\", "/").endswith("root_scout/hts001.body"):
        continue
    actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    check("frozen_hash:" + relative, actual == expected, actual)

train = set(split["train"])
validation = set(split["validation"])
check("11_train_only_alpha_trials", len(frozen["alpha_trials"]) == 11 and all(
    set(trial["per_drug"]) == train and near(trial["alpha"], i / 10)
    and near(trial["macro_mae"], sum(trial["per_drug"].values()) / 8)
    for i, trial in enumerate(frozen["alpha_trials"])))
best_alpha = min(frozen["alpha_trials"], key=lambda trial: (trial["macro_mae"], trial["alpha"]))["alpha"]
check("alpha_selection_and_search_equal", frozen["alpha"] == best_alpha == frozen["ordinary_search_alpha"])
expected_names = {"ridge_" + str(a) for a in [.01, .1, 1, 10, 100, 1000]}
expected_names |= {f"hgb_{leaves}_{l2}" for leaves in [7, 15] for l2 in [0, 10]}
expected_names |= {f"extratrees_{depth}_{leaf}" for depth in [8, None] for leaf in [3, 10]}
check("14_validation_only_direct_trials", len(frozen["direct_trials"]) == 14
      and {trial["name"] for trial in frozen["direct_trials"]} == expected_names
      and all(set(trial["per_drug"]) == validation
              and near(trial["macro_mae"], sum(trial["per_drug"].values()) / 3)
              for trial in frozen["direct_trials"]))
best_direct = min(frozen["direct_trials"], key=lambda trial: (trial["macro_mae"], trial["name"]))["name"]
check("direct_selected_by_validation", frozen["selected_direct"] == best_direct)

keys, target, predictions = frozen["test_keys"], result["test_targets"], frozen["test_predictions"]
check("420_unique_test_wells_three_drugs", len(keys) == len(target) == 420
      and len({tuple(key) for key in keys}) == 420
      and set(key[0] for key in keys) == set(split["test"])
      and Counter(key[0] for key in keys) == Counter({drug: 140 for drug in split["test"]}))
groups = Counter(tuple(key[:3]) for key in keys)
backgrounds = Counter(tuple(key[:2]) for key in keys)
check("balanced_test_macro_cells_doses_wells", len(groups) == 210 and set(groups.values()) == {2}
      and len(backgrounds) == 21 and set(backgrounds.values()) == {20})
check("finite_nonnegative_log_targets", all(math.isfinite(value) and value >= 0 for value in target))

recomputed = {}
prediction_ranges = {}
for name, prediction in predictions.items():
    check("finite_prediction_shape:" + name, len(prediction) == len(keys)
          and all(math.isfinite(value) for value in prediction))
    macro, by_drug = metrics(keys, prediction, target)
    saved = result["scores"][name]
    check("independent_saved_score:" + name, near(macro, saved["macro_mae"])
          and set(by_drug) == set(saved["per_drug"])
          and all(near(value, saved["per_drug"][drug]) for drug, value in by_drug.items()))
    recomputed[name] = {"macro_mae": macro, "per_drug": by_drug}
    prediction_ranges[name] = {"min_log2_count_plus_one": min(prediction),
                              "max_log2_count_plus_one": max(prediction),
                              "negative_log_predictions": sum(value < 0 for value in prediction)}
check("saved_forecasts_nonnegative_log_counts", all(
    info["negative_log_predictions"] == 0 for info in prediction_ranges.values()))

check("exact_inherited_search_half_mixture_predictions", predictions["inherited_psi1"]
      == predictions["equal_budget_search"] == predictions["simple_half_mixture"])
check("independent_updater_affine_identity", all(near(p, (1 - best_alpha) * initial + best_alpha * local)
      for p, initial, local in zip(predictions["inherited_psi1"], predictions["readout_only"],
                                   predictions["ordinary_local_psi0"])))
check("blend_prediction_identity", all(near(blend, .5 * (direct + inherited))
      for blend, direct, inherited in zip(predictions["direct_world_half_blend"],
      predictions["selected_direct"], predictions["inherited_psi1"])))

for comparison in result["contrasts"]:
    a, b = comparison["candidate"], comparison["comparator"]
    gain = recomputed[b]["macro_mae"] - recomputed[a]["macro_mae"]
    check("contrast_and_threshold:" + b, near(gain, comparison["mae_reduction"])
          and near(gain / recomputed[b]["macro_mae"], comparison["relative_reduction"])
          and comparison["useful_gain_pass"] == (gain >= .1 and gain >= .1 * recomputed[b]["macro_mae"])
          and all(near(recomputed[b]["per_drug"][drug] - recomputed[a]["per_drug"][drug], value)
                  for drug, value in comparison["per_drug_gain"].items()))
check("primary_advance_false_consistent", result["advance_signal"] is False
      and result["advance_signal"] == all(comparison["useful_gain_pass"] for comparison in result["contrasts"][:2]))

code_path = ROOT / "research/functional_dynamics_gate_20261022/hts_gate.py"
tree = ast.parse(code_path.read_text(encoding="utf-8"))
main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
freeze_line = next(node.lineno for node in ast.walk(main) if isinstance(node, ast.Call)
                   and isinstance(node.func, ast.Name) and node.func.id == "save"
                   and node.args and "MODEL_FREEZE_BEFORE_TEST_TARGETS.json" in ast.unparse(node.args[0]))
target_line = next(node.lineno for node in main.body if isinstance(node, ast.Assign)
                   and any(isinstance(name, ast.Name) and name.id == "yt" for name in node.targets))
check("static_freeze_before_test_target_call", freeze_line < target_line,
      {"model_freeze_line": freeze_line, "test_target_line": target_line})
check("no_future_fit_after_test_target_call", not any(isinstance(node, ast.Call)
      and ((isinstance(node.func, ast.Name) and node.func.id == "fit_direct")
           or (isinstance(node.func, ast.Attribute) and node.func.attr == "fit"))
      and node.lineno > target_line for node in ast.walk(main)))
check("local_artifact_order", (OUT / "IDENTITY_SPLIT_BEFORE_RESPONSES.json").stat().st_mtime_ns
      <= freeze_path.stat().st_mtime_ns <= result_path.stat().st_mtime_ns)

report = {"utc": datetime.now(timezone.utc).isoformat(), "checks": checks,
          "all_pass": all(item["pass"] for item in checks), "check_count": len(checks),
          "prediction_ranges": prediction_ranges,
          "no_fit": True, "source_csv_opened": False, "pickle_loaded": False,
          "artifact_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                              for path in [freeze_path, result_path, code_path]},
          "scope": "Static implementation and saved-prediction arithmetic; no cryptographic chronology or independent biological replication"}
(BASE / "skeptic/POST_RUN_AUDIT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({key: report[key] for key in ["all_pass", "check_count", "no_fit", "source_csv_opened"]}))
for item in checks:
    if not item["pass"]:
        print(json.dumps(item))
