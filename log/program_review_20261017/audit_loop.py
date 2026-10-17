"""Synthetic diagnosis of the committed and working-copy thin research loop.

No biological outcomes, assay purchases, model training or provider calls.
Synthetic observations use the legacy admission fields only to exercise control
flow; their source strings are fixtures, not authenticated experimental evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import types

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / "src/maestro/research_loop.py"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_source(source, name):
    module = types.ModuleType(name)
    sys.modules[name] = module
    exec(compile(source, str(SOURCE), "exec"), module.__dict__)
    return module


def fixture(module, outcome, count):
    names = ("A", "B", "C") if count == 3 else tuple(f"A{i:02}" for i in range(count))
    actions = tuple(module.ActionCandidate(name, 1.0, float(count - i)) for i, name in enumerate(names))
    forecasts = {}
    for action in actions:
        values = {"action_id": action.identifier, "probabilities": {"H1": .8, "H2": .2},
                  "information_gain": action.expected_information, "support": 1,
                  "basis": "synthetic fixture", "scope": ""}
        forecasts[action.identifier] = module.Forecast(**{k: v for k, v in values.items() if k in module.Forecast.__dataclass_fields__})

    class Executor:
        def execute(self, action):
            values = {"action_id": action.identifier, "outcome": outcome,
                      "source_id": "synthetic://not-biological-evidence/" + action.identifier,
                      "context_identifier": "synthetic-control-flow", "independent_units": 1,
                      "detail": {"fixture_only": True}}
            return module.Observation(**{k: v for k, v in values.items() if k in module.Observation.__dataclass_fields__})

    loop = module.ResearchLoop(module.HypothesisPair("H1", "H2"), actions, forecasts, Executor(), budget=float(count))
    loop.run()
    return {"outcome_fixture": outcome, "actions": list(loop.state.selected_actions),
            "label_shares": loop._posterior(), "stop_reason": loop.state.stop_reason,
            "remaining_budget": loop.state.remaining_budget,
            "receipt_digest": loop.digest()}


def diagnose(source, name):
    module = load_source(source, name)
    positive, negative = fixture(module, "H1", 3), fixture(module, "H2", 3)
    sixteen, eighteen = fixture(module, "H1", 16), fixture(module, "H1", 18)
    assert positive["actions"] == negative["actions"] == ["A", "B", "C"]
    assert positive["label_shares"]["H1"] != negative["label_shares"]["H1"]
    assert sixteen["label_shares"]["H1"] == 17 / 18
    assert sixteen["stop_reason"] == "budget_exhausted"
    assert eighteen["label_shares"]["H1"] == .95
    assert eighteen["stop_reason"] == "confidence_reached"
    return {"source_sha256": sha(source), "three_actions_H1": positive,
            "three_actions_H2": negative, "sixteen_actions_H1": sixteen,
            "eighteen_actions_H1": eighteen,
            "diagnosis": "Default scores are static; labels affect heuristic support/termination, not automatic recomputation of future forecasts or values.",
            "inference_limit": "A label share is neither a likelihood posterior nor a calibrated mechanism-correctness probability. This is a control-flow diagnostic, not a scientific benchmark."}


def audit():
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    committed = subprocess.check_output(["git", "show", "HEAD:src/maestro/research_loop.py"], cwd=ROOT)
    current = SOURCE.read_bytes()
    return {"grade": "SYNTHETIC_ENGINEERING_DIAGNOSTIC", "head": head,
            "committed": diagnose(committed, "committed_loop_audit"),
            "working_copy": diagnose(current, "working_loop_audit"),
            "working_copy_differs_from_head": sha(current) != sha(committed),
            "new_biological_experiments": 0, "new_model_fits": 0,
            "paid_provider_calls": 0, "purchased_assays": 0,
            "policy_or_learning_benefit_tested": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = audit()
    target = HERE / "LOOP_AUDIT.json"
    if args.verify:
        assert result == json.loads(target.read_text(encoding="utf-8")), "audit_replay_changed"
        preserved = json.loads((HERE / "PRESERVED.json").read_text(encoding="utf-8"))
        for name, expected in preserved.items():
            assert sha((ROOT / name).read_bytes()) == expected, name
        print(json.dumps({"audit_replay": "PASS", "preserved_files": len(preserved),
                          "scientific_grade": result["grade"]}))
    else:
        if target.exists():
            raise FileExistsError("existing audit: use --verify")
        target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
