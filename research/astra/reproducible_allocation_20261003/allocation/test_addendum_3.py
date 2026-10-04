"""Behaviour tests for post hoc addendum 3 (synthetic release only; no Jaaks outcomes).

File summary
- Path: research/astra/reproducible_allocation_20261003/allocation/test_addendum_3.py
- Purpose: information-matched rankings must use other lines only, the S and R references must
  reproduce the main-replay and addendum-2 purchases, and target validation labels stay inert.
- Interfaces: `pytest research/astra/reproducible_allocation_20261003/allocation/test_addendum_3.py`.
- Depends on: numpy, pytest, addendum_3_information, addendum_2x2, replay.
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from research.astra.feedback_validation_20261003 import jaaks
from research.certified_discovery.screens import sha256

from . import addendum_2x2 as ad
from . import addendum_3_information as a3
from . import replay as rp


@pytest.fixture(scope="module")
def synthetic_lines(tmp_path_factory):
    path = jaaks.synthetic_release(tmp_path_factory.mktemp("rel3") / "release.csv")
    ticket = {"freeze_sha256": "TEST_NOT_A_VAULT", "data_sha256": sha256(path)}
    panels, _, candidates = jaaks.build_panels(ticket, path)
    return rp.build_lines(panels, candidates, rp.load_design(path))


def test_recomputed_history_mean_matches_world(synthetic_lines):
    for L in synthetic_lines:
        assert np.allclose(a3.history_scores(L)["S_recomputed"], L.static, atol=1e-9)


@pytest.mark.parametrize("unit", ["measurement", "physical"])
def test_references_reproduce_earlier_arms(synthetic_lines, unit):
    spec = rp.Spec("verify_hits_terminal", "static", "verify_hits", terminal=True)
    for L in synthetic_lines:
        keys = a3.arm_keys(L)
        assert a3.simulate_v(L, keys["S"], unit)["purchases"] == rp.simulate(L, spec, unit)["purchases"]
        assert a3.simulate_v(L, keys["R"], unit)["purchases"] == ad.simulate_cell(L, "R", "V", unit)["purchases"]


def test_scores_ignore_target_line_outcomes(synthetic_lines):
    L = next(x for x in synthetic_lines if x.replicate == "SV")
    rows = L.world.rows
    panel = L.panel
    flipped = replace(panel, valid_hit=panel.valid_hit.copy(), valid_y=panel.valid_y.copy())
    flipped.valid_hit[rows] = ~flipped.valid_hit[rows]
    flipped.valid_y[rows] = flipped.valid_y[rows] + 1000.0
    a = a3.history_scores(L)
    b = a3.history_scores(replace(L, panel=flipped))
    for name in ("S_both", "S_valid", "S_vrate"):
        assert np.allclose(a[name], b[name])


@pytest.mark.parametrize("unit", ["measurement", "physical"])
def test_budget_and_validation_labels_inert(synthetic_lines, unit):
    for L in synthetic_lines[:6]:
        keys = a3.arm_keys(L)
        for arm in a3.ARMS:
            rec = a3.simulate_v(L, keys[arm], unit)
            if unit == "measurement":
                assert rec["spent"] == L.M
            else:
                assert rec["spent"] <= L.W and rec["remainder_class"] in ("none", "unavoidable")
            vh = np.random.default_rng(3).random(L.n) < 0.5
            assert a3.simulate_v(replace(L, valid_hit=vh), keys[arm], unit)["purchases"] == rec["purchases"]
