"""Independent, fixed-artifact C2 arithmetic verification. No original code imports.
Run only after source inspection; emits independent_verification.json beside this file.
"""
import os
for _key in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
    os.environ[_key] = "1"
import csv
import hashlib
import json
import time
import traceback
from pathlib import Path
import numpy as np

BASE = Path(__file__).resolve().parent
RAW = Path(r"D:\MAESTRO\data\external\prism_19q4\raw\primary-screen-replicate-collapsed-logfold-change.csv")
ARMS = ("fixed_global", "fixed_initial10", "random", "adaptive")
CPU_START = time.process_time()
WALL_START = time.monotonic()
REPORT = {"verification_kind": "independent implementation arithmetic audit; not scientific confirmation",
          "requested_model": "gpt-6.1-sol/high", "effective_model": "unknown",
          "http_calls": 0, "new_scientific_experiments": 0, "max_differences": {},
          "anomalies": [], "checks": {}, "read_boundary": {
              "numeric_source": str(RAW), "training_columns": 192, "test_scoring_columns": 128,
              "test_probes": "only union of logged queries for each cell; unqueried strings never converted",
              "forbidden_inputs_read": []}}

def peak_memory_bytes():
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                        ("PrivateUsage", ctypes.c_size_t)]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessMemoryCounters), wintypes.DWORD]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return int(counters.PeakWorkingSetSize), int(counters.PeakPagefileUsage)
    import resource
    import sys
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(rss if sys.platform == "darwin" else rss * 1024), None


def budget():
    peak_rss, peak_commit = peak_memory_bytes()
    REPORT["peak_rss_bytes"] = peak_rss
    REPORT["peak_rss_kib"] = peak_rss / 1024.0
    REPORT["peak_commit_bytes"] = peak_commit
    if max(peak_rss, peak_commit or 0) > 2_000_000_000:
        raise RuntimeError("Independent verification 2 GB memory budget exceeded")
    if time.process_time() - CPU_START > 600:
        raise RuntimeError("Independent verification CPU budget exceeded")

def check(name, condition, detail=None):
    REPORT["checks"][name] = bool(condition)
    if not condition:
        REPORT["anomalies"].append({"check": name, "detail": detail})

def difference(name, actual, expected, tolerance=1e-8):
    a, b = np.asarray(actual, dtype=float), np.asarray(expected, dtype=float)
    same_shape = a.shape == b.shape
    masks_equal = same_shape and np.array_equal(np.isfinite(a), np.isfinite(b))
    if same_shape:
        finite = np.isfinite(a) & np.isfinite(b)
        delta = float(np.max(np.abs(a[finite] - b[finite]))) if finite.any() else 0.0
    else:
        delta = float("inf")
    REPORT["max_differences"][name] = delta if np.isfinite(delta) else None
    check(name, masks_equal and delta <= tolerance,
          {"shape_actual": list(a.shape), "shape_expected": list(b.shape), "finite_masks_equal": masks_equal})

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def finite_number(value):
    if value.strip().lower() in ("", "na", "nan", "null"):
        return np.nan
    return float(value)

