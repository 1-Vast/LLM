import numpy as np

from research.astra.mono_pretraining_20261005.mono import (
    Records, drug_mean, lineage_mean, lineage_ridge, ridge_per_drug, score)


def _data(seed=0, n=400, nd=15, f=14, signal=1.0):
    g = np.random.default_rng(seed)
    z = g.normal(size=(n, f))
    lin = g.integers(0, 4, n)
    base = g.normal(size=nd) * 2
    shift = g.normal(size=(4, nd)) * 0.7
    W = g.normal(size=(f, nd)) * 0.4 * signal
    cell, drug = np.meshgrid(np.arange(n), np.arange(nd), indexing="ij")
    cell, drug = cell.ravel(), drug.ravel()
    y = base[drug] + shift[lin[cell], drug] + (z[cell] * W[:, drug].T).sum(1) + g.normal(0, 0.5, len(cell))
    return z, lin, cell, drug, y, nd


def _split(seed=0, **kw):
    z, lin, cell, drug, y, nd = _data(seed, **kw)
    tr = cell < 300
    return Records(cell[tr], drug[tr], y[tr], z, lin, nd), Records(cell[~tr], drug[~tr], y[~tr], z, lin, nd)


def test_context_signal_is_detected_and_ordered():
    tr, te = _split()
    s = {k: score(te, f(tr, te)) for k, f in (("mean", drug_mean), ("lin", lineage_mean), ("ridge", ridge_per_drug),
                                              ("linridge", lineage_ridge))}
    assert s["lin"]["per_drug_spearman"] > s["mean"]["per_drug_spearman"] + 0.1
    assert s["linridge"]["per_drug_spearman"] > s["lin"]["per_drug_spearman"] + 0.1


def test_no_signal_means_no_gain_over_the_drug_mean():
    tr, te = _split(seed=3, signal=0.0)
    m = score(te, drug_mean(tr, te))["within_cell_spearman"]
    r = score(te, ridge_per_drug(tr, te))["within_cell_spearman"]
    assert abs(r - m) < 0.05


def test_scores_use_only_heldout_cells():
    tr, te = _split()
    assert not set(tr.cell) & set(te.cell)
