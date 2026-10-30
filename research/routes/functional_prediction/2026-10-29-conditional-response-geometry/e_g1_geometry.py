"""One frozen G1 proxy experiment; no hyperparameter search or core promotion."""
import os
import time

START_WALL, START_CPU = time.perf_counter(), time.process_time()
for thread_var in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[thread_var] = "1"

import ctypes
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import threading

import numpy as np
import pandas as pd
import psutil

HERE = Path(__file__).resolve().parent
OUT = HERE / "g1_run"
D = 8
P = np.eye(D) - np.ones((D, D)) / D
STOP_MONITOR = threading.Event()
JOB_HANDLE = None


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2,
                                     allow_nan=False) + "\n", encoding="utf-8")


def install_resource_limits():
    # Hard Windows process-memory/user-CPU limits plus a total-CPU/output monitor.
    global JOB_HANDLE
    class Basic(ctypes.Structure):
        _fields_ = [("process_time", ctypes.c_longlong), ("job_time", ctypes.c_longlong),
                    ("flags", ctypes.c_uint32), ("min_ws", ctypes.c_size_t),
                    ("max_ws", ctypes.c_size_t), ("active", ctypes.c_uint32),
                    ("affinity", ctypes.c_size_t), ("priority", ctypes.c_uint32),
                    ("scheduling", ctypes.c_uint32)]
    class Extended(ctypes.Structure):
        _fields_ = [("basic", Basic), ("io", ctypes.c_ulonglong * 6),
                    ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                    ("peak_process_memory", ctypes.c_size_t), ("peak_job_memory", ctypes.c_size_t)]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
    kernel.CreateJobObjectW.restype = ctypes.c_void_p
    kernel.SetInformationJobObject.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                             ctypes.c_void_p, ctypes.c_uint32]
    kernel.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    limits = Extended()
    limits.basic.flags = 0x100 | 0x2
    limits.basic.process_time = 120 * 10_000_000
    limits.process_memory = 1_073_741_824
    JOB_HANDLE = kernel.CreateJobObjectW(None, None)
    assert JOB_HANDLE and kernel.SetInformationJobObject(JOB_HANDLE, 9, ctypes.byref(limits),
                                                        ctypes.sizeof(limits))
    assert kernel.AssignProcessToJobObject(JOB_HANDLE, kernel.GetCurrentProcess())

    def monitor():
        process = psutil.Process()
        while not STOP_MONITOR.wait(.02):
            cpu = process.cpu_times()
            peak = process.memory_info().peak_wset
            size = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
            if cpu.user + cpu.system > 120 or peak > 1_073_741_824 or size > 50_000_000:
                save("resource_abort.json", {"state": "resource_abort", "cpu_seconds": cpu.user + cpu.system,
                                             "peak_working_set_bytes": peak, "output_bytes": size})
                os._exit(124)
    threading.Thread(target=monitor, daemon=True).start()


def fit(y, labels):
    z = y - y.mean(axis=1, keepdims=True)
    mean = z.mean(axis=0)
    groups, pooled, degrees = {}, np.zeros((D, D)), 0
    for label in sorted(set(labels)):
        sub = z[labels == label]
        residual = sub - sub.mean(axis=0)
        ss = residual.T @ residual
        groups[label] = (len(sub), sub.mean(axis=0), ss)
        pooled += ss
        degrees += len(sub) - 1
    assert degrees > 0, "design_invalid: no within-class degrees of freedom"
    c0 = pooled / degrees
    trace = np.trace(c0)
    assert trace > 1e-12, "design_invalid: degenerate pooled covariance"
    ridge = 1e-6 * trace / D * P
    estimates = {}
    for label, (n, sample_mean, ss) in groups.items():
        mu = n / (n + 8) * sample_mean + 8 / (n + 8) * mean
        gamma = (n - 1) / (n - 1 + 8) if n >= 2 else 0.
        covariance = ss / (n - 1) if n >= 2 else c0
        scaled = covariance * trace / np.trace(covariance) if np.trace(covariance) > 1e-12 else c0
        estimates[label] = (mu, (1 - gamma) * c0 + gamma * scaled + ridge)
    return mean, c0, c0 + ridge, estimates


