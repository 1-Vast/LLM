"""One development replay of the frozen C6 candidate; no production promotion."""
from pathlib import Path
from time import perf_counter, process_time
import hashlib
import importlib.util
import json
import os
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np
import psutil

HERE = Path(__file__).resolve().parent
C4 = HERE.parent / "2026-10-29-common-functional-transfer"
STRATEGIES = ("rank8", "static_global13", "static_tissue13", "matched_blind",
              "random13", "rank1", "knn5")
SPEC = importlib.util.spec_from_file_location("frozen_c4_functions", C4 / "e_c4_budget.py")
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)


def save(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                      allow_nan=False) + "\n", encoding="utf-8")


def synthetic():
    # Shared unknowns cancel; only the opposing unique unknown lowers a difference.
    event = np.array([False, True, False, False])
    finite = np.array([False, True, False, True])
    assert BASE.paired_bounds(event, finite, [0, 1], [0, 2]) == (0, 1)
    assert BASE.choose(np.array([.5, .5, .1]), 2, [0]) == [1, 2]
    a = np.array([[1., .3], [1., -.7], [1., 1.1]])
    model = (a, np.zeros(2), np.array([[1., .1], [.1, .5]]), np.array([.2, .4, .3]))
    m, p = model[1].copy(), model[2].copy()
    for j, value in zip([0, 2], [.8, -.3]):
        m, p = BASE.update(model, m, p, j, value)
    dm, dp = BASE.direct(model, np.array([0, 2]), np.array([.8, -.3]))
    assert np.allclose(m, dm, atol=1e-12) and np.allclose(p, dp, atol=1e-12)
    assert BASE.probabilities(np.zeros(2), np.ones(2), np.array([0., 1.]),
                              np.array([0., -1.])).tolist() == [0., 0.]
    print("Synthetic contracts passed; no real data loaded")


