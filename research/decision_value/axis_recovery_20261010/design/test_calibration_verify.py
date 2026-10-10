"""Scientific counterexamples for finite source-axis certification."""
import numpy as np
import pytest

from research.decision_value.axis_recovery_20261010.design.calibration_verify import (
    RetainedFile, allocate_rows, certify_coordinate, covered_interval, validate_groups,
)


def certificate(names, discovery, heldout, trajectory, heldout_trajectory):
    return certify_coordinate(names, np.asarray(discovery), np.asarray(heldout),
                              np.asarray(trajectory), np.asarray(heldout_trajectory), "A", 1e-5)


def test_nonendpoint_match_defeats_false_uniqueness():
    result = certificate(["A", "OUTSIDE_PANEL"], [[1.,1.],[2.,2.]], [[3.,3.]], [1.,2.], [3.])
    assert result["matching_raw_gene_count"] == 2 and not result["passed"]


def test_allzero_holdout_does_not_certify_an_informative_discovery():
    result = certificate(["A", "B"], [[1.,0.],[2.,0.]], [[0.,0.]], [1.,2.], [0.])
    assert result["discovery_pass"] and not result["heldout_pass"]


def test_wrong_name_and_duplicate_source_symbols_remain_blocked():
    wrong = certificate(["B", "A"], [[1.,0.],[2.,0.]], [[3.,0.]], [1.,2.], [3.])
    duplicate = certificate(["A", "A"], [[1.,0.],[2.,0.]], [[3.,0.]], [1.,2.], [3.])
    assert not wrong["passed"] and not duplicate["passed"]


def test_holdout_contradiction_blocks_discovered_identity():
    result = certificate(["A", "B"], [[1.,0.],[2.,0.]], [[3.,0.]], [1.,2.], [4.])
    assert result["discovery_pass"] and not result["passed"]


def test_disjoint_cells_do_not_override_pooled_sample_exclusion():
    group = dict(file="c44.h5ad", label="eligible", sample="protected", role="holdout", rows=list(range(16)))
    exclusions = dict(excluded_exact_sentinel_labels=[], excluded_pooled_sample_ids=["protected"])
    with pytest.raises(AssertionError):
        validate_groups([group], exclusions, set())


def test_hidden_gap_in_retained_ranges_never_synthesizes_source_bytes():
    source = RetainedFile(8, [(0,b"abcd"),(5,b"fgh")])
    with pytest.raises(ValueError, match="unretained"):
        source.at(2,7)
    assert RetainedFile(8, [(0,b"abcd"),(4,b"efgh")]).at(2,7) == b"cdefg"


def test_download_coalescing_must_not_cross_unselected_expression():
    assert covered_interval(10, 29, [(10,19),(20,29)])
    assert not covered_interval(10, 30, [(10,19),(21,30)])


def test_rare_holdout_reservation_preserves_two_discovery_hits():
    group = dict(condition_id="one", label="eligible", samples=["sample"])
    jobs = [dict(condition_id="one", row=row) for row in range(40)]
    presence = np.ones((40,2), dtype=bool)
    presence[3:,0] = False
    chosen, status, _ = allocate_rows("file", [group], jobs, presence, dict(hash_seed="frozen"))
    assert status == "INDEX_ALLOCATION_READY"
    discovery, holdout = chosen[0]["discovery_rows"], chosen[0]["holdout_rows"]
    assert len(discovery) == len(holdout) == 16 and not set(discovery) & set(holdout)
    assert presence[discovery,0].sum() >= 2 and presence[holdout,0].sum() == 1
    presence[2,0] = False
    chosen, status, _ = allocate_rows("file", [group], jobs, presence, dict(hash_seed="frozen"))
    assert chosen is None and status == "BLOCKED/NECESSARY_INDEX_SUPPORT_BELOW_THREE"
