"""Transition diagnostics cannot substitute any elimination for a correct elimination."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dyn_model as D  # noqa: E402


SOURCE = ("A549", 24.0, 10000.0)
TARGET = ("A549", 72.0, 10000.0)


@pytest.mark.parametrize("outcome,eliminated", [("eliminate_a", "h1"), ("eliminate_b", "h2")])
def test_directional_elimination_is_never_reported_as_correct(monkeypatch, outcome, eliminated):
    # This context deliberately exposes no held-out truth or target profile: selection may use
    # only the already bought source profile and the training-fitted model/reference tables.
    data = SimpleNamespace(index={SOURCE: {"heldout": 0}}, shift=np.array([[1.0, 0.0, -1.0]]))
    ctx = SimpleNamespace(data=data, ft=SimpleNamespace(fold=1), params={})
    model = SimpleNamespace(predict=lambda arm, y: y)
    monkeypatch.setattr(D.T, "fitted", lambda *args: model)
    monkeypatch.setattr(D, "loo_residuals", lambda *args: np.zeros((1, 3)))
    monkeypatch.setattr(D, "replicate_noise", lambda *args: np.zeros((1, 3)))
    monkeypatch.setattr(D.C, "read_profile", lambda *args: {"outcome": outcome})

    card = D.forecast_card(ctx, "heldout", SOURCE, TARGET, "A", "B", 0.5, np.random.default_rng(0))

    assert card["p_elimination"] == 1.0
    assert card[f"p_eliminate_{eliminated}"] == 1.0
    assert card["p_eliminate_h1"] + card["p_eliminate_h2"] == 1.0
    assert card["counts"][outcome] == D.DRAWS
    assert not card["served"]
    assert card["reason"] == "hypothesis_conditional_forecast_unavailable"
    assert "p_correct" not in card and "p_wrong" not in card
    # In particular, removing A in every draw cannot imply P(correct)=1 when A might be true.
    chosen, note = D.E.select_by_cards([TARGET], {TARGET: card}, "A", "B")
    assert chosen is None
    assert note["reason"] == "no_action_distinguishes_the_contrast"


def test_policy_uses_conditioned_references_and_retains_forecast_refusal(monkeypatch):
    ctx = SimpleNamespace()
    executed = [{"key": SOURCE, "outcome": "ambiguous"}]
    reference_note = {"cards": {D.C.action_id(TARGET): {"served": True, "p_correct": 0.4, "p_wrong": 0.1}}}
    calls = []

    def choose(policy, context, compound, h1, h2, history, rng):
        calls.append((policy, context, compound, h1, h2, history, rng))
        return TARGET, reference_note

    diagnostic = {"served": False, "reason": "hypothesis_conditional_forecast_unavailable",
                  "p_elimination": 1.0, "p_eliminate_h1": 1.0, "p_eliminate_h2": 0.0}
    monkeypatch.setattr(D, "forecast_card", lambda *args: diagnostic)
    monkeypatch.setattr(D.E, "choose", choose)

    chosen, note = D.make_policy({"A549|72": {"threshold": 0.5}})(
        ctx, "heldout", "A", "B", executed, [TARGET])

    assert chosen == TARGET
    assert calls == [("dyn_ref", ctx, "heldout", "A", "B", executed, None)]
    assert note["cards"] == reference_note["cards"]
    assert note["forecast_fallback"] == "dyn_ref"
    assert note["forecast_refusal"] == "hypothesis_conditional_forecast_unavailable"
    assert note["dynamic_forecasts"][D.C.action_id(TARGET)] == diagnostic
