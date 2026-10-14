"""Evaluator-audit findings C1-C7 as executable contracts (maestro.evaluation_contract), on synthetic matrices only."""
import hashlib
import inspect

import numpy as np
import pytest

from maestro import evaluation_contract as ec
from maestro.evaluation_contract import (IdentityRefused, PinnedInputs, Readout, TrainNormaliser, eligible_units, hit_labels,
                                         nominate_wells, resolve_identity, settle, viability_fraction, viability_hit)

CORE = lambda n: f"BRD-K{n:08d}"                                       # 13 characters, like a Broad core


def test_c1_eligibility_is_defined_by_metadata_and_has_no_outcome_input():
    assert "outcome" not in " ".join(inspect.signature(eligible_units).parameters)
    meta = [{"unit": u, "screen": s, "pert_type": "trt_cp", "line": l} for u, s, l in
            [("a", "REP1M", "L1"), ("a", "REP.1M", "L2"), ("b", "REP1M", "L1"), ("c", "REP.300", "L1"), ("c", "REP.300", "L2")]]
    assert eligible_units(meta, screen="REP.1M", perturbation_type="trt_cp", min_lines=2) == ("a",)   # spelling normalised
    assert eligible_units(reversed(meta), screen="REP.1M", perturbation_type="trt_cp", min_lines=2) == ("a",)


def test_c2_nominations_ignore_outcomes_and_missing_or_failed_wells_are_consumed():
    wells = [(f"c{i}", "L1") for i in range(8)]
    scores = {w: float(i % 5) for i, w in enumerate(wells)}
    nominated = nominate_wells(scores, set(wells), 4, salt="s")
    assert nominated == nominate_wells(dict(reversed(list(scores.items()))), set(wells), 4, salt="s")   # order-invariant
    rng = np.random.default_rng(0)
    seen = set()
    for trial in range(5):                                                     # hidden outcomes (incl. missingness) change freely
        values = {w: (np.nan if rng.random() < 0.4 else rng.random()) for w in wells}
        qc = {w: bool(rng.random() < 0.7) for w in wells}
        settle(nominated, [Readout("primary", "fraction", values, qc)], 0.5)
        seen.add(nominate_wells(scores, set(wells), 4, salt="s"))
    assert len(seen) == 1
    values = {nominated[0]: 0.1, nominated[1]: 0.1, nominated[2]: 0.1}      # nominated[3] never measured
    qc = {nominated[0]: True, nominated[1]: False, nominated[2]: True}
    s = settle(nominated, [Readout("primary", "fraction", values, qc)], 0.5)
    assert (s.wells_consumed, s.hits["primary"], s.qc_failed["primary"], s.missing["primary"]) == (4, 2, 1, 1)
    with pytest.raises(ValueError, match="NOMINATION_OUTSIDE_FROZEN_SET"):
        nominate_wells(scores, set(wells[:4]), 2, salt="s")


def test_c3_normaliser_is_fitted_on_authorised_training_rows_only():
    train, test = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]), np.array([[100.0, 100.0]])
    norm = TrainNormaliser({"t1", "t2", "t3"}).fit(train, ["t1", "t2", "t3"])
    assert list(norm.median) == [3.0, 4.0]
    with pytest.raises(ValueError, match="NORMALISER_ROW_NOT_AUTHORISED"):
        TrainNormaliser({"t1", "t2", "t3"}).fit(np.vstack([train, test]), ["t1", "t2", "t3", "x1"])
    before = norm.residualise(train).copy()
    norm.residualise(test)                                                     # applying to test rows never refits
    assert np.array_equal(norm.residualise(train), before)


def test_c4_hit_labels_are_row_local_and_ignore_the_other_test_compounds():
    rng = np.random.default_rng(1)
    train = rng.normal(size=(30, 12))
    norm = TrainNormaliser({str(i) for i in range(30)}).fit(train, [str(i) for i in range(30)])
    test = rng.normal(size=(6, 12))
    test[2, 3] -= 8.0
    labels = hit_labels(test, norm, 3.0)
    assert labels[2, 3]
    assert np.array_equal(hit_labels(test[[2]], norm, 3.0), labels[[2]])       # alone
    shifted = np.vstack([test, rng.normal(loc=50.0, size=(9, 12))])            # an outlying batch of other compounds
    assert np.array_equal(hit_labels(shifted, norm, 3.0)[:6], labels)


