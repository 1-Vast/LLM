"""Finite-sample checks for the design-based certificates.

File summary
- Path: research/certified_discovery/test_certify.py
- Purpose: show that the certificates hold where the theory says they do, fail where it says
  they would, and refuse by name when nothing can be certified.
- Core points: brute-force BH and hypergeometric references; Monte Carlo FDR and coverage
  under a deliberately miscalibrated, adaptively chosen shortlist; a violated design (audit
  taken from the top of the shortlist instead of at random) is shown to break FDR control.
- Depends on: numpy, scipy (reference distributions), `certify`.
"""
from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from research.certified_discovery import certify as cert


def test_conformal_pvalues_count_nulls_at_or_above_the_candidate():
    p = cert.conformal_pvalues([0.9, 0.8, 0.7, 0.1], [True, False, False, False], [0.85, 0.75, 0.05])
    assert np.allclose(p, [1 / 5, 2 / 5, 4 / 5])


def test_benjamini_hochberg_matches_brute_force():
    rng = np.random.default_rng(0)
    for _ in range(200):
        p = rng.random(rng.integers(1, 30)) ** 2
        alpha = rng.choice([0.05, 0.1, 0.2])
        m = p.size
        k = max([i for i in range(1, m + 1) if np.sort(p)[i - 1] <= alpha * i / m], default=0)
        expected = p <= (np.sort(p)[k - 1] if k else -1)
        assert np.array_equal(cert.benjamini_hochberg(p, alpha), expected)


@pytest.mark.parametrize("population,draws,observed", [(60, 20, 7), (300, 100, 40), (45, 15, 0), (45, 15, 15)])
def test_yield_bound_inverts_the_hypergeometric_tail(population, draws, observed):
    delta = 0.1
    bound = cert.yield_lower_bound(population, draws, observed, delta)
    total = bound + observed
    assert stats.hypergeom.sf(observed - 1, population, total, draws) > delta
    if total - 1 >= observed:
        assert stats.hypergeom.sf(observed - 1, population, total - 1, draws) <= delta


def test_refusals_are_named():
    shortlist = np.arange(30)
    scores = np.linspace(1, 0, 30)
    too_small = cert.certify(shortlist, scores, np.array([0, 5, 9]), np.array([True, True, True]), alpha=0.2, delta=0.1)
    assert too_small.refusal == cert.AUDIT_TOO_SMALL and too_small.nominated.size == 0
    no_hit = cert.certify(shortlist, scores, np.arange(0, 30, 3), np.zeros(10, bool), alpha=0.2, delta=0.1)
    assert no_hit.refusal == cert.NO_CANDIDATE_PASSES and no_hit.nominated.size == 0
    empty = cert.certify(np.array([], int), np.array([]), np.array([], int), np.array([], bool), alpha=0.2, delta=0.1)
    assert empty.refusal == cert.EMPTY_SHORTLIST


def _adaptive_world(rng):
    """A pool whose model is overconfident at the top; the shortlist is the model's top slice."""
    n = 2000
    signal = rng.normal(size=n)
    hits = rng.random(n) < 1 / (1 + np.exp(-(signal - 2.0)))
    model = signal + rng.normal(scale=1.5, size=n)          # noisy, miscalibrated ranking
    model[rng.random(n) < 0.05] += 4.0                        # a cluster of confident errors
    shortlist = np.argsort(-model)[:150]
    return shortlist, model[shortlist], hits


@pytest.mark.parametrize("alpha", [0.1, 0.2])
def test_random_audit_controls_fdr_and_covers_yield_under_adaptive_selection(alpha):
    rng = np.random.default_rng(1)
    fdp, covered, nominated = [], [], []
    for _ in range(600):
        shortlist, scores, hits = _adaptive_world(rng)
        audit, _ = cert.draw_audit(shortlist, 50, rng)
        result = cert.certify(shortlist, scores, audit, hits[audit], alpha=alpha, delta=0.1)
        chosen = result.nominated
        fdp.append(0.0 if chosen.size == 0 else float(np.mean(~hits[chosen])))
        nominated.append(chosen.size)
        covered.append(result.yield_bound <= hits[result.remainder].sum())
    standard_error = np.std(fdp) / np.sqrt(len(fdp))
    assert np.mean(fdp) <= alpha + 3 * standard_error
    assert np.mean(nominated) > 0                       # the test is not passed by refusing
    assert np.mean(covered) >= 0.9 - 3 * np.sqrt(0.09 / len(covered))


def _two_cluster_shortlist(rng):
    """Cluster 0 is ranked sensibly; cluster 1 is a block of confident model errors."""
    familiar = rng.random(100) < 0.6
    familiar_scores = rng.normal(size=100) + familiar
    errors_scores = rng.normal(loc=3.0, size=100)       # scored highest, never hits
    hits = np.concatenate([familiar, np.zeros(100, bool)])
    return np.arange(200), np.concatenate([familiar_scores, errors_scores]), hits


def test_a_hand_picked_audit_breaks_the_guarantee_and_a_random_one_does_not():
    """An agent that audits only what it is comfortable with is not exchangeable with the rest."""
    rng = np.random.default_rng(2)
    picked, random_fdp = [], []
    for _ in range(300):
        shortlist, scores, hits = _two_cluster_shortlist(rng)
        for store, audit in ((picked, rng.choice(100, 50, replace=False)),
                             (random_fdp, cert.draw_audit(shortlist, 50, rng)[0])):
            result = cert.certify(shortlist, scores, audit, hits[audit], alpha=0.1, delta=0.1)
            chosen = result.nominated
            store.append(0.0 if chosen.size == 0 else float(np.mean(~hits[chosen])))
    assert np.mean(picked) > 0.5
    assert np.mean(random_fdp) <= 0.1 + 3 * np.std(random_fdp) / np.sqrt(len(random_fdp))
