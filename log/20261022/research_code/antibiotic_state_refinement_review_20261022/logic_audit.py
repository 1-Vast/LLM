"""Exhaustive analytical toy: history benefit is not specific to a world model."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/antibiotic_state_refinement_review/logic_audit"
ROWS = [(history, action, float(history ^ action)) for history in (0, 1) for action in (0, 1)]


def mse(predictions):
    return sum((prediction - row[2]) ** 2 for prediction, row in zip(predictions, ROWS)) / len(ROWS)


def shared_action_collision(rows):
    return any(h1 != h2 and a1 == a2 and y1 != y2
               for h1, a1, y1 in rows for h2, a2, y2 in rows)


def main():
    target = OUT / "RESULT.json"
    if target.exists():
        raise FileExistsError(target)
    current_only = [sum(y for h, a, y in ROWS if a == action) / 2 for history, action, y in ROWS]
    refined_state = [float(history ^ action) for history, action, y in ROWS]
    direct_table = {(history, action): y for history, action, y in ROWS}
    direct = [direct_table[history, action] for history, action, y in ROWS]
    scores = {"current_state_action_mse": mse(current_only),
              "minimal_history_state_mse": mse(refined_state), "same_history_direct_table_mse": mse(direct)}
    assert scores == {"current_state_action_mse": 0.25, "minimal_history_state_mse": 0.0,
                      "same_history_direct_table_mse": 0.0}
    assert shared_action_collision(ROWS)
    assert not shared_action_collision([ROWS[0], ROWS[-1]])
    observed_marker_prediction = [float(history ^ action) for history, action, y in ROWS]
    assert mse(observed_marker_prediction) == 0.0
    result = {"scope": "EXHAUSTIVE_SYNTHETIC_LOGIC_ONLY", "scores": scores,
              "direct_equals_refinement_on_all_cells": direct == refined_state,
              "current_state_with_accurate_marker_mse": mse(observed_marker_prediction),
              "no_common_action_mutation_refuses_collision": True,
              "decision": "STOP_INFERRING_WORLD_MODEL_BENEFIT_FROM_MEMORY_ONLY_ABLATION",
              "biological_agent_inheritance_RSI": "NOT_TESTED",
              "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "protocol_sha256": hashlib.sha256((OUT / "PROTOCOL.md").read_bytes()).hexdigest()}
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
