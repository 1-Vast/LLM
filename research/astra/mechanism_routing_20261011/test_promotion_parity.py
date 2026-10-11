"""Post-freeze promotion parity: src/virtual_cell/transcriptional_transfer.py reproduces the frozen arithmetic.

The frozen study computes similarity and transfer in ``predictors.World.l1000_sim`` / ``knn``.
* On complete profiles the promoted code must match them exactly.
* With missing reference values the promoted code skips them, while the frozen kNN read them as
  zero with full weight. On the confirmation killers that changes mean selective r by at most
  0.001 (``posthoc/missing_value_rule.json``).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import predictors as PR  # noqa: E402
from virtual_cell.transcriptional_transfer import selective_r, signature_similarity, transfer_profile  # noqa: E402


def _world(rng, n=40, options=6, genes=20, lines=60, missing_options=0.2):
    X = rng.normal(size=(n, options, genes))
    X[rng.random((n, options)) < missing_options] = np.nan
    w = object.__new__(PR.World)  # only the arrays the frozen methods read
    w.l1000_have = np.isfinite(X[..., 0])
    w.Xf = np.nan_to_num(X)
    w.l1000_norm = np.linalg.norm(w.Xf, axis=2)
    w.P = rng.normal(size=(n, lines))
    return w, X


@pytest.mark.parametrize("seed", range(5))
def test_promoted_transfer_matches_the_frozen_virtual_cell(seed):
    rng = np.random.default_rng(seed)
    w, X = _world(rng)
    pool = np.arange(1, len(X))
    frozen_sim = w.l1000_sim(0, pool)
    assert np.allclose(signature_similarity(X[0], X[pool]), frozen_sim, atol=1e-12, equal_nan=True)
    frozen = w.knn(frozen_sim, pool)
    promoted = transfer_profile(X[0], X[pool], w.P[pool], k=PR.K)
    assert np.allclose(promoted.values, frozen, atol=1e-12)


def test_promoted_selective_r_matches_the_frozen_score():
    rng = np.random.default_rng(7)
    g, a, b = rng.normal(size=(3, 578))
    b[rng.random(578) < 0.03] = np.nan
    assert selective_r(a + g, b, g) == pytest.approx(PR.selective_r(a + g, b, g), abs=1e-12)


def test_missing_value_rule_effect_is_recorded_and_negligible():
    rec = json.loads((HERE / "posthoc" / "missing_value_rule.json").read_text(encoding="utf-8"))
    for key in ("known_class", "novel_class", "own160"):
        assert abs(rec[key]["skip_minus_frozen"]) < 0.002
