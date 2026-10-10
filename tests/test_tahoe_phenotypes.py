"""Contract tests for same-spheroid Tahoe phenotypes (tools/datasets/tahoe_phenotypes.py)."""
from __future__ import annotations

import numpy as np
import pytest

from tools.datasets.tahoe_phenotypes import CONTROL, counts_from_codes, phenotype_frame, qualify_lines

DRUG = "[('Drug', 5.0, 'uM')]"


def _table(held_n=250):
    table = {}
    for line in ("ref1", "ref2", "held"):
        table[(line, CONTROL, "p1")] = {"n": 1000, "G1": 500, "S": 250, "G2M": 250}
    table[("ref1", DRUG, "p1")] = {"n": 1000, "G1": 500, "S": 250, "G2M": 250}
    table[("ref2", DRUG, "p1")] = {"n": 1000, "G1": 500, "S": 250, "G2M": 250}
    table[("held", DRUG, "p1")] = {"n": held_n, "G1": 200, "S": 25, "G2M": 25}
    return table


def test_codes_are_counted_per_condition_plate_and_phase():
    rows = counts_from_codes("L", np.array([0, 0, 1, 1, 1]), np.array([0, 0, 0, 1, 1]), np.array([0, 1, 2, 0, 0]),
                             ["A", "B"], ["p1", "p2"], ["G1", "G2M", "S"])
    assert rows[("L", "A", "p1")] == {"n": 2, "G1": 1, "S": 0, "G2M": 1}
    assert rows[("L", "B", "p2")] == {"n": 2, "G1": 2, "S": 0, "G2M": 0}
    with pytest.raises(ValueError):
        counts_from_codes("L", np.array([0]), np.array([0, 1]), np.array([0]), ["A"], ["p1", "p2"], ["G1", "G2M", "S"])


def test_survival_is_a_share_change_whose_denominator_excludes_undeclared_lines():
    frame = phenotype_frame(_table(), ["held", "ref1"], ["ref1", "ref2"])
    assert frame[("ref1", DRUG, "p1")]["survival"] == pytest.approx(0.0, abs=1e-6)
    assert frame[("held", DRUG, "p1")]["survival"] == pytest.approx(np.log2(250.5 / 2000) - np.log2(1000.5 / 2000))
    other = phenotype_frame(_table(held_n=5), ["ref1"], ["ref1", "ref2"])
    assert other[("ref1", DRUG, "p1")]["survival"] == pytest.approx(0.0, abs=1e-6)


def test_phase_shift_is_measured_against_the_same_plate_control():
    frame = phenotype_frame(_table(), ["held"], ["ref1", "ref2"])
    assert frame[("held", DRUG, "p1")]["G1"] == pytest.approx(np.log(200.5 / 50.5) - np.log(500.5 / 500.5))


def test_undercounted_lines_are_refused_by_name():
    table = _table(held_n=50)
    kept, refused = qualify_lines(table, ["ref1", "held"], min_median=200)
    assert kept == ["ref1"]
    assert refused["held"]["reason"] == "CONTEXT_UNDERCOUNTED" and refused["held"]["median_treated_count"] == 50
