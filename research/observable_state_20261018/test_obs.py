"""Data-dependent tests for the per-family bets study (labels, fingerprints, DepMap and PRISM tables; no LLM, no network)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import obs_core as O  # noqa: E402


@pytest.fixture(scope="module")
def W():
    return O.build_world()


def test_splits_are_chemically_separated_and_comparators_purged(W):
    fp, T = W.T["fp"], W.T
    for f in list(W.episodes)[:12]:
        ep = W.episodes[f]
        assert O.tc.tanimoto(fp[ep["S"]], fp[ep["H"]]).max() < 0.5
        members = np.concatenate([ep["S"], ep["H"]])
        assert O.tc.tanimoto(fp[ep["Fp"]], fp[members]).max() < 0.5
        assert not np.intersect1d(ep["Fp"], members).size and f not in set(T["family"][ep["Fp"]])


def test_vocabulary_admissibility_counts(W):
    assert W.admissible.sum() > 500
    for v in np.where(W.admissible)[0][:50]:
        for lines in (~W.held_lines, W.held_lines):
            assert (W.Z[v] & W.known[v] & lines).sum() >= O.MIN_LINES
            assert (~W.Z[v] & W.known[v] & lines).sum() >= O.MIN_LINES


def test_no_proposal_input_depends_on_held_out_cells(W):
    f = next(iter(W.episodes))
    base = O.search_stats(W, f)
    rng = np.random.default_rng(1)
    Y2 = W.Y.copy()
    Y2[:, W.held_lines] = rng.normal(size=Y2[:, W.held_lines].shape)
    Y2[W.episodes[f]["H"], :] = rng.normal(size=Y2[W.episodes[f]["H"], :].shape)
    W2 = O.World(**{**W.__dict__, "Y": Y2})
    assert np.allclose(np.nan_to_num(O.search_stats(W2, f)[1]), np.nan_to_num(base[1]))


def test_confirm_detects_planted_effect_and_is_calibrated_under_null(W, monkeypatch):
    monkeypatch.setattr(O, "PERMS", 2000)
    f = list(W.episodes)[3]
    ep = W.episodes[f]
    rng = np.random.default_rng(2)
    Y0 = rng.normal(0, 0.5, W.Y.shape)
    adm = np.where(W.admissible)[0]
    W0 = O.World(**{**W.__dict__, "Y": Y0})
    hits = sum(O.confirm(W0, f, int(rng.choice(adm)), -1, 0.0)["confirmed"] for _ in range(60))
    assert hits <= 9  # nominal 5% and |contrast| >= 0.10; generous bound for 60 draws
    v = int(adm[5])
    Y1 = Y0.copy()
    on = W.Z[v] & W.known[v] & W.held_lines
    for r in ep["H"]:
        Y1[r, on] -= 1.0
    W1 = O.World(**{**W.__dict__, "Y": Y1})
    assert O.confirm(W1, f, v, -1, 0.3)["confirmed"]
    assert not O.confirm(W1, f, v, +1, 0.3)["confirmed"]
