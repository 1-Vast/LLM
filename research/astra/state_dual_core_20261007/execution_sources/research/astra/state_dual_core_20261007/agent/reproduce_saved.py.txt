"""Recompute frozen factorial choices with saved API decisions; never call a provider."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from replay import load_records, paired_doses, fit_transfer, replay_pair, sensitivity_choice, empirical_value_choice


def run(source, output):
    protocol = json.loads((source / "FACTORIAL_PROTOCOL.json").read_text())
    freeze = json.loads((source / "FACTORIAL_FREEZE.json").read_text())
    assert sha256((source / "FACTORIAL_PROTOCOL.json").read_bytes()).hexdigest() == freeze["protocol_sha256"]
    records = source.parent / "technical_screen_bound_records.csv"
    assert sha256(records.read_bytes()).hexdigest() == protocol["records_sha256"]
    pairs = paired_doses(load_records(records))
    lookup = {pair[0]["drug"]: pair for pair in pairs if pair[0]["split"] == "evaluation"}
    saved = [json.loads(line) for line in (source / "factorial_actions.jsonl").read_text().splitlines()]
    assert not output.exists(), "Use new directory to preserve prior runs"
    output.mkdir(parents=True)
    comparisons = []
    for original in saved:
        world = original["world"]
        if original["arm"] in ("C", "D"):
            assert original["api_receipt"]["status"] == "accepted"
            selected = original["api_receipt"]["answer"]["acquire_condition_id"]
            policy = lambda view, selected=selected: selected
        else:
            policy = {"sensitivity": sensitivity_choice, "empirical_value": empirical_value_choice,
                      "stop": lambda view: None}[protocol["deterministic_policy_by_world"][world]]
        result = replay_pair(tuple(lookup[drug] for drug in original["drugs"]), world, fit_transfer(pairs, world),
                             output, original["case_id"], policy)
        assert result["final_choice"] == original["final_choice"]
        assert result["observed_selected_rms"] == original["observed_selected_rms"]
        assert result["budget"]["recorded_use"] == original["budget"]["recorded_use"]
        comparisons.append({"case_id": result["case_id"], "choice_and_metric_equal": True})
    receipt = {"cases": comparisons, "all_reproduced": True, "API_calls": 0,
               "actual_replay_access_units": sum(row["budget"]["recorded_use"] for row in saved),
               "basis": "saved actual LLM decisions; not a new LLM run"}
    (output / "reproduction.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.source, args.output), indent=2))
