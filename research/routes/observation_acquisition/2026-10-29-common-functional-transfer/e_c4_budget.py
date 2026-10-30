"""One frozen C4 fitted-candidate replay; all exploratory code stays in research."""
from pathlib import Path
from time import perf_counter, process_time
import csv
import hashlib
import json
import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np
import psutil
from scipy.special import ndtr

HERE = Path(__file__).resolve().parent
META = HERE / "metadata_freeze.json"
PROTOCOL = HERE / "protocol_c4_v2.md"
RECEIPT = HERE / "experiment_receipt.json"
STRATEGIES = ("rank8", "static_global13", "static_tissue13", "probe_blind",
              "random13", "rank1", "ridge", "knn5")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(name, data):
    (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def select_raw(source, cells, conditions):
    """Select rows by metadata, retaining response tokens without conversion."""
    ci = {c["id"]: i for i, c in enumerate(cells)}
    cj = {(c["drug_id"], c["min_conc_raw"], c["max_conc_raw"]): j
          for j, c in enumerate(conditions)}
    selected = {}
    with Path(source).open(encoding="utf-8-sig", newline="") as handle:
        for source_row, row in enumerate(csv.DictReader(handle)):
            if row["DATASET"] != "GDSC2" or row["SANGER_MODEL_ID"] not in ci:
                continue
            key = (row["DRUG_ID"], row["MIN_CONC"], row["MAX_CONC"])
            if key not in cj:
                continue
            ij = (ci[row["SANGER_MODEL_ID"]], cj[key])
            order = (int(row["NLME_RESULT_ID"]), source_row)
            if ij not in selected or order < selected[ij][0]:
                selected[ij] = (order, row["LN_IC50"])
    return {ij: raw for ij, (_, raw) in selected.items()}


def number(raw):
    try:
        value = float(raw)
    except (ValueError, TypeError):
        return np.nan
    return value if np.isfinite(value) else np.nan


def read_values(source, cells, conditions):
    result = np.full((len(cells), len(conditions)), np.nan)
    for ij, raw in select_raw(source, cells, conditions).items():
        result[ij] = number(raw)
    return result


def labels(values, low, high):
    finite = np.isfinite(values)
    event = finite & (values > low + 1e-8) & (values < high - 1e-8) & (values <= 0)
    return finite, event


def fit_model(s, mask, rank):
    b = s.mean(axis=1)
    u, singular, vt = np.linalg.svd(s - b[:, None], full_matrices=False)
    z, load = u[:, :rank] * singular[:rank], vt[:rank].T
    a = np.column_stack((np.ones(s.shape[1]), load))
    theta = np.column_stack((b, z))
    m = theta.mean(axis=0)
    p = np.cov(theta, rowvar=False, ddof=1) + np.eye(rank+1) * 1e-6
    noise = np.maximum((((s-theta @ a.T)**2) * mask).sum(axis=0) / mask.sum(axis=0), .0025)
    return a, m, p, noise


def update(model, m, p, j, value):
    a, _, _, noise = model
    v = p @ a[j]
    denominator = noise[j] + a[j] @ v
    return m + v * ((value-a[j] @ m)/denominator), p - np.outer(v, v)/denominator


def direct(model, indices, values):
    a, prior, covariance, noise = model
    if not len(indices):
        return prior.copy(), covariance.copy()
    precision = np.linalg.inv(covariance)
    aa = a[indices]
    rhs = precision @ prior + aa.T @ (values/noise[indices])
    inverse = np.linalg.inv(precision + (aa.T/noise[indices]) @ aa)
    return inverse @ rhs, inverse


def probabilities(mean, variance, low_s, high_s):
    sigma = np.sqrt(variance)
    return np.where(high_s > low_s,
                    np.maximum(0, ndtr((high_s-mean)/sigma)-ndtr((low_s-mean)/sigma)), 0)


def choose(probability, n, exclude=()):
    excluded = set(exclude)
    return [int(j) for j in np.argsort(-probability, kind="stable") if int(j) not in excluded][:n]


def paired_bounds(event, finite, first, second):
    only_first = list(set(first)-set(second))
    only_second = list(set(second)-set(first))
    difference = int(event[only_first].sum()) - int(event[only_second].sum())
    return difference-int((~finite[only_second]).sum()), difference+int((~finite[only_first]).sum())


def main():
    assert not RECEIPT.exists(), "Existing receipt: no automatic rerun"
    clock0, cpu0 = perf_counter(), process_time()
    meta = json.loads(META.read_text(encoding="utf-8"))
    assert sha(meta["source"]) == meta["source_sha256"]
    audit = json.loads((HERE / "metadata_audit.json").read_text(encoding="utf-8"))
    assert not audit["inconsistent_cell_metadata"] and not audit["unique_cell_mode_changes"]
    receipt = {"state": "started", "protocol_sha256": sha(PROTOCOL), "implementation_sha256": sha(__file__),
               "metadata_sha256": sha(META), "source_sha256": sha(meta["source"]),
               "functional_test_values_consumed": False, "one_scientific_run": True}
    write_json(RECEIPT.name, receipt)
    train_cells = [c for c in meta["cells"] if c["role"] == "train"]
    test_cells = [c for c in meta["cells"] if c["role"] != "train"]
    all_train = read_values(meta["source"], train_cells, meta["conditions"])
    coverage = np.isfinite(all_train).mean(axis=0)
    sd_all = np.nanstd(all_train, axis=0, ddof=0)
    eligible = np.flatnonzero((coverage >= .9) & (sd_all >= .1))
    if len(eligible) < 64:
        receipt.update(state="qualification_stop", eligible_conditions=int(len(eligible)),
                       cpu_seconds=process_time()-cpu0, wall_seconds=perf_counter()-clock0)
        write_json(RECEIPT.name, receipt)
        print(json.dumps(receipt))
        return
    menu_indices = eligible[:64]
    menu = [meta["conditions"][j] for j in menu_indices]
    y = all_train[:, menu_indices]
    finite = np.isfinite(y)
    mu, sd = np.nanmean(y, axis=0), np.nanstd(y, axis=0, ddof=0)
    s = np.where(finite, (mu-y)/sd, 0)
    low = np.log([float(c["min_conc_raw"]) for c in menu])
    high = np.log([float(c["max_conc_raw"]) for c in menu])
    low_s, high_s = (mu-np.minimum(0, high))/sd, (mu-low)/sd
    _, event = labels(y, low, high)
    global_rate = event.sum(axis=0)/finite.sum(axis=0)
    models = {rank: fit_model(s, finite, rank) for rank in (1, 8)}
    a, m0, p0, noise = models[8]
    p = p0.copy()
    probes = []
    for _ in range(8):
        projected = a @ p @ a.T
        gain = (projected**2).sum(axis=0)/(noise+np.diag(projected))
        j = choose(gain, 1, probes)[0]
        probes.append(j)
        _, p = update(models[8], m0, p, j, 0)
    design = np.column_stack((np.ones(len(y)), s[:, probes]))
    penalty = np.diag([0.] + [1.]*8)
    ridge_weights, ridge_noise = [], []
    for j in range(64):
        observed = finite[:, j]
        xj, target = design[observed], s[observed, j]
        weights = np.linalg.solve(xj.T @ xj + penalty, xj.T @ target)
        ridge_weights.append(weights)
        ridge_noise.append(max(float(np.mean((target-xj @ weights)**2)), .0025))
    ridge_weights, ridge_noise = np.column_stack(ridge_weights), np.array(ridge_noise)
    np.savez(HERE / "training_model.npz", train_y=y, mu=mu, sd=sd, low=low, high=high,
             s=s, finite=finite, event=event, probes=probes, global_rate=global_rate,
             ridge_weights=ridge_weights, ridge_noise=ridge_noise,
             **{f"{name}{rank}": value for rank, model in models.items()
                for name, value in zip(("a", "m", "p", "noise"), model)})
    write_json("training_freeze.json", {"menu": menu, "all_eligible_indices": eligible.tolist(),
               "menu_indices": menu_indices.tolist(), "probes": probes,
               "train_ids": [c["id"] for c in train_cells], "test_ids": [c["id"] for c in test_cells],
               "implementation_sha256": sha(__file__), "protocol_sha256": sha(PROTOCOL),
               "training_artifact_sha256": sha(HERE / "training_model.npz"),
               "test_functional_values_consumed": False})
    assert sha(__file__) == receipt["implementation_sha256"] and sha(PROTOCOL) == receipt["protocol_sha256"]
    test_raw = select_raw(meta["source"], test_cells, menu)
    observed_queries = []

    def query(i, j, allowed, phase):
        assert j in allowed, "Feedback access outside selected action set"
        if not receipt["functional_test_values_consumed"]:
            receipt.update(state="feedback_running", functional_test_values_consumed=True)
            write_json(RECEIPT.name, receipt)
        value = number(test_raw.get((i, j)))
        observed_queries.append({"cell_index": i, "condition_index": j, "phase": phase,
                                 "value": float(value) if np.isfinite(value) else None})
        return value

    actions = np.zeros((len(test_cells), len(STRATEGIES), 13), dtype=int)
    predictions = np.zeros((len(test_cells), 2, 64))
    probability_predictions = np.zeros_like(predictions)
    errors, changed_actions, traces = [], 0, []
    for i, cell in enumerate(test_cells):
        probe_values = np.array([query(i, j, probes, "shared_probe") for j in probes])
        standardized = np.full(64, np.nan)
        standardized[probes] = (mu[probes]-probe_values)/sd[probes]
        known = [j for j in probes if np.isfinite(standardized[j])]
        same_tissue = np.array([c["tissue"] == cell["tissue"] for c in train_cells])
        rate = (event[same_tissue].sum(axis=0)+5*global_rate)/(finite[same_tissue].sum(axis=0)+5)
        policies = {"static_global13": choose(global_rate, 13), "static_tissue13": choose(rate, 13),
                    "probe_blind": probes+choose(rate, 5, probes),
                    "random13": sorted(range(64), key=lambda j: hashlib.sha256(
                        ("C4-random|"+cell["id"]+"|"+menu[j]["id"]).encode()).hexdigest())[:13]}
        for rank in (1, 8):
            model = models[rank]
            aa, mm, pp, rr = model
            mm, pp = mm.copy(), pp.copy()
            for j in known:
                mm, pp = update(model, mm, pp, j, standardized[j])
            dm, dp = direct(model, np.array(known, dtype=int), standardized[known])
            errors.extend((float(np.max(np.abs(dm-mm))), float(np.max(np.abs(dp-pp)))))
            probs = probabilities(aa @ mm, rr+np.einsum("ij,jk,ik->i", aa, pp, aa), low_s, high_s)
            chosen = probes+choose(probs, 5, probes)
            policies[f"rank{rank}"] = chosen
            if rank == 8:
                predictions[i, 0], predictions[i, 1] = aa @ model[1], aa @ mm
                probability_predictions[i, 0] = probabilities(aa @ model[1], rr+np.einsum(
                    "ij,jk,ik->i", aa, model[2], aa), low_s, high_s)
                probability_predictions[i, 1] = probs
            seen = {j: standardized[j] for j in known}
            for j in chosen[8:]:
                value = query(i, j, chosen[8:], f"rank{rank}_selected_followup")
                if np.isfinite(value):
                    seen[j] = (mu[j]-value)/sd[j]
                    mm, pp = update(model, mm, pp, j, seen[j])
            known_all = list(seen)
            dm, dp = direct(model, np.array(known_all, dtype=int), np.array(list(seen.values())))
            errors.extend((float(np.max(np.abs(dm-mm))), float(np.max(np.abs(dp-pp)))))
        ridge_input = np.r_[1., np.where(np.isfinite(standardized[probes]), standardized[probes], 0)]
        policies["ridge"] = probes+choose(probabilities(ridge_input @ ridge_weights, ridge_noise, low_s, high_s), 5, probes)
        if known:
            distance = ((s[:, known]-standardized[known])**2).mean(axis=1)
            neighbors = np.argsort(distance, kind="stable")[:5]
            weights = 1/(distance[neighbors]+.1)
            denominator = (weights[:, None]*finite[neighbors]).sum(axis=0)
            nn_rate = np.divide((weights[:, None]*event[neighbors]).sum(axis=0), denominator,
                                out=global_rate.copy(), where=denominator > 0)
        else:
            nn_rate = global_rate
        policies["knn5"] = probes+choose(nn_rate, 5, probes)
        changed_actions += set(policies["rank8"]) != set(policies["probe_blind"])
        for k, name in enumerate(STRATEGIES):
            assert len(policies[name]) == len(set(policies[name])) == 13
            actions[i, k] = policies[name]
        traces.append({"cell": cell["id"], "policies": policies, "finite_probe_updates": len(known)})
    max_error = max(errors)
    assert max_error <= 1e-8, "Recursive/direct posterior mismatch"
    # All policies are immutable before the evaluator converts unselected truth.
    write_json("actions_freeze.json", {"actions_sha256": hashlib.sha256(actions.tobytes()).hexdigest(),
               "cells": len(test_cells), "strategy_order": STRATEGIES,
               "all_actions_fixed_before_full_truth_conversion": True,
               "feedback_numeric_accesses": len(observed_queries)})
    (HERE / "query_trace.jsonl").write_text("".join(json.dumps(t, ensure_ascii=False)+"\n" for t in traces), encoding="utf-8")
    (HERE / "feedback_access.jsonl").write_text("".join(json.dumps(t)+"\n" for t in observed_queries), encoding="utf-8")
    test = np.full((len(test_cells), 64), np.nan)
    for ij, raw in test_raw.items():
        test[ij] = number(raw)
    receipt["functional_test_values_consumed"] = True
    test_finite, test_event = labels(test, low, high)
    samples = np.random.default_rng(20261029).integers(0, len(test), (2000, len(test)))
    metrics, comparisons = {}, {}
    for k, name in enumerate(STRATEGIES):
        selected = actions[:, k]
        hits = np.take_along_axis(test_event, selected, axis=1).sum(axis=1)
        unknown = (~np.take_along_axis(test_finite, selected, axis=1)).sum(axis=1)
        metrics[name] = {"candidate_count_lower": float(hits.mean()),
                         "candidate_count_upper": float((hits+unknown).mean()),
                         "mean_unknown_attempts": float(unknown.mean()), "attempts_per_cell": 13}
    for control in STRATEGIES[1:]:
        bounds = np.array([paired_bounds(test_event[i], test_finite[i], actions[i, 0], actions[i, STRATEGIES.index(control)])
                           for i in range(len(test))])
        interval = np.quantile(bounds[:, 0][samples].mean(axis=1), [.025, .975], method="linear")
        comparisons[control] = {"mean_difference_lower": float(bounds[:, 0].mean()),
                                "mean_difference_upper": float(bounds[:, 1].mean()),
                                "difference_lower_bootstrap_ci95": interval.tolist(),
                                "passes_point_and_ci": bool(bounds[:, 0].mean() >= .5 and interval[0] > 0)}
    joint = all(comparisons[name]["passes_point_and_ci"] for name in STRATEGIES[1:4])
    probability_orders = np.argsort(-probability_predictions, axis=2, kind="stable")
    followup_probability_orders = np.array([[[int(j) for j in order if int(j) not in probes]
                                             for order in cell_orders] for cell_orders in probability_orders])
    np.savez(HERE / "replay_arrays.npz", actions=actions, predictions=predictions, bootstrap_indices=samples,
             probability_predictions=probability_predictions, probability_orders=probability_orders,
             followup_probability_orders=followup_probability_orders)
    summary = {"state": "executed_pending_independent_verification", "hypothesis_joint_supported": joint,
               "train_cells": len(train_cells), "test_cells": len(test_cells), "menu": 64,
               "metrics": metrics, "comparisons": comparisons, "max_posterior_error": max_error,
               "cells_with_changed_action_set_vs_probe_blind": int(changed_actions),
               "max_probe_prediction_change": float(np.max(np.abs(predictions[:, 1]-predictions[:, 0]))),
               "max_probe_probability_change": float(np.max(np.abs(probability_predictions[:, 1]-probability_predictions[:, 0]))),
               "cells_with_changed_probability_order": int(np.any(probability_orders[:, 0] != probability_orders[:, 1], axis=1).sum()),
               "finite_below_minimum_test_entries": int((test_finite & (test < low-1e-8)).sum()),
               "finite_above_maximum_test_entries": int((test_finite & (test > high+1e-8)).sum()),
               "finite_minimum_boundary_band_entries": int((test_finite & (np.abs(test-low) <= 1e-8)).sum()),
               "finite_maximum_boundary_band_entries": int((test_finite & (np.abs(test-high) <= 1e-8)).sum()),
               "finite_window_interior_test_entries": int((test_finite & (test > low+1e-8) & (test < high-1e-8)).sum()),
               "training_eligible_count": len(eligible), "cpu_seconds": process_time()-cpu0,
               "wall_seconds": perf_counter()-clock0,
               "peak_working_set_bytes": psutil.Process().memory_info().peak_wset,
               "scope": "Conditional archived fitted-candidate development replay, not independent functional benefit"}
    assert summary["cpu_seconds"] <= 1200 and summary["peak_working_set_bytes"] <= 2_000_000_000
    write_json("experiment_summary.json", summary)
    receipt.update(state=summary["state"], summary_sha256=sha(HERE / "experiment_summary.json"),
                   cpu_seconds=summary["cpu_seconds"], wall_seconds=summary["wall_seconds"],
                   peak_working_set_bytes=summary["peak_working_set_bytes"])
    write_json(RECEIPT.name, receipt)
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
