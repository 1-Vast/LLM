"""Core contract: design-based certificates for an agent's untested candidates.

File summary
- Path: tests/test_certification.py
- Purpose: the promoted `maestro.certification` is exact where it claims exactness, valid under
  adaptive and miscalibrated selection when its audit is random, invalid when the audit is
  hand-picked, and refuses by name.
- Depends on: standard library and numpy (synthetic worlds only; asset-free).
"""
from __future__ import annotations

import math
import random

import numpy as np

from maestro import certification as cert


def test_pvalues_and_bh_match_brute_force():
    assert cert.conformal_pvalues([0.9, 0.8, 0.7, 0.1], [True, False, False, False], [0.85, 0.75, 0.05]) == [0.2, 0.4, 0.8]
    rng = random.Random(0)
    for _ in range(200):
        p = [rng.random() ** 2 for _ in range(rng.randint(1, 25))]
        alpha = rng.choice([0.05, 0.1, 0.2])
        ordered = sorted(p)
        k = max([i for i in range(1, len(p) + 1) if ordered[i - 1] <= alpha * i / len(p)], default=0)
        assert cert.benjamini_hochberg(p, alpha) == [x <= (ordered[k - 1] if k else -1) for x in p]


def test_yield_bound_inverts_the_exact_hypergeometric_tail():
    def tail(observed, population, successes, draws):
        return sum(math.comb(successes, k) * math.comb(population - successes, draws - k)
                   for k in range(observed, min(draws, successes) + 1)) / math.comb(population, draws)

    for population, draws, observed in [(60, 20, 7), (45, 15, 0), (45, 15, 15), (200, 50, 22)]:
        bound = cert.yield_lower_bound(population, draws, observed, 0.1)
        assert tail(observed, population, bound + observed, draws) > 0.1
        if bound > 0:
            assert tail(observed, population, bound + observed - 1, draws) <= 0.1


def test_refusals_are_named():
    shortlist, scores = list(range(30)), [1 - i / 30 for i in range(30)]
    assert cert.certify(shortlist, scores, [0, 5, 9], [True] * 3, alpha=0.2, delta=0.1).refusal == cert.AUDIT_TOO_SMALL
    empty = cert.certify(shortlist, scores, list(range(0, 30, 3)), [False] * 10, alpha=0.2, delta=0.1)
    assert empty.refusal == cert.NO_CANDIDATE_PASSES and empty.nominated == ()
    assert cert.certify([], [], [], [], alpha=0.2, delta=0.1).refusal == cert.EMPTY_SHORTLIST
    assert cert.certify(shortlist, scores, [99], [True], alpha=0.2, delta=0.1).refusal == cert.AUDIT_NOT_IN_SHORTLIST
    assert cert.minimum_audit(0.2) == 4 and cert.minimum_audit(0.1) == 9


def _overconfident_shortlist(rng: np.random.Generator):
    signal = rng.normal(size=1500)
    hits = rng.random(1500) < 1 / (1 + np.exp(-(signal - 2.0)))
    model = signal + rng.normal(scale=1.5, size=1500)
    model[rng.random(1500) < 0.05] += 4.0                 # confident errors
    shortlist = np.argsort(-model)[:120].tolist()
    return shortlist, [float(model[i]) for i in shortlist], hits


def test_random_audit_holds_fdr_and_coverage_under_adaptive_selection():
    rng = np.random.default_rng(1)
    fdp, covered, nominated = [], [], 0
    for trial in range(300):
        shortlist, scores, hits = _overconfident_shortlist(rng)
        audit, _ = cert.draw_audit(shortlist, 40, random.Random(trial))
        c = cert.certify(shortlist, scores, audit, [bool(hits[i]) for i in audit], alpha=0.2, delta=0.1)
        fdp.append(0.0 if not c.nominated else float(np.mean([not hits[i] for i in c.nominated])))
        covered.append(c.yield_bound <= sum(bool(hits[i]) for i in c.remainder))
        nominated += len(c.nominated)
    assert np.mean(fdp) <= 0.2 + 3 * np.std(fdp) / np.sqrt(len(fdp))
    assert np.mean(covered) >= 0.9 - 3 * math.sqrt(0.09 / len(covered))
    assert nominated > 0


def test_hand_picked_audit_breaks_the_guarantee():
    rng = np.random.default_rng(2)
    fdp = []
    for _ in range(200):
        familiar = rng.random(100) < 0.6
        scores = list(rng.normal(size=100) + familiar) + list(rng.normal(loc=3.0, size=100))
        hits = list(familiar) + [False] * 100
        audit = rng.choice(100, 50, replace=False).tolist()        # avoids the confident errors
        c = cert.certify(list(range(200)), scores, audit, [hits[i] for i in audit], alpha=0.1, delta=0.1)
        fdp.append(0.0 if not c.nominated else float(np.mean([not hits[i] for i in c.nominated])))
    assert np.mean(fdp) > 0.5
