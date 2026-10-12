"""Contracts of routed knowledge transfer (virtual cell), its profiling designs and the campaign runner."""
import numpy as np
import pytest

from agent.profiling import ProfilingSpec, run_profiling
from maestro.transfer_value import plan_batch, profiling_value, sparse_transfer_design
from virtual_cell.knowledge_transfer import (NO_TRANSFER_ROUTE, SPECIFIC_DIRECTION_UNSUPPORTED, Certifier,
                                             TransferAtlas, expected_cosine, predict, transfer_table, unit_rows)


class _Constant:
    """A duck-typed meta-model returning one value (the certifier needs only predict/predict_proba)."""

    def __init__(self, value):
        self.value = value

    def predict(self, X):
        return np.full(len(X), self.value)

    def predict_proba(self, X):
        return np.column_stack([np.full(len(X), 1 - self.value), np.full(len(X), self.value)])


def _responses(seed=0, n_ref=120, n_query=10, lines=3, genes=12):
    """Half the references respond strongly along a shared direction; line t+1 is a linear map of line t."""
    rng = np.random.default_rng(seed)
    n = n_ref + n_query
    M = rng.normal(size=(genes, genes)) / np.sqrt(genes)
    amp = np.where(rng.random(n) < 0.5, 3.0, 0.1)
    amp[n_ref:] = 3.0
    base = amp[:, None] * (rng.normal(size=genes)[None] + rng.normal(size=(n, genes)))
    Y = np.stack([base, base @ M, base @ M @ M], 1)[:, :lines] + rng.normal(size=(n, lines, genes)) * 0.3
    ref = np.r_[np.ones(n_ref, bool), np.zeros(n_query, bool)]
    fps = rng.random((n, 64)) < 0.2
    know = rng.random((n, 16)) < 0.1
    thr = np.median(np.linalg.norm(Y[:n_ref], axis=2), axis=0)
    return Y, ref, fps, know, thr


def _world(seed=0):
    Y, ref, fps, know, thr = _responses(seed)
    return TransferAtlas.build(Y, ref, fps, know, thr), Y


def _certifier(rho=0.6, p=0.9):
    return Certifier(_Constant(p), {r: _Constant(rho) for r in ("context", "pheno", "chem", "know")}, _Constant(rho))


def test_atlas_fits_maps_generic_directions_and_share():
    atlas, _ = _world()
    assert set(atlas.maps) == {(s, t) for s in range(3) for t in range(3) if s != t}
    assert np.allclose(np.linalg.norm(atlas.G, axis=1), 1.0)
    assert 0 <= atlas.gamma <= 1
    with pytest.raises(ValueError, match="AXIS_MISMATCH"):
        TransferAtlas.build(np.zeros((3, 2, 4)), np.ones(2, bool), np.zeros((3, 8), bool), np.zeros((3, 2), bool),
                            np.ones(2))


def test_context_transfer_recovers_the_query_response_from_a_visible_line():
    atlas, _ = _world()
    q = np.arange(120, 130)
    visible = np.zeros((10, 3), bool)
    visible[:, 0] = True
    out = predict(atlas, _certifier(), q, 1, visible)
    truth = atlas.Yc[q, 1]
    cos = (out.direction * truth).sum(1) / np.linalg.norm(truth, axis=1)
    assert cos.mean() > 0.5
    assert (out.certificate.refusal == "").all()
    assert np.allclose(out.certificate.expected_cosine, expected_cosine(atlas.gamma, 0.6))


def test_refusals_fall_back_to_the_generic_direction():
    atlas, _ = _world()
    q = np.arange(120, 125)
    nothing = np.zeros((5, 3), bool)
    atlas.fps[:] = False
    atlas.know[:] = False
    out = predict(atlas, _certifier(), q, 2, nothing)
    assert (out.certificate.refusal == NO_TRANSFER_ROUTE).all()
    assert np.allclose(out.direction, atlas.G[2])
    weak = predict(atlas, _certifier(rho=0.05), q, 2, np.ones((5, 3), bool))
    assert (weak.certificate.refusal == SPECIFIC_DIRECTION_UNSUPPORTED).all()
    assert np.allclose(weak.certificate.rho, 0.0) and np.allclose(weak.direction, atlas.G[2])


def test_query_rows_are_read_only_through_the_visibility_mask():
    atlas, _ = _world()
    q = np.arange(120, 125)
    visible = np.zeros((5, 3), bool)
    visible[:, 0] = True
    before = predict(atlas, _certifier(), q, 1, visible).direction
    atlas.Yc[q, 2] = 1e3                      # an invisible line of the query changes
    after = predict(atlas, _certifier(), q, 1, visible).direction
    assert np.allclose(before, after)
    with pytest.raises(ValueError, match="AXIS_MISMATCH"):
        predict(atlas, _certifier(), q, 1, np.zeros((5, 2), bool))


def test_transfer_table_is_lines_by_lines_with_an_empty_diagonal():
    atlas, _ = _world()
    kappa = transfer_table(atlas)
    assert kappa.shape == (3, 3) and np.allclose(np.diag(kappa), 0.0)


