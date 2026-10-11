"""Asset-free numerical prototype; no biological efficacy claim."""
from __future__ import annotations

import json
from pathlib import Path

from maestro.acquisition import OutcomeBranch, OutcomeForecast, expected_terminal_decision_value


def verify():
    candidates = frozenset({"a", "b"})
    useful = OutcomeForecast("assay", (
        OutcomeBranch("a", {"a": 0.99, "b": 0.01}, 100),
        OutcomeBranch("b", {"a": 0.01, "b": 0.99}, 100),
    ))
    flat = OutcomeForecast("assay", (
        OutcomeBranch("a", {"loud": 1.0}, 100),
        OutcomeBranch("b", {"loud": 1.0}, 100),
    ))
    kwargs = dict(wrong_decision_loss=4.0, defer_loss=1.0, measurement_cost=0.1)
    value = expected_terminal_decision_value(candidates, useful, {}, **kwargs)
    trap = expected_terminal_decision_value(candidates, flat, {}, **kwargs)
    assert value.admissible and abs(value.net_value - 0.86) < 1e-12
    assert not trap.admissible and trap.decision_sensitivity == 0.0
    return {"status": "ENGINEERING_CONTRACT_ONLY", "useful": value.payload(), "magnitude_trap": trap.payload(),
            "limitation": "Synthetic likelihoods; independent calibration and biological value are not established."}


if __name__ == "__main__":
    result = verify()
    Path(__file__).with_name("prototype_contract.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))
