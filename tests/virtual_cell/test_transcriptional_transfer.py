"""Contract tests for transcriptional transfer of viability profiles (src/virtual_cell/transcriptional_transfer.py)."""
from __future__ import annotations

import numpy as np
import pytest

from virtual_cell.transcriptional_transfer import (GENERIC_AXES_SCOPE, UNVALIDATED_SCOPE, VALIDATED_SCOPE,
                                                   fit_generic_axes, remove_generic_axes, selective_r,
                                                   signature_similarity, transfer_profile)


def _signatures(rng, n, conditions=3, genes=8):
    return rng.normal(size=(n, conditions, genes))


def test_the_most_similar_reference_dominates():
    rng = np.random.default_rng(0)
    refs = _signatures(rng, 4)
    query = refs[2] + 0.01 * rng.normal(size=refs[2].shape)
    profiles = np.arange(4)[:, None] * np.ones((4, 5))
    out = transfer_profile(query, refs, profiles, k=1)
    assert out.refusal is None and out.scope == VALIDATED_SCOPE
    assert list(out.neighbours) == [2] and out.values == pytest.approx(np.full(5, 2.0))
    assert out.trust == pytest.approx(out.similarities[0]) and out.trust > 0.99


def test_similarity_uses_only_conditions_measured_for_both():
    q = np.array([[1.0, 0.0], [np.nan, np.nan]])
    refs = np.array([[[1.0, 0.0], [0.0, 1.0]], [[np.nan, np.nan], [1.0, 0.0]]])
    s = signature_similarity(q, refs)
    assert s[0] == pytest.approx(1.0) and np.isnan(s[1])


def test_missing_reference_values_are_skipped_not_read_as_zero():
    refs = np.array([[[1.0, 0.0]], [[0.9, 0.1]]])
    profiles = np.array([[np.nan, 1.0], [4.0, 1.0]])
    out = transfer_profile(np.array([[1.0, 0.05]]), refs, profiles, k=2)
    assert out.values[0] == pytest.approx(4.0)


def test_negatively_similar_neighbours_fall_back_to_an_unweighted_mean():
    refs = np.array([[[-1.0, 0.0]], [[0.0, -1.0]]])
    out = transfer_profile(np.array([[1.0, 0.0]]), refs, np.array([[2.0], [4.0]]), k=2)
    assert out.values[0] == pytest.approx(3.0)


def test_unusable_inputs_are_refused_by_name():
    rng = np.random.default_rng(1)
    refs = _signatures(rng, 3)
    assert transfer_profile(refs[0], np.empty((0, 3, 8)), np.empty((0, 5))).refusal == "NO_REFERENCE_DRUGS"
    assert transfer_profile(refs[0][:2], refs, np.ones((3, 5))).refusal == "SIGNATURE_AXIS_MISMATCH"
    assert transfer_profile(np.full((3, 8), np.nan), refs, np.ones((3, 5))).refusal == "NO_QUERY_SIGNATURE"
    q = np.full((3, 8), np.nan)
    q[0] = 1.0
    blind = refs.copy()
    blind[:, 0] = np.nan
    assert transfer_profile(q, blind, np.ones((3, 5))).refusal == "NO_SHARED_CONDITION"
    with pytest.raises(ValueError):
        transfer_profile(refs[0], refs, np.ones((3, 5)), k=0)


def test_selective_r_gives_no_credit_for_the_generic_profile():
    rng = np.random.default_rng(2)
    g, sel = rng.normal(size=300), rng.normal(size=300)
    obs = 2.0 * g + sel
    assert np.isnan(selective_r(3.0 * g, obs, g))
    assert selective_r(sel - 4.0 * g, obs, g) == pytest.approx(1.0)
    assert np.isnan(selective_r(sel[:40], obs[:40], g[:40]))


def _shared_axis_world(seed, n=60, conditions=2, genes=40):
    """References = random strength x one shared direction per condition + a weaker compound-specific part."""
    rng = np.random.default_rng(seed)
    shared = rng.normal(size=(conditions, genes))
    specific = rng.normal(size=(n, conditions, genes))
    strength = rng.uniform(1.0, 6.0, size=n)
    refs = strength[:, None, None] * shared[None] + 0.4 * specific
    return rng, shared, specific, refs


def test_fitted_generic_axes_recover_the_shared_direction():
    _, shared, _, refs = _shared_axis_world(4)
    axes = fit_generic_axes(refs, n_axes=2)
    assert axes.directions.shape == (2, 2, 40) and axes.n_axes == 2
    for o in range(2):
        u = shared[o] / np.linalg.norm(shared[o])
        assert abs(axes.directions[o, 0] @ u) > 0.95
        assert axes.directions[o] @ axes.directions[o].T == pytest.approx(np.eye(2), abs=1e-9)
    cleaned = remove_generic_axes(refs, axes)
    assert np.abs(np.einsum("pog,oag->poa", cleaned, axes.directions)).max() < 1e-9


def test_removing_the_shared_axis_finds_the_compound_specific_neighbour():
    # the true neighbour responds weakly on the shared axis, the query strongly: raw cosine pairs by strength
    rng, shared, specific, refs = _shared_axis_world(5)
    refs[7] = 1.0 * shared + 0.4 * specific[7]
    query = 6.0 * shared + 0.4 * specific[7] + 0.05 * rng.normal(size=shared.shape)
    profiles = np.arange(60, dtype=float)[:, None] * np.ones((60, 3))
    raw = transfer_profile(query, refs, profiles, k=1)
    clean = transfer_profile(query, refs, profiles, k=1, generic_axes=fit_generic_axes(refs, n_axes=1))
    assert raw.neighbours[0] != 7
    assert clean.neighbours[0] == 7 and clean.values == pytest.approx(np.full(3, 7.0))


def test_generic_axes_skip_unmeasured_conditions():
    refs = np.random.default_rng(6).normal(size=(5, 3, 4))
    refs[:, 2] = np.nan
    refs[1:, 1] = np.nan
    axes = fit_generic_axes(refs, n_axes=2)
    assert np.isnan(axes.means[2]).all() and not axes.directions[1:].any()
    q = refs[0].copy()
    out = remove_generic_axes(q, axes)
    assert np.isnan(out[2]).all() and np.isfinite(out[:2]).all()
    with pytest.raises(ValueError):
        fit_generic_axes(refs, n_axes=-1)


def test_generic_axes_report_their_scope_and_refuse_mismatched_axes():
    rng, shared, _, refs = _shared_axis_world(7)
    profiles = rng.normal(size=(60, 4))
    query = refs[3] + 0.1 * rng.normal(size=refs[3].shape)
    assert transfer_profile(query, refs, profiles).scope == VALIDATED_SCOPE
    assert transfer_profile(query, refs, profiles, k=20, generic_axes=fit_generic_axes(refs, 5)).scope == GENERIC_AXES_SCOPE
    assert transfer_profile(query, refs, profiles, k=5, generic_axes=fit_generic_axes(refs, 5)).scope == UNVALIDATED_SCOPE
    other = fit_generic_axes(refs[:, :1], 5)
    assert transfer_profile(query, refs, profiles, k=20, generic_axes=other).refusal == "SIGNATURE_AXIS_MISMATCH"