def parameters(model, label, conditional):
    mean, c0, global_shape, estimates = model
    mu, shape = estimates.get(label, (mean, global_shape))
    return mu, shape if conditional else global_shape


def predict(mu, shape, action, delta):
    ca = shape @ action
    denominator = float(action @ ca)
    assert denominator > 0
    return mu + ca / denominator * (delta - action @ mu)


def first_tie(values, minimum=False):
    best = np.min(values) if minimum else np.max(values)
    return int(np.flatnonzero(np.abs(values - best) <= 1e-12 * max(1., abs(best)))[0])


def raw_pair_loss(prediction, truth, actions):
    return float(np.mean((actions @ prediction - actions @ truth) ** 2))


def plan(training, train_labels, dev_names, dev_labels, pairs):
    # No development values or development centers are in this function's inputs.
    actions = np.eye(D)[pairs[:, 0]] - np.eye(D)[pairs[:, 1]]
    loo = np.zeros((2, len(pairs)))
    for held in range(len(training)):
        keep = np.arange(len(training)) != held
        fold = fit(training[keep], train_labels[keep])
        for mode in range(2):
            mu, shape = parameters(fold, train_labels[held], bool(mode))
            for j, action in enumerate(actions):
                delta = float(action @ training[held])
                loo[mode, j] += raw_pair_loss(predict(mu, shape, action, delta), training[held], actions)
    loo /= len(training)
    fixed = [first_tie(row, minimum=True) for row in loo]
    model = fit(training, train_labels)
    selected, gains = {}, {}
    for condition, label in zip(dev_names, dev_labels):
        _, shape = parameters(model, label, True)
        ca = shape @ actions.T
        value = np.sum(ca ** 2, axis=0) / np.sum(actions.T * ca, axis=0)
        selected[condition] = {"B0": fixed[0], "B1": fixed[1], "C": first_tie(value)}
        gains[condition] = value.tolist()
    return model, actions, loo, fixed, selected, gains


class Scorer:
    """Logical observation/scoring interface, not a memory-security sandbox."""
    def __init__(self, truth):
        self.__truth = truth
        self.calls = []
        self.losses = []

    def delta(self, condition, policy, pair):
        assert (OUT / "actions_frozen.json").exists()
        q, r = pair
        value = float(self.__truth[condition][q] - self.__truth[condition][r])
        self.calls.append({"condition": condition, "policy": policy, "pair": [int(q), int(r)],
                           "signed_delta_only": value, "curve_attempts": 2})
        return value

    def loss(self, condition, prediction, actions):
        return raw_pair_loss(prediction, self.__truth[condition], actions)


