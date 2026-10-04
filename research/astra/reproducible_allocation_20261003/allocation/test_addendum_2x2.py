"""Behaviour tests for the post hoc predictor x scheduler addendum (synthetic data only).

File summary
- Path: research/astra/reproducible_allocation_20261003/allocation/test_addendum_2x2.py
- Purpose: the 2x2 cells must reproduce the two main-replay arms they coincide with, conserve
  the budget, never let validation labels steer purchases, and count deferrals only under I.
- Interfaces: `pytest research/astra/reproducible_allocation_20261003/allocation/test_addendum_2x2.py`.
- Depends on: numpy, pytest, addendum_2x2, replay, test_allocation helpers.
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from research.astra.feedback_validation_20261003 import jaaks
from research.certified_discovery.screens import sha256

from . import addendum_2x2 as ad
from . import replay as rp
from .test_allocation import make_line


@pytest.fixture(scope="module")
def synthetic_lines(tmp_path_factory):
    path = jaaks.synthetic_release(tmp_path_factory.mktemp("rel2") / "release.csv")
    ticket = {"freeze_sha256": "TEST_NOT_A_VAULT", "data_sha256": sha256(path)}
    panels, _, candidates = jaaks.build_panels(ticket, path)
    return rp.build_lines(panels, candidates, rp.load_design(path))


@pytest.mark.parametrize("unit", ["measurement", "physical"])
def test_corner_cells_reproduce_main_replay_arms(synthetic_lines, unit):
    for L in synthetic_lines:
        for cell, spec in ad.REFERENCE.items():
            assert ad.simulate_cell(L, *cell, unit)["purchases"] == rp.simulate(L, spec, unit)["purchases"]


@pytest.mark.parametrize("seed", [0, 1, 2, 3])
def test_corner_cells_reproduce_on_hand_made_lines(seed):
    line = make_line(150, seed=seed, varied=True)
    for unit in ("measurement", "physical"):
        for cell, spec in ad.REFERENCE.items():
            assert ad.simulate_cell(line, *cell, unit, base=0.4)["purchases"] == rp.simulate(line, spec, unit)["purchases"]


@pytest.mark.parametrize("unit", ["measurement", "physical"])
def test_budget_conserved_and_validation_labels_inert(unit):
    line = make_line(140, seed=21, varied=True)
    for cell in ad.CELLS:
        rec = ad.simulate_cell(line, *cell, unit, base=0.4)
        if unit == "measurement":
            assert rec["spent"] == line.M
        else:
            assert rec["spent"] <= line.W and rec["remainder_class"] in ("none", "unavoidable")
        vh = np.random.default_rng(5).random(line.n) < 0.5
        again = ad.simulate_cell(replace(line, valid_hit=vh), *cell, unit, base=0.4)
        assert again["purchases"] == rec["purchases"], cell


def test_deferrals_only_under_index_scheduler():
    for seed in range(6):
        line = make_line(160, seed=seed)
        for predictor in ("S", "R"):
            assert ad.simulate_cell(line, predictor, "V", base=0.4)["deferred_by_priority"] == 0
    # under S with unit costs the verify value (base) beats every screen value (p_s x base): no deferral
    line = make_line(160, seed=1)
    assert ad.simulate_cell(line, "S", "I", base=0.4)["deferred_by_priority"] == 0
    # under R a low P(v|s) hit can lose to a high p_sv screen: construct one
    line = make_line(160, seed=2)
    p_vs = np.full(line.n, 0.01)
    p_sv = np.full(line.n, 0.5)
    rec = ad.simulate_cell(replace(line, p_vs=p_vs, p_sv=p_sv), "R", "I")
    assert rec["deferred_by_priority"] > 0 and rec["deferred_hits"] > 0
