"""Freeze and execute common-policy sequential factorial; no LLM or API calls."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import time

import numpy as np

import sequential as s
from eligibility import require_dual_core_opportunity


def freeze(records, development, output):
    table = s.load_study_records(records)
    if s.r.ENDPOINT != "signed_noise_corrected_mean_squared_native_rna_delta":
        raise ValueError("raw_RMS_evaluation_not_permitted")
    evidence = json.loads((development / "summary.json").read_text())
    eligibility = require_dual_core_opportunity(table, evidence)
    if evidence["endpoint"] != s.r.ENDPOINT:
        raise ValueError("development_endpoint_mismatch")
    pairs = sorted([pair for pair in s.r.paired_doses(table) if pair[0]["split"] == "evaluation"],
                   key=lambda pair: s.r.digest({"drug": pair[0]["drug"], "salt": "sequential-four-v1"}))
    episodes = [[pair[0]["drug"] for pair in pairs[index:index + 4]] for index in range(0, len(pairs) - 3, 4)]
    protocol = {"created_unix_time": time.time(), "endpoint": s.r.ENDPOINT, "eligibility": eligibility,
        "status": "exploratory_on_previously_exposed_source", "episodes": episodes,
        "records_sha256": sha256(records.read_bytes()).hexdigest(),
        "development_sha256": sha256((development / "summary.json").read_bytes()).hexdigest(),
        "sources": {path.name: sha256(path.read_bytes()).hexdigest() for path in
                    [Path(s.__file__), Path(__file__)]},
        "legacy_receipt_sha256": sha256(s.LEGACY.read_bytes()).hexdigest(),
        "worlds": ["reference", "state"], "common_policies": ["myopic", "lookahead"],
        "no_update": "score initial chosen candidate postdecision; no simulated acquisition changes permitted",
        "budget": {"screens_max": 2, "validation_reveals": 1, "replay_access_units": 3,
                   "API_calls": 0, "laboratory_credits": 0},
        "deadline_seconds_per_episode": 2.0,
        "compute": "same exact24training empirical update support and allowance; lookahead spends more enumerations, recorded separately",
        "primary_decision_metric": "mean selected signed_noise_corrected_squared_response, descriptive3episode result",
        "interaction": "(lookahead_state-lookahead_reference)-(myopic_state-myopic_reference)",
        "scientific_hypothesis": "two-step planning changes useful acquisitions under fixed information/budget/deadline",
        "uncertainty": "no significance or population biological interval from three menus/one cell source",
        "dependence": "independent residual marginals planning approximation, not identified crossdrug biology",
        "limitations": ["original evaluation chemistry and full RNA source previously exposed",
                        "screen/validation disjoint cells share culture and reference controls",
                        "signed moment correction assumptions may fail with correlated cells",
                        "selected endpoint conditional on QC-valid source observations"]}
    if output.exists():
        raise FileExistsError("preserve_previous_run")
    output.mkdir(parents=True)
    encoded = json.dumps(protocol, indent=2).encode()
    (output / "PROTOCOL.json").write_bytes(encoded)
    (output / "FREEZE.json").write_text(json.dumps({"protocol_sha256": sha256(encoded).hexdigest(),
        "before_current_action_evaluation": True}, indent=2))
    return protocol


def evaluate(records, output):
    encoded = (output / "PROTOCOL.json").read_bytes()
    protocol = json.loads(encoded)
    if protocol.get("eligibility", {}).get("eligible") is not True:
        raise ValueError("evaluation_requires_positive_frozen_eligibility_receipt")
    assert sha256(encoded).hexdigest() == json.loads((output / "FREEZE.json").read_text())["protocol_sha256"]
    assert sha256(records.read_bytes()).hexdigest() == protocol["records_sha256"]
    assert sha256(s.LEGACY.read_bytes()).hexdigest() == protocol["legacy_receipt_sha256"]
    for name, expected in protocol["sources"].items():
        assert sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() == expected
    if (output / "episodes.json").exists():
        raise FileExistsError("preserve_finished_evaluation")
    pairs = s.r.paired_doses(s.load_study_records(records))
    available = {pair[0]["drug"]: pair for pair in pairs if pair[0]["split"] == "evaluation"}
    rows = []
    for index, drugs in enumerate(protocol["episodes"]):
        candidates = tuple(available[drug] for drug in drugs)
        for world in protocol["worlds"]:
            transfer = s.r.fit_transfer(pairs, world)
            for policy in protocol["common_policies"]:
                row = s.episode(candidates, world, transfer, output / "cases", f"eval-{index}-{world}-{policy}", policy)
                row["episode"] = index
                row["deadline_compliant"] = row["elapsed_seconds"] <= protocol["deadline_seconds_per_episode"]
                rows.append(row)
    means = {world: {policy: float(np.mean([row["selected_value"] for row in rows if row["world"] == world and row["policy"] == policy]))
                    for policy in protocol["common_policies"]} for world in protocol["worlds"]}
    summary = {"status": "descriptive_only", "mean_selected_value": means,
        "interaction": means["state"]["lookahead"] - means["reference"]["lookahead"] - means["state"]["myopic"] + means["reference"]["myopic"],
        "no_update_mean": {world: float(np.mean([row["no_update_value_postdecision"] for row in rows if row["world"] == world])) for world in protocol["worlds"]},
        "planning_resources": {policy: {"seconds": sum(step["planning"].get("planning_seconds", 0) for row in rows if row["policy"] == policy for step in row["steps"]),
            "action_integrals": sum(step["planning"].get("compute_counts", {}).get("action_integrals", 0) for row in rows if row["policy"] == policy for step in row["steps"]),
            "empirical_outcomes": sum(step["planning"].get("compute_counts", {}).get("empirical_outcomes", 0) for row in rows if row["policy"] == policy for step in row["steps"])} for policy in protocol["common_policies"]},
        "resources": {"replay_units": sum(row["budget"]["recorded_use"] for row in rows),
            "episode_seconds": sum(row["elapsed_seconds"] for row in rows),
            "deadline_failures": sum(not row["deadline_compliant"] for row in rows),
            "API_calls": 0, "tokens": 0, "financial_cost": 0, "downloaded_bytes": 0, "laboratory_credits": 0}}
    (output / "episodes.json").write_text(json.dumps(rows, indent=2))
    (output / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["freeze", "evaluate"])
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--development", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(freeze(args.records, args.development, args.output) if args.mode == "freeze"
                     else evaluate(args.records, args.output), indent=2))