def load_data(frozen):
    assert sha(frozen["source"]) == frozen["source_sha256"], "design_invalid: source SHA"
    assert sha(HERE / "metadata_projection.json") == frozen["metadata_projection_sha256"]
    dependency = frozen["metadata_window_dependency"]
    assert sha(dependency["path"]) == dependency["sha256"]
    old = json.loads(Path(dependency["path"]).read_text(encoding="utf-8"))
    cell_meta = {c["id"]: c for c in old["cells"]}
    columns = ["DRUG_ID", "DRUG_NAME", "SANGER_MODEL_ID", "CELL_LINE_NAME", "TCGA_DESC",
               "PATHWAY_NAME", "MIN_CONC", "MAX_CONC", "LN_IC50"]
    frame = pd.read_csv(frozen["source"], usecols=columns, dtype=str, keep_default_na=False)
    panel = frozen["panel"]
    subset = frame[frame.SANGER_MODEL_ID.isin(panel)]
    values, metadata_rows = {}, []
    for condition in frozen["conditions"]:
        name, drug_id = condition["condition"], condition["drug_ids"][0]
        records = subset[subset.DRUG_ID == drug_id]
        records = records[[Decimal(a) == Decimal(condition["min_conc_raw"]) and
                           Decimal(b) == Decimal(condition["max_conc_raw"])
                           for a, b in zip(records.MIN_CONC, records.MAX_CONC)]]
        assert len(records) == D and records.SANGER_MODEL_ID.nunique() == D, "design_invalid: incomplete/duplicate cross"
        responses = []
        for cell in panel:
            row = records[records.SANGER_MODEL_ID == cell].iloc[0]
            assert row.DRUG_NAME == condition["drug_names"][0], "design_invalid: drug annotation"
            assert row.PATHWAY_NAME == condition["pathways"][0], "design_invalid: class annotation"
            assert row.CELL_LINE_NAME == cell_meta[cell]["name"] and row.TCGA_DESC == cell_meta[cell]["tissue"]
            value = float(row.LN_IC50)
            assert np.isfinite(value), "design_invalid: nonfinite response"
            responses.append(value)
            metadata_rows.append({"condition": name, "cell": cell, "csv_row_1based": int(row.name) + 2,
                                  "drug_id": drug_id, "min_conc_raw": row.MIN_CONC,
                                  "max_conc_raw": row.MAX_CONC})
        values[name] = np.array(responses)
    train_names, dev_names = frozen["train_conditions"], frozen["development_conditions"]
    assert len(values) == 173 and len(train_names) == 125 and len(dev_names) == 48
    assert not set(train_names) & set(dev_names) and set(values) == set(train_names) | set(dev_names)
    labels = {c["condition"]: c["pathways"][0] for c in frozen["conditions"]}
    assert sorted({labels[n] for n in dev_names}) == frozen["bootstrap"]["cluster_order"]
    training = np.array([values[n] for n in train_names])
    scorer = Scorer({n: values[n] for n in dev_names})
    save("selected_source_rows.json", {"columns_read": columns, "rows": metadata_rows,
                                       "finite_response_count": len(metadata_rows),
                                       "no_response_filtering": True})
    return training, np.array([labels[n] for n in train_names]), dev_names, [labels[n] for n in dev_names], scorer


