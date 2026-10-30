"""One frozen, development-only replay on common PRISM functional responses."""
import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import csv
import ctypes
import hashlib
import json
from pathlib import Path
import time
import warnings
import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE = Path(r"D:\MAESTRO\data\external\prism_19q4\raw\primary-screen-replicate-collapsed-logfold-change.csv")
SEED = 20261028
ARMS = ["frozen", "fixed_global", "fixed_initial10", "random", "adaptive", "nearest5", "offset"]

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")

def numeric(token):
    try:
        value = float(token)
        return value if np.isfinite(value) else np.nan
    except (ValueError, TypeError):
        return np.nan

def process_memory():
    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong)] + [
            (name, ctypes.c_size_t) for name in ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    current_process = ctypes.windll.kernel32.GetCurrentProcess
    current_process.restype = ctypes.c_void_p
    memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
    memory_info.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
    memory_info.restype = ctypes.c_int
    handle = current_process()
    if not memory_info(handle, ctypes.byref(counters), counters.cb):
        raise OSError("Cannot verify memory budget")
    return int(counters.PeakWorkingSetSize)

def guard(start_cpu, start_wall):
    assert time.process_time() - start_cpu < 1200, "CPU budget exceeded"
    assert time.monotonic() - start_wall < 1200, "Wall budget exceeded"
    assert process_memory() < 2_000_000_000, "Memory budget exceeded"

def read_training(meta):
    cells = [r for r in meta["cells"] if r["role"] == "train"]
    lookup = {r["row_name"]: i for i, r in enumerate(cells)}
    matrix = np.full((len(cells), len(meta["conditions"])), np.nan)
    found = set()
    with SOURCE.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        column = {key: i for i, key in enumerate(header)}
        indexes = [column.get(r["column_name"]) for r in meta["conditions"]]
        for row in reader:
            if row[0] not in lookup:
                continue  # no numeric conversion for model-unseen cells
            assert row[0] not in found, "Duplicate source row"
            found.add(row[0])
            matrix[lookup[row[0]]] = [numeric(row[j]) if j is not None else np.nan for j in indexes]
    return cells, matrix, {"training_rows_found": len(found), "missing_condition_headers": sum(j is None for j in indexes)}

def train(meta):
    cells, raw, audit = read_training(meta)
    observed = np.isfinite(raw)
    count = observed.sum(axis=0)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        sd = np.nanstd(raw, axis=0, ddof=0)
        mean = np.nanmean(raw, axis=0)
    active = np.divide((raw <= -1).sum(axis=0), count, out=np.zeros(len(count), dtype=float), where=count > 0)
    eligible = np.flatnonzero((count / len(cells) >= .8) & (active >= .05) & (active <= .8) & (sd >= .2))
    eligible = sorted(eligible, key=lambda j: hashlib.sha256(("C2-drug|" + meta["conditions"][j]["group_id"]).encode()).hexdigest())
    audit["training_eligible_conditions"] = len(eligible)
    if len(eligible) < 192 or meta["ntest"] < 60:
        write_json(HERE / "training_gate.json", {"state": "stopped_before_test", "audit": audit})
        return None
    chosen = eligible[:192]
    raw = raw[:, chosen]
    observed = np.isfinite(raw)
    mu = mean[chosen]
    filled = np.where(observed, raw, mu[None, :])
    centered = filled - mu
    offset = centered.mean(axis=1)
    u, s, vt = np.linalg.svd(centered - offset[:, None], full_matrices=False)
    scores = u[:, :8] * s[:8]
    features = np.column_stack([np.ones(192), vt[:8].T])
    theta = np.column_stack([offset, scores])
    prior = np.cov(theta, rowvar=False) + 1e-6 * np.eye(9)
    reconstruction = mu[None, :] + theta @ features.T
    sigma2 = max(float(np.mean((filled[observed] - reconstruction[observed]) ** 2)), .0025)
    return cells, [meta["conditions"][j] for j in chosen], raw, filled, mu, features, prior, sigma2, audit

def gain(features, covariance, target, tried, sigma2):
    probe_features = features[:64]
    cross = features[target] @ covariance @ probe_features.T
    denominator = sigma2 + np.einsum("ij,jk,ik->i", probe_features, covariance, probe_features)
    values = (cross ** 2).sum(axis=0) / denominator
    values[list(tried)] = -np.inf
    return int(np.argmax(values))

def update(mean, covariance, feature, residual, sigma2):
    vector = covariance @ feature
    denominator = sigma2 + feature @ vector
    return mean + vector * (residual - feature @ mean) / denominator, covariance - np.outer(vector, vector) / denominator

def design(features, prior, target, sigma2):
    covariance = prior.copy()
    chosen = []
    for _ in range(8):
        q = gain(features, covariance, target, chosen, sigma2)
        _, covariance = update(np.zeros(9), covariance, features[q], 0, sigma2)
        chosen.append(q)
    return chosen

def direct_refit(features, prior, observations, mu, sigma2):
    if not observations:
        return np.zeros(9)
    q = [r[0] for r in observations]
    values = np.array([r[1] for r in observations]) - mu[q]
    precision = np.linalg.inv(prior) + features[q].T @ features[q] / sigma2
    return np.linalg.solve(precision, features[q].T @ values / sigma2)

def source_test_tokens(cells, conditions):
    # Only the oracle holds source tokens. Selectors receive queried floats, never tokens/masks.
    needed = {r["row_name"] for r in cells}
    result = {}
    with SOURCE.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        header = {name: i for i, name in enumerate(next(reader))}
        indexes = [header.get(r["column_name"]) for r in conditions]
        for row in reader:
            if row[0] in needed:
                assert row[0] not in result, "Duplicate model-unseen source row"
                result[row[0]] = [row[j] if j is not None else "" for j in indexes]
    return result

def run_cell(cell, tokens, mu, features, prior, sigma2, filled, panels, trace):
    predictions = {"frozen": mu[64:].copy()}
    budgets = {"frozen": (0, 0, 0)}
    initial10 = np.argsort(mu[64:], kind="stable")[:10] + 64
    observations_adaptive = []
    max_error = 0.0
    for arm in ("fixed_global", "fixed_initial10", "random", "adaptive"):
        mean, covariance, observations, tried = np.zeros(9), prior.copy(), [], []
        if arm == "random":
            order = sorted(range(64), key=lambda j: hashlib.sha256(("C2-random|" + cell["depmap_id"] + "|" + panels["probe_ids"][j]).encode()).hexdigest())[:8]
        else:
            order = panels.get(arm)
        for step in range(8):
            before = mu[64:] + features[64:] @ mean
            target = np.argsort(before, kind="stable")[:10] + 64
            q = gain(features, covariance, target, tried, sigma2) if arm == "adaptive" else order[step]
            assert q not in tried and 0 <= q < 64 and len(tried) < 8
            tried.append(q)
            y = numeric(tokens[q])  # the sole feedback reveal for this attempt
            if np.isfinite(y):
                mean, covariance = update(mean, covariance, features[q], y - mu[q], sigma2)
                observations.append((q, y))
            after = mu[64:] + features[64:] @ mean
            trace.write(json.dumps({"cell": cell["depmap_id"], "arm": arm, "step": step + 1,
                "probe": q, "observed_response": float(y) if np.isfinite(y) else None,
                "target_before": (target - 64).tolist(), "target_after": np.argsort(after, kind="stable")[:10].tolist(),
                "prediction_mean_abs_change": float(np.abs(after - before).mean()), "posterior_mean": mean.tolist()}, allow_nan=False) + "\n")
        predictions[arm] = mu[64:] + features[64:] @ mean
        error = float(np.max(np.abs(mean - direct_refit(features, prior, observations, mu, sigma2))))
        max_error = max(max_error, error)
        assert error <= 1e-8, "Recursive/direct Bayesian refit disagreement"
        budgets[arm] = (8, len(observations), 8 if arm == "adaptive" else 1)
        if arm == "adaptive":
            observations_adaptive = observations
    if observations_adaptive:
        q = [r[0] for r in observations_adaptive]
        y = np.array([r[1] for r in observations_adaptive])
        variance = np.maximum(np.var(filled[:, q], axis=0), 1e-6)
        distance = np.mean((filled[:, q] - y) ** 2 / variance, axis=1)
        neighbors = np.argsort(distance, kind="stable")[:5]
        weights = 1 / (distance[neighbors] + .1)
        predictions["nearest5"] = np.average(filled[neighbors, 64:], weights=weights, axis=0)
        predictions["offset"] = mu[64:] + float(np.mean(y - mu[q]))
    else:
        predictions["nearest5"] = predictions["frozen"].copy()
        predictions["offset"] = predictions["frozen"].copy()
    budgets["nearest5"] = budgets["offset"] = budgets["adaptive"]
    truth = np.array([numeric(x) for x in tokens[64:]])  # scoring only after all arms finish
    return predictions, budgets, truth, max_error

def summarize(cells, predictions, truths, costs):
    rows = []
    for i, cell in enumerate(cells):
        truth = truths[i]
        finite = np.isfinite(truth)
        for arm in ARMS:
            pred = predictions[arm][i]
            selected = np.argsort(pred, kind="stable")[:10]
            hits = int(np.sum(truth[selected] <= -1))
            measured = int(np.sum(finite[selected]))
            attempts, feedback, rounds = costs[arm][i]
            rows.append({"cell": cell["depmap_id"], "arm": arm,
                         "hit_lower": hits / 10, "hit_upper": (hits + 10 - measured) / 10,
                         "top10_measured_fraction": measured / 10,
                         "mae_observed_menu": float(np.mean(np.abs(pred[finite] - truth[finite]))) if finite.any() else None,
                         "menu_measured_fraction": float(finite.mean()),
                         "attempts": attempts, "returned_feedback": feedback, "potential_turnaround_rounds": rounds})
    metrics = {}
    by_arm = {a: [r for r in rows if r["arm"] == a] for a in ARMS}
    for arm, data in by_arm.items():
        metrics[arm] = {key: float(np.mean([r[key] for r in data])) for key in (
            "hit_lower", "hit_upper", "top10_measured_fraction", "menu_measured_fraction", "attempts", "returned_feedback", "potential_turnaround_rounds")}
        observed_mae = [r["mae_observed_menu"] for r in data if r["mae_observed_menu"] is not None]
        metrics[arm]["mae_observed_menu"] = float(np.mean(observed_mae)) if observed_mae else None
    draws = np.random.default_rng(SEED).integers(len(cells), size=(2000, len(cells)))
    comparisons = {}
    for arm in ARMS:
        if arm == "adaptive":
            continue
        difference = np.array([a["hit_lower"] - b["hit_upper"] for a, b in zip(by_arm["adaptive"], by_arm[arm])])
        boot = difference[draws].mean(axis=1)
        threshold = .05 if arm == "frozen" else .02
        comparisons[arm] = {"worst_case_mean_difference": float(difference.mean()),
            "bootstrap_ci95": np.quantile(boot, [.025, .975]).tolist(),
            "point_threshold": threshold, "meets_primary_rule": bool(difference.mean() >= threshold and np.quantile(boot, .025) > 0)}
    primary = ["frozen", "fixed_global", "fixed_initial10", "random"]
    return rows, {"by_arm": metrics, "adaptive_minus": comparisons,
                  "H_C2_joint_development_support": all(comparisons[a]["meets_primary_rule"] for a in primary),
                  "primary_comparators": primary, "bootstrap_unit": "frozen model-unseen development cell", "bootstrap_draws": 2000}

def main():
    start_cpu, start_wall = time.process_time(), time.monotonic()
    receipt_path = HERE / "experiment_receipt.json"
    assert not receipt_path.exists(), "Existing run: do not retry or overwrite"
    meta = json.loads((HERE / "metadata_freeze.json").read_text(encoding="utf-8"))
    assert sha(HERE / "protocol_v1.md") == meta["protocol_sha256"]
    receipt = {"state": "locked_before_training_values", "numeric_reads_prior_to_lock": 0,
        "source": str(SOURCE), "source_bytes": SOURCE.stat().st_size, "source_sha256": sha(SOURCE),
        "locked_sha256": {name: sha(HERE / name) for name in (
            "metadata_freeze.json", "protocol_v1.md", "protocol_v2.md", "e_c2_feedback.py")},
        "budget": {"cpu_seconds": 1200, "wall_seconds": 1200, "memory_bytes": 2_000_000_000,
                   "feedback_attempts_per_arm_cell": 8, "gpu": 0, "new_data_downloads": 0},
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    write_json(receipt_path, receipt)
    try:
        trained = train(meta)
        if trained is None:
            receipt["state"] = "stopped_training_qualification_before_test"
            return
        train_cells, conditions, train_raw, filled, mu, features, prior, sigma2, audit = trained
        evaluation = np.arange(64, 192)
        initial10 = np.argsort(mu[64:], kind="stable")[:10] + 64
        panels = {"fixed_global": design(features, prior, evaluation, sigma2),
                  "fixed_initial10": design(features, prior, initial10, sigma2),
                  "probe_ids": [r["group_id"] for r in conditions[:64]]}
        np.savez_compressed(HERE / "training_model.npz", raw=train_raw, filled=filled, mu=mu,
                            features=features, prior=prior, sigma2=sigma2)
        write_json(HERE / "menu_freeze.json", {"conditions": conditions, "probe_count": 64,
            "evaluation_count": 128, "panels": panels, "audit": audit,
            "training_cells": train_cells, "test_cells": [r for r in meta["cells"] if r["role"] != "train"],
            "model_sha256": sha(HERE / "training_model.npz"), "implementation_sha256": sha(Path(__file__)),
            "protocol_v2_sha256": sha(HERE / "protocol_v2.md"), "test_values_read_before_model_lock": 0})
        receipt.update(state="model_locked_before_test_values", training_audit=audit,
                       menu_freeze_sha256=sha(HERE / "menu_freeze.json"), model_sha256=sha(HERE / "training_model.npz"))
        write_json(receipt_path, receipt)
        guard(start_cpu, start_wall)
        test_cells = [r for r in meta["cells"] if r["role"] != "train"]
        tokens = source_test_tokens(test_cells, conditions)
        predictions = {a: [] for a in ARMS}
        costs = {a: [] for a in ARMS}
        truths, max_error = [], 0.0
        with (HERE / "query_trace.jsonl").open("w", encoding="utf-8") as trace:
            for cell in test_cells:
                pred, cost, truth, error = run_cell(cell, tokens.get(cell["row_name"], [""] * 192),
                    mu, features, prior, sigma2, filled, panels, trace)
                for arm in ARMS:
                    predictions[arm].append(pred[arm])
                    costs[arm].append(cost[arm])
                truths.append(truth)
                max_error = max(max_error, error)
                guard(start_cpu, start_wall)
        predictions = {a: np.array(p) for a, p in predictions.items()}
        truths = np.array(truths)
        rows, summary = summarize(test_cells, predictions, truths, costs)
        with (HERE / "cell_metrics.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        np.savez_compressed(HERE / "replay_predictions.npz", truth=truths, **predictions)
        summary.update(source_exposure="historically exposed development, no independent biological confirmation",
            ntrain=len(train_cells), ntest=len(test_cells), rank=8, sigma2=sigma2,
            max_recursive_direct_mean_error=max_error, test_rows_found=len(tokens),
            potential_preprocessing_leakage="published ComBat and replicate collapse predate the model split",
            code_sha256=sha(Path(__file__)), menu_sha256=sha(HERE / "menu_freeze.json"))
        guard(start_cpu, start_wall)
        write_json(HERE / "experiment_summary.json", summary)
        receipt.update(state="executed_pending_independent_verification", results_sha256=sha(HERE / "experiment_summary.json"),
                       query_trace_sha256=sha(HERE / "query_trace.jsonl"))
        print(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False))
    except Exception as exc:
        receipt.update(state="invalid_no_automatic_retry", error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        receipt.update(cpu_seconds=round(time.process_time() - start_cpu, 3),
                       wall_seconds=round(time.monotonic() - start_wall, 3), peak_working_set_bytes=process_memory())
        if receipt["cpu_seconds"] >= 1200 or receipt["wall_seconds"] >= 1200 or receipt["peak_working_set_bytes"] >= 2_000_000_000:
            receipt.update(state="invalid_no_automatic_retry", error="Budget exceeded including final export")
        write_json(receipt_path, receipt)

if __name__ == "__main__":
    main()
