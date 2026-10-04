"""Behaviour tests for the verify workstream's independent P1 / P3 (synthetic data only).

File summary
- Path: research/astra/confirmation_campaign_20261004/verify/test_frontier.py
- Purpose: hand-checked P3 reserve rule (stop at first failure, ceil of the rounded sum), round
  structure and cap for P3, P1 arithmetic, and the design-record invariant checker catching illegal
  records. No real outcome is read.
- Interfaces: pytest tests.
"""
from __future__ import annotations

import numpy as np
import pytest

from research.astra.confirmation_campaign_20261004.verify import independent_check as ic
from research.astra.confirmation_campaign_20261004.verify import independent_frontier as fr
from research.astra.confirmation_campaign_20261004.verify.check_design import invariants


def test_p3_reserve_rule_by_hand():
    # M = 10: round 1 screens 5 (positions 0-4); hits at 0 and 3; verify order = identity
    sh = np.array([1, 0, 0, 1, 0, 1, 1, 0, 0, 0], bool)
    vh = np.array([1, 0, 0, 0, 0, 1, 0, 0, 0, 0], bool)
    p_s = np.array([.5, .5, .5, .5, .5, 0.4, 0.4, 0.3, 0.9, 0.1])
    order = np.arange(10)
    r = fr.run_p3(order, order, p_s, 10, ic.Market(sh, vh))
    # v2 = 2, B2 = 10 - 5 - 2 = 3; candidates 5 (0.4): 1 + ceil(0.4)=2 <= 3 ok; 6: 2 + ceil(0.8)=3 ok;
    # 7: 3 + ceil(1.1)=5 > 3 -> stop (8 and 9 never considered)
    assert r["n_r1"] == 5 and r["v2"] == 2 and r["B2"] == 3 and r["round2_screens"] == 2
    assert r["screens"] == [0, 1, 2, 3, 4, 5, 6] and r["verifies"] == [0, 3, 5]
    assert r["confirmed"] == 2 and r["spent"] == 10 and r["rounds_used"] == 3


def test_p3_no_round2_screens_when_hits_fill_the_cap():
    sh = np.ones(10, bool)
    vh = np.ones(10, bool)
    r = fr.run_p3(np.arange(10), np.arange(10)[::-1], np.full(10, 0.9), 10, ic.Market(sh, vh))
    assert r["v2"] == 5 and r["B2"] == 0 and r["round2_screens"] == 0
    assert r["verifies"] == [4, 3, 2, 1, 0] and r["spent"] == 10 and r["rounds_used"] == 2


@pytest.mark.parametrize("seed", range(20))
def test_p3_cap_and_legality_random(seed):
    rng = np.random.default_rng(seed)
    n = int(rng.integers(5, 60))
    m = ic.cap_m(n)
    sh, vh = rng.random(n) < 0.3, rng.random(n) < 0.5
    so, vo = rng.permutation(n), rng.permutation(n)
    r = fr.run_p3(so, vo, rng.random(n), m, ic.Market(sh, vh))
    assert r["spent"] <= m and set(r["verifies"]) <= set(r["screen_hits"])
    assert r["confirmed"] == int(sum(sh[i] and vh[i] for i in r["verifies"]))


def test_p1():
    joint = np.array([1, 0, 1, 1, 0], bool)
    r = fr.p1_confirmed(np.array([4, 2, 3, 0, 1]), joint, 5)
    assert r["n1"] == 2 and r["screens"] == [4, 2] and r["confirmed"] == 1 and r["spent"] == 4


def _record(rounds, spent=2, cap=2, policy="P2"):
    screens = [i for e in rounds for i in e["screens"]]
    verifies = [i for e in rounds for i in e["verifies"]]
    return {"policy": policy, "cap": cap, "spent": spent, "screens": screens, "verifies": verifies, "rounds": rounds}


def _round(r, screens, verifies, hits):
    return {"round": r, "screens": screens, "verifies": verifies,
            "reveals": {"screens": [[i, 0.0, hits.get(i, False)] for i in screens],
                        "verifies": [[i, 0.0, True] for i in verifies]}}


def test_invariant_checker_catches_illegal_records():
    ok = _record([_round(1, [0], [], {0: True}), _round(2, [], [0], {})])
    assert invariants(ok) == []
    assert "screen in final round" in invariants(_record([_round(1, [0], [], {0: True}), _round(2, [1], [0], {})], spent=3, cap=3))
    assert "verify of a non-hit" in invariants(_record([_round(1, [0], [], {0: False}), _round(2, [], [0], {})]))
    assert "verify without earlier screen" in invariants(_record([_round(1, [0], [0], {0: True})]))
    assert "spent>cap" in invariants(_record([_round(1, [0], [], {0: True}), _round(2, [], [0], {})], spent=2, cap=1))