def run():
    assert not OUT.exists(), "No automatic scientific rerun"
    OUT.mkdir()
    receipt = {"state": "started", "implementation_sha256": sha(__file__),
               "protocol_sha256": sha(HERE / "protocol_g1_v1_1.md"),
               "freeze_sha256": sha(HERE / "input_freeze_v1_1.json"),
               "ram_limit_bytes": 1_073_741_824, "cpu_limit_seconds": 120,
               "output_limit_bytes": 50_000_000, "one_main_run": True,
               "development_interface": "logical scorer/predictor separation; signed delta only"}
    save("experiment_receipt.json", receipt)
    try:
        install_resource_limits()
        receipt["windows_job_installed"] = True
        save("experiment_receipt.json", receipt)
        pre = json.loads((HERE / "preexecution_freeze_receipt.json").read_text(encoding="utf-8"))
        assert receipt["protocol_sha256"] == pre["sha256"]["protocol_g1_v1_1.md"]
        assert receipt["freeze_sha256"] == pre["sha256"]["input_freeze_v1_1.json"]
        frozen = json.loads((HERE / "input_freeze_v1_1.json").read_text(encoding="utf-8"))
        training, train_labels, names, labels, scorer = load_data(frozen)
        pairs = np.array(frozen["pairs"], dtype=int)
        model, actions, loo, fixed, selected, gains = plan(training, train_labels, names, labels, pairs)
        save("loo_selection.json", {"pairs": pairs.tolist(), "raw_mean_losses": loo.tolist(), "fixed_pair_indices": fixed})
        save("actions_frozen.json", {"conditions_order": names, "actions": selected,
                                     "C_gains": gains, "delta_calls_at_freeze": len(scorer.calls)})
        action_sha = sha(OUT / "actions_frozen.json")
        denominator = float(2 * np.trace(model[1]) / (D - 1))
        predictions, losses = {}, {}
        for name, label in zip(names, labels):
            predictions[name], losses[name] = {}, {}
            for policy in ("B0", "B1", "C"):
                j = selected[name][policy]
                delta = scorer.delta(name, policy, pairs[j])
                mu, shape = parameters(model, label, policy != "B0")
                prediction = predict(mu, shape, actions[j], delta)
                predictions[name][policy] = prediction.tolist()
                losses[name][policy] = scorer.loss(name, prediction, actions) / denominator
            mu, _ = parameters(model, label, True)
            predictions[name]["mean_noquery"] = mu.tolist()
            losses[name]["mean_noquery"] = scorer.loss(name, mu, actions) / denominator
        assert len(scorer.calls) == 144 and sha(OUT / "actions_frozen.json") == action_sha
        save("delta_access_ledger.json", scorer.calls)
        save("predictions.json", predictions)
        save("losses.json", losses)
        clusters = frozen["bootstrap"]["cluster_order"]
        assert len(clusters) == 18
        draw = np.random.Generator(np.random.PCG64(20261029)).integers(0, 18, size=(9999, 18))
        np.save(OUT / "bootstrap_draws.npy", draw, allow_pickle=False)
        sizes = np.array([labels.count(g) for g in clusters])
        comparisons = {}
        for baseline in ("B0", "B1"):
            improvement = np.array([losses[n][baseline] - losses[n]["C"] for n in names])
            sums = np.array([improvement[np.array(labels) == g].sum() for g in clusters])
            distribution = sums[draw].sum(axis=1) / sizes[draw].sum(axis=1)
            interval = np.quantile(distribution, [.025, .975], method="linear")
            comparisons[baseline] = {"mean_improvement": float(improvement.mean()),
                                     "stability_interval_95": interval.tolist(),
                                     "point_and_interval_pass": bool(improvement.mean() > 0 and interval[0] > 0)}
        distinct = len({selected[n]["C"] for n in names})
        summary = {"state": "executed", "task": "historically exposed fitted-label difference-only proxy",
                   "counts": {"train_conditions": 125, "development_conditions": 48, "cells": 8,
                              "development_clusters": 18, "curve_attempts_per_policy": 96},
                   "common_D_pre_ridge": denominator, "trace_C0": float(np.trace(model[1])),
                   "fixed_pairs": {p: pairs[j].tolist() for p, j in zip(("B0", "B1"), fixed)},
                   "C_distinct_pairs": distinct, "comparisons": comparisons,
                   "mean_losses": {p: float(np.mean([losses[n][p] for n in names]))
                                   for p in ("B0", "B1", "C", "mean_noquery")},
                   "H_G1_supported_in_proxy": bool(distinct >= 2 and all(v["point_and_interval_pass"] for v in comparisons.values())),
                   "bootstrap_draw_sha256": sha(OUT / "bootstrap_draws.npy"),
                   "actions_frozen_sha256": action_sha,
                   "not_established": ["new algorithm", "biological mechanism", "co-learning", "real assay savings", "external generalization"]}
        save("summary.json", summary)
        receipt.update(state="completed", functional_values_read=True, source_sha256=frozen["source_sha256"])
        print(json.dumps(summary, ensure_ascii=False), flush=True)
    except Exception as exc:
        receipt.update(state="design_invalid" if "design_invalid" in str(exc) else "engineering_failed",
                       error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        STOP_MONITOR.set()
        receipt.update(wall_seconds=time.perf_counter() - START_WALL,
                       cpu_seconds=time.process_time() - START_CPU,
                       peak_working_set_bytes=psutil.Process().memory_info().peak_wset,
                       versions={"numpy": np.__version__, "pandas": pd.__version__})
        save("experiment_receipt.json", receipt)
        receipt["output_bytes"] = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
        save("experiment_receipt.json", receipt)


if __name__ == "__main__":
    run()