def test_profiling_value_adds_transfer_gain_to_direct_gain():
    p = np.array([[1.0, 1.0], [0.0, 0.0]])
    ecos = np.full((2, 2), 0.4)
    rho = np.zeros((2, 2))
    kappa = np.array([[0.0, 0.8], [0.2, 0.0]])
    v = profiling_value(p, ecos, rho, np.ones((2, 2), bool), kappa, 0.4)
    assert v[0, 0] > v[0, 1] > v[1, 0] == v[1, 1] == 0.0      # line 0 transfers better into line 1
    assert np.isneginf(profiling_value(p, ecos, rho, np.zeros((2, 2), bool), kappa, 0.4)).all()
    with pytest.raises(ValueError, match="AXIS_MISMATCH"):
        profiling_value(p, ecos, rho, np.ones((2, 2), bool), np.zeros((3, 3)), 0.4)


def test_batch_updates_a_compound_after_each_pick():
    p = np.ones((2, 3))
    p[1] *= 0.5
    ecos = np.full((2, 3), 0.4)
    rho = np.zeros((2, 3))
    kappa = np.full((3, 3), 0.9)
    np.fill_diagonal(kappa, 0.0)
    chosen = plan_batch(p, ecos, rho, np.ones((2, 3), bool), kappa, 0.4, 2)
    assert chosen.sum() == 2 and chosen[0].sum() == 1 and chosen[1].sum() == 1
    assert plan_batch(p, ecos, rho, np.zeros((2, 3), bool), kappa, 0.4, 2).sum() == 0
    with pytest.raises(ValueError):
        plan_batch(p, ecos, rho, np.ones((2, 3), bool), kappa, 0.4, -1)


def test_sparse_design_covers_every_compound_in_its_best_open_hub_before_any_twice():
    kappa = np.array([[0.0, 0.5, 0.4], [0.1, 0.0, 0.1], [0.8, 0.7, 0.0]])    # hub order: line 2, 0, 1
    grid = np.ones((5, 3), bool)
    grid[3, 2] = False                                                       # compound 3 cannot use line 2
    once = sparse_transfer_design(grid, kappa, 5, seed=1)
    assert (once.sum(1) == 1).all()
    assert once[[0, 1, 2, 4], 2].all() and once[3, 0]
    twice = sparse_transfer_design(grid, kappa, 7, seed=1)
    assert twice.sum() == 7 and (twice.sum(1) >= 1).all() and (once <= twice).all()
    assert (twice == sparse_transfer_design(grid, kappa, 7, seed=1)).all()
    assert (sparse_transfer_design(grid, kappa, 100) == grid).all()
    assert not (sparse_transfer_design(grid, kappa, 100) & ~grid).any()
    with pytest.raises(ValueError, match="AXIS_MISMATCH"):
        sparse_transfer_design(grid, np.zeros((2, 2)), 3)
    with pytest.raises(ValueError):
        sparse_transfer_design(grid, kappa, -1)


def _library_world(seed=0):
    """The atlas sees no library response; ``measure`` replays the hidden truth and logs every request."""
    Y, ref, fps, know, thr = _responses(seed)
    hidden = Y.copy()
    Y = Y.copy()
    Y[~ref] = np.nan
    atlas = TransferAtlas.build(Y, ref, fps, know, thr)
    library = np.flatnonzero(~ref)
    requested = []

    def measure(cells):
        requested.extend(map(tuple, cells.tolist()))
        return hidden[library[cells[:, 0]], cells[:, 1]]

    return atlas, library, hidden, measure, requested


@pytest.mark.parametrize("planner,turnarounds", [("sparse_transfer", 1), ("value_of_information", 4)])
def test_campaign_spends_the_budget_and_reads_only_what_it_profiles(planner, turnarounds):
    atlas, library, hidden, measure, requested = _library_world()
    grid = np.ones((len(library), 3), bool)
    report = run_profiling(atlas, _certifier(), library, grid, measure,
                           ProfilingSpec(len(library), planner=planner), seed=3)
    assert report.wells == len(library) and report.turnarounds == turnarounds
    assert sorted(requested) == sorted(map(tuple, np.argwhere(report.profiled).tolist()))
    assert np.allclose(report.fills[report.profiled], 0.0) and (report.refusal[report.profiled] == "").all()
    open_cells = np.argwhere(~report.profiled)
    truth = hidden[library[open_cells[:, 0]], open_cells[:, 1]] - atlas.mu[open_cells[:, 1]]
    fills = report.fills[open_cells[:, 0], open_cells[:, 1]]
    assert ((unit_rows(fills) * unit_rows(truth)).sum(1)).mean() > 0.5       # certified transfer fills the rest


def test_campaign_refuses_visible_library_responses_references_and_unknown_planners():
    atlas, library, _, measure, requested = _library_world()
    grid = np.ones((len(library), 3), bool)
    with pytest.raises(ValueError, match="LIBRARY_CONTAINS_REFERENCES"):
        run_profiling(atlas, _certifier(), np.r_[0, library], np.ones((len(library) + 1, 3), bool), measure,
                      ProfilingSpec(2))
    atlas.Yc[library[0], 1] = 0.0
    with pytest.raises(ValueError, match="LIBRARY_RESPONSES_VISIBLE"):
        run_profiling(atlas, _certifier(), library, grid, measure, ProfilingSpec(2))
    assert requested == []
    with pytest.raises(ValueError, match="UNKNOWN_PLANNER"):
        ProfilingSpec(2, planner="llm")
    with pytest.raises(ValueError, match="AXIS_MISMATCH"):
        run_profiling(atlas, _certifier(), library, grid[:, :2], measure, ProfilingSpec(2))
