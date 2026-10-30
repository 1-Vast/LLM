"""One bounded arithmetic diagnostic; never fit, sample, or change actions."""
import os
for key in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
    os.environ[key] = "1"
import hashlib
import json
import math
from pathlib import Path
import time
import traceback

START = time.process_time()
import numpy as np
from scipy.special import ndtr

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8-sig"))


def arrays(name):
    with np.load(ROOT / name, allow_pickle=False) as f:
        return {k: f[k] for k in f.files}


def sha(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


def budget():
    assert time.process_time() - START <= 10, "Numerical diagnostic CPU exceeded 10 seconds"


def posterior(a, m, p, r, js, s, mode):
    if mode == "direct":
        if len(js) == 0:
            return m.copy(), p.copy()
        b = a[js]
        cross = p @ b.T
        gram = b @ cross + np.diag(r[js])
        return m + cross @ np.linalg.solve(gram, s - b @ m), p - cross @ np.linalg.solve(gram, cross.T)
    m, p = m.copy(), p.copy()
    for j, value in zip(js, s):
        cross = p @ a[j]
        denominator = r[j] + a[j] @ cross
        m = m + cross * ((value - a[j] @ m) / denominator)
        p = p - np.outer(cross, cross) / denominator
    return m, p


def prob(mean, variance, lo, hi, cdf_name):
    sigma = np.sqrt(variance)
    if cdf_name == "ndtr":
        cdf = ndtr
    else:
        cdf = np.vectorize(lambda x: math.erfc(-x / math.sqrt(2)) * 0.5, otypes=[float])
    return cdf((hi - mean) / sigma) - cdf((lo - mean) / sigma)


def run(result):
    names = ["independent_verification.json", "independent_verification_v2.json", "independent_verification_final.json",
             "independent_training_model.npz", "independent_replay_arrays.npz", "independent_training_freeze.json",
             "training_model.npz", "replay_arrays.npz", "training_freeze.json", "feedback_access.jsonl"]
    hashes = {name: sha(name) for name in names}
    prior = load("independent_verification_final.json")
    assert prior["status"] == "MISMATCH"
    assert prior["feedback_log_audit"]["issues"] == []
    assert prior["feedback_log_audit"]["max_value_difference"] == 0
    own, main = arrays("independent_training_model.npz"), arrays("training_model.npz")
    saved, replay = arrays("independent_replay_arrays.npz"), arrays("replay_arrays.npz")
    freeze = load("independent_training_freeze.json")
    test_ids = load("training_freeze.json")["test_ids"]
    menu, probes = freeze["menu"], own["probes"].tolist()
    remaining = np.array([j for j in range(64) if j not in probes])
    x = np.full((243, 64), np.nan)
    for line in (ROOT / "feedback_access.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row["phase"] == "shared_probe" and row["value"] is not None:
            x[row["cell_index"], row["condition_index"]] = row["value"]
    probabilities, prediction_means = {}, {}
    for source, model, keys in (("independent", own, ("A8", "m8", "P8", "r8")),
                                ("main", main, ("a8", "m8", "p8", "noise8"))):
        a, m, p, r = (model[k] for k in keys)
        lo = (model["mu"] - np.minimum(0, model["high"])) / model["sd"]
        hi = (model["mu"] - model["low"]) / model["sd"]
        for mode in ("direct", "recursive"):
            mean_array = np.zeros((243, 2, 64))
            variance_array = np.zeros((243, 2, 64))
            for i in range(243):
                js = [j for j in probes if np.isfinite(x[i, j])]
                s = (model["mu"][js] - x[i, js]) / model["sd"][js]
                pm, pc = posterior(a, m, p, r, js, s, mode)
                mean_array[i, 0], mean_array[i, 1] = a @ m, a @ pm
                variance_array[i, 0], variance_array[i, 1] = r + np.diag(a @ p @ a.T), r + np.diag(a @ pc @ a.T)
                if i % 50 == 0:
                    budget()
            prediction_means[source + "_" + mode] = mean_array
            for cdf_name in ("erfc", "ndtr"):
                key = source + "_" + mode + "_" + cdf_name
                probabilities[key] = prob(mean_array, variance_array, lo, hi, cdf_name)
    probabilities["logged"] = replay["probability_predictions"]
    order_full = {k: np.argsort(-v, axis=2, kind="stable") for k, v in probabilities.items()}
    order_remaining = {k: remaining[np.argsort(-v[:, :, remaining], axis=2, kind="stable")] for k, v in probabilities.items()}
    baseline = "independent_direct_erfc"
    result["variant_comparison"] = {}
    for key, values in probabilities.items():
        result["variant_comparison"][key] = {
            "max_probability_difference_vs_logged": float(np.max(np.abs(values - probabilities["logged"]))),
            "max_probability_difference_vs_independent_direct_erfc": float(np.max(np.abs(values - probabilities[baseline]))),
            "complete_order_coordinate_differences_vs_logged_order": int((order_full[key] != replay["probability_orders"]).sum()),
            "nonprobe_order_coordinate_differences_vs_logged_order": int((order_remaining[key] != replay["followup_probability_orders"]).sum())}
    result["mean_arithmetic_comparison"] = {key: float(np.max(np.abs(values - replay["predictions"]))) for key, values in prediction_means.items()}
    result["controlled_factor_differences"] = {}
    for left, right, label in (("independent_direct_erfc", "independent_direct_ndtr", "cdf_only_independent_direct"),
                               ("independent_direct_ndtr", "independent_recursive_ndtr", "conditioning_only_independent_ndtr"),
                               ("independent_direct_ndtr", "main_direct_ndtr", "saved_model_and_standardization_only_direct_ndtr"),
                               ("main_direct_ndtr", "main_recursive_ndtr", "conditioning_only_main_ndtr")):
        result["controlled_factor_differences"][label] = {
            "max_probability_difference": float(np.max(np.abs(probabilities[left] - probabilities[right]))),
            "complete_order_coordinate_differences": int((order_full[left] != order_full[right]).sum()),
            "nonprobe_order_coordinate_differences": int((order_remaining[left] != order_remaining[right]).sum())}
    coordinates, involved = [], set()
    for scope, own_order, logged_order in (("complete", order_full[baseline], replay["probability_orders"]),
                                          ("nonprobe", order_remaining[baseline], replay["followup_probability_orders"])):
        for i, stage, position in np.argwhere(own_order != logged_order):
            i, stage, position = int(i), int(stage), int(position)
            expected, actual = int(own_order[i, stage, position]), int(logged_order[i, stage, position])
            involved.add((i, stage))
            coordinates.append(dict(scope=scope, cell_index=i, sidm=test_ids[i], stage=stage, rank_zero_based=position,
                independent_condition=menu[expected], logged_condition=menu[actual],
                independent_probability_pair=[float(probabilities[baseline][i, stage, j]) for j in (expected, actual)],
                logged_probability_pair=[float(probabilities["logged"][i, stage, j]) for j in (expected, actual)]))
    result["all_different_coordinates"] = coordinates
    pairs, boundary = [], []
    own_action_index = saved["strategy_order"].tolist().index("rank8")
    for i, stage in sorted(involved):
        expected_order, logged_order = order_full[baseline][i, stage], replay["probability_orders"][i, stage]
        expected_rank, logged_rank = np.argsort(expected_order), np.argsort(logged_order)
        changed = set(expected_order[expected_order != logged_order].tolist()) | set(logged_order[expected_order != logged_order].tolist())
        selected_followup = saved["actions"][i, own_action_index, 8:].tolist()
        for first in sorted(changed):
            for second in sorted(changed):
                if first >= second or (expected_rank[first] - expected_rank[second]) * (logged_rank[first] - logged_rank[second]) >= 0:
                    continue
                pairs.append(dict(cell_index=i, sidm=test_ids[i], stage=stage, condition_indices=[first, second],
                    conditions=[menu[first], menu[second]],
                    independent_ranks_zero_based=[int(expected_rank[first]), int(expected_rank[second])],
                    logged_ranks_zero_based=[int(logged_rank[first]), int(logged_rank[second])],
                    selected_followup=[j in selected_followup for j in (first, second)],
                    probabilities={key: [float(values[i, stage, first]), float(values[i, stage, second])] for key, values in probabilities.items()},
                    pair_probability_differences={key: float(values[i, stage, first] - values[i, stage, second]) for key, values in probabilities.items()}))
        eb, lb = order_remaining[baseline][i, stage], replay["followup_probability_orders"][i, stage]
        boundary.append(dict(cell_index=i, sidm=test_ids[i], stage=stage,
            independent_first_five_conditions=[menu[j] for j in eb[:5]], logged_first_five_conditions=[menu[j] for j in lb[:5]],
            same_first_five_order=bool(np.array_equal(eb[:5], lb[:5])),
            any_changed_condition_in_recorded_followup=bool(changed.intersection(selected_followup)),
            independent_fifth_sixth_probability_gap=float(probabilities[baseline][i, stage, eb[4]] - probabilities[baseline][i, stage, eb[5]]),
            logged_fifth_sixth_probability_gap=float(probabilities["logged"][i, stage, lb[4]] - probabilities["logged"][i, stage, lb[5]])))
    result["inverted_condition_pairs"] = pairs
    result["first_five_boundary_audit"] = boundary
    result["summary"] = dict(different_complete_coordinates=sum(c["scope"] == "complete" for c in coordinates),
        different_nonprobe_coordinates=sum(c["scope"] == "nonprobe" for c in coordinates),
        affected_cell_stage_count=len(involved), inverted_pair_count=len(pairs),
        changed_first_five_orders=sum(not b["same_first_five_order"] for b in boundary),
        affected_cells_with_changed_condition_in_recorded_followup=sum(b["any_changed_condition_in_recorded_followup"] for b in boundary),
        maximum_inverted_pair_absolute_probability_gap=max((abs(delta) for pair in pairs for delta in pair["pair_probability_differences"].values()), default=0),
        complete_rank_zero_based_range=[min(c["rank_zero_based"] for c in coordinates if c["scope"] == "complete"), max(c["rank_zero_based"] for c in coordinates if c["scope"] == "complete")],
        nonprobe_rank_zero_based_range=[min(c["rank_zero_based"] for c in coordinates if c["scope"] == "nonprobe"), max(c["rank_zero_based"] for c in coordinates if c["scope"] == "nonprobe")])
    result["artifact_sha256"] = hashes
    assert all(sha(name) == value for name, value in hashes.items()), "Existing artifact changed"
    result["existing_artifacts_unchanged"] = True
    result["status"] = "AUDIT_COMPLETE"
    result["interpretation_boundary"] = "Records numerical differences without changing tolerance or prior MISMATCH. No scientific or mechanistic hypothesis is re-evaluated."


def main():
    target = ROOT / "order_numerics_audit.json"
    with target.open("x", encoding="utf-8") as f:
        json.dump({"status": "RUNNING"}, f)
    result = dict(status="RUNNING", scientific_replays=0, diagnostic_runs=1,
                  implementation_sha256=sha(Path(__file__).name),
                  label_provenance="Previously source-verified fixed shared-probe feedback_access values; prior audit exact value difference zero")
    try:
        run(result)
        budget()
    except Exception as exc:
        result["status"] = "AUDIT_INVALID"
        result["error"] = type(exc).__name__ + ": " + str(exc)
        result["traceback"] = traceback.format_exc()
    result["cpu_seconds"] = time.process_time() - START
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "cpu_seconds", "summary", "variant_comparison", "controlled_factor_differences") if k in result}, ensure_ascii=False))


if __name__ == "__main__":
    main()