def test_c5_identity_collisions_duplicates_and_losses_are_refused_or_listed():
    rows = [{"id": CORE(1) + "-001-01-1", "screen": "REP.1M"}, {"id": CORE(2) + "-001-01-1", "screen": "REP1M"}]
    res = resolve_identity([CORE(1), CORE(2)], rows)
    assert set(res.mapping) == {CORE(1), CORE(2)} and res.unmapped == ()
    with pytest.raises(IdentityRefused, match="CROSS_SCREEN_COLLISION"):
        resolve_identity([CORE(1)], rows + [{"id": CORE(1) + "-002-02-2", "screen": "REP.300"}])
    with pytest.raises(IdentityRefused, match="AMBIGUOUS_DUPLICATE_ROWS"):
        resolve_identity([CORE(1)], rows + [{"id": CORE(1) + "-009-09-9", "screen": "REP1M"}])            # would be averaged otherwise
    with pytest.raises(IdentityRefused, match="DUPLICATE_ID"):
        resolve_identity([CORE(1)], rows + [rows[0]])
    with pytest.raises(IdentityRefused, match="UNMAPPED_CORES_EXCEED_ALLOWANCE"):
        resolve_identity([CORE(1), CORE(3)], rows)
    assert resolve_identity([CORE(1), CORE(3)], rows, max_unmapped=1).unmapped == (CORE(3),)             # a declared, recorded loss


def test_c6_only_pinned_unchanged_inputs_can_be_read(tmp_path):
    (tmp_path / "meta.csv").write_bytes(b"id,screen\n")
    pins = PinnedInputs(tmp_path, {"meta.csv": hashlib.sha256(b"id,screen\n").hexdigest()})
    assert pins.read_bytes("meta.csv") == b"id,screen\n" and pins.problems() == []
    (tmp_path / "other.csv").write_bytes(b"x")
    with pytest.raises(PermissionError, match="UNPINNED_INPUT"):
        pins.read_bytes("other.csv")
    (tmp_path / "meta.csv").write_bytes(b"id,screen\nchanged\n")
    assert pins.problems() == ["PINNED_DIGEST_MISMATCH: meta.csv"]


def test_c7_secondary_readouts_follow_the_same_qc_and_unit_rules():
    well = ("c", "L1")
    primary = Readout("primary", "fraction", {well: 0.4}, {well: False})
    secondary = Readout("secondary", "percent", {well: 40.0}, {well: False})
    s = settle([well], [primary, secondary], 0.5)
    assert s.hits == {"primary": 0, "secondary": 0} and s.qc_failed == {"primary": 1, "secondary": 1}
    ok = settle([well], [Readout("primary", "fraction", {well: 0.4}, {well: True}), Readout("secondary", "percent", {well: 40.0}, {well: True})], 0.5)
    assert ok.hits == {"primary": 1, "secondary": 1}


def test_viability_units_are_declared_and_the_threshold_boundary_is_stable():
    with pytest.raises(ValueError, match="UNIT_UNDECLARED"):
        viability_fraction([0.5, 0.2], None)
    assert list(viability_fraction([50.0, 25.0], "percent")) == [0.5, 0.25]
    assert list(viability_fraction([29.0, 33.0, 57.0, 58.0], "percent")) == [0.29, 0.33, 0.57, 0.58]   # division, not a product
    with pytest.raises(ValueError, match="UNIT_RANGE_SUSPECT"):
        viability_fraction(np.linspace(40, 120, 30), "fraction")                         # percent labelled as a fraction
    with pytest.raises(ValueError, match="UNIT_RANGE_SUSPECT"):
        viability_fraction(np.linspace(0.1, 1.2, 30), "percent")                         # fraction labelled as percent
    assert list(viability_fraction([0.1, 2.66], "fraction")) == [0.1, 2.66]              # overgrowth is legitimate
    for inclusive, expected in ((True, True), (False, False)):
        assert viability_hit([0.5], "fraction", 0.5, inclusive=inclusive)[0] == expected
        assert viability_hit([50.0], "percent", 0.5, inclusive=inclusive)[0] == expected  # same class under both units
    assert not viability_hit([float("nan")], "fraction", 0.5, inclusive=True)[0]
    for percent in (29.0, 33.0, 57.0):                                                    # no x100 round trip
        assert viability_hit([percent], "percent", percent / 100.0, inclusive=True)[0]
    assert ec.NORMALISER_ROW_NOT_AUTHORISED in "NORMALISER_ROW_NOT_AUTHORISED"
