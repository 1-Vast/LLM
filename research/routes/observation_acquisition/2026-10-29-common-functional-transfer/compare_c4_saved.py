"""Resume comparison of the ONE completed independent C4 computation.

Never train, select a menu/panel/action, or draw bootstrap samples here.
Saved independent artifacts are immutable expected values. Source access only
recovers feedback labels at already-saved row indices for posterior/log checks.
"""
import os
for key in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[key] = "1"
import csv
import ctypes
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import traceback

START_CPU = time.process_time()
START_WALL = time.monotonic()
import numpy as np

ROOT = Path(__file__).resolve().parent
SOURCE = Path("D:/MAESTRO/tmp/extq1/GDSC2_fitted_dose_response.csv")


def read_json(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8-sig"))


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def peak_memory():
    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("faults", ctypes.c_ulong)] + [
            (name, ctypes.c_size_t) for name in ("peak_working", "working", "peak_paged", "paged",
                                               "peak_nonpaged", "nonpaged", "pagefile", "peak_pagefile")]
    c = Counters()
    c.cb = ctypes.sizeof(c)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(c), c.cb):
        raise OSError(ctypes.get_last_error(), "GetProcessMemoryInfo")
    return max(c.peak_working, c.peak_pagefile)


def load_npz(name):
    with np.load(ROOT / name, allow_pickle=False) as data:
        return {k: data[k] for k in data.files}


def direct(a, m, p, r, observed, values):
    if len(observed) == 0:
        return m.copy(), p.copy()
    design = a[observed]
    cross = p @ design.T
    gram = design @ cross + np.diag(r[observed])
    return (m + cross @ np.linalg.solve(gram, values - design @ m),
            p - cross @ np.linalg.solve(gram, cross.T))


def interval_probability(mean, variance, lo, hi):
    cdf = np.vectorize(lambda x: math.erfc(-x / math.sqrt(2)) * 0.5, otypes=[float])
    scale = np.sqrt(variance)
    return cdf((hi - mean) / scale) - cdf((lo - mean) / scale)


def restore_feedback(meta, frozen, saved, own_actions, probes):
    """Do not select records anew: every accessed row number was saved by v2."""
    test_cells = [c for c in meta["cells"] if c["role"] == "model_unseen_exposed_development"]
    condition_by_id = {c["id"]: c for c in meta["conditions"]}
    menu = [condition_by_id[name] for name in frozen["menu"]]
    needed, values = {}, np.full((243, 64), np.nan)
    selected_mask = np.zeros((243, 64), dtype=bool)
    for i in range(243):
        js = set(probes) | set(own_actions["rank1"][i, 8:]) | set(own_actions["rank8"][i, 8:])
        for j in js:
            selected_mask[i, j] = True
            row_index = int(saved["test_source_rows"][i, j])
            if row_index >= 0:
                assert row_index not in needed, "Saved source row assigned to multiple identities"
                needed[row_index] = (i, j)
    found = 0
    with SOURCE.open(encoding="utf-8-sig", newline="") as f:
        for row_index, row in enumerate(csv.DictReader(f)):
            if row_index not in needed:
                continue
            i, j = needed[row_index]
            cond = menu[j]
            assert row["SANGER_MODEL_ID"] == test_cells[i]["id"]
            assert (row["DRUG_ID"], row["MIN_CONC"], row["MAX_CONC"]) == (cond["drug_id"], cond["min_conc_raw"], cond["max_conc_raw"])
            assert int(row["NLME_RESULT_ID"]) == int(saved["test_result_ids"][i, j])
            raw = row["LN_IC50"]
            try:
                values[i, j] = float(raw)
            except ValueError:
                assert raw.strip().lower() in ("", "na", "nan", "null", "none")
            found += 1
    assert found == len(needed), "A previously saved source row is absent"
    return values, selected_mask