def main():
    receipt_path = HERE / "experiment_receipt.json"
    assert not receipt_path.exists(), "Receipt exists: no automatic scientific rerun"
    wall0, cpu0 = perf_counter(), process_time()
    frozen = json.loads((HERE / "input_freeze.json").read_text(encoding="utf-8"))
    for item in frozen["files"]:
        assert BASE.sha(item["path"]) == item["sha256"], item["path"]
    protocol = HERE / "candidate_c6_v1.md"
    receipt = {"state": "started", "protocol_sha256": BASE.sha(protocol),
               "implementation_sha256": BASE.sha(__file__),
               "input_freeze_sha256": BASE.sha(HERE / "input_freeze.json"),
               "functional_test_values_consumed": False, "one_scientific_run": True}
    save(receipt_path.name, receipt)
    meta = json.loads((C4 / "metadata_freeze.json").read_text(encoding="utf-8"))
    train = [c for c in meta["cells"] if c["role"] == "train"]
    test_cells = [c for c in meta["cells"] if c["role"] == "model_unseen_exposed_development"]
    training = json.loads((C4 / "training_freeze.json").read_text(encoding="utf-8"))
    assert BASE.sha(meta["source"]) == meta["source_sha256"]
    assert BASE.sha(C4 / "training_model.npz") == training["training_artifact_sha256"]
    assert training["train_ids"] == [c["id"] for c in train]
    assert training["test_ids"] == [c["id"] for c in test_cells]
    assert len(train) == 566 and len(test_cells) == 243
    data = np.load(C4 / "training_model.npz", allow_pickle=False)
    menu, n = training["menu"], len(test_cells)
    mu, sd, low, high = (data[k] for k in ("mu", "sd", "low", "high"))
    s, finite, event, global_rate = (data[k] for k in ("s", "finite", "event", "global_rate"))
    assert s.shape == finite.shape == event.shape == (566, 64) and len(menu) == 64
    models = {r: tuple(data[f"{key}{r}"] for key in ("a", "m", "p", "noise")) for r in (1, 8)}
    low_s, high_s = (mu-np.minimum(0, high))/sd, (mu-low)/sd
    raw = BASE.select_raw(meta["source"], test_cells, menu)
    accesses = []

    def query(i, j, allowed, phase):
        assert j in allowed, "Feedback outside the selected action set"
        if not receipt["functional_test_values_consumed"]:
            receipt.update(state="feedback_running", functional_test_values_consumed=True)
            save(receipt_path.name, receipt)
        value = BASE.number(raw.get((i, j)))
        accesses.append({"cell_index": i, "condition_index": int(j), "phase": phase,
                         "value": float(value) if np.isfinite(value) else None})
        return value

    actions = np.zeros((n, 7, 13), dtype=np.int64)
    first6 = np.zeros((n, 6), dtype=np.int64)
    observed = np.full((n, 64), np.nan)
    probabilities = np.zeros((n, 2, 64))
    post = {r: (np.zeros((n, r+1)), np.zeros((n, r+1, r+1))) for r in (1, 8)}
    errors, traces = [], []
    for i, cell in enumerate(test_cells):
        same_tissue = np.array([c["tissue"] == cell["tissue"] for c in train])
        rate = (event[same_tissue].sum(axis=0)+5*global_rate)/(finite[same_tissue].sum(axis=0)+5)
        tissue13 = BASE.choose(rate, 13)
        batch = tissue13[:6]
        first6[i] = batch
        feedback = np.array([query(i, j, batch, "shared_first6") for j in batch])
        observed[i, batch] = (mu[batch]-feedback)/sd[batch]
        known = [j for j in batch if np.isfinite(observed[i, j])]
        policies = {"static_global13": BASE.choose(global_rate, 13), "static_tissue13": tissue13,
                    "random13": sorted(range(64), key=lambda j: hashlib.sha256(
                        ("C6-random|"+cell["id"]+"|"+menu[j]["id"]).encode()).hexdigest())[:13]}
        assert batch+BASE.choose(rate, 7, batch) == tissue13
        for rank in (1, 8):
            model = models[rank]
            a, m, p, noise = model
            m, p = m.copy(), p.copy()
            for j in known:
                m, p = BASE.update(model, m, p, j, observed[i, j])
            dm, dp = BASE.direct(model, np.array(known, dtype=int), observed[i, known])
            errors.extend((float(np.max(np.abs(dm-m))), float(np.max(np.abs(dp-p)))))
            prob = BASE.probabilities(a@m, noise+np.einsum("ij,jk,ik->i", a, p, a), low_s, high_s)
            direct_prob = BASE.probabilities(a@dm, noise+np.einsum("ij,jk,ik->i", a, dp, a), low_s, high_s)
            assert BASE.choose(prob, 7, batch) == BASE.choose(direct_prob, 7, batch)
            policies[f"rank{rank}"] = batch+BASE.choose(prob, 7, batch)
            post[rank][0][i], post[rank][1][i] = m, p
            if rank == 8:
                prior = BASE.probabilities(a@model[1], noise+np.einsum(
                    "ij,jk,ik->i", a, model[2], a), low_s, high_s)
                probabilities[i] = prior, prob
                policies["matched_blind"] = batch+BASE.choose(prior, 7, batch)
        nn_rate = global_rate.copy()
        if known:
            distance = ((s[:, known]-observed[i, known])**2).mean(axis=1)
            neighbors = np.argsort(distance, kind="stable")[:5]
            weights = 1/(distance[neighbors]+.1)
            denominator = (weights[:, None]*finite[neighbors]).sum(axis=0)
            nn_rate = np.divide((weights[:, None]*event[neighbors]).sum(axis=0), denominator,
                                out=global_rate.copy(), where=denominator > 0)
        policies["knn5"] = batch+BASE.choose(nn_rate, 7, batch)
        for k, name in enumerate(STRATEGIES):
            assert len(policies[name]) == len(set(policies[name])) == 13
            actions[i, k] = policies[name]
        traces.append({"cell": cell["id"], "policies": policies, "finite_first6_updates": len(known)})
    assert max(errors) <= 1e-8
    assert BASE.sha(__file__) == receipt["implementation_sha256"]
    assert BASE.sha(protocol) == receipt["protocol_sha256"]
    np.savez(HERE / "actions_only.npz", actions=actions, first6=first6)
    save("actions_freeze.json", {"actions_sha256": hashlib.sha256(actions.tobytes()).hexdigest(),
         "first6_sha256": hashlib.sha256(first6.tobytes()).hexdigest(), "strategy_order": STRATEGIES,
         "all_actions_fixed_before_full_truth_conversion": True, "feedback_accesses_at_freeze": len(accesses),
         "actions_only_file_sha256": BASE.sha(HERE / "actions_only.npz")})
    (HERE / "query_trace.jsonl").write_text("".join(json.dumps(t)+"\n" for t in traces), encoding="utf-8")
    # Selected followups only, after every policy's actions have been persisted.
    for i in range(n):
        for rank in (1, 8):
            selected = actions[i, STRATEGIES.index(f"rank{rank}"), 6:]
            known = [int(j) for j in first6[i] if np.isfinite(observed[i, j])]
            values = [observed[i, j] for j in known]
            m, p = post[rank][0][i].copy(), post[rank][1][i].copy()
            for j in selected:
                value = query(i, int(j), selected, f"rank{rank}_selected_followup")
                if np.isfinite(value):
                    v = (mu[j]-value)/sd[j]
                    known.append(int(j))
                    values.append(v)
                    m, p = BASE.update(models[rank], m, p, j, v)
            dm, dp = BASE.direct(models[rank], np.array(known, dtype=int), np.array(values))
            errors.extend((float(np.max(np.abs(dm-m))), float(np.max(np.abs(dp-p)))))
    assert max(errors) <= 1e-8
    (HERE / "feedback_access.jsonl").write_text("".join(json.dumps(t)+"\n" for t in accesses), encoding="utf-8")
    truth = np.full((n, 64), np.nan)
    for ij, token in raw.items():
        truth[ij] = BASE.number(token)
    truth_finite, truth_event = BASE.labels(truth, low, high)
    samples = np.random.default_rng(20261029).integers(0, n, (2000, n))
    metrics, comparisons = {}, {}
    hits, unknown = np.zeros((n, 7), dtype=int), np.zeros((n, 7), dtype=int)
    bounds = np.zeros((n, 6, 2), dtype=int)
    for k, name in enumerate(STRATEGIES):
        hits[:, k] = np.take_along_axis(truth_event, actions[:, k], axis=1).sum(axis=1)
        unknown[:, k] = (~np.take_along_axis(truth_finite, actions[:, k], axis=1)).sum(axis=1)
        metrics[name] = {"candidate_count_lower": float(hits[:, k].mean()),
                         "candidate_count_upper": float((hits[:, k]+unknown[:, k]).mean()),
                         "mean_unknown_attempts": float(unknown[:, k].mean()), "attempts_per_cell": 13}
        if k:
            bounds[:, k-1] = [BASE.paired_bounds(truth_event[i], truth_finite[i], actions[i, 0], actions[i, k])
                             for i in range(n)]
            lower, upper = bounds[:, k-1, 0], bounds[:, k-1, 1]
            ci = np.quantile(lower[samples].mean(axis=1), [.025, .975], method="linear")
            comparisons[name] = {"mean_difference_lower": float(lower.mean()),
                                 "mean_difference_upper": float(upper.mean()),
                                 "difference_lower_bootstrap_ci95": ci.tolist(),
                                 "passes_point_and_ci": bool(lower.mean() >= .5 and ci[0] > 0)}
    np.savez(HERE / "replay_arrays.npz", actions=actions, first6=first6, probability_predictions=probabilities,
             posterior_m8=post[8][0], posterior_p8=post[8][1], posterior_m1=post[1][0], posterior_p1=post[1][1],
             bootstrap_indices=samples, hits=hits, unknown=unknown, paired_bounds=bounds)
    summary = {"state": "executed_pending_independent_verification", "hypothesis_joint_supported": all(
        comparisons[k]["passes_point_and_ci"] for k in STRATEGIES[1:4]), "strategy_order": STRATEGIES,
        "train_cells": 566, "test_cells": n, "menu": 64, "metrics": metrics, "comparisons": comparisons,
        "max_posterior_error": max(errors), "direct_first6_actions_identical": True,
        "tissue_continuation_identical": True, "feedback_numeric_accesses": len(accesses),
        "cells_with_changed_action_set_vs_matched_blind": sum(
            set(actions[i, 0]) != set(actions[i, 3]) for i in range(n)),
        "cpu_seconds": process_time()-cpu0, "wall_seconds": perf_counter()-wall0,
        "peak_working_set_bytes": psutil.Process().memory_info().peak_wset,
        "scope": "Outcome-informed development on archived fitted candidates; no independent functional benefit"}
    assert summary["cpu_seconds"] <= 1200 and summary["peak_working_set_bytes"] <= 2_000_000_000
    save("experiment_summary.json", summary)
    receipt.update(state=summary["state"], summary_sha256=BASE.sha(HERE / "experiment_summary.json"),
                   cpu_seconds=summary["cpu_seconds"], wall_seconds=summary["wall_seconds"],
                   peak_working_set_bytes=summary["peak_working_set_bytes"])
    save(receipt_path.name, receipt)
    print(json.dumps(summary))


if __name__ == "__main__":
    if sys.argv[1:] == ["--synthetic"]:
        synthetic()
    elif not sys.argv[1:]:
        main()
    else:
        raise SystemExit("Only --synthetic or no arguments are supported")
