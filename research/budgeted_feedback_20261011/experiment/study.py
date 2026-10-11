"""Two-round, resource-matched development replay. No LLM or network calls."""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRIOR = ROOT / "research/dual_core_scientific_20261011/experiment"
sys.path.insert(0, str(PRIOR))
import campaign as C
import run as R

P = json.loads((HERE / "PROTOCOL.json").read_text(encoding="utf-8"))
CFG = {"tau": 0.05, "sigma": 2.0}
SEED = P["seed"]


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def stage_plan(posterior, count, mode="kg"):
    """All actions in this batch are chosen before its feedback exists."""
    designer = copy.deepcopy(posterior)
    actions = []
    for _ in range(count):
        values = designer.values(mode)
        index = int(np.argmax(values))
        line = int(designer.query.menu[index])
        actions.append((line, float(values[index])))
        designer.observe(line, None)
    return actions


def buy_batch(posterior, environment, plan, round_number):
    marginal = []
    for line, _ in plan:
        j = posterior.position[line]
        marginal.append((float(posterior.mean[j]),
                         float(np.sqrt(posterior.covariance[j, j] + posterior.sigma ** 2))))
    values = [environment.measure(line, gain) for line, gain in plan]
    innovations = [abs(y - m) / s for y, (m, s) in zip(values, marginal)]
    for (line, _), value in zip(plan, values):
        posterior.observe(line, value)
    return {"round": round_number, "action": "buy_batch", "plan": [p[0] for p in plan],
            "predicted_gains": [p[1] for p in plan], "values": values,
            "max_standardized_innovation": float(max(innovations))}


def snapshot(posterior, environment):
    prediction = posterior.predict()
    score, ledger = environment.score(prediction)
    covariance = posterior.covariance[:posterior.n_targets, :posterior.n_targets]
    projection = posterior.target_projector
    # diag(P C P^T), avoiding another full matrix product.
    sd = np.sqrt(np.maximum(np.sum((projection @ covariance) * projection, axis=1), 1e-12))
    selected = np.argsort(prediction, kind="stable")[:C.TOP_K]
    truth = np.array(ledger["truth"])
    score["selected_error"] = float(np.max(np.abs(prediction[selected] - truth[selected])))
    score["selected_standardized_error"] = float(np.max(np.abs(prediction[selected] - truth[selected]) / sd[selected]))
    score["selected_mean_sd"] = float(sd[selected].mean())
    ledger.update(posterior_sd=sd.tolist(), selected_indices=selected.tolist())
    return score, ledger


def finish(query, arm, score, ledger, events, snapshots, risk, predicted_gain=0.0):
    reads = len(ledger["purchases"])
    rounds = len(events)
    resource = reads + P["turnaround_read_equivalents"] * rounds
    if resource > P["resource_budget"] or rounds > 2:
        raise AssertionError("RESOURCE_BUDGET_EXCEEDED")
    row = dict(score, drug=query.drug, moa=query.moa, old_role=query.role, arm=arm,
               reads=reads, rounds=rounds, resource=resource,
               net_utility=score["utility"] - P["read_utility_price"] * resource,
               path_standardized_error=max(x["selected_standardized_error"] for x in snapshots),
               path_absolute_error=max(x["selected_error"] for x in snapshots),
               risk_feature=risk, predicted_remaining_gain=predicted_gain)
    ledger.update(drug=query.drug, arm=arm, events=events,
                  decision_snapshots=[{"selected_standardized_error": s["selected_standardized_error"],
                                       "selected_error": s["selected_error"]} for s in snapshots],
                  stop_reason="planned_budget_exhausted", resource=resource)
    return row, ledger


