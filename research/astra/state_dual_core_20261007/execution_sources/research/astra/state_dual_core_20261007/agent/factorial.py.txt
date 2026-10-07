"""Frozen, bounded secondary factorial: six disjoint held-out drug comparisons."""
from __future__ import annotations

import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import time

import numpy as np

from agent.llm import DeepSeekChatClient, MAESTROSettings
from replay import (digest, fit_transfer, LLMAcquisitionPolicy, load_records, paired_doses,
                    replay_pair, sensitivity_choice, empirical_value_choice)


def freeze(records_path, opportunity_path, output, minimum_meaningful_improvement, empirical_opportunity_path=None):
    records = load_records(records_path)
    opportunity = json.loads(opportunity_path.read_text(encoding="utf-8"))
    if opportunity["partition"] != "development_only":
        raise ValueError("opportunity_must_use_development_only")
    ceilings = [entry["maximum_mean_acquisition_gain_diagnostic"] for entry in opportunity["results"].values()]
    if not any(value is not None and value > 0 for value in ceilings):
        raise ValueError("no_demonstrated_acquisition_opportunity")
    selection = {world: "sensitivity" for world in ("reference", "state")}
    policy_options = {world: {"sensitivity": opportunity["results"][world]["mean_gain"], "stop": 0.0}
                      for world in selection}
    if empirical_opportunity_path:
        empirical = json.loads(empirical_opportunity_path.read_text())
        for world in selection:
            policy_options[world]["empirical_value"] = empirical["results"][world]["mean_gain"]
    for world, options in policy_options.items():
        selection[world] = max(options, key=options.get)
    evaluation = sorted((pair for pair in paired_doses(records) if pair[0]["split"] == "evaluation"),
                        key=lambda pair: digest({"drug": pair[0]["drug"], "salt": "native-rna-pairs-v1"}))
    if len(evaluation) < 4:
        raise ValueError("insufficient_evaluation_drugs")
    pairs = [[evaluation[index][0]["drug"], evaluation[index + 1][0]["drug"]]
             for index in range(0, len(evaluation) - 1, 2)][:6]
    protocol = {"version": "native_rna_factorial_v1", "status": "secondary_exploratory",
        "observation_task": "technical_screen_to_disjoint_cell_validation" if "response_role" in records else "cross_dose_reference",
        "prior_evaluation_exposure": "root H1 full-pseudobulk metrics already computed; technical validation choices not consulted for policy selection; exploratory",
        "records_sha256": sha256(records_path.read_bytes()).hexdigest(),
        "code_sha256": {name: sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                        for name in ("replay.py", "factorial.py")},
        "opportunity_sha256": sha256(opportunity_path.read_bytes()).hexdigest(),
        "pairs": pairs, "primary_decision_endpoint": "mean observed selected top-dose native RNA delta RMS",
        "minimum_meaningful_improvement": float(minimum_meaningful_improvement),
        "minimum_improvement_basis": "larger of both worlds median absolute development technical-transfer residual",
        "deterministic_policy_development_options": policy_options,
        "deterministic_policy_by_world": selection,
        "arms": {"A": ["reference", "deterministic"], "B": ["state", "deterministic"],
                 "C": ["reference", "LLM"], "D": ["state", "LLM"]},
        "information_access": "identical forecasts and train residual uncertainty within each world column",
        "cost": {"replay_access_units": 2, "max_screen_or_reference_acquisitions": 1, "validation_reveals": 1,
                 "laboratory_credits": 0, "max_API_calls_total": 12, "API_max_output_tokens_per_call": 350},
        "deadline_seconds_per_episode": 120, "deadline_failure": "count failure; selected utility zero if deadline exceeded",
        "failed_API": "log failure and use registered deterministic acquisition fallback",
        "final_selection": "maximum permitted updated forecast; stable condition-ID tie break",
        "interaction_scale": "raw RNA RMS: (D-C)-(B-A)",
        "interval": "bootstrap disjoint drug-pair comparison units 10000 times, seed 719; conditional on one cell/source",
        "same_information_control": "rerun deterministic final rule using each LLM acquired source; must exactly match final choice",
        "limitations": ["one historical previously exposed cell", "unknown checkpoint pretraining overlap",
                        "dose and source-plate confounding in cross-dose arm; shared control denominator in technical screen",
                        "disjoint technical cells are not independent culture confirmation",
                        "no ATP or viability", "small six-pair secondary study"]}
    output.mkdir(parents=True, exist_ok=True)
    target = output / "FACTORIAL_PROTOCOL.json"
    if target.exists():
        raise FileExistsError("frozen_protocol_exists")
    encoded = json.dumps(protocol, indent=2, sort_keys=True).encode()
    target.write_bytes(encoded)
    (output / "FACTORIAL_FREEZE.json").write_text(json.dumps({"protocol_sha256": sha256(encoded).hexdigest(),
        "created_unix_time": time.time(), "before_evaluation": True}, indent=2), encoding="utf-8")
    return protocol


