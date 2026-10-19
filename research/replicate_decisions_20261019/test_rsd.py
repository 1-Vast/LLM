"""Isolation, poisoning and accounting checks for the RSD study (real arena; run explicitly, not in the default suite).

python -B -m pytest research/replicate_decisions_20261019/test_rsd.py -p no:cacheprovider -q
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rsd_core as C  # noqa: E402
import rsd_data as D  # noqa: E402
import rsd_run as R  # noqa: E402

CFG = dict(q=2, rho=0.0, q_pca=40)


@pytest.fixture(scope="module")
def arena():
    R.setup("search")
    return R.setup.__defaults__[0]["arena"]


def _with(arena, **arrays):
    t, lines, Tsim, audit, E, A, B, T, P = arena
    A2, B2, T2 = arrays.get("A", A), arrays.get("B", B), arrays.get("T", T)
    R.setup.__defaults__[0]["arena"] = (t, lines, Tsim, audit, E, A2, B2, T2, P)


def _restore(arena):
    R.setup.__defaults__[0]["arena"] = arena


def test_arena_reads_no_outcomes(monkeypatch):
    monkeypatch.setattr(D, "LFC", Path("does-not-exist.csv"))
    monkeypatch.setattr(D, "PRIM_LFC", Path("does-not-exist.csv"))
    t, lines, Tsim, audit, E = D.build_arena()
    assert audit["n_compounds"] == len(t) and set(t.role) == {"reference", "search", "selection", "evaluation"}


def test_block_references_are_purged_and_disjoint(arena):
    t, lines, Tsim, audit, E, *_ = arena
    for blk in ("search", "selection", "evaluation"):
        S = R.setup(blk)
        assert not E[np.ix_(S["ref"], S["q"])].any(), blk
        assert set(S["ref"]).isdisjoint(S["q"])
        assert (t.role.to_numpy()[S["ref"]] == "reference").all()


def test_truth_poisoning_leaves_policies_unchanged(arena):
    # search block: no policy output is computed on the selection or evaluation blocks before the freeze
    S = R.setup("search")
    q = S["q"]
    acq = R.Acquisition(S["A"][q], S["B"][q])
    A = acq.read_A()
    base, _ = R.arms_single(S, CFG, A)
    t, lines, Tsim, audit, E, A0, B0, T0, P = arena
    T2 = T0.copy()
    T2[q] = np.random.default_rng(0).normal(size=T2[q].shape)
    _with(arena, T=T2)
    try:
        pois, _ = R.arms_single(R.setup("search"), CFG, A)
    finally:
        _restore(arena)
    for k in base:
        assert np.array_equal(base[k], pois[k], equal_nan=True), k


def test_other_blocks_do_not_train_search_block(arena):
    S = R.setup("search")
    vc = R.build_vc(S, CFG)
    t, lines, Tsim, audit, E, A0, B0, T0, P = arena
    other = np.where(t.role.isin(["selection", "evaluation", "search"]))[0]
    rng = np.random.default_rng(1)
    A2, B2, T2 = A0.copy(), B0.copy(), T0.copy()
    for X in (A2, B2, T2):
        X[other] = rng.normal(size=X[other].shape)
    _with(arena, A=A2, B=B2, T=T2)
    try:
        vc2 = R.build_vc(R.setup("search"), CFG)
    finally:
        _restore(arena)
    # g is NaN for the one listed line without any HTS002 2.5 uM read (ACH-001192); compare NaN-aware
    for a, b in ((vc.S0, vc2.S0), (vc.N0, vc2.N0), (vc.g, vc2.g), (vc.alpha, vc2.alpha), (vc.beta, vc2.beta)):
        assert np.array_equal(a, b, equal_nan=True)


def test_unpurchased_B_is_invisible():
    rng = np.random.default_rng(2)
    A, B = rng.normal(size=(6, 4)), rng.normal(size=(6, 4))
    acq = R.Acquisition(A, B)
    acq.read_A()
    got = acq.buy_B([1, 3])
    assert np.isnan(got[[0, 2, 4, 5]]).all() and np.array_equal(got[[1, 3]], B[[1, 3]])
    assert acq.reads == 8


def test_posterior_shrinks_toward_prior_without_reads():
    rng = np.random.default_rng(3)
    L = 12
    vc = C.VirtualCell.__new__(C.VirtualCell)
    vc.g = np.zeros(L); vc.tiers = False; vc.alpha = np.ones(3); vc.beta = np.ones(3)
    vc.S0 = np.eye(L); vc.N0 = np.eye(L)
    mu = rng.normal(size=(2, L))
    y = np.full((2, L), np.nan)
    m, v, n1 = vc.posterior(mu, y, np.ones(2), np.zeros(2, int))
    assert np.allclose(m, mu) and np.allclose(v, 1.0)
    y = rng.normal(size=(2, L))
    m, v, n1 = vc.posterior(mu, y, np.ones(2), np.zeros(2, int))
    s = y - y.mean(1, keepdims=True)
    assert np.allclose(m, mu + 0.5 * (s - mu)) and np.allclose(v, 0.5)
