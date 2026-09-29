"""Tests for the in-context world model: transitions, metrics, prompt availability and exact nesting.

File summary
- Path: research/incontext_world/test_incontext_world.py
- Purpose: pin the properties the E-WM1/E-WM2 claims rest on.
- Core points:
  - The ridge transition recovers a low-rank map that additive and mean baselines cannot.
  - Metrics: discrimination is 1 for a perfect predictor and about 0 for a shuffled one;
    `projected_cosine` equals the validator's own projected similarity.
  - With kappa 0, no prompt, or the target's own condition offered as a prompt, the in-context
    world returns exactly the reference world's forecast. With a real prompt it moves and stays a
    distribution.
  - Everything the world model fits comes from the public view: no transition contains a held-out
    compound.
- Interfaces: pytest tests
- Depends on: transition.py, metrics.py, world.py, research/protocol_v2 (L1000 T fold 1 fixture)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from research.incontext_world import metrics as M  # noqa: E402
from research.incontext_world import transition as TR  # noqa: E402


def _synthetic(seed=0, n=80, d=120):
    rng = np.random.default_rng(seed)
    A, B = rng.normal(size=(3, d)), rng.normal(size=(3, d))
    Z = rng.normal(size=(n, 3))
    X = Z @ A + 0.05 * rng.normal(size=(n, d)) + 0.7
    Y = Z @ B + 0.05 * rng.normal(size=(n, d)) - 0.3
    z = rng.normal(size=(12, 3))
    return X, Y, z @ A + 0.7, z @ B - 0.3


def test_ridge_transition_recovers_a_low_rank_map():
    X, Y, x, y = _synthetic()
    tr = TR.fit("p", "c", [str(i) for i in range(len(X))], X, Y, np.zeros(Y.shape[1]))
    score = {arm: np.mean([M.centred_cosine(tr.predict(a, arm), b, tr.mean_target) for a, b in zip(x, y)])
             for arm in TR.ARMS}
    assert score["ridge_st"] > 0.95
    assert all(score["ridge_st"] > score[arm] + 0.3 for arm in TR.BASELINES)
    loo = tr.loo_predictions()
    assert loo.shape == Y.shape
    assert np.mean((loo - Y) ** 2) >= np.mean((tr.mean_target + tr.fitted - Y) ** 2)


def test_transition_with_too_few_references_falls_back_to_the_context_mean():
    X, Y, x, _ = _synthetic(n=2)
    tr = TR.fit("p", "c", ["a", "b"], X, Y, np.zeros(Y.shape[1]))
    assert tr.k == 0
    assert np.allclose(tr.predict(x[0]), Y.mean(0))


def test_discrimination_and_auroc_bounds():
    rng = np.random.default_rng(1)
    truth = rng.normal(size=(30, 50))
    assert np.allclose(M.discrimination(truth, truth), 1.0)
    shuffled = np.mean([M.discrimination(truth[rng.permutation(30)], truth).mean() for _ in range(50)])
    assert abs(shuffled) < 0.1
    assert M.effect_auroc([3, 2, 1, 0], [1, 1, 0, 0]) == 1.0
    assert M.effect_auroc([1, 1], [1, 0]) == 0.5
    assert M.pearson_delta(np.zeros(5), truth[0, :5]) == 0.0


def test_projected_cosine_matches_the_validator_geometry():
    from research.dynamic_world_model import common as C
    rng = np.random.default_rng(2)
    Y = rng.normal(size=(15, 40)) + 0.5
    G = Y @ Y.T
    S = Y.sum(0)
    table = C.ConditionTable(("L", 24.0, 1.0), [f"c{i}" for i in range(15)], np.array(["a"] * 8 + ["b"] * 7, dtype=object),
                             np.ones(15, bool), Y, G, G.sum(1), float(G.sum(1).sum()), S)
    y = rng.normal(size=40)
    scores = C.heldout_class_scores(table, y, ("a", "b"))
    cos = M.projected_cosine(Y, y)
    assert np.isclose(cos[:8].max(), scores[0]) and np.isclose(cos[8:].max(), scores[1])


@pytest.fixture(scope="module")
def l1000_t1():
    from research.belief_planning import arms as BA
    from research.incontext_world import world as IW
    from research.protocol_v2 import contracts as K
    from research.protocol_v2 import tasks_v21 as TV
    data, real_ctx, setting, design = TV.load("l1000", "T", 1)
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    heldout = set(comp.index[comp.fold == 1])
    training = TV.training_compounds(real_ctx, 1)
    view = K.public_view(real_ctx, heldout, training_compounds=training, design=design)
    reference = BA.world_for(view, "on", "true")
    fp, pos = view.extra["fingerprints"]
    public = view.data.compounds.drop_duplicates("compound").set_index("compound")
    groups = {c: g for c, g in public["component"].items() if isinstance(g, str)}
    common = dict(fingerprints=fp, positions=pos, vc="on", feedback="true", hyperparameters=reference.hyperparameters,
                  groups=groups)
    auto = IW.InContextWorld(view.ft, view.params, training, source="auto", **common)
    episodes = TV.episode_list(real_ctx, 1)
    return {"real": real_ctx, "view": view, "reference": reference, "auto": auto, "common": common,
            "training": training, "heldout": heldout, "episodes": episodes, "IW": IW, "K": K}


def _episode_with_prompt(fx):
    from research.belief_planning import world as W
    E = fx["K"].T.E
    for compound, truth, decoy, h1, h2 in fx["episodes"]:
        keys = sorted(fx["view"].data.availability[compound])
        results = {k: E.execute(fx["real"], compound, k, h1, h2) for k in keys}
        prompts = [k for k in keys if results[k]["qc"] and W.label_of(results[k]["outcome"]) in (W.UNRESOLVED, W.ABSENT)]
        if prompts and len(keys) > 1:
            p = prompts[0]
            target = next(k for k in keys if k != p)
            shift = fx["real"].data.shift[results[p]["row"]]
            return compound, h1, h2, p, W.label_of(results[p]["outcome"]), target, shift
    pytest.skip("no episode with a non-eliminating prompt")


def test_incontext_nests_the_reference_world_exactly(l1000_t1):
    fx = l1000_t1
    IW = fx["IW"]
    compound, h1, h2, p, label, target, shift = _episode_with_prompt(fx)
    history = ((p, label),)
    reference = fx["reference"].forecast(target, h1, h2, compound, history)
    off = IW.InContextWorld(fx["view"].ft, fx["view"].params, fx["training"], source="prompt",
                            incontext={"source": "prompt", "kappa": 0.0, "tau": 4.0}, **fx["common"])
    on = IW.InContextWorld(fx["view"].ft, fx["view"].params, fx["training"], source="prompt",
                           incontext={"source": "prompt", "kappa": 8.0, "tau": 4.0}, **fx["common"])

    def probs(f):
        return [f.branch_for(h).probabilities for h in (h1, h2)]

    assert probs(off.forecast(target, h1, h2, compound, history, profiles={p: shift})) == probs(reference)
    assert probs(on.forecast(target, h1, h2, compound, history)) == probs(reference)
    # the target's own shift is never a prompt
    assert probs(on.forecast(target, h1, h2, compound, history, profiles={target: shift})) == probs(reference)
    moved = on.forecast(target, h1, h2, compound, history, profiles={p: shift})
    assert moved.model_version == IW.MODEL_VERSION and "incontext[prompt" in moved.basis
    assert probs(moved) != probs(reference)
    for branch in moved.branches:
        assert abs(sum(branch.probabilities.values()) - 1.0) < 1e-9
        assert min(branch.probabilities.values()) >= 0.0


def test_world_model_fits_only_public_training_references(l1000_t1):
    fx = l1000_t1
    auto = fx["auto"]
    compound, h1, h2, p, label, target, shift = _episode_with_prompt(fx)
    for source in ("prompt", "transfer"):
        world = fx["IW"].InContextWorld(fx["view"].ft, fx["view"].params, fx["training"], source=source,
                                        incontext={"source": source, "kappa": 1.0, "tau": 4.0}, **fx["common"])
        world.forecast(target, h1, h2, compound, ((p, label),), profiles={p: shift})
        for tr in world._transitions.values():
            assert not set(tr.names) & fx["heldout"]
    for tr in auto._transitions.values():
        assert not set(tr.names) & fx["heldout"]
    assert fx["K"].public_view_problems(fx["view"], fx["heldout"]) == []
    fitted = auto.incontext
    if fitted["source"] != "off":
        restricted = fx["IW"].restrict(fitted, fitted["source"])
        assert (restricted["kappa"], restricted["tau"]) == (fitted["kappa"], fitted["tau"])
