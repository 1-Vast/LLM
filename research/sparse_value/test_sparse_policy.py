"""Net measurement value, honest unknown stops, replanning, and evidence boundaries."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import policy as Q  # noqa: E402
import model as M  # noqa: E402
from test_sparse_model import make_model  # noqa: E402

EARLY = ("A549", 6.0, 10000.0)
LATE = ("A549", 24.0, 10000.0)
OTHER = ("MCF7", 24.0, 10000.0)
SETTING = Q.P.Setting("test", (EARLY, LATE, OTHER), (EARLY, LATE), lambda key: 1.0, 2.0)


def forecast(*, correct=0.0, wrong=0.0, absent=0.0, h1_absent=None, h2_absent=None):
    branches = {}
    for own, good, bad, absent_override in (("H1", 0, 1, h1_absent), ("H2", 1, 0, h2_absent)):
        p_absent = absent if absent_override is None else absent_override
        probs = {M.LABELS[good]: correct, M.LABELS[bad]: wrong, M.LABELS[3]: p_absent,
                 M.LABELS[2]: 1 - correct - wrong - p_absent}
        branches[own] = SimpleNamespace(probabilities=probs, p_correct=correct, p_wrong=wrong,
                                       value_variance=0.01, wrong_upper95=wrong + 0.02,
                                       local_support=10, parent_support=10, basis="test", prior_strength=2.0)
    return M.Forecast(branches)


def history(outcome="undetected", *, first=EARLY):
    return [{"key": first, "action": Q.P.C.action_id(first), "outcome": outcome,
             "qc": outcome != "quality_failed"}]


def test_missing_pairs_can_buy_target_supported_value_when_price_is_low(monkeypatch):
    rows = [(f"{h}_{i}", h, "ambiguous", "eliminate_b") for h in ("H1", "H2") for i in range(12)]
    model = make_model(monkeypatch, rows)
    action, note = Q.choose(model, [LATE], "H1", "H2", history(), 1.0, SETTING, 0.02)
    assert action == LATE
    assert note["expected_net"] > 0
    assert all(branch["basis"] == "marginal_backoff" and branch["local_support"] == 0
               for branch in note["prediction_by_hypothesis"].values())


def test_same_small_gain_is_bought_at_low_price_and_stopped_at_high_price():
    model = SimpleNamespace(forecast=lambda *a, **kw: forecast(correct=0.04, wrong=0.005, absent=0.8))
    cheap, _ = Q.choose(model, [LATE], "H1", "H2", history(), 1.0, SETTING, 0.01)
    costly, note = Q.choose(model, [LATE], "H1", "H2", history(), 1.0, SETTING, 0.05)
    assert cheap == LATE and costly is None
    assert note["reason"] == "estimated_net_non_positive"


def test_wrong_risk_stops_even_with_zero_measurement_price():
    model = SimpleNamespace(forecast=lambda *a, **kw: forecast(correct=0.1, wrong=0.3, absent=0.5))
    action, note = Q.choose(model, [LATE], "H1", "H2", history(), 1.0, SETTING, 0.0)
    assert action is None and note["reason"] == "estimated_net_non_positive"


def test_two_step_cost_weights_both_mutually_exclusive_branches():
    def predict(target, *args, source=None, observed_label=None):
        if source is not None:
            return forecast(correct=1.0)
        return forecast(correct=0.2, wrong=0.1, absent=0.3) if target == EARLY else forecast(absent=1.0)

    action, note = Q.choose(SimpleNamespace(forecast=predict), [EARLY, LATE], "H1", "H2", [], 2.0, SETTING, 0.1)
    assert action == EARLY
    # Immediate elimination mass .3; absence .3 and unresolved .4 each buy one tail.
    assert note["expected_measurements"] == pytest.approx(1.7)
    assert note["expected_terminal_correct"] == pytest.approx(0.9)
    assert note["expected_terminal_wrong"] == pytest.approx(0.1)
    assert note["expected_net"] == pytest.approx(0.9 - 2 * 0.1 - 0.1 * 1.7)
    assert len(note["planned_followups"]) == 2


def test_replans_after_actual_fallback_action_without_an_initial_plan():
    queries = []

    def predict(target, *args, source=None, observed_label=None):
        queries.append((target, source, observed_label))
        return forecast(correct=0.8, absent=0.2) if source else forecast(absent=1.0)

    action, note = Q.choose(SimpleNamespace(forecast=predict), [LATE], "H1", "H2", history(), 1.0, SETTING, 0.02)
    assert action == LATE
    assert (LATE, EARLY, M.LABELS[3]) in queries
    assert note["after"] == M.LABELS[3]


def test_unknown_action_prevents_calling_mixed_menu_an_informed_stop():
    def predict(target, *args, **kwargs):
        return M.Forecast({}, "no_target_references:H1") if target == OTHER else forecast(absent=1.0)

    action, note = Q.choose(SimpleNamespace(forecast=predict), [LATE, OTHER], "H1", "H2", history(), 1.0, SETTING, 0.02)
    assert action is None and note["reason"] == "value_unknown"
    assert Q.P.C.action_id(OTHER) in note["unknown_forecasts"]


def test_absence_updates_planning_weights_without_updating_evidence():
    def predict(target, *args, **kwargs):
        return forecast(h1_absent=0.9, h2_absent=0.1) if target == EARLY else forecast(correct=0.7)

    model = SimpleNamespace(forecast=predict)
    ctx = SimpleNamespace(extra={"sparse_value_models": {(True, False): model}}, params={"eliminates": True})
    contrast = Q.P.E.contrast_for("H1", "H2", [Q.P.make_action(k, "H1", "H2", SETTING) for k in (EARLY, LATE)])
    state = Q.P.EvidenceState.open(contrast.hypotheses)
    before = state
    action, note = Q.make_policy(0.02)(ctx, "withheld", "H1", "H2", history(), [LATE], 1.0, SETTING, state)
    assert action == LATE
    assert note["planning_hypothesis_weights"] == pytest.approx({"H1": 0.9, "H2": 0.1})
    assert state == before and state.candidates == frozenset({"H1", "H2"}) and not state.updates


def test_disabled_validator_does_not_buy_elimination_from_prior_pseudocounts():
    model = SimpleNamespace(forecast=lambda *a, **kw: forecast(correct=1.0))
    ctx = SimpleNamespace(extra={"sparse_value_models": {(True, False): model}}, params={"eliminates": False})
    action, note = Q.make_policy(0.0)(ctx, "withheld", "H1", "H2", [], [EARLY], 2.0, SETTING, None)
    assert action is None
    assert "validator" in note["reason"]
