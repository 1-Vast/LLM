"""Verify minimum-cost full hint constraints offline without producer imports."""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


HERE = Path(__file__).resolve().parent
PLAN = HERE.parent.parent
BASE = PLAN.parent


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    result = load(HERE / "SELECTION.json")
    for directory in (PLAN, PLAN / "cost_review", HERE):
        for path, expected in load(directory / "FREEZE.json")["sha256"].items():
            assert hashlib.sha256((BASE / path).read_bytes()).hexdigest() == expected
    pool = sorted(load(PLAN / "CANDIDATE_POOL.json"), key=lambda c: (c["file"], c["label"]))
    requirements = result["requirements"]
    pool = [c for c in pool if any(c["file"] == r["file"] and c["all39_named_deltas"][r["gene"]] > 0 for r in requirements)]
    keys = {(c["file"], c["label"]): c for c in pool}
    selected_keys = {(c["file"], c["label"]) for c in result["selected"]}
    assert len(selected_keys) == 15
    decision = np.array([int((c["file"], c["label"]) in selected_keys) for c in pool])
    costs = np.array([c["index_screen_bytes"] for c in pool])
    cover = np.array([[int(c["file"] == r["file"] and c["all39_named_deltas"][r["gene"]] > 0) for c in pool] for r in requirements])
    file_counts = np.array([[int(c["file"] == file) for c in pool] for file in ("c44.h5ad", "c45.h5ad")])
    need = np.array([r["new_positive_hint_conditions_required"] for r in requirements])
    assert (cover @ decision >= need).all()
    assert list(file_counts @ decision) == [7, 8]
    for i, requirement in enumerate(requirements):
        assert int(cover[i] @ decision) == requirement["selected_positive_hint_conditions"]
    for c in result["selected"]:
        original = keys[(c["file"], c["label"])]
        assert all(c[key] == value for key, value in original.items())
    assert int(costs @ decision) == result["exact_new_index_payload_bytes"] == 10_652_056
    assert sum(c["full_qc_available"] for c in result["selected"]) == result["new_full_qc_index_cells"] == 2312
    # Independent solver call recomputes global byte minimum under the same finite
    # 15 named-hint requirements and max-eight constraints, without producer code.
    matrix = np.concatenate([cover, file_counts])
    lower = np.concatenate([need, [0, 0]])
    upper = np.concatenate([np.full(len(need), np.inf), [8, 8]])
    optimizer = milp(costs.astype(float), integrality=np.ones(len(pool)), bounds=Bounds(0, 1),
        constraints=LinearConstraint(matrix, lower, upper), options={"mip_rel_gap": 0.0, "time_limit": 60.0})
    assert optimizer.status == 0 and optimizer.mip_gap == 0
    assert int(round(optimizer.fun)) == 10_652_056
    assert all(r["status"] in (0, 2) for r in result["solver_receipts"])
    assert result["new_network_calls"] == 0 and result["new_index_reads"] is False
    assert result["projected_total_with_reserves"] == 27_152_056 <= 28_000_000
    outcome = {"schema": "offline_full_hint_cost_review_verification_v1", "status": "PASS",
        "constraints_verified": len(requirements), "global_minimum_index_bytes": 10_652_056,
        "source_QC_rows": 2312, "new_conditions": 15, "new_network_calls": 0,
        "producer_imports": False, "actual_index_support_claimed": False,
        "new_indices_read": False, "all_named_hint_requirements_satisfied": True}
    (HERE / "VERIFIED.json").write_text(json.dumps(outcome, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(outcome))


if __name__ == "__main__":
    main()
