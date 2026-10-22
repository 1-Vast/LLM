"""Bounded, sealed ordinary-model experiment; all artifacts stay in log/."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
from time import perf_counter
import traceback

import numpy as np
from threadpoolctl import threadpool_limits

from models import GRIDS, fit_model
from metrics import make_actions, score, paired_bootstrap
from prepare import LOG, sha, write

BASES = ("effect", "dose", "direct", "combo_direct")
VARIANTS = BASES + ("effect_offset", "dose_offset", "direct_offset")
ORDINARY = ("bliss", "historical", "dose", "combo_direct", "direct", "dose_offset", "direct_offset")
ETAS = (0., .25, .5, .75, 1.)
ENDPOINTS = ("mae", "utility")


def verify_freeze(log):
    freeze = json.loads((log / "PRE_RESPONSE_FREEZE.json").read_text(encoding="utf-8"))
    root = Path(__file__).resolve().parents[2]
    for name, expected in freeze["files"].items():
        if sha(root / name) != expected:
            raise ValueError(f"Pre-response freeze changed: {name}")


def load(log):
    with np.load(log / "DATA.npz", allow_pickle=False) as z:
        data = {k: z[k] for k in z.files}
    if not np.isnan(data["y"][data["role"] == "test"]).all():
        raise ValueError("Test labels present in input artifact")
    meta = json.loads((log / "EPISODE_META.json").read_text(encoding="utf-8"))
    summaries = json.loads((log / "PAID_SUMMARIES.json").read_text(encoding="utf-8"))
    design = json.loads((log / "DESIGN.json").read_text(encoding="utf-8"))
    if list(range(len(meta))) != [e["episode_id"] for e in meta]:
        raise ValueError("Episode metadata is not in its frozen index order")
    cells = np.array([e["cell"] for e in meta])[data["episode"]]
    for role in ("train", "validation", "test"):
        if set(cells[data["role"] == role]) != set(design["role_cells"][role]):
            raise ValueError("Assigned source-model population changed")
    if len(np.unique(data["episode"])) != len(meta):
        raise ValueError("A nominal episode has no rows")
    return data, meta, summaries, cells


def offset_values(meta, summaries, reference_roles):
    """One mean per unique paid matrix, rather than repeated episode purchases."""
    groups, seen = defaultdict(list), set()
    for s in summaries:
        key = tuple(s["key"])
        if key in seen:
            raise ValueError("Duplicate paid summary")
        seen.add(key)
        if s["role"] in reference_roles and s["mean_residual"] is not None:
            groups[tuple(s["pair"])].append(s["mean_residual"])
    means = {p: float(np.mean(v)) for p, v in groups.items()}
    values = np.full(len(meta), np.nan)
    missing = []
    for e in meta:
        if not e["valid"]:
            continue
        deviations = []
        for p, value in zip(e["query_pairs"], e["query_residual_means"]):
            p = tuple(p)
            if value is None:
                raise ValueError("Valid episode lacks paid residual")
            deviations.append(value - means.get(p, 0.))
            if p not in means:
                missing.append([e["episode_id"], list(p)])
        values[e["episode_id"]] = np.mean(deviations)
    return values, {"pair_means": {"|".join(p): v for p, v in means.items()},
                    "missing_historical_query_pairs": missing,
                    "unique_reference_matrices": sum(map(len, groups.values()))}


def historical(data, train, predict):
    groups = defaultdict(list)
    for i in np.flatnonzero(train & np.isfinite(data["y"])):
        groups[(int(data["pair"][i]), *data["dose"][i])].append(data["y"][i])
    by_pair = defaultdict(list)
    for (p, a, b), values in sorted(groups.items()):
        by_pair[p].append((a, b, float(np.mean(values))))
    global_mean = float(np.mean(data["y"][train & np.isfinite(data["y"])]))
    out = np.full(len(train), np.nan)
    for i in np.flatnonzero(predict):
        options = by_pair.get(int(data["pair"][i]), [])
        if options:
            a, b = data["dose"][i]
            chosen = min(options, key=lambda x: ((x[0]-a)**2 + (x[1]-b)**2, x[0], x[1]))
            out[i] = chosen[2]
        else:
            out[i] = global_mean
    return out


def role_score(data, cells, prediction, role, y=None, global_actions=None):
    idx = np.flatnonzero(data["role"] == role)
    actions = None
    if global_actions is not None:
        inverse = {int(g): i for i, g in enumerate(idx)}
        actions = {int(e): [inverse[int(g)] for g in v] for e, v in global_actions.items()}
    return score(data["y"][idx] if y is None else y[idx], prediction[idx],
                 data["episode"][idx], cells[idx], data["effect"][idx], data["valid_mask"][idx],
                 assigned_masters=sorted(set(cells[idx])), nominal_actions=actions)


def nominal_actions(data, prediction, role):
    idx = np.flatnonzero(data["role"] == role)
    local = make_actions(prediction[idx], data["effect"][idx], data["episode"][idx], data["valid_mask"][idx])
    return {str(e): [int(idx[i]) for i in values] for e, values in local.items()}


def metric(result, endpoint):
    return result["forecast"]["mae"] if endpoint == "mae" else result["recommendation"][endpoint]


def best(candidates, endpoint):
    # Stable candidate order breaks exact ties.
    return min(candidates, key=lambda x: metric(x["metrics"], endpoint) * (1 if endpoint == "mae" else -1))


def append(log, name, value):
    with (log / name).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, allow_nan=False) + "\n")


def fit_stage(log):
    stage_started = perf_counter()
    verify_freeze(log)
    marker = log / "FITS_STARTED.json"
    if marker.exists():
        raise RuntimeError("Fit stage already started; no retry")
    write(marker, {"code_sha256": sha(Path(__file__)), "input_sha256": sha(log / "DATA.npz")})
    data, meta, summaries, cells = load(log)
    write(log / "TRAIN_VALIDATION_MISSINGNESS.json", missingness(data, meta, data["y"], {"train", "validation"}))
    train = (data["role"] == "train") & data["valid_mask"]
    val = (data["role"] == "validation") & data["valid_mask"]
    test = (data["role"] == "test") & data["valid_mask"]
    anchor = data["effect"].sum(axis=1) - data["effect"].prod(axis=1)
    for role in ("train", "validation"):
        qualification = role_score(data, cells, anchor, role)
        write(log / f"{role.upper()}_QUALIFICATION.json", qualification)
        if not qualification["coverage_pass"]:
            write(log / "PRE_FIT_STOP.json", {"reason": "coverage", "role": role})
            return
    test_meta = [e for e in meta if e["role"] == "test"]
    if (np.mean([e["valid"] for e in test_meta]) < .95 or
            any(not any(e["valid"] for e in test_meta if e["cell"] == c) for c in set(cells[data["role"] == "test"]))):
        write(log / "PRE_FIT_STOP.json", {"reason": "test_input_coverage"})
        return
    offsets, offset_audit = offset_values(meta, summaries, {"train"})
    row_offsets = offsets[data["episode"]]
    write(log / "VALIDATION_OFFSET_AUDIT.json", offset_audit)
    candidates = {v: [] for v in VARIANTS}
    validation_predictions = {}
    total_pipelines = 0
    for arm in BASES:
        for ci, config in enumerate(GRIDS[arm]):
            started = perf_counter()
            with threadpool_limits(limits=2):
                model = fit_model(arm, config, data, train)
                pred = np.full(len(train), np.nan)
                pred[val] = model.predict(data, val)
            total_pipelines += 1
            validation_predictions[f"{arm}_{ci}"] = pred
            rec = {"phase": "selection", "arm": arm, "config_index": ci, "config": config,
                   "pipeline": total_pipelines, "fit_seconds": model.fit_seconds,
                   "solver_fits": model.solver_fits, "total_seconds": perf_counter()-started}
            append(log, "FIT_RUNS.jsonl", rec)
            for variant in (arm, arm + "_offset") if arm != "combo_direct" else (arm,):
                for eta in ETAS if variant.endswith("_offset") else (0.,):
                    p = pred.copy()
                    p[val] += eta * row_offsets[val]
                    result = role_score(data, cells, p, "validation")
                    candidates[variant].append({"base": arm, "config_index": ci, "eta": eta, "metrics": result})
            print(json.dumps(rec), flush=True)
            del model
    np.savez_compressed(log / "VALIDATION_PREDICTIONS.npz", **validation_predictions)
    selected = {ep: {v: best(candidates[v], ep) for v in VARIANTS} for ep in ENDPOINTS}
    history_val = historical(data, train, val)
    common = {"bliss": anchor, "historical": history_val}
    endpoint_val, selection = {}, {"policies": selected, "mixture": {}, "enumerator": {}, "ordinary": {}}
    for endpoint in ENDPOINTS:
        policies = dict(common)
        for v, choice in selected[endpoint].items():
            p = validation_predictions[f"{choice['base']}_{choice['config_index']}"].copy()
            p[val] += choice["eta"] * row_offsets[val]
            policies[v] = p
        mixtures = []
        for w in ETAS:
            p = w * policies["effect"] + (1-w) * policies["direct_offset"]
            mixtures.append({"weight": w, "metrics": role_score(data, cells, p, "validation")})
        chosen = best(mixtures, endpoint)
        selection["mixture"][endpoint] = chosen
        w = chosen["weight"]
        policies["mixture"] = w * policies["effect"] + (1-w) * policies["direct_offset"]
        results = {v: role_score(data, cells, p, "validation") for v, p in policies.items()}
        selection["ordinary"][endpoint] = best([{"arm": v, "metrics": results[v]} for v in ORDINARY], endpoint)
        selection["enumerator"][endpoint] = best([{"arm": v, "metrics": r} for v, r in results.items()], endpoint)
        endpoint_val[endpoint] = results
    write(log / "VALIDATION_TRIALS.json", candidates)
    write(log / "VALIDATION_SELECTED_METRICS.json", endpoint_val)
    write(log / "SELECTION.json", selection)
    final_offsets, final_offset_audit = offset_values(meta, summaries, {"train", "validation"})
    final_row_offsets = final_offsets[data["episode"]]
    write(log / "FINAL_OFFSET_AUDIT.json", final_offset_audit)
    final_predictions = {}
    unique = sorted({(c["base"], c["config_index"]) for values in selected.values() for c in values.values()})
    if len(unique) > 14:
        raise AssertionError("Final refit budget exceeded")
    for arm, ci in unique:
        started = perf_counter()
        with threadpool_limits(limits=2):
            model = fit_model(arm, GRIDS[arm][ci], data, train | val)
            pred = np.full(len(train), np.nan)
            pred[test] = model.predict(data, test)
        total_pipelines += 1
        final_predictions[(arm, ci)] = pred
        rec = {"phase": "final", "arm": arm, "config_index": ci, "pipeline": total_pipelines,
               "fit_seconds": model.fit_seconds, "solver_fits": model.solver_fits,
               "total_seconds": perf_counter()-started}
        append(log, "FIT_RUNS.jsonl", rec)
        print(json.dumps(rec), flush=True)
        del model
    outputs, actions = {}, {}
    historical_final = historical(data, train | val, test)
    for endpoint in ENDPOINTS:
        policies = {"bliss": anchor.copy(), "historical": historical_final.copy()}
        for v, choice in selected[endpoint].items():
            p = final_predictions[(choice["base"], choice["config_index"])].copy()
            p[test] += choice["eta"] * final_row_offsets[test]
            policies[v] = p
        w = selection["mixture"][endpoint]["weight"]
        policies["mixture"] = w * policies["effect"] + (1-w) * policies["direct_offset"]
        policies["enumerator"] = policies[selection["enumerator"][endpoint]["arm"]].copy()
        for v, pred in policies.items():
            pred[~test] = np.nan
            name = f"{v}__{endpoint}"
            outputs[name] = pred
            actions[name] = nominal_actions(data, pred, "test")
    np.savez_compressed(log / "TEST_PREDICTIONS.npz", **outputs)
    write(log / "TEST_ACTIONS.json", actions)
    write(log / "PREDICTIONS_SEAL.json", {"predictions_sha256": sha(log / "TEST_PREDICTIONS.npz"),
          "actions_sha256": sha(log / "TEST_ACTIONS.json"), "selection_sha256": sha(log / "SELECTION.json"),
          "pipeline_fits": total_pipelines, "selection_fits": 48, "unique_final_fits": len(unique),
          "fit_stage_elapsed_seconds": perf_counter()-stage_started})


def evaluate_stage(log):
    stage_started = perf_counter()
    verify_freeze(log)
    if (log / "EVALUATION_STARTED.json").exists():
        raise RuntimeError("Evaluation already started")
    seal = json.loads((log / "PREDICTIONS_SEAL.json").read_text(encoding="utf-8"))
    for name, field in (("TEST_PREDICTIONS.npz", "predictions_sha256"), ("TEST_ACTIONS.json", "actions_sha256"), ("SELECTION.json", "selection_sha256")):
        if sha(log / name) != seal[field]:
            raise ValueError("Sealed predictions/actions/selection changed")
    write(log / "EVALUATION_STARTED.json", {"test_targets_sha256": sha(log / "TEST_TARGETS.npz")})
    data, meta, summaries, cells = load(log)
    with np.load(log / "TEST_TARGETS.npz", allow_pickle=False) as z:
        y = z["y"]
    write(log / "TEST_MISSINGNESS.json", missingness(data, meta, y, {"test"}))
    actions = json.loads((log / "TEST_ACTIONS.json").read_text(encoding="utf-8"))
    selection = json.loads((log / "SELECTION.json").read_text(encoding="utf-8"))
    results = {}
    predictions = {}
    with np.load(log / "TEST_PREDICTIONS.npz", allow_pickle=False) as z:
        for name in z.files:
            predictions[name] = z[name]
            results[name] = role_score(data, cells, z[name], "test", y=y, global_actions=actions[name])
    write(log / "TEST_METRICS.json", results)
    coverage = all(r["coverage_pass"] for r in results.values())
    comparisons, gates = {}, {"coverage": coverage}
    for endpoint in ENDPOINTS:
        baseline = selection["ordinary"][endpoint]["arm"]
        c, b = results[f"effect__{endpoint}"], results[f"{baseline}__{endpoint}"]
        if not coverage:
            gates[endpoint] = False
            continue
        boot = paired_bootstrap(c["per_master"][endpoint], b["per_master"][endpoint], higher_is_better=endpoint == "utility")
        gain = metric(b, endpoint)-metric(c, endpoint) if endpoint == "mae" else metric(c, endpoint)-metric(b, endpoint)
        headroom = metric(b, "mae") if endpoint == "mae" else metric(b, "regret")
        # The .02 absolute U gain must also reduce registered comparator regret by 10%.
        gates[endpoint] = endpoint_gate(endpoint, gain, headroom, boot["lower"], coverage)
        comparisons[endpoint] = {"ordinary": baseline, "candidate": "effect", "gain": gain,
                                 "baseline_headroom": headroom, "bootstrap": boot}
    gates["both"] = bool(coverage and all(gates.get(ep, False) for ep in ENDPOINTS))
    write(log / "GATES.json", {"gates": gates, "comparisons": comparisons,
          "interpretation": "ordinary source-specific family gate; no new algorithm, agent or RSI claim"})
    paired = {}
    if coverage:
        for endpoint in ENDPOINTS:
            candidate = results[f"effect__{endpoint}"]["per_master"][endpoint]
            for name, result in results.items():
                if name.endswith("__" + endpoint):
                    paired[f"effect_vs_{name}"] = paired_bootstrap(candidate, result["per_master"][endpoint], higher_is_better=endpoint == "utility")
            paired[f"direct_vs_combo_direct__{endpoint}"] = paired_bootstrap(
                results[f"direct__{endpoint}"]["per_master"][endpoint],
                results[f"combo_direct__{endpoint}"]["per_master"][endpoint], higher_is_better=endpoint == "utility")
    write(log / "ALL_PAIRED_COMPARISONS.json", {"comparisons": paired,
          "interpretation": "registered attribution and descriptive secondary comparisons; no multiplicity-adjusted discovery claims"})
    write(log / "SUPPORT_PLATEAU_DIAGNOSTICS.json", diagnostics(data, y, predictions))
    fit_runs = [json.loads(line) for line in (log / "FIT_RUNS.jsonl").read_text().splitlines()]
    write(log / "COSTS.json", {"pipeline_fits": len(fit_runs),
          "solver_estimator_fits": sum(r["solver_fits"] for r in fit_runs),
          "fit_seconds": sum(r["fit_seconds"] for r in fit_runs),
          "fit_plus_prediction_seconds": sum(r["total_seconds"] for r in fit_runs),
          "logical_bundles": sum(e["logical_bundles"] for e in meta),
          "logical_paid_rows": sum(e["logical_paid_rows"] for e in meta),
          "logical_paid_response_fields": 3*sum(e["logical_paid_rows"] for e in meta),
          "unique_paid_matrices": len(summaries), "unique_paid_rows": sum(s["rows"] for s in summaries),
          "physical_conversion_receipt": "ACCESS_INPUTS.json", "episode_updates": 0,
          "fit_stage_elapsed_seconds": seal["fit_stage_elapsed_seconds"],
          "evaluation_elapsed_seconds": perf_counter()-stage_started,
          "biological_independence_claim": False})
    print(json.dumps({"gates": gates, "comparisons": comparisons}), flush=True)


def endpoint_gate(endpoint, gain, headroom, lower, coverage):
    return bool(coverage and gain >= .02 and headroom > (0 if endpoint == "mae" else .02)
                and gain >= .1*headroom and lower > 0)


def diagnostics(data, y, predictions):
    train = (data["role"] != "test") & data["valid_mask"] & np.isfinite(data["y"])
    test = (data["role"] == "test") & data["valid_mask"] & np.isfinite(y)
    inside = np.zeros(len(y), bool)
    missing_pairs = []
    for p in np.unique(data["pair"][test]):
        reference = train & (data["pair"] == p)
        selected = test & (data["pair"] == p)
        if not reference.any():
            missing_pairs.append(int(p))
            continue
        lo, hi = data["effect"][reference].min(axis=0), data["effect"][reference].max(axis=0)
        inside[selected] = ((data["effect"][selected] >= lo) & (data["effect"][selected] <= hi)).all(axis=1)
    support = {}
    for name, mask in (("inside", test & inside), ("outside", test & ~inside)):
        support[name] = {"rows": int(mask.sum()), "row_mean_mae": {
            arm: float(np.abs(pred[mask]-y[mask]).mean()) if mask.any() else None
            for arm, pred in predictions.items() if arm.endswith("__mae")}}
    plateau = []
    nominal_test = (data["role"] == "test") & data["valid_mask"]
    for eid in np.unique(data["episode"][nominal_test]):
        idx = np.flatnonzero(nominal_test & (data["episode"] == eid))
        uv, logdose = data["effect"][idx], np.log10(data["raw_dose"][idx])
        select = np.triu(np.max(np.abs(uv[:, None]-uv[None, :]), axis=2) <= .02, 1)
        select &= np.max(np.abs(logdose[:, None]-logdose[None, :]), axis=2) >= 1.
        a, b = np.where(select)
        if len(a):
            finite_pair = np.isfinite(y[idx[a]]) & np.isfinite(y[idx[b]])
            gap = np.abs(y[idx[a[finite_pair]]]-y[idx[b[finite_pair]]])
            plateau.append({"episode_id": int(eid), "pairs": len(a),
                            "finite_response_pairs": int(finite_pair.sum()),
                            "missing_response_pairs": int((~finite_pair).sum()),
                            "mean_absolute_response_gap": float(gap.mean()) if len(gap) else None,
                            "max_absolute_response_gap": float(gap.max()) if len(gap) else None})
    return {"support": support, "pairs_absent_from_training": missing_pairs, "plateau": plateau,
            "plateau_pair_count": sum(e["pairs"] for e in plateau),
            "interpretation": "descriptive row/pair summaries with overlapping correlated points; no new panel or universal impossibility claim"}


def missingness(data, meta, y, roles):
    output = []
    for e in meta:
        if e["role"] not in roles:
            continue
        idx = data["episode"] == e["episode_id"]
        finite = np.isfinite(y[idx])
        output.append({"episode_id": e["episode_id"], "cell": e["cell"], "role": e["role"],
                       "pair": e["pair"], "input_valid": e["valid"], "input_reason": e["abstain_reason"],
                       "rows": int(idx.sum()), "finite_targets": int(finite.sum()),
                       "forecast_scorable": bool(e["valid"] and finite.sum() >= 5),
                       "utility_scorable": bool(e["valid"] and finite.all())})
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("fit", "evaluate"))
    parser.add_argument("--log-dir", type=Path, default=LOG)
    args = parser.parse_args()
    try:
        (fit_stage if args.stage == "fit" else evaluate_stage)(args.log_dir)
    except Exception:
        append(args.log_dir, "DRIVER_FAILURES.jsonl", {"stage": args.stage, "traceback": traceback.format_exc()})
        raise
