"""Scientific counterexamples for prospective qualification boundaries."""
import numpy as np
import pytest

from research.decision_value.axis_recovery_20261010.design.named_verify import (
    calibration_eligible, check_old_gate, singleton_indices,
)


def test_duplicate_or_missing_named_gene_cannot_be_repaired_by_first_match():
    with pytest.raises(ValueError, match="missing_or_duplicate"):
        singleton_indices(["CD38", "CD38", "TNF"], ["CD38", "TNF"])
    with pytest.raises(ValueError, match="missing_or_duplicate"):
        singleton_indices(["CD38", "TNF"], ["CD38", "IFNB1"])


def test_direct_named_zero_is_observed_but_cannot_identify_hidden_column():
    assert singleton_indices(["OTHER", "TNF"], ["TNF"]) == [1]
    named = np.zeros((8, 2))
    hidden = np.zeros(8)
    matching = np.flatnonzero(np.max(np.abs(named-hidden[:, None]), axis=0) <= 1e-5)
    assert len(matching) == 2  # The valid named zero supplies no unique hidden-axis identity.


def test_file_specific_gate_rejects_borrowed_axis_and_uninformative_holdout():
    c44 = dict(file="c44.h5ad", passed_coordinates=39, heldout_informative=True)
    assert not check_old_gate({"c44.h5ad": c44}, ["c44.h5ad", "c45.h5ad"])
    assert not check_old_gate({"c44.h5ad": c44, "c45.h5ad": c44}, ["c44.h5ad", "c45.h5ad"])
    c45 = dict(file="c45.h5ad", passed_coordinates=39, heldout_informative=False)
    assert not check_old_gate({"c44.h5ad": c44, "c45.h5ad": c45}, ["c44.h5ad", "c45.h5ad"])


def test_pooled_sample_exclusion_survives_cell_line_partition():
    c44 = dict(file="c44.h5ad", label="calibration candidate", sample="shared-pool")
    c45 = dict(file="c45.h5ad", label="another-line-label", sample="shared-pool")
    assert not calibration_eligible(c44, set(), {"shared-pool"})
    assert not calibration_eligible(c45, set(), {"shared-pool"})
    assert not calibration_eligible(dict(c45, sample="other-pool"), {"another-line-label"}, set())


def test_matching_endpoint_panel_only_would_false_certify_duplicate_trajectory():
    raw = np.array([[0., 1., 1.], [0., 2., 2.]])
    target = raw[:, 1]
    endpoint_only = np.flatnonzero(np.max(np.abs(raw[:, :2]-target[:, None]), axis=0) <= 1e-5)
    all_genes = np.flatnonzero(np.max(np.abs(raw-target[:, None]), axis=0) <= 1e-5)
    assert len(endpoint_only) == 1 and len(all_genes) == 2