def run_campaign(library, datum):
    query, primary, secondary = datum
    rows, ledgers = [], []
    env = C.MeasuredEnvironment(library, query, primary, secondary)
    prediction = library.transfer(query)
    score, ledger = env.score(prediction)
    selected = np.argsort(prediction, kind="stable")[:C.TOP_K]
    absolute = float(np.max(np.abs(prediction[selected] - np.array(ledger["truth"])[selected])))
    score.update(selected_error=absolute, selected_standardized_error=absolute, selected_mean_sd=1.0)
    ledger.update(posterior_sd=np.ones(len(prediction)).tolist(), selected_indices=selected.tolist())
    row, ledger = finish(query, "source_only", score, ledger, [], [score], 0)
    rows.append(row)
    ledgers.append(ledger)

    kg_plan = None
    for mode in ("ivr", "kg"):
        initial = C.GaussianPosterior(library, query, **CFG)
        plan = stage_plan(initial, 16, mode)
        if mode == "kg":
            kg_plan = plan
        for count in (4, 14, 16):
            posterior = copy.deepcopy(initial)
            env = C.MeasuredEnvironment(library, query, primary, secondary)
            event = buy_batch(posterior, env, plan[:count], 1)
            score, ledger = snapshot(posterior, env)
            # The first four positions are fixed pre-feedback. Their innovations
            # are available after the one whole batch has returned.
            risk = max(abs(primary[line] - initial.mean[initial.position[line]]) /
                       np.sqrt(initial.covariance[initial.position[line], initial.position[line]] + initial.sigma ** 2)
                       for line, _ in plan[:4])
            row, ledger = finish(query, f"batch_gp_{mode}_{count}", score, ledger, [event], [score], float(risk))
            rows.append(row)
            ledgers.append(ledger)

    for arm in ("two_stage_kg_14", "fixed_split_kg_14", "shuffled_two_stage_kg_14"):
        posterior = C.GaussianPosterior(library, query, **CFG)
        env = C.MeasuredEnvironment(library, query, primary, secondary,
                                    feedback_shuffle=arm.startswith("shuffled"))
        first = buy_batch(posterior, env, kg_plan[:4], 1)
        first_score, first_ledger = snapshot(posterior, env)
        remaining = stage_plan(posterior, 10)
        predicted = float(sum(value for _, value in remaining))
        if arm == "two_stage_kg_14":
            stoprow, stopledger = finish(query, "stop_after_4", first_score, first_ledger, [first],
                                         [first_score], first["max_standardized_innovation"], predicted)
            stopledger["stop_reason"] = "stop_counterfactual_for_gate_fit"
            rows.append(stoprow)
            ledgers.append(stopledger)
        second_plan = kg_plan[4:14] if arm == "fixed_split_kg_14" else remaining
        second = buy_batch(posterior, env, second_plan, 2)
        score, ledger = snapshot(posterior, env)
        row, ledger = finish(query, arm, score, ledger, [first, second], [first_score, score],
                             first["max_standardized_innovation"], predicted)
        # Preserve full predictions at the adaptation decision as well as final.
        ledger["first_decision"] = first_ledger
        rows.append(row)
        ledgers.append(ledger)
    return rows, ledgers


def partition(data):
    dev = [d for d in data if d[0].role == "development"]
    ordered = sorted(dev, key=lambda d: hashlib.sha256(f"{SEED}:{d[0].drug}".encode()).hexdigest())
    fit = {d[0].drug for d in ordered[:141]}
    calibrate = {d[0].drug for d in ordered[141:]}
    assert len(fit) == 141 and len(calibrate) == 140
    return {d[0].drug: "fit" if d[0].drug in fit else "calibration" if d[0].drug in calibrate else "exposed_replay"
            for d in data}


def fit_gate(frame):
    fit = frame[frame.partition == "fit"]
    continued = fit[fit.arm == "two_stage_kg_14"].set_index("drug")
    stopped = fit[fit.arm == "stop_after_4"].set_index("drug").loc[continued.index]
    median = float(continued.predicted_remaining_gain.median())
    gain = continued.utility - stopped.utility
    bins = continued.predicted_remaining_gain.gt(median).astype(int)
    rng = np.random.default_rng(SEED)
    groups = []
    for group in (0, 1):
        values = gain[bins == group].to_numpy()
        bootstrap = values[rng.integers(len(values), size=(4000, len(values)))].mean(axis=1)
        lower = float(np.quantile(bootstrap, 0.05))
        cost = 12 * P["read_utility_price"]
        groups.append({"group": group, "n": len(values), "mean_gain": float(values.mean()),
                       "gain_lower_estimate": lower, "incremental_cost": cost,
                       "continue": lower > cost})
    baseline_scores = fit[fit.arm.isin(P["baseline_family"])].groupby("arm").net_utility.mean().to_dict()
    baseline = sorted(baseline_scores, key=lambda arm: (-baseline_scores[arm], arm))[0]
    return {"gain_median": median, "groups": groups, "best_baseline": baseline,
            "fit_baseline_net_utility": baseline_scores,
            "risk_medians": fit.groupby("arm").risk_feature.median().to_dict()}


def continue_after_first(gain, gate):
    group = int(gain > gate["gain_median"])
    return bool(gate["groups"][group]["continue"]), group


def apply_gate(frame, gate):
    records = []
    for drug, data in frame.groupby("drug", sort=False):
        indexed = data.set_index("arm")
        continued = indexed.loc["two_stage_kg_14"]
        proceed, group = continue_after_first(continued.predicted_remaining_gain, gate)
        origin = "two_stage_kg_14" if proceed else "stop_after_4"
        row = indexed.loc[origin].to_dict()
        row.update(arm="gated_two_stage", chosen_origin=origin, gate_group=group,
                   gate_lower_estimate=gate["groups"][group]["gain_lower_estimate"],
                   gate_reason="continue_lower_gain_exceeds_cost" if proceed else "stop_insufficient_lower_gain")
        records.append(row)
    return pd.concat([frame, pd.DataFrame(records)], ignore_index=True)


