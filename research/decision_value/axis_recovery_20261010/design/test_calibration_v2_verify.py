"""Counterexamples for the bounded adaptive allocation, not biological claims."""
import numpy as np

from research.decision_value.axis_recovery_20261010.design.calibration_v2_verify import compact_allocation, uncovered


def test_compact_allocation_preserves_rare_discovery_support_without_filling():
    group = dict(condition_id="one", label="eligible", samples=["sample"])
    jobs = [dict(condition_id="one", row=row) for row in range(40)]
    presence = np.ones((40,2), dtype=bool)
    presence[3:,0] = False
    protocol = dict(hash_seed="frozen", maximum_discovery_cells_per_file=80, maximum_holdout_cells_per_file=48)
    chosen, status, _ = compact_allocation("file", [group], jobs, presence, protocol)
    assert status == "INDEX_ALLOCATION_READY"
    discovery, holdout = chosen[0]["discovery_rows"], chosen[0]["holdout_rows"]
    assert len(discovery) == 2 and len(holdout) == 1 and not set(discovery) & set(holdout)
    assert presence[discovery,0].sum() == 2 and presence[holdout,0].sum() == 1


def test_allocation_cap_failure_does_not_claim_global_infeasibility():
    group = dict(condition_id="one", label="eligible", samples=["sample"])
    jobs = [dict(condition_id="one", row=row) for row in range(6)]
    presence = np.zeros((6,2), dtype=bool)
    presence[:3,0] = True
    presence[3:,1] = True
    protocol = dict(hash_seed="frozen", maximum_discovery_cells_per_file=80, maximum_holdout_cells_per_file=1)
    chosen, status, occurrences = compact_allocation("file", [group], jobs, presence, protocol)
    assert chosen is None and status == "BLOCKED/INDEX_ALLOCATION_HEURISTIC_FAILURE"
    assert occurrences.tolist() == [3,3]


def test_exact_cost_counts_unretained_gaps_and_reuses_actual_overlaps_only():
    assert uncovered([(0,9),(5,14),(20,29)], [(0,4),(7,11),(22,24)]) == 12