def compare(report, prior):
    def check(name, expected, actual, tolerance=1e-8):
        a, b = np.asarray(expected), np.asarray(actual)
        result = dict(name=name, expected_shape=list(a.shape), actual_shape=list(b.shape), tolerance=tolerance)
        if a.shape != b.shape:
            result.update(matches=False, reason="shape mismatch")
        elif a.dtype.kind in "OUS" or b.dtype.kind in "OUS":
            result["matches"] = bool(np.array_equal(a, b))
        else:
            mask = np.isfinite(a) & np.isfinite(b)
            differences = np.abs(a[mask].astype(float) - b[mask].astype(float))
            result["max_absolute_difference"] = float(differences.max()) if differences.size else 0.
            result["matching_finite_masks"] = bool(np.array_equal(np.isfinite(a), np.isfinite(b)))
            result["matches"] = bool(np.array_equal(a, b, equal_nan=True)) if tolerance == 0 else bool(np.allclose(a, b, rtol=0, atol=tolerance, equal_nan=True))
            if not result["matches"] and a.shape == b.shape:
                bad = ~np.isclose(a, b, rtol=0, atol=tolerance, equal_nan=True)
                result["different_element_count"] = int(bad.sum())
                result["first_different_indices"] = np.argwhere(bad)[:10].tolist()
        report["comparisons"].append(result)
        if not result["matches"]:
            report["errors"].append(name + " differs")
        return result["matches"]

    immutable = dict(prior["independent_artifact_sha256"])
    immutable.update(prior["main_artifact_sha256"])
    actual_hashes = {name: sha(ROOT / name) for name in immutable}
    for name, expected in immutable.items():
        assert actual_hashes[name] == expected, "Artifact changed since v2 comparison: " + name
    report["verified_existing_artifact_sha256"] = actual_hashes
    independent = load_npz("independent_training_model.npz")
    saved = load_npz("independent_replay_arrays.npz")
    frozen = read_json("independent_training_freeze.json")
    main_freeze = read_json("training_freeze.json")
    main = load_npz("training_model.npz")
    replay = load_npz("replay_arrays.npz")
    summary = read_json("experiment_summary.json")
    action_freeze = read_json("actions_freeze.json")
    own_action_freeze = read_json("independent_actions_freeze.json")
    meta = read_json("metadata_freeze.json")
    own_order = saved["strategy_order"].tolist()
    main_order = action_freeze["strategy_order"]
    actions = {name: saved["actions"][:, i, :] for i, name in enumerate(own_order)}
    probes = independent["probes"].tolist()
    expected_actions = np.stack([actions[name] for name in main_order], axis=1)
    report["strategy_order"] = main_order
    check("frozen source hash", frozen["source_sha256"], sha(SOURCE), 0)
    check("metadata source hash", meta["source_sha256"], sha(SOURCE), 0)
    check("protocol at independent freeze", frozen["protocol_sha256"], sha(ROOT / "protocol_c4_v2.md"), 0)
    check("protocol at main freeze", main_freeze["protocol_sha256"], sha(ROOT / "protocol_c4_v2.md"), 0)
    check("independent model freeze hash", frozen["training_model_sha256"], actual_hashes["independent_training_model.npz"], 0)
    check("main model freeze hash", main_freeze["training_artifact_sha256"], actual_hashes["training_model.npz"], 0)
    check("independent implementation recorded", prior["implementation_sha256"], frozen["implementation_sha256"], 0)
    check("independent computation implementation unchanged", prior["implementation_sha256"], sha(ROOT / "independent_c4_verify.py"), 0)
    check("independent training before test", True, frozen["training_complete_before_test_numeric_conversion"], 0)
    check("main training before test", False, main_freeze["test_functional_values_consumed"], 0)
    check("panel indices", probes, main_freeze["probes"], 0)
    check("independent frozen panel indices", probes, frozen["probes"], 0)
    check("train identity order", [c["id"] for c in meta["cells"] if c["role"] == "train"], main_freeze["train_ids"], 0)
    test_ids = [c["id"] for c in meta["cells"] if c["role"] == "model_unseen_exposed_development"]
    check("test identity order", test_ids, main_freeze["test_ids"], 0)
    mappings = {"train_y": "train_x", "s": "s", "finite": "finite", "event": "event", "mu": "mu", "sd": "sd",
                "low": "low", "high": "high", "global_rate": "global_rate", "probes": "probes",
                "ridge_weights": "ridge_weights", "ridge_noise": "ridge_noise"}
    for key, own_key in mappings.items():
        check("training." + key, independent[own_key], main[key], 0 if key in ("finite", "event", "probes") else 1e-8)
    check("all eight policy actions", expected_actions, replay["actions"], 0)
    check("shared bootstrap indices", saved["bootstrap_indices"], replay["bootstrap_indices"], 0)
    check("main actions SHA", sha_bytes(replay["actions"]), action_freeze["actions_sha256"], 0)
    check("independent actions SHA", sha_bytes(saved["actions"]), own_action_freeze["actions_sha256"], 0)
    check("main actions before full truth", True, action_freeze["all_actions_fixed_before_full_truth_conversion"], 0)
    check("independent actions before full truth", True, own_action_freeze["all_actions_fixed_before_full_truth_conversion"], 0)
    for index, name in enumerate(own_order):
        lower, upper = saved["candidate_lower"][:, index], saved["candidate_upper"][:, index]
        main_choices = replay["actions"][:, main_order.index(name), :]
        derived_lower = np.take_along_axis(saved["test_event"], main_choices, axis=1).sum(axis=1)
        derived_unknown = (~np.take_along_axis(saved["test_finite"], main_choices, axis=1)).sum(axis=1)
        check(name + ".per_cell_lower_from_main_actions", lower, derived_lower, 0)
        check(name + ".per_cell_upper_from_main_actions", upper, derived_lower + derived_unknown, 0)
        for field, value in (("candidate_count_lower", lower.mean()), ("candidate_count_upper", upper.mean()),
                             ("mean_unknown_attempts", (upper - lower).mean()), ("attempts_per_cell", 13)):
            check(name + "." + field, value, summary["metrics"][name][field])
    recovered_main = {}
    for index, name in enumerate(saved["paired_control_order"].tolist()):
        bounds = saved["paired_bounds"][:, index]
        derived_bounds = []
        for cell in range(243):
            left = replay["actions"][cell, main_order.index("rank8")]
            right = replay["actions"][cell, main_order.index(name)]
            only_left, only_right = np.setdiff1d(left, right), np.setdiff1d(right, left)
            known_difference = int(saved["test_event"][cell, only_left].sum()) - int(saved["test_event"][cell, only_right].sum())
            derived_bounds.append([known_difference - int((~saved["test_finite"][cell, only_right]).sum()),
                                   known_difference + int((~saved["test_finite"][cell, only_left]).sum())])
        check(name + ".per_cell_paired_bounds_from_main_actions", bounds, derived_bounds, 0)
        boot_mean = bounds[saved["bootstrap_indices"], 0].mean(axis=1)
        ci = np.quantile(boot_mean, [0.025, 0.975], method="linear")
        lower, upper = float(bounds[:, 0].mean()), float(bounds[:, 1].mean())
        gate = bool(lower >= 0.5 and ci[0] > 0)
        recovered_main[name] = dict(mean_lower=lower, mean_upper=upper, ci=ci.tolist(), gate=gate)
        for field, value in (("mean_difference_lower", lower), ("mean_difference_upper", upper),
                             ("difference_lower_bootstrap_ci95", ci), ("passes_point_and_ci", gate)):
            check(name + "." + field, value, summary["comparisons"][name][field])
        check(name + ".v2_saved_ci", ci, prior["independent_main"][name]["ci"])
    joint = all(row["gate"] for row in recovered_main.values())
    check("joint hypothesis gate", joint, summary["hypothesis_joint_supported"], 0)
    check("joint hypothesis gate from v2", joint, prior["independent_joint_gate"], 0)
    report["independent_main"] = recovered_main
    report["independent_joint_gate"] = joint
    feedback, feedback_mask = restore_feedback(meta, frozen, saved, actions, probes)
    check("restored feedback finite mask", saved["test_finite"][feedback_mask], np.isfinite(feedback[feedback_mask]), 0)
    event = np.isfinite(feedback) & (feedback > independent["low"] + 1e-8) & (feedback < independent["high"] - 1e-8) & (feedback <= 0)
    check("restored feedback saved events", saved["test_event"][feedback_mask], event[feedback_mask], 0)
    lo = (independent["mu"] - np.minimum(0, independent["high"])) / independent["sd"]
    hi = (independent["mu"] - independent["low"]) / independent["sd"]
    for rank in (1, 8):
        a, m, p, r = (independent[k + str(rank)] for k in ("A", "m", "P", "r"))
        ma, mm, mp, mr = (main[k + str(rank)] for k in ("a", "m", "p", "noise"))
        check(f"rank{rank}.prior_mean", a @ m, ma @ mm)
        check(f"rank{rank}.prior_covariance", a @ p @ a.T, ma @ mp @ ma.T)
        check(f"rank{rank}.loading_subspace", a[:, 1:] @ a[:, 1:].T, ma[:, 1:] @ ma[:, 1:].T)
        check(f"rank{rank}.noise", r, mr)
        own_means, main_means, own_covs, main_covs = [], [], [], []
        own_final, main_final = [], []
        for i in range(243):
            observed = [j for j in probes if np.isfinite(feedback[i, j])]
            values = (independent["mu"][observed] - feedback[i, observed]) / independent["sd"][observed]
            pm, pc = direct(a, m, p, r, observed, values)
            mpm, mpc = direct(ma, mm, mp, mr, observed, values)
            own_means.append(a @ pm)
            main_means.append(ma @ mpm)
            own_covs.append(a @ pc @ a.T)
            main_covs.append(ma @ mpc @ ma.T)
            final_observed = [int(j) for j in actions["rank" + str(rank)][i] if np.isfinite(feedback[i, j])]
            final_values = (independent["mu"][final_observed] - feedback[i, final_observed]) / independent["sd"][final_observed]
            fm, fc = direct(a, m, p, r, final_observed, final_values)
            mfm, mfc = direct(ma, mm, mp, mr, final_observed, final_values)
            own_final.append(np.r_[a @ fm, (a @ fc @ a.T).ravel()])
            main_final.append(np.r_[ma @ mfm, (ma @ mfc @ ma.T).ravel()])
        own_means, own_covs = np.array(own_means), np.array(own_covs)
        check(f"rank{rank}.postprobe_predictive_mean", own_means, main_means)
        check(f"rank{rank}.postprobe_predictive_covariance", own_covs, main_covs)
        check(f"rank{rank}.final_direct_predictive_mean_and_covariance", own_final, main_final)
        if rank == 8:
            predicted = np.stack((np.tile(a @ m, (243, 1)), own_means), axis=1)
            check("rank8 serialized prior/postprobe means", predicted, replay["predictions"])
            prior_prob = interval_probability(a @ m, r + np.diag(a @ p @ a.T), lo, hi)
            posterior_prob = np.array([interval_probability(own_means[i], r + np.diag(own_covs[i]), lo, hi) for i in range(243)])
            probabilities = np.stack((np.tile(prior_prob, (243, 1)), posterior_prob), axis=1)
            check("rank8 serialized prior/postprobe probabilities", probabilities, replay["probability_predictions"])
            # These are diagnostic order checks only, never new policy choices.
            orders = np.argsort(-probabilities, axis=2, kind="stable")
            check("rank8 serialized complete probability orders", orders, replay["probability_orders"], 0)
            remaining = np.array([j for j in range(64) if j not in probes])
            followup_orders = remaining[np.argsort(-probabilities[:, :, remaining], axis=2, kind="stable")]
            check("rank8 serialized nonprobe probability orders", followup_orders, replay["followup_probability_orders"], 0)
    verify_logs(report, check, saved, actions, feedback, feedback_mask, probes, test_ids, action_freeze)
    # Confirm comparison did not mutate any model, receipt, or scientific output.
    for name, expected in actual_hashes.items():
        assert sha(ROOT / name) == expected, "Artifact mutated during comparison: " + name
    report["existing_artifacts_unchanged"] = True