def calibrate_reliability(frame, gate):
    fit = frame[frame.partition == "fit"]
    calibration = frame[frame.partition == "calibration"]
    result = {}
    for arm, rows in calibration.groupby("arm"):
        median = float(fit[fit.arm == arm].risk_feature.median())
        groups = rows.risk_feature.gt(median).astype(int)
        group_quantiles = {}
        for group in (0, 1):
            errors = rows.loc[groups == group, "path_standardized_error"].to_numpy()
            # Source-only has one observable group; no empty-bin claim is made.
            if len(errors):
                q = R.conformal_quantile(errors) if len(errors) >= 9 else None
                group_quantiles[str(group)] = {"n": len(errors), "q": q}
        result[arm] = {"global_q": R.conformal_quantile(rows.path_standardized_error.to_numpy()),
                       "risk_median": median, "risk_groups": group_quantiles}
    return result


def report(frame, gate, reliability):
    replay = frame[frame.partition == "exposed_replay"].copy()
    summary, coverage = {}, {}
    for arm, rows in replay.groupby("arm"):
        calibration = reliability[arm]
        groups = rows.risk_feature.gt(calibration["risk_median"]).astype(int)
        quantiles = np.array([calibration["risk_groups"].get(str(g), {}).get("q")
                             if calibration["risk_groups"].get(str(g), {}).get("q") is not None
                             else float("inf") for g in groups])
        covered = rows.path_standardized_error.to_numpy() <= quantiles
        active = rows.active_query.to_numpy(dtype=bool)
        summary[arm] = {key: float(rows[key].mean()) for key in
                        ("utility", "net_utility", "precision", "reads", "rounds", "resource", "secondary_utility")}
        coverage[arm] = {"n": len(rows), "selected_path_coverage": float(covered.mean()),
                         "active_n": int(active.sum()),
                         "active_selected_path_coverage": float(covered[active].mean()) if active.any() else None,
                         "mean_selected_final_width": float(np.mean(2 * quantiles * rows.selected_mean_sd)) if np.isfinite(quantiles).all() else None,
                         "infinite_radius_refusal_n": int(np.sum(~np.isfinite(quantiles))),
                         "global_only_path_coverage": float(np.mean(rows.path_standardized_error <= calibration["global_q"])),
                         "risk_group_n": {str(g): int((groups == g).sum()) for g in (0, 1)}}
    baseline = gate["best_baseline"]
    comparisons = {}
    pairs = [("primary_net", "gated_two_stage", baseline, "net_utility"),
             ("two_stage_net", "two_stage_kg_14", baseline, "net_utility"),
             ("adaptation_same_resources", "two_stage_kg_14", "fixed_split_kg_14", "utility"),
             ("feedback", "two_stage_kg_14", "shuffled_two_stage_kg_14", "utility"),
             ("secondary_primary", "gated_two_stage", baseline, "secondary_utility"),
             ("secondary_two_stage", "two_stage_kg_14", baseline, "secondary_utility")]
    for name, a, b, metric in pairs:
        aa = replay[replay.arm == a].set_index("drug")
        bb = replay[replay.arm == b].set_index("drug").loc[aa.index]
        delta = aa[metric] - bb[metric]
        comparisons[name] = dict(R.paired_statistics(delta, aa.moa.to_numpy(), SEED), a=a, b=b, metric=metric)
        if metric.startswith("secondary"):
            both = delta.notna()
            comparisons[name]["missing_or_ineligible_n"] = int((~both).sum())
            comparisons[name]["a_selected_measured_mean"] = float(aa.loc[both, "secondary_n_selected"].mean())
            comparisons[name]["b_selected_measured_mean"] = float(bb.loc[both, "secondary_n_selected"].mean())
    primary = comparisons["primary_net"]
    secondary = comparisons["secondary_primary"]
    reliability_ok = coverage["gated_two_stage"]["selected_path_coverage"] >= 0.9 and coverage["gated_two_stage"]["active_selected_path_coverage"] >= 0.9 and coverage["gated_two_stage"]["infinite_radius_refusal_n"] == 0
    signal = primary["cluster_ci95"][0] > 0 and secondary["cluster_ci95"][0] > 0 and reliability_ok
    return {"status": "PROMISING_EXPLORATORY_SIGNAL" if signal else "NOT_SUPPORTED",
            "scope": P["scope"], "best_fit_baseline": baseline, "arms": summary,
            "reliability": coverage, "comparisons": comparisons,
            "gated_stop_fraction": float((replay[replay.arm == "gated_two_stage"].reads == 4).mean()),
            "calibration_caveat": "Old tau/sigma used all 281 development compounds. Frozen new split does not erase that exposure; intervals are empirical diagnostics and no newly independent conformal guarantee is claimed.",
            "secondary_caveat": "Scoring-only independent assay; selected-outcome missingness and different doses remain. No fresh confirmation.",
            "llm_api_calls": 0}


