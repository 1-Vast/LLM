"""Fast checks of the study's pure components (no PRISM data needed).

File summary
- Path: research/program_revision_20261017/test_science.py
- Purpose: the endpoint, the state grammar, identifiability, loading recovery, tie-breaking and
  readout accounting behave as PROTOCOL.md says. Run: ``python -m pytest -q test_science.py``
  from this folder.
"""
from __future__ import annotations

import numpy as np

from common import qualified_hits
from revise import identifiable
from vc import Program, ProgramLibrary, atoms, hit_probability, is_binary, parse_state, state_text, top_k


def test_endpoint_unknown_needs_both_replicates_missing_and_relative_threshold():
    neutral = [0.0, 0.1, -0.1, 0.0, 0.05]
    X2 = np.array([[-2.0, np.nan, np.nan, -2.0] + neutral, [0.1] * 9])
    X3 = np.array([[-2.2, -1.8, np.nan, 0.5] + neutral, [0.0] * 9])
    hit, known = qualified_hits(X2, X3)
    assert known[0, :4].tolist() == [True, True, False, True] and known[1].all()
    # a positive replicate disqualifies; a single replicate is enough; unknown is never a hit
    assert hit[0, :4].tolist() == [True, True, False, False] and not hit[0, 4:].any()
    assert not hit[1].any()


def test_relative_threshold_excludes_generically_toxic_drug():
    X = np.full((1, 6), -3.0)
    hit, _ = qualified_hits(X, X)
    assert not hit.any()  # every line equals the drug median: not context-specific


def test_state_grammar_round_trip_and_types():
    for text in ("mut:BRAF", "and(mut:KRAS,mut:TP53)", "andnot(mut:BRAF,mut:PTEN)", "mul(probe:X,mut:TP53)", "b"):
        tree = parse_state(text)
        assert state_text(tree) == text
    assert is_binary(parse_state("andnot(mut:A,lin:lung)"))
    assert not is_binary(parse_state("mul(b,mut:A)"))
    assert len(atoms(parse_state("and(mut:A,and(mut:B,mut:C))"))) == 3


def test_crossed_design_interaction_is_not_identifiable():
    rng = np.random.default_rng(0)
    obs = rng.random((200, 80)) < 0.85
    scope = rng.random(200) < 0.1
    gate = rng.random(80) < 0.3
    assert identifiable(obs, scope, gate)
    crossed = obs & (np.outer(scope, gate) | np.outer(~scope, ~gate))
    assert not identifiable(crossed, scope, gate)


def test_library_recovers_planted_shared_loading_and_novel_drugs_use_it():
    rng = np.random.default_rng(1)
    D, L = 40, 120
    dfeat = {"moa_tokens": [["MEK inhibitor"] if d < 10 else ["other"] for d in range(D)], "target_tokens": [[] for _ in range(D)]}
    g = (rng.random(L) < 0.3).astype(float)
    R = rng.normal(0, 0.3, (D, L))
    R[:10] += -1.5 * (g - g.mean())[None, :]
    lib = ProgramLibrary([Program("moa:MEK inhibitor", "mut:G")])
    lib.fit(R, g[:, None], dfeat, np.arange(D))
    assert lib.beta[0] < -0.5
    corr = lib.correction(np.array([[1.0], [0.0]]), dfeat, np.arange(D), novel=True)
    assert np.all(corr[:10, 0] < corr[:10, 1]) and np.allclose(corr[10:], 0.0)


def test_ties_are_broken_by_fixed_hashed_order_not_index():
    score = np.zeros((5, 1))
    tie = np.array([0.9, 0.1, 0.5, 0.3, 0.7])
    assert top_k(score, 2, tie)[:, 0].tolist() == [1, 3]


def test_hit_probability_is_monotone_in_mean():
    p = hit_probability(np.array([[-3.0], [-1.0], [0.0]]), np.ones((3, 1)), np.full((3, 1), -1.0))
    assert p[0, 0] > p[1, 0] > p[2, 0]