def evaluate(records_path, output, workspace):
    if (output / "factorial_actions.jsonl").exists():
        raise FileExistsError("preserve_existing_evaluation; use a separate reproduction directory")
    encoded = (output / "FACTORIAL_PROTOCOL.json").read_bytes()
    protocol = json.loads(encoded)
    receipt = json.loads((output / "FACTORIAL_FREEZE.json").read_text())
    if sha256(encoded).hexdigest() != receipt["protocol_sha256"]:
        raise ValueError("protocol_changed")
    if sha256(records_path.read_bytes()).hexdigest() != protocol["records_sha256"]:
        raise ValueError("records_changed")
    for name, expected in protocol["code_sha256"].items():
        if sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() != expected:
            raise ValueError("code_changed_since_freeze")
    records = load_records(records_path)
    all_pairs = paired_doses(records)
    by_drug = {pair[0]["drug"]: pair for pair in all_pairs if pair[0]["split"] == "evaluation"}
    settings = replace(MAESTROSettings.from_workspace(workspace), timeout_seconds=20, max_tokens=350,
                       log_directory=output / "api")
    client = DeepSeekChatClient(settings)
    agent = LLMAcquisitionPolicy(client)
    results = []
    for episode, drugs in enumerate(protocol["pairs"]):
        pair = tuple(by_drug[drug] for drug in drugs)
        for arm, (world, policy_name) in protocol["arms"].items():
            started = time.perf_counter()
            transfer = fit_transfer(all_pairs, world)
            deterministic = {"sensitivity": sensitivity_choice, "empirical_value": empirical_value_choice,
                             "stop": lambda view: None}[protocol["deterministic_policy_by_world"][world]]
            policy = agent if policy_name == "LLM" else deterministic
            result = replay_pair(pair, world, transfer, output / "runs", f"evaluation-{episode}-{arm}", policy)
            result.update(arm=arm, episode=episode, elapsed_seconds=time.perf_counter() - started)
            result["deadline_compliant"] = result["elapsed_seconds"] <= protocol["deadline_seconds_per_episode"]
            result["decision_utility"] = result["observed_selected_rms"] if result["deadline_compliant"] else 0.0
            if policy_name == "LLM":
                # No second API call: hold acquired information identical and check usage.
                shared_started = time.perf_counter()
                sources = [action["condition_id"] for action in result["actions"] if action["kind"] == "acquire"]
                shared = replay_pair(pair, world, transfer, output / "shared_information",
                    f"same-information-{episode}-{arm}", (lambda view: None) if not sources else sensitivity_choice,
                    shared_acquisitions=sources)
                result["same_information_final_choice"] = shared["final_choice"]
                result["same_information_equal"] = shared["final_choice"] == result["final_choice"]
                result["same_information_replay_access_units"] = shared["budget"]["recorded_use"]
                result["same_information_elapsed_seconds"] = time.perf_counter() - shared_started
                result["api_receipt"] = agent.receipts[-1]
            results.append(result)
            with (output / "factorial_actions.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(result) + "\n")
    values = np.array([[next(row["decision_utility"] for row in results
                            if row["episode"] == episode and row["arm"] == arm)
                        for arm in "ABCD"] for episode in range(len(protocol["pairs"]))])
    contrast = values[:, 3] - values[:, 2] - values[:, 1] + values[:, 0]
    rng = np.random.default_rng(719)
    boot = contrast[rng.integers(0, len(contrast), size=(10000, len(contrast)))].mean(axis=1)
    summary = {"status": "secondary_exploratory", "disjoint_drug_pair_units": len(contrast),
        "biological_cell_contexts": 1, "arms": {arm: {"mean_selected_rms": float(values[:, index].mean()),
            "changed_choices": sum(row["changed"] for row in results if row["arm"] == arm),
            "replay_access_units": sum(row["budget"]["recorded_use"] for row in results if row["arm"] == arm),
            "deadline_failures": sum(not row["deadline_compliant"] for row in results if row["arm"] == arm)} for index, arm in enumerate("ABCD")},
        "interaction": {"estimate": float(contrast.mean()), "bootstrap_95_interval": np.quantile(boot, [.025, .975]).tolist(),
            "scale": protocol["interaction_scale"]},
        "world_effect_under_deterministic": float((values[:, 1] - values[:, 0]).mean()),
        "agent_effect_reference": float((values[:, 2] - values[:, 0]).mean()),
        "agent_effect_state": float((values[:, 3] - values[:, 1]).mean()),
        "same_information_all_equal": all(row.get("same_information_equal", True) for row in results),
        "no_update_offline_postdecision": {arm: float(np.mean([row["initial_selected_rms_for_posthoc_scoring_only"]
            for row in results if row["arm"] == arm])) for arm in "ABCD"},
        "provider_usage": client.provider_usage, "API_actual_billed_cost": None,
        "API_cost_status": "unknown: provider returned token counts but no invoice amount",
        "laboratory_credits": 0, "downloaded_bytes": 0,
        "local_elapsed_seconds": sum(row["elapsed_seconds"] for row in results),
        "auxiliary_same_information_replay_access_units": sum(row.get("same_information_replay_access_units", 0) for row in results),
        "auxiliary_same_information_elapsed_seconds": sum(row.get("same_information_elapsed_seconds", 0) for row in results),
        "minimum_meaningful_improvement": protocol["minimum_meaningful_improvement"]}
    (output / "factorial_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["freeze", "evaluate"])
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--opportunity", type=Path)
    parser.add_argument("--minimum-improvement", type=float)
    parser.add_argument("--empirical-opportunity", type=Path)
    parser.add_argument("--workspace", type=Path, default=Path(__file__).resolve().parents[4])
    args = parser.parse_args()
    answer = freeze(args.records, args.opportunity, args.output, args.minimum_improvement, args.empirical_opportunity) if args.mode == "freeze" else evaluate(args.records, args.output, args.workspace)
    print(json.dumps(answer, indent=2))
