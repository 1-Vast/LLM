"""Fixed-probe context-transfer diagnostic with separate commit and score phases."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
from maestro.campaign_budget import CampaignBudget
from tools.evaluation.decision_report import CampaignResult, paired_campaign_report
from research.context_probe_20261011.model import fit_reference

P = json.loads((HERE / "PROTOCOL.json").read_text(encoding="utf-8"))
ARMS = P["arms"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def load_data(path):
    with np.load(path, allow_pickle=False) as data:
        return {key: data[key] for key in data.files}


def selection(prediction, terminal):
    return terminal[np.argsort(prediction[terminal], kind="stable")[:P["top_k"]]]


def utility(truth, chosen):
    return -float(truth[chosen].mean()) if np.isfinite(truth[chosen]).all() else None


def choose_setting(predictions, truths, terminal):
    """Development only; compare settings on exactly the same scored contexts."""
    scores = [[utility(truth, selection(prediction, terminal)) for prediction, truth in zip(setting, truths)]
              for setting in predictions]
    values = np.array([[np.nan if x is None else x for x in row] for row in scores])
    common = np.isfinite(values).all(axis=0)
    if common.sum() < 10:
        raise RuntimeError("INSUFFICIENT_COMMON_DEVELOPMENT_OUTCOMES")
    means = values[:, common].mean(axis=1)
    return int(np.argmax(means)), {"common_contexts": int(common.sum()), "total_contexts": len(common),
                                   "mean_utility": means.tolist(), "complete_mask": common.tolist()}


def update(model, basal, probes, values, method, config):
    # An attempted but unobserved probe is not imputed, replaced or free.
    if not np.isfinite(values).all():
        return model.predict_prior(basal)
    return model.predict(basal, probes, values, method=method, **config, shuffle_seed=P["seed"])


def fit_and_choose(data, on_probes=None):
    """Only reference responses and development outcomes may enter this phase."""
    reference = np.flatnonzero(data["role"] == "reference")
    development = np.flatnonzero(data["role"] == "development")
    basal, response = data["basal"][reference], data["y"][reference]
    fixed = fit_reference(basal, response, prior="knn", n_neighbors=15, seed=P["seed"])
    probes = fixed.select_probes(P["probe_count"])
    terminal = np.setdiff1d(np.arange(response.shape[1]), probes)
    if on_probes is not None:
        on_probes({"probe_indices": probes.tolist(), "probe_ids": data["drug_id"][probes].tolist(),
                   "reference_context_ids": data["context_id"][reference].tolist(),
                   "phase": "Fixed from reference-only residuals before scoring development outcomes"})
    models = [fit_reference(basal, response, **config, seed=P["seed"]) for config in P["prior_configs"]]
    predictions = [[model.predict_prior(data["basal"][index]) for index in development] for model in models]
    best, prior_scores = choose_setting(predictions, data["y"][development], terminal)
    model = models[best]
    family_choices, reports = {}, {}
    for family, configs in (("lowrank", P["lowrank_configs"]),
                            ("conditional", [{"ridge": v} for v in P["conditional_ridge"]])):
        predictions = [[update(model, data["basal"][index], probes, data["y"][index, probes], family, config)
                        for index in development] for config in configs]
        winner, scores = choose_setting(predictions, data["y"][development], terminal)
        family_choices[family] = configs[winner]
        reports[family] = {"configs": configs, "selected_index": winner, **scores}
    frozen = {"prior": P["prior_configs"][best], "prior_scores": prior_scores,
              "updates": family_choices, "update_scores": reports,
              "probe_indices": probes.tolist(), "probe_ids": data["drug_id"][probes].tolist(),
              "terminal_count": len(terminal), "reference_contexts": len(reference),
              "development_contexts": len(development),
              "limitation": "Model and settings use exposed reference/development outcomes; no evaluation responses enter fitting"}
    return model, probes, terminal, frozen


def commit_context(model, basal, probes, probe_values, terminal, frozen):
    """The function cannot receive terminal truth or target-wide availability."""
    prior = model.predict_prior(basal)
    predictions = {"zero_purchase": prior, "paid_no_update": prior,
                   "offset": update(model, basal, probes, probe_values, "offset", {}),
                   "lowrank": update(model, basal, probes, probe_values, "lowrank", frozen["updates"]["lowrank"]),
                   "shuffled_lowrank": update(model, basal, probes, probe_values, "shuffled", frozen["updates"]["lowrank"]),
                   "conditional": update(model, basal, probes, probe_values, "conditional", frozen["updates"]["conditional"])}
    selected = {arm: selection(prediction, terminal).tolist() for arm, prediction in predictions.items()}
    assert selected["zero_purchase"] == selected["paid_no_update"] == selected["offset"]
    return np.array([predictions[arm] for arm in ARMS]), selected


def create_commits(data, model, probes, terminal, frozen):
    budget = CampaignBudget(**P["budget"])
    predictions, records = [], []
    for index in np.flatnonzero(data["role"] == "evaluation"):
        values = data["y"][index, probes].copy()
        matrix, selected = commit_context(model, data["basal"][index], probes, values, terminal, frozen)
        predictions.append(matrix)
        for arm in ARMS:
            paid = arm != "zero_purchase"
            records.append({"context": str(data["context_id"][index]), "index": int(index),
                            "lineage": str(data["lineage"][index]), "arm": arm,
                            "selected_indices": selected[arm], "selected_ids": data["drug_id"][selected[arm]].tolist(),
                            "probe_indices": probes.tolist() if paid else [],
                            "probe_ids": data["drug_id"][probes].tolist() if paid else [],
                            "probe_values": [float(v) if np.isfinite(v) else None for v in values] if paid else [],
                            "measurements": P["probe_count"] if paid else 0, "turnarounds": int(paid),
                            "resource": budget.require_feasible(P["probe_count"] if paid else 0, int(paid)),
                            "probe_missing": int((~np.isfinite(values)).sum()) if paid else 0,
                            "update_status": "zero_purchase" if not paid else "missing_probe_fallback" if not np.isfinite(values).all()
                            else "ignored_for_ranking" if arm == "paid_no_update" else "applied"})
    return np.asarray(predictions), records


def score(data, predictions, records, out):
    terminal = np.setdiff1d(np.arange(len(data["drug_id"])), records[1]["probe_indices"])
    eval_indices = np.flatnonzero(data["role"] == "evaluation")
    position = {int(index): j for j, index in enumerate(eval_indices)}
    rows = []
    for record in records:
        index, arm = record["index"], record["arm"]
        truth = data["y"][index]
        prediction = predictions[position[index], ARMS.index(arm)]
        chosen = np.array(record["selected_indices"])
        measured = terminal[np.isfinite(truth[terminal])]
        observed_selected = chosen[np.isfinite(truth[chosen])]
        base_choice = records[position[index] * len(ARMS)]["selected_indices"]
        row = {**record, "utility": utility(truth, chosen),
               "selected_missing": int((~np.isfinite(truth[chosen])).sum()),
               "selected_measured": len(observed_selected), "terminal_measured": len(measured),
               "terminal_mse": float(np.square(prediction[measured] - truth[measured]).mean()) if len(measured) else None,
               "selected_mae": float(np.abs(prediction[observed_selected] - truth[observed_selected]).mean()) if len(observed_selected) else None,
               "changed_selected": len(set(chosen) - set(base_choice))}
        rows.append(row)
    dump(out / "ROWS.json", rows)
    summary = {}
    for arm in ARMS:
        rr = [r for r in rows if r["arm"] == arm]
        complete = [r for r in rr if r["utility"] is not None]
        summary[arm] = {"contexts": len(rr), "fully_scored_contexts": len(complete),
                        "missing_probe_fallback_contexts": sum(r["update_status"] == "missing_probe_fallback" for r in rr),
                        "mean_utility_complete_only": float(np.mean([r["utility"] for r in complete])) if complete else None,
                        "mean_terminal_mse_available_only": float(np.mean([r["terminal_mse"] for r in rr if r["terminal_mse"] is not None])),
                        "mean_changed_selected": float(np.mean([r["changed_selected"] for r in rr])),
                        "resource_per_context": rr[0]["resource"]}
    comparisons = {}
    problem_prefix = sha(out / "FREEZE.json")
    for candidate, reference in (("lowrank", "paid_no_update"), ("lowrank", "shuffled_lowrank"),
                                  ("lowrank", "conditional"), ("conditional", "paid_no_update"),
                                  ("offset", "paid_no_update"), ("lowrank", "zero_purchase")):
        lookup = {(r["context"], r["arm"]): r for r in rows}
        contexts = [r["context"] for r in rows if r["arm"] == reference]
        complete = [context for context in contexts if all(lookup[context, arm]["utility"] is not None
                                                           for arm in (reference, candidate))]
        pair_rows = [CampaignResult(context, lookup[context, arm]["lineage"], arm,
                                   "prism_hts_2.5um_negative_mean_log2fc",
                                   hashlib.sha256(f"{problem_prefix}:{context}".encode()).hexdigest(), 8,
                                   lookup[context, arm]["utility"], lookup[context, arm]["measurements"],
                                   lookup[context, arm]["turnarounds"]) for context in complete for arm in (reference, candidate)]
        prices = P["price_grid"] if reference == "zero_purchase" else [0]
        for price in prices:
            key = f"{candidate}_minus_{reference}_price_{price}"
            result = None if not pair_rows else paired_campaign_report(pair_rows, reference=reference, candidate=candidate,
                        measurement_price=price, turnaround_price=2 * price, resource_budget=CampaignBudget(**P["budget"]),
                        seed=P["seed"], resamples=2000)
            diffs = [lookup[context, candidate]["utility"] - lookup[context, reference]["utility"] for context in complete]
            comparisons[key] = {"report": result, "intended_contexts": len(contexts), "paired_contexts": len(complete),
                                "unscored_contexts": [c for c in contexts if c not in complete],
                                "improved": sum(d > 1e-12 for d in diffs), "harmed": sum(d < -1e-12 for d in diffs),
                                "equal": sum(abs(d) <= 1e-12 for d in diffs),
                                "scope": "Complete selected-outcome subset; may be informative missingness. Lineages are not independent culture units"}
    keys = ["lowrank_minus_paid_no_update_price_0", "lowrank_minus_shuffled_lowrank_price_0",
            "lowrank_minus_conditional_price_0", "lowrank_minus_zero_purchase_price_0.001"]
    complete = all(not comparisons[key]["unscored_contexts"] for key in keys)
    positive = all(comparisons[key]["report"] and comparisons[key]["report"]["cluster_bootstrap_95"]
                   and comparisons[key]["report"]["cluster_bootstrap_95"][0] > 0 for key in keys)
    output = {"scope": P["scope"], "status": "PROMISING_EXPLORATORY_ONLY" if complete and positive else "NOT_ESTABLISHED",
              "all_primary_contrasts_complete": complete, "arms": summary, "comparisons": comparisons,
              "reliability": P["reliability"], "llm_api_calls": 0,
              "interpretation": "A positive subset contrast cannot establish full-population benefit or independent biology. No empirical model is promoted"}
    dump(out / "RESULTS.json", output)
    return output


def run(data_path, out):
    if (out / "FREEZE.json").exists():
        raise RuntimeError("OUTPUT_ALREADY_FROZEN: choose a fresh --output directory")
    out.mkdir(parents=True, exist_ok=True)
    paths = [HERE / "PROTOCOL.json", HERE / "model.py", Path(__file__), HERE / "data/prepare.py",
             HERE / "data/MANIFEST.json", ROOT / "tools/evaluation/decision_report.py",
             ROOT / "tools/evaluation/scoring.py", ROOT / "src/maestro/campaign_budget.py"]
    dump(out / "FREEZE.json", {"scope": P["scope"], "input_path": str(data_path.resolve()),
                              "input_sha256": sha(data_path), "files": {str(p.relative_to(ROOT)): sha(p) for p in paths}})
    started = time.perf_counter()
    with threadpool_limits(limits=1):
        data = load_data(data_path)
        model, probes, terminal, frozen = fit_and_choose(data, lambda panel: dump(out / "PROBE_FREEZE.json", panel))
        dump(out / "FIT_FREEZE.json", frozen)
        print(json.dumps({"prior": frozen["prior"], "updates": frozen["updates"], "probe_ids": frozen["probe_ids"]}), flush=True)
        predictions, records = create_commits(data, model, probes, terminal, frozen)
        dump(out / "COMMITS.json", records)
        np.savez_compressed(out / "predictions.npz", predictions=predictions)
        dump(out / "COMMIT_RECEIPT.json", {"commits_sha256": sha(out / "COMMITS.json"),
                                          "predictions_sha256": sha(out / "predictions.npz"),
                                          "fit_sha256": sha(out / "FIT_FREEZE.json"),
                                          "phase": "Written before reading evaluation terminal responses for scoring"})
        result = score(data, predictions, records, out)
        dump(out / "RECEIPT.json", {"seconds": time.perf_counter() - started, "contexts": len(predictions),
                                   "arm_contexts": len(records), "llm_api_calls": 0,
                                   "results_sha256": sha(out / "RESULTS.json"), "rows_sha256": sha(out / "ROWS.json")})
        print(json.dumps({"status": result["status"], "arms": result["arms"]}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=HERE / "data/output.npz")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.data, args.output)
