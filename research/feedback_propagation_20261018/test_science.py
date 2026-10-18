"""Behaviour tests for the feedback-propagation study code (run explicitly: pytest research/feedback_propagation_20261018).

File summary
- Path: research/feedback_propagation_20261018/test_science.py
- Purpose: protect the properties the study's claims rest on: the chemical purge, outcome masking, the
  unmeasured-only nomination rule, agreement of the re-implemented updates with the world's own, the
  closed-form leave-one-probe-out residuals, and the repair's reduction to the base update.
- Tests build one small fold (evaluation fold 0, training fold 1) once per module.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bench  # noqa: E402
import loop as L  # noqa: E402
import repair as RP  # noqa: E402
import rules as R  # noqa: E402


@pytest.fixture(scope="module")
def fold():
    T = bench.load_tables()
    return bench.make_fold(T, 0, (1,))


def test_purge_leaves_no_training_analogue_at_the_boundary(fold):
    assert fold.max_sim_after.max() < bench.SEPARATION
    assert fold.max_sim_before.max() >= bench.SEPARATION
    assert fold.n_purged > 0
    assert set(fold.train_idx.tolist()).isdisjoint(set(np.where(np.load(bench.CACHE / "tables.npz")["fold"] == 0)[0].tolist()))


def test_oracle_returns_only_queried_cells_and_logs_them(fold):
    o = fold.oracle()
    y = o.observe(3, [5, 9])
    assert o.queried[3, [5, 9]].all() and o.queried.sum() == 2 and o.units == 2
    assert np.allclose(y, fold.hidden.Y[3, [5, 9]] + fold.hidden.sd[3, [5, 9]] * fold.hidden.z[3, [5, 9]], equal_nan=True)


def test_unmeasured_nominations_never_list_a_queried_or_inadmissible_pair(fold):
    o = fold.oracle()
    hist = L.fixed_histories(fold, o, 16)
    q = L.queried_from(fold, hist)
    S = L.score_matrix(fold, "ridge", hist)
    lists = L.nominate_lists(fold, S, q, only_unmeasured=True)
    for idx, picks in zip(fold.campaigns, lists):
        assert len(picks) <= bench.FOLLOW_UP
        per = {}
        for i, l in picks:
            assert not q[idx[i], l] and fold.avail[l]
            per[i] = per.get(i, 0) + 1
        assert max(per.values()) <= bench.CAP


def test_conditional_mean_matches_the_world_point_mean(fold):
    o = fold.oracle()
    P = fold.design[:12]
    y = o.observe(7, P)
    a = R.conditional_mean(fold, fold.prior[7], P, y)
    b = fold.world.point_mean(fold.prior[7], P, y)
    assert np.allclose(a, b)


def test_mixture_profile_matches_the_world_posterior_mixture(fold):
    o = fold.oracle()
    P = fold.design[:12]
    y = o.observe(11, P)
    post = fold.world.posterior(fold.prior[11], P, y, mixture=True)
    ref = np.zeros(len(fold.lines))
    for w, g in zip(post.weights, post.gains):
        ref += w * (fold.prior[11] + g @ post.residual)
    ref[post.probes] = fold.prior[11][post.probes] + post.residual
    assert np.allclose(R.mixture_profile(fold, 11, P, y), ref, atol=1e-8)


def test_lopo_closed_form_matches_brute_force(fold):
    o = fold.oracle()
    P = fold.design[:10]
    y = o.observe(5, P)
    m = fold.prior[5]
    r, sd = R.lopo(fold, m, P, y)
    Spp, _ = fold.world._blocks(P)
    A = Spp + fold.world.s2 * np.eye(len(P))
    for k in range(len(P)):
        rest = [j for j in range(len(P)) if j != k]
        Arr = A[np.ix_(rest, rest)]
        pred = m[P[k]] + A[k, rest] @ np.linalg.solve(Arr, y[rest] - m[P[rest]])
        var = A[k, k] - A[k, rest] @ np.linalg.solve(Arr, A[rest, k])
        assert np.isclose((y[k] - pred) / np.sqrt(var), r[k], atol=1e-8)
        assert np.isclose(np.sqrt(var), sd[k], atol=1e-8)


def test_repair_reduces_to_the_base_update_when_closed_or_lam_zero(fold):
    o = fold.oracle()
    P = L.pool_lines_for(fold, 3)
    y = o.observe(9, P)
    base = R.conditional_mean(fold, fold.prior[9], P, y)
    assert np.allclose(base, RP.repair_profile(fold, 9, P, y, gate="never"))
    assert np.allclose(base, RP.repair_profile(fold, 9, P, y, lam=0.0, gate="always"))
    assert np.allclose(base, RP.repair_profile(fold, 9, P, y, gate="lopo", margin=1e9))
    assert not np.allclose(base, RP.repair_profile(fold, 9, P, y, gate="always"))


def test_gate_reads_only_the_history_not_the_hidden_side(fold):
    o = fold.oracle()
    P = L.pool_lines_for(fold, 3)
    y = o.observe(9, P)
    a = RP.repair_profile(fold, 9, P, y)
    Y = fold.hidden.Y.copy()
    Y[9] = np.random.default_rng(3).normal(size=Y.shape[1])
    saved, fold.hidden = fold.hidden, bench.Hidden(Y=Y, truth=fold.hidden.truth, sd=fold.hidden.sd, z=fold.hidden.z)
    try:
        b = RP.repair_profile(fold, 9, P, y)
    finally:
        fold.hidden = saved
    assert np.array_equal(a, b)


def test_scrambling_unqueried_cells_changes_no_trajectory(fold):
    rows = list(range(24))
    import audit_task as A
    h1, q1 = A._run_closed(fold, fold.hidden, "ridge", rows)
    Y2 = fold.hidden.Y.copy()
    Y2[~q1] = np.random.default_rng(1).normal(size=int((~q1).sum()))
    h2, q2 = A._run_closed(fold, bench.Hidden(Y=Y2, truth=fold.hidden.truth, sd=fold.hidden.sd, z=fold.hidden.z), "ridge", rows)
    assert np.array_equal(q1, q2)
    assert all(np.array_equal(h1[i][1], h2[i][1], equal_nan=True) for i in rows)


def test_grade_counts_unknown_pairs_as_non_hits(fold):
    q = np.zeros((len(fold.cores), len(fold.lines)), dtype=bool)
    S = np.where(np.isnan(fold.hidden.Y), 1e6, -1.0)
    S[:, ~fold.avail] = -np.inf
    lists = L.nominate_lists(fold, S, q, only_unmeasured=True)
    g = L.grade_lists(fold, lists, q)
    assert sum(c["unknown"] for c in g["campaigns"]) > 0
    assert sum(c["hits"] for c in g["campaigns"]) == 0
