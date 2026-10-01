"""Executed software swaps, frozen STATE replay, and optional real input audit.

Software terminals are constructed validator fixtures, never biology. STATE
reading accuracy and physical terminal utility are unavailable and stay unknown.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np

from tools.datasets.state_prospective_input import digest, write_json


def compare_paths(first, second):
    """Action-mediated influence is undefined when no action changes occur."""
    if set(first) != set(second) or not first:
        raise ValueError("Complete matched question sets required")
    switches, concrete, refusal, terminal, known_terminal = 0, 0, 0, 0, 0
    for key in first:
        a, b = first[key], second[key]
        changed = a["action"] != b["action"]
        switches += changed
        concrete += changed and a["action"] is not None and b["action"] is not None
        refusal += changed and (a["action"] is None or b["action"] is None)
        if changed and a.get("terminal") is not None and b.get("terminal") is not None:
            known_terminal += 1
            terminal += a["terminal"] != b["terminal"]
    return dict(questions=len(first), action_changes=switches,
                action_influence=switches / len(first), concrete_action_changes=concrete,
                abstention_changes=refusal, action_changed_with_known_terminal=known_terminal,
                terminal_changes_given_action_change=(terminal / known_terminal if known_terminal else None),
                terminal_status="undefined_without_known_matched_terminals" if not known_terminal else "scoped_to_supplied_terminals",
                terminal_utility="not_identified")


def replay_paired_grid(directory):
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    for name in ("summary.json", "freeze.json", "mean_predictions.npz"):
        if digest(directory / name) != manifest.get(name):
            raise ValueError(f"Frozen paired input changed: {name}")
    summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
    observed = {(p, s): dict(action=c["selected"], terminal=None)
                for (p, s), c in zip(summary["row_keys"], summary["choices"])}
    pools = sorted({p for p, _ in observed})
    replaced = {(p, s): observed[pools[(pools.index(p) + 1) % len(pools)], s]
                for p, s in observed}
    # Fixed-action is a predeclared technical choice, not optimal treatment.
    fixed = {key: dict(action=0, terminal=None) for key in observed}
    return dict(scope=summary["scope"], model="STATE, registered historical development checkpoint",
                true_pool_vs_cyclic_replacement=compare_paths(observed, replaced),
                predicted_selector_vs_fixed_action=compare_paths(observed, fixed),
                zero_endpoint_values=summary["endpoint_exact_zeros"],
                endpoint_values=summary["endpoint_values"],
                abstentions=sum(v["action"] is None for v in observed.values()),
                seed_averaged_choices=summary["seed_averaged_choices"],
                response_accuracy="not_measured", reading_accuracy="not_measured",
                terminal_accuracy="not_measured", terminal_utility="not_identified",
                physical_attempts=0, physical_CI="not_reported",
                limitation="pool and plate confounded; replacement is a technical intervention, not randomized biology")


def software_swaps(out):
    """Execute the actual DecisionPath using declared constructed predictions.

    Both timing arms call the same two-action forecaster exactly twice. The
    first planner receives forecasts; the late planner proposes action a before
    the forecasts exist. Global legal menu, action costs and validator are fixed.
    """
    from agent.memory import CaseStore
    from maestro.models import EvidenceAction, FunctionalInterventionProfile
    from research.astra.decision_path import Candidate, DecisionPath
    from research.astra.interface import ExecutionBinding, ScientificQuery, StateRef

    state = StateRef("1" * 64, "2" * 64, "fixture-transform", "fixture-unit", "historical")
    binding = ExecutionBinding("4" * 64, "fixture-transform", "5" * 64, 42, "fixture-runtime")
    candidates = tuple(Candidate(EvidenceAction(a, "software fixture", 1, ()),
                                ScientificQuery(state, a, "3" * 64, "fixture", "fixture", "reading", 1, "valid_readout"),
                                binding) for a in ("a", "b"))
    forecasts = {"reference": {"a": .8, "b": .2}, "swapped": {"a": .2, "b": .8},
                 "constant": {"a": .5, "b": .5}}
    # Frozen deterministic toy readings have no biological provenance.
    readings = {"a": "unresolved", "b": "confirm_fixture_h1"}
    records = []
    for forecast_name, values in forecasts.items():
        for policy in ("fixed", "aware"):
            for timing in ("late", "early"):
                events, cache = [], {}
                def generate_all():
                    if not cache:
                        for candidate in candidates:
                            action = candidate.action.identifier
                            events.append("forecast:" + action)
                            cache[action] = {"valid": True, "value": values[action],
                                             "distribution": {"confirm_fixture_h1": values[action], "unresolved": 1 - values[action]},
                                             "source": "constructed_software_forecast_not_STATE"}
                if timing == "early":
                    generate_all()
                def planner(case, profile):
                    events.append("planner")
                    if timing == "early" and policy == "aware":
                        return (max(candidates, key=lambda c: cache[c.action.identifier]["value"]),)
                    return candidates if policy == "aware" and timing == "late" else candidates[:1]
                def predictor(query, execution):
                    generate_all()
                    return cache[query.action_id]
                def selector(eligible, predictions):
                    events.append("selector")
                    return (max(eligible, key=lambda c: predictions[c.action.identifier]["value"]),) if policy == "aware" else eligible[:1]
                name = f"{forecast_name}_{policy}_{timing}"
                core = DecisionPath(CaseStore(out / "software_cases.sqlite"), planner, selector, predictor)
                result = core.run(name, FunctionalInterventionProfile("fixture", context_identifier="fixture"),
                                  budget=1, prediction_use="selection")
                action = result.actions[0].identifier if result.actions else None
                reading = readings.get(action)
                terminal = "correct_fixture" if reading == "confirm_fixture_h1" else "unresolved_fixture"
                records.append(dict(case_id=name, forecast=forecast_name, policy=policy, timing=timing,
                                    action=action, reading=reading, terminal=terminal,
                                    events=events, forecaster_calls=sum(e.startswith("forecast:") for e in events),
                                    planned_cost=sum(a.cost for a in result.actions), actual_experiment_cost=None,
                                    observed_real_experiment=False))
    indexed = {(r["forecast"], r["policy"], r["timing"]): r for r in records}
    pair = lambda a, b: compare_paths({"fixture": indexed[a]}, {"fixture": indexed[b]})
    return dict(scope="constructed software pipeline; actual DecisionPath executed; no STATE/WorldV2 efficacy",
                records=records,
                forecast_swap=pair(("reference", "aware", "late"), ("swapped", "aware", "late")),
                policy_swap=pair(("swapped", "fixed", "late"), ("swapped", "aware", "late")),
                timing_swap=pair(("swapped", "aware", "late"), ("swapped", "aware", "early")),
                response_accuracy="not_applicable", reading_accuracy="constructed_fixture_only",
                biological_gain="not_tested", terminal_utility="not_identified")


def real_input_dependencies(root, out):
    """New fixed-compute requests, never rows from real treated observations."""
    import anndata as ad
    from tools.datasets.state_prospective_input import (
        KEY, build_requests, load_contract, predict, validate_requests,
    )

    contract = load_contract(root)
    history = root / "tools/datasets/audit_results/20261001_state_response/sensitivity_v1"
    baseline = ad.read_h5ad(history / "baseline_plate1.h5ad")
    actions = [str([("Trametinib", d, "uM")]) for d in (.05, .5)]
    variants = {"base": (16, 42, 0.), "expression": (16, 42, 123.),
                "unused_metadata": (16, 42, 0.), "query_slots": (32, 42, 0.),
                "sampling_seed": (16, 17, 0.)}
    plan = dict(frozen_at_utc=datetime.now(timezone.utc).isoformat(), baseline_sha256=digest(history / "baseline_plate1.h5ad"),
                actions=actions, variants=variants, matrix_tolerance=1e-6,
                comparison="identical-input dimensions for expression/unused metadata; means descriptive for slots/seed",
                legal_metadata_mutation="explicit mismatch rejection; biological population is never required invariant",
                model_assets=contract["hashes"], source_sha256=digest(Path(__file__)),
                wrapper_sha256=digest(Path(__import__("tools.datasets.state_prospective_input", fromlist=["__file__"]).__file__)),
                physical_attempts=0, scope="historical control technical query-dependency certification")
    write_json(out / "real_input_freeze.json", plan)
    (out / "input_wrapper.py.txt").write_bytes(Path(__import__("tools.datasets.state_prospective_input", fromlist=["__file__"]).__file__).read_bytes())
    receipts, arrays, rejections = {}, {}, {}
    for name, (count, seed, placeholder) in variants.items():
        query = build_requests(baseline, actions, count, contract, placeholder)
        if name == "unused_metadata":
            query.obs["unused_query_note"] = [f"technical_note:{i}" for i in range(query.n_obs)]
        if name == "base":
            for mutation in ("mismatched_plate", "missing_queries"):
                invalid = query.copy()
                if mutation == "mismatched_plate":
                    invalid.obs.loc[invalid.obs["role"].astype(str) == "prediction_request", "plate"] = "wrong_plate"
                else:
                    invalid = invalid[invalid.obs["role"].astype(str) == "baseline_control"].copy()
                try:
                    validate_requests(invalid, actions, count, contract)
                except ValueError as exc:
                    rejections[mutation] = str(exc)
                else:
                    raise ValueError(f"Illegal input was accepted: {mutation}")
        path = out / f"{name}.h5ad"
        query.write_h5ad(path)
        receipt = predict(path, out / name, contract, actions, count, seed)
        receipts[name] = receipt
        write_json(out / "partial_real_receipts.json", receipts)
        if not receipt["valid"]:
            raise RuntimeError(f"STATE dependency request failed: {name}")
        arrays[name] = np.load(out / name / "request_predictions.npy", allow_pickle=False).reshape(len(actions), count, -1)
        print(f"real STATE input variant completed: {name}", flush=True)
    checks = {}
    for name in ("expression", "unused_metadata"):
        difference = float(np.max(np.abs(arrays[name] - arrays["base"])))
        checks[name] = dict(max_abs_difference=difference, tolerance=1e-6, passed=difference <= 1e-6)
    for name in ("query_slots", "sampling_seed"):
        difference = arrays[name].mean(axis=1) - arrays["base"].mean(axis=1)
        checks[name] = dict(mean_prediction_RMS=float(np.sqrt(np.mean(difference ** 2))),
                            expectation="sampling dependence descriptive; not an invariance requirement")
    return dict(scope=plan["scope"], checks=checks, expected_rejections=rejections,
                successful_requests=len(receipts), actual_forwards=sum(r["forward_calls"] for r in receipts.values()),
                physical_attempts=0, cost="unknown", independent_cultures="unknown",
                action_gain="not_tested", terminal_utility="not_identified", receipts=receipts)


def run(root, out, real_state=False):
    root, out = Path(root).resolve(), Path(out).resolve()
    grid = root / "research/astra/results/20261002_paired_matrix_v1"
    out.mkdir(parents=True, exist_ok=False)
    plan = dict(frozen_at_utc=datetime.now(timezone.utc).isoformat(),
                grid_inputs={name: digest(grid / name) for name in ("summary.json", "freeze.json", "mean_predictions.npz")},
                source_sha256=digest(Path(__file__)),
                software_menu=["a", "b"], forecast_variants=["reference", "swapped", "constant"],
                software_forecasts={"reference": [.8, .2], "swapped": [.2, .8], "constant": [.5, .5]},
                software_readings={"a": "unresolved", "b": "confirm_fixture_h1"},
                software_terminal_rule="confirm_fixture_h1 -> correct_fixture; otherwise unresolved_fixture",
                action_cost=1, budget=1, policies=["fixed", "aware"], timing=["late", "early"],
                real_state_requested=real_state, biological_gain="not_tested")
    write_json(out / "freeze.json", plan)
    (out / "execution_source.py.txt").write_bytes(Path(__file__).read_bytes())
    result = dict(frozen_grid=replay_paired_grid(grid), software=software_swaps(out),
                  real_STATE=real_input_dependencies(root, out) if real_state else {"status": "not_run"},
                  corrections=["CI crossing zero is insufficient evidence, not absence of oracle headroom",
                               "display/ranking/risk permissions are not measurement evidence levels"],
                  promotion=["strict declared query menu/count and finite matrix validation"],
                  scientific_vetoes=["no default risk-select promotion", "no model status changed from unknown to in-distribution",
                                     "no expression magnitude translated into causal hypothesis likelihood",
                                     "no simulated result admitted as real measurement",
                                     "no seed or cell repeat counted as physical replication"],
                  biological_state_gain="not_identified", measured_terminal_utility="not_identified")
    write_json(out / "summary.json", result)
    write_json(out / "manifest.json", {p.relative_to(out).as_posix(): digest(p) for p in out.rglob("*") if p.is_file()})
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--real-state", action="store_true")
    args = parser.parse_args()
    result = run(args.root, args.out, args.real_state)
    print(json.dumps({"out": str(args.out), "software_paths": len(result["software"]["records"]),
                      "STATE_status": result["real_STATE"].get("status", "executed")}))