def main():
    metadata = json.loads((BASE / "metadata_freeze.json").read_text(encoding="utf-8"))
    menu = json.loads((BASE / "menu_freeze.json").read_text(encoding="utf-8"))
    model = np.load(BASE / "training_model.npz", allow_pickle=False)
    saved = np.load(BASE / "replay_predictions.npz", allow_pickle=False)
    logs = [json.loads(line) for line in (BASE / "query_trace.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    check("protocol_v1_hash", sha(BASE / "protocol_v1.md") == metadata["protocol_sha256"])
    check("protocol_v2_hash", sha(BASE / "protocol_v2.md") == menu["protocol_v2_sha256"])
    check("model_hash", sha(BASE / "training_model.npz") == menu["model_sha256"])
    train, test = menu["training_cells"], menu["test_cells"]
    check("frozen_dimensions", len(train) == 397 and len(test) == 171 and len(menu["conditions"]) == 192)
    check("role_disjoint", not ({x["depmap_id"] for x in train} & {x["depmap_id"] for x in test}))
    check("metadata_training_order", train == [x for x in metadata["cells"] if x["role"] == "train"])
    check("metadata_test_order", test == [x for x in metadata["cells"] if x["role"] != "train"])
    columns = [x["column_name"] for x in menu["conditions"]]
    check("unique_menu_entities", len(set(columns)) == 192 and len({x["group_id"] for x in menu["conditions"]}) == 192)
    probe_ids = [x["group_id"] for x in menu["conditions"][:64]]
    check("probe_ids", probe_ids == menu["panels"]["probe_ids"])
    traces = {(x["depmap_id"], arm): [] for x in test for arm in ARMS}
    for event in logs:
        key = (event["cell"], event["arm"])
        if key not in traces:
            raise ValueError("Trace contains cell or arm outside frozen cohort")
        if not (isinstance(event["probe"], int) and 0 <= event["probe"] < 64):
            raise ValueError("Trace contains out-of-menu query")
        traces[key].append(event)
    for key, events in traces.items():
        events.sort(key=lambda e: e["step"])
        check("trace_budget_" + "|".join(key), [e["step"] for e in events] == list(range(1, 9)) and len({e["probe"] for e in events}) == 8)
    wanted = {cell["row_name"]: set(range(64, 192)) | {e["probe"] for arm in ARMS for e in traces[(cell["depmap_id"], arm)]} for cell in test}
    train_index = {cell["row_name"]: i for i, cell in enumerate(train)}
    test_index = {cell["row_name"]: i for i, cell in enumerate(test)}
    raw_train = np.full((397, 192), np.nan)
    truth = np.full((171, 128), np.nan)
    feedback = {}
    found_train, found_test = set(), set()
    parsed_train, parsed_test = 0, 0
    with RAW.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        positions = [header.index(c) for c in columns]
        for row in reader:
            row_id = row[0]
            if row_id in train_index:
                if row_id in found_train:
                    raise ValueError("Duplicated frozen training row")
                found_train.add(row_id)
                raw_train[train_index[row_id]] = [finite_number(row[j]) for j in positions]
                parsed_train += 192
            elif row_id in test_index:
                if row_id in found_test:
                    raise ValueError("Duplicated frozen test row")
                found_test.add(row_id)
                i = test_index[row_id]
                for j in sorted(wanted[row_id]):
                    value = finite_number(row[positions[j]])
                    parsed_test += 1
                    if j >= 64:
                        truth[i, j - 64] = value
                    else:
                        feedback[(i, j)] = value
            budget()
    REPORT["source_audit"] = {"train_rows_found": len(found_train), "test_rows_found": len(found_test),
                              "train_values_parsed": parsed_train, "test_values_parsed": parsed_test,
                              "raw_sha256": sha(RAW)}
    check("all_training_rows_present", len(found_train) == 397)
    difference("raw_training_matrix", raw_train, model["raw"], 0)
    difference("score_truth", truth, saved["truth"], 0)
    mu = np.nanmean(raw_train, axis=0)
    filled = np.where(np.isfinite(raw_train), raw_train, mu)
    difference("training_mu", mu, model["mu"])
    difference("training_filled", filled, model["filled"])
    A, P0 = model["features"], model["prior"]
    variance = float(model["sigma2"])
    check("frozen_model_shapes", A.shape == (192, 9) and P0.shape == (9, 9) and variance >= 0.0025)
    check("prior_positive_definite", np.linalg.eigvalsh(P0).min() > 0)
    AP, AS = A[:64], A[64:]
    mu_score = mu[64:]
    prior_precision = np.linalg.solve(P0, np.eye(9))

    def posterior(qs, values):
        # Direct normal equations from all finite feedback seen so far. No recursive updater.
        if not qs:
            return np.zeros(9), P0.copy()
        design = AP[np.asarray(qs)]
        precision = prior_precision + design.T @ design / variance
        covariance = np.linalg.solve(precision, np.eye(9))
        rhs = design.T @ (np.asarray(values) - mu[np.asarray(qs)]) / variance
        return np.linalg.solve(precision, rhs), covariance

    def top10(prediction):
        return np.argsort(prediction, kind="stable")[:10]

    def select(covariance, targets, attempted):
        # Each candidate's conditional covariance reduction, computed independently.
        cross_covariance = AS[targets] @ covariance @ AP.T
        marginal = variance + np.einsum("ij,jk,ik->i", AP, covariance, AP)
        gains = np.sum(cross_covariance * cross_covariance, axis=0) / marginal
        gains[list(attempted)] = -np.inf
        return int(np.argmax(gains))

    fixed_panels = {}
    for arm, targets in (("fixed_global", np.arange(128)), ("fixed_initial10", top10(mu_score))):
        panel = []
        for _ in range(8):
            _, covariance = posterior(panel, list(mu[np.asarray(panel, dtype=int)]))
            panel.append(select(covariance, targets, panel))
        fixed_panels[arm] = panel
        check("design_" + arm, panel == menu["panels"][arm], {"independent": panel, "frozen": menu["panels"][arm]})
    predictions = {arm: np.tile(mu_score, (171, 1)) for arm in (*ARMS, "frozen", "nearest5", "offset")}
    maxima = {"query_feedback": 0.0, "logged_posterior": 0.0, "logged_prediction_change": 0.0}
    action_mismatches, target_mismatches, feedback_mismatches = [], [], []
    train_variance = np.maximum(filled.var(axis=0), 1e-6)
    for i, cell in enumerate(test):
        for arm in ARMS:
            attempts, qs, values = [], [], []
            random_order = sorted(range(64), key=lambda q: hashlib.sha256(("C2-random|" + cell["depmap_id"] + "|" + probe_ids[q]).encode()).hexdigest())[:8]
            for step, event in enumerate(traces[(cell["depmap_id"], arm)]):
                mean, covariance = posterior(qs, values)
                before = mu_score + AS @ mean
                expected = (select(covariance, top10(before), attempts) if arm == "adaptive" else
                            random_order[step] if arm == "random" else fixed_panels[arm][step])
                if expected != event["probe"]:
                    action_mismatches.append({"cell": cell["depmap_id"], "arm": arm, "step": step + 1, "expected": expected, "saved": event["probe"]})
                q = event["probe"]
                observed = feedback.get((i, q), np.nan)
                logged = np.nan if event["observed_response"] is None else float(event["observed_response"])
                if np.isfinite(observed) != np.isfinite(logged):
                    feedback_mismatches.append({"cell": cell["depmap_id"], "arm": arm, "step": step + 1})
                elif np.isfinite(observed):
                    maxima["query_feedback"] = max(maxima["query_feedback"], abs(observed - logged))
                attempts.append(q)
                if np.isfinite(observed):
                    qs.append(q)
                    values.append(observed)
                mean_after, _ = posterior(qs, values)
                after = mu_score + AS @ mean_after
                maxima["logged_posterior"] = max(maxima["logged_posterior"], float(np.max(np.abs(mean_after - event["posterior_mean"]))))
                maxima["logged_prediction_change"] = max(maxima["logged_prediction_change"], abs(float(np.mean(np.abs(after - before))) - event["prediction_mean_abs_change"]))
                if list(top10(before)) != event["target_before"] or list(top10(after)) != event["target_after"]:
                    target_mismatches.append({"cell": cell["depmap_id"], "arm": arm, "step": step + 1})
            predictions[arm][i] = after
            if arm == "adaptive" and qs:
                qarr = np.asarray(qs)
                distance = np.mean((filled[:, qarr] - np.asarray(values)) ** 2 / train_variance[qarr], axis=1)
                near = np.argsort(distance, kind="stable")[:5]
                weights = 1.0 / (distance[near] + 0.1)
                predictions["nearest5"][i] = np.average(filled[near, 64:], axis=0, weights=weights)
                predictions["offset"][i] = mu_score + np.mean(np.asarray(values) - mu[qarr])
            budget()
    for name, value in maxima.items():
        REPORT["max_differences"][name] = value
        check(name, value <= 1e-8)
    check("query_feedback_missingness", not feedback_mismatches, feedback_mismatches)
    check("all_actions", not action_mismatches, action_mismatches)
    check("logged_target_lists", not target_mismatches, target_mismatches)
    for arm, pred in predictions.items():
        difference("prediction_" + arm, pred, saved[arm])
    bounds = {}
    selection_masks = {}
    for arm, pred in predictions.items():
        top = np.argsort(pred, axis=1, kind="stable")[:, :10]
        chosen = np.take_along_axis(truth, top, axis=1)
        lower = np.mean(np.isfinite(chosen) & (chosen <= -1), axis=1)
        upper = lower + np.mean(~np.isfinite(chosen), axis=1)
        bounds[arm] = (lower, upper)
        mask = np.zeros((171, 128), dtype=bool)
        np.put_along_axis(mask, top, True, axis=1)
        selection_masks[arm] = mask
        finite_scores = np.isfinite(truth)
        observed_counts = finite_scores.sum(axis=1)
        error_sums = np.where(finite_scores, np.abs(pred - truth), 0).sum(axis=1)
        per_cell_mae = np.divide(error_sums, observed_counts, out=np.full(171, np.nan), where=observed_counts > 0)
        mean_cell_mae = float(np.nanmean(per_cell_mae)) if np.any(observed_counts > 0) else None
        REPORT.setdefault("metrics", {})[arm] = {"hit10_lower_mean": float(lower.mean()), "hit10_upper_mean": float(upper.mean()),
            "selected_missing_count": int((~np.isfinite(chosen)).sum()), "mae_observed": mean_cell_mae,
            "mae_observed_definition": "equal mean of per-cell finite-score MAE over cells with at least one finite score",
            "mae_scored_cell_count": int(np.count_nonzero(observed_counts)),
            "score_coverage": float(np.isfinite(truth).mean()), "top10_indices": top.tolist(),
            "per_cell_lower": lower.tolist(), "per_cell_upper": upper.tolist()}
    # Same seed, exactly 2000 paired cell bootstrap samples, no seed search.
    shared = np.random.default_rng(20261028).integers(0, 171, size=(2000, 171))
    joint_shared = True
    for opponent, threshold in (("frozen", 0.05), ("fixed_global", 0.02), ("fixed_initial10", 0.02), ("random", 0.02)):
        conservative = bounds["adaptive"][0] - bounds[opponent][1]
        broad_upper = bounds["adaptive"][1] - bounds[opponent][0]
        # Complete sharp identification interval cancels unobserved conditions selected by both arms.
        coefficient = (selection_masks["adaptive"].astype(int) - selection_masks[opponent].astype(int)) / 10.0
        known = np.sum(coefficient * (np.isfinite(truth) & (truth <= -1)), axis=1)
        missing = ~np.isfinite(truth)
        sharp_lower = known + np.sum(np.minimum(coefficient, 0) * missing, axis=1)
        sharp_upper = known + np.sum(np.maximum(coefficient, 0) * missing, axis=1)
        shared_ci = np.percentile(conservative[shared].mean(axis=1), [2.5, 97.5])
        passed_shared = bool(conservative.mean() >= threshold and shared_ci[0] > 0)
        joint_shared &= passed_shared
        REPORT.setdefault("comparisons", {})[opponent] = {
            "threshold_point_estimate": threshold, "worst_case_difference_mean": float(conservative.mean()),
            "conservative_interval_mean": [float(conservative.mean()), float(broad_upper.mean())],
            "sharp_identification_interval_mean": [float(sharp_lower.mean()), float(sharp_upper.mean())],
            "sharp_lower_per_cell": sharp_lower.tolist(), "sharp_upper_per_cell": sharp_upper.tolist(),
            "bootstrap_shared_indices_ci95": shared_ci.tolist(),
            "sharp_lower_bootstrap_ci95": np.percentile(sharp_lower[shared].mean(axis=1), [2.5, 97.5]).tolist(),
            "sharp_upper_bootstrap_ci95": np.percentile(sharp_upper[shared].mean(axis=1), [2.5, 97.5]).tolist(),
            "passes_shared": passed_shared,
            "interpretation": "A negative conservative lower endpoint or its CI does not establish actual harm; inspect the complete identification interval."}
    REPORT["joint_development_support_shared"] = bool(joint_shared)
    REPORT["bootstrap_convention_note"] = "Verification execution convention: seed 20261028 generates one 2000 by 171 cell-resampling matrix shared by all four paired comparisons. This convention was fixed without consulting original scores. No extra experiment, split, or seed."
    REPORT["interpretation_limits"] = "Arithmetic PASS cannot establish H_C2, generalization, mechanism, end-to-end preprocessing independence, or real assay cost. Joint support is a separate development-set result. No original metrics or implementation were read."
    REPORT["artifact_hashes"] = {name: sha(BASE / name) for name in ("protocol_v1.md", "protocol_v2.md", "metadata_freeze.json", "menu_freeze.json", "training_model.npz", "query_trace.jsonl", "replay_predictions.npz", "independent_c2_verify.py")}
    budget()

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        REPORT["anomalies"].append({"fatal": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()})
    # Include JSON preparation before the final resource check and output write.
    json.dumps(REPORT, ensure_ascii=False, indent=2, allow_nan=False)
    try:
        budget()
    except Exception as exc:
        REPORT["anomalies"].append({"fatal_final_budget": type(exc).__name__, "message": str(exc)})
    REPORT["cpu_seconds"] = time.process_time() - CPU_START
    REPORT["wall_seconds"] = time.monotonic() - WALL_START
    check("final_cpu_budget", REPORT["cpu_seconds"] <= 600)
    check("final_memory_budget", max(REPORT.get("peak_rss_bytes", 0), REPORT.get("peak_commit_bytes") or 0) <= 2_000_000_000
          and REPORT.get("peak_rss_bytes") is not None)
    REPORT["resource_limits"] = {"cpu_seconds": 600, "memory_bytes": 2_000_000_000,
                                 "memory_measure": "Windows maximum of process peak working set and peak commit; POSIX peak RSS"}
    REPORT["arithmetic_verification_status"] = "PASS" if not REPORT["anomalies"] else "FAIL"
    (BASE / "independent_verification.json").write_text(json.dumps(REPORT, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({k: REPORT[k] for k in ("arithmetic_verification_status", "cpu_seconds", "wall_seconds", "anomalies")}, ensure_ascii=False))