def sha_bytes(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def verify_logs(report, check, saved, actions, feedback, feedback_mask, probes, test_ids, action_freeze):
    traces = [json.loads(line) for line in (ROOT / "query_trace.jsonl").read_text().splitlines() if line.strip()]
    check("query trace count", 243, len(traces), 0)
    for i, row in enumerate(traces):
        check(f"trace.{i}.identity", test_ids[i], row["cell"], 0)
        check(f"trace.{i}.finite_probe_updates", saved["test_finite"][i, probes].sum(), row["finite_probe_updates"], 0)
        check(f"trace.{i}.policies", np.stack([actions[k][i] for k in actions]), np.stack([row["policies"][k] for k in actions]), 0)
    accesses = [json.loads(line) for line in (ROOT / "feedback_access.jsonl").read_text().splitlines() if line.strip()]
    phases = {"shared_probe": None, "rank1_selected_followup": "rank1", "rank8_selected_followup": "rank8"}
    seen, issues = {}, []
    maximum_value_difference = 0.
    for entry in accesses:
        i, j, phase = entry["cell_index"], entry["condition_index"], entry["phase"]
        if not (0 <= i < 243 and 0 <= j < 64 and phase in phases):
            issues.append("invalid index/phase")
            continue
        expected_js = probes if phase == "shared_probe" else actions[phases[phase]][i, 8:].tolist()
        if phase != "shared_probe" and seen.get((i, "shared_probe")) != probes:
            issues.append(f"incomplete probes before followup: {i}")
        seen.setdefault((i, phase), []).append(j)
        if j not in expected_js or not feedback_mask[i, j]:
            issues.append(f"unselected feedback: {i},{j},{phase}")
            continue
        expected = float(feedback[i, j]) if np.isfinite(feedback[i, j]) else None
        if expected is None:
            if entry["value"] is not None:
                issues.append(f"missing value mismatch: {i},{j}")
        elif entry["value"] is None:
            issues.append(f"unexpected missing value: {i},{j}")
        else:
            difference = abs(expected - entry["value"])
            maximum_value_difference = max(maximum_value_difference, difference)
            if difference > 1e-12:
                issues.append(f"feedback value differs: {i},{j}")
    for i in range(243):
        for phase, policy in phases.items():
            expected = probes if policy is None else actions[policy][i, 8:].tolist()
            if seen.get((i, phase)) != expected:
                issues.append(f"sequence/count mismatch: {i},{phase}")
    check("feedback access declared count", len(accesses), action_freeze["feedback_numeric_accesses"], 0)
    check("feedback access expected count", 243 * 18, len(accesses), 0)
    report["feedback_log_audit"] = dict(access_count=len(accesses), issues=issues, max_value_difference=maximum_value_difference)
    report["errors"].extend(issues)


def main():
    target = ROOT / "independent_verification_final.json"
    with target.open("x", encoding="utf-8") as f:
        json.dump({"status": "RUNNING", "comparison_only_resume": True}, f)
    first, prior = read_json("independent_verification.json"), read_json("independent_verification_v2.json")
    report = dict(status="RUNNING", comparison_only_resume=True, completed_independent_scientific_recomputations=1,
                  comparison_implementation_sha256=sha(Path(__file__)), errors=[],
                  comparisons=list(prior["comparisons"]),
                  recovered_prior_comparison_count=len(prior["comparisons"]),
                  upstream_engineering_errors=[dict(receipt="independent_verification.json", error=first["errors"],
                       scientific_numeric_values_consumed=0, stage="metadata role assertion; raw CSV bytes hashed"),
                      dict(receipt="independent_verification_v2.json", error=prior["errors"],
                       stage="independent science completed and saved; comparison schema probes8 KeyError")],
                  prior_receipt_sha256={name: sha(ROOT / name) for name in ("independent_verification.json", "independent_verification_v2.json")},
                  not_repeated=["source row selection", "eligibility/menu selection", "SVD training", "A-opt panel selection",
                                "policy action selection", "bootstrap sampling"],
                  scope_limitations=[
                      "Eligibility/menu checks are inherited from the completed v2 comparisons, not recomputed in this resume.",
                      "Stored independent paired bounds/events/actions are the expected values; per-cell bounds are checked against main actions and saved independent events. Main artifacts contain no internal per-cell bound arrays; reported means/CI are compared directly.",
                      "Direct posterior comparisons use saved independent models and recovered fixed feedback. Main recursive intermediate/final states are not serialized and are not independently certified.",
                      "Access logs and freeze declarations cannot rule out unlogged memory access.",
                      "No verification of upstream NLME/export independence, donor/batch independence, actual efficacy, dose-level quality, auxiliary boundary tallies, or physical cost."])
    try:
        compare(report, prior)
        elapsed = time.process_time() - START_CPU
        assert elapsed + first["cpu_seconds"] + prior["cpu_seconds"] <= 600, "Cumulative independent CPU exceeds 600 s"
        assert max(peak_memory(), first["peak_memory_bytes"], prior["peak_memory_bytes"]) <= 2 * 1024**3, "Cumulative peak memory exceeds 2 GiB"
        report["status"] = "VERIFIED" if not report["errors"] else "MISMATCH"
    except Exception as exc:
        report["status"] = "INVALID"
        report["errors"].append(type(exc).__name__ + ": " + str(exc))
        report["traceback"] = traceback.format_exc()
    finally:
        report["comparison_cpu_seconds"] = time.process_time() - START_CPU
        report["comparison_wall_seconds"] = time.monotonic() - START_WALL
        report["cumulative_cpu_seconds"] = report["comparison_cpu_seconds"] + first["cpu_seconds"] + prior["cpu_seconds"]
        report["cumulative_wall_seconds"] = report["comparison_wall_seconds"] + first["wall_seconds"] + prior["wall_seconds"]
        report["comparison_peak_memory_bytes"] = peak_memory()
        report["cumulative_peak_memory_bytes"] = max(report["comparison_peak_memory_bytes"], first["peak_memory_bytes"], prior["peak_memory_bytes"])
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "cumulative_cpu_seconds", "cumulative_peak_memory_bytes", "errors")}, ensure_ascii=False))
    return 0 if report["status"] == "VERIFIED" else 1


if __name__ == "__main__":
    sys.exit(main())