def analyze():
    frame = pd.read_csv(HERE / "RAW_ROWS.csv")
    gate = json.loads((HERE / "GATE_FREEZE.json").read_text())
    frame = apply_gate(frame, gate)
    reliability = calibrate_reliability(frame, gate)
    dump(HERE / "RELIABILITY.json", reliability)
    frame.to_csv(HERE / "ROWS.csv", index=False)
    result = report(frame, gate, reliability)
    dump(HERE / "RESULTS.json", result)
    with gzip.open(HERE / "LEDGER.jsonl.gz", "rt", encoding="utf-8") as stream, \
            gzip.open(HERE / "GATED_LEDGER.jsonl.gz", "wt", encoding="utf-8") as out:
        for line in stream:
            ledger = json.loads(line)
            if ledger["arm"] not in ("stop_after_4", "two_stage_kg_14"):
                continue
            row = frame[(frame.drug == ledger["drug"]) & (frame.arm == "gated_two_stage")].iloc[0]
            if row.chosen_origin != ledger["arm"]:
                continue
            ledger["arm"] = "gated_two_stage"
            ledger["stop_reason"] = row.gate_reason
            ledger["gate"] = {"group": int(row.gate_group), "lower_gain_estimate": float(row.gate_lower_estimate),
                              "incremental_cost": 12 * P["read_utility_price"],
                              "predicted_remaining_gain": float(row.predicted_remaining_gain)}
            out.write(json.dumps(ledger, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "baseline": result["best_fit_baseline"],
                      "primary": result["comparisons"]["primary_net"], "stopped": result["gated_stop_fraction"]}), flush=True)


def run():
    if (HERE / "FREEZE.json").exists():
        raise RuntimeError("RUN_ALREADY_STARTED: use a fresh output directory for a new protocol")
    C.verify_sources()
    tracked = [HERE / "study.py", HERE / "PROTOCOL.json", PRIOR / "campaign.py", PRIOR / "PROTOCOL_FREEZE.json", PRIOR / "CALIBRATION_FREEZE.json"]
    dump(HERE / "FREEZE.json", {"scope": P["scope"], "sha256": {str(p.relative_to(ROOT)): C.sha256(p) for p in tracked}})
    started = time.perf_counter()
    with threadpool_limits(limits=1):
        library, data = C.load_data()
        splits = partition(data)
        # Fit rows precede held-out calibration and replay. Freeze gate before the latter execute.
        data.sort(key=lambda d: ({"fit": 0, "calibration": 1, "exposed_replay": 2}[splits[d[0].drug]], d[0].drug))
        all_rows = []
        with gzip.open(HERE / "LEDGER.jsonl.gz", "wt", encoding="utf-8") as stream:
            for index, datum in enumerate(data):
                if splits[datum[0].drug] != "fit" and not (HERE / "GATE_FREEZE.json").exists():
                    gate = fit_gate(pd.DataFrame(all_rows))
                    gate["study_sha256"] = C.sha256(HERE / "study.py")
                    dump(HERE / "GATE_FREEZE.json", gate)
                    print("gate frozen " + json.dumps(gate["groups"]), flush=True)
                rows, ledgers = run_campaign(library, datum)
                for row in rows:
                    row["partition"] = splits[datum[0].drug]
                all_rows.extend(rows)
                for ledger in ledgers:
                    stream.write(json.dumps(ledger, allow_nan=False) + "\n")
                if index % 50 == 0:
                    print(f"replay {index}/{len(data)} seconds={time.perf_counter() - started:.1f}", flush=True)
        pd.DataFrame(all_rows).to_csv(HERE / "RAW_ROWS.csv", index=False)
        analyze()
        dump(HERE / "RECEIPT.json", {"seconds": time.perf_counter() - started, "campaigns": len(data),
                                    "rows": len(all_rows), "llm_api_calls": 0,
                                    "raw_rows_sha256": C.sha256(HERE / "RAW_ROWS.csv"),
                                    "ledger_sha256": C.sha256(HERE / "LEDGER.jsonl.gz")})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["run", "analyze"])
    args = parser.parse_args()
    if args.command == "run":
        run()
    else:
        with threadpool_limits(limits=1):
            analyze()
