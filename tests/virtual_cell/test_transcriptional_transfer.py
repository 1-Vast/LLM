"""Contract tests for transcriptional transfer of viability profiles (src/virtual_cell/transcriptional_transfer.py)."""
from __future__ import annotations

import numpy as np
import pytest

from virtual_cell.transcriptional_transfer import (VALIDATED_SCOPE, selective_r, signature_similarity,
                                                   transfer_profile)


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
