"""Belief-space planning values terminal decisions coherently and keeps forecasts out of evidence."""
from __future__ import annotations

import pytest

from maestro.acquisition import OutcomeBranch, OutcomeForecast, expected_terminal_decision_value
from maestro.models import EvidenceAction
from maestro.planning import plan_measurement, update_belief

M1, M2, U, A = "matches_h1", "matches_h2", "unresolved", "absent"
RULES = {M1: frozenset({"H2"}), M2: frozenset({"H1"}), U: frozenset(), A: frozenset()}


def _action(name, cost=1.0, time=24.0):
    return EvidenceAction(name, name, cost, ("H1", "H2"), time_hours=time)


def _forecast(name, h1, h2, support=50):
    return OutcomeForecast(name, (OutcomeBranch("H1", h1, support), OutcomeBranch("H2", h2, support)), basis="fixture")


def _legal(actions, horizon=2):
    def legal(history):
        done = {a for a, _ in history}
        return () if len(history) >= horizon else tuple(a for a in actions if a.identifier not in done)
    return legal


def test_decision_value_keeps_the_wrong_elimination_risk_of_a_noisy_reading():
    # 80% of H1 compounds read as H1 and 20% as H2: a single-survivor reading is wrong 20% of the time
    forecast = _forecast("noisy", {M1: 0.8, M2: 0.2}, {M2: 0.8, M1: 0.2})
    value = expected_terminal_decision_value({"H1", "H2"}, forecast, RULES)
    assert value.expected_wrong_decision == pytest.approx(0.2)
    assert value.expected_loss_after == pytest.approx(2.0 * 0.2)


def test_planner_scores_an_elimination_by_the_posterior_mass_it_removes():
    act = _action("a")
    f = _forecast("a", {M1: 0.8, M2: 0.2}, {M2: 0.8, M1: 0.2})
    plan = plan_measurement(("H1", "H2"), None, _legal([act], 1), lambda a, h: f, RULES, horizon=1)
    assert plan.chosen == "a"
    assert plan.value.p_correct == pytest.approx(0.8)
    assert plan.value.p_wrong == pytest.approx(0.2)
    assert plan.value.utility == pytest.approx(0.8 - 2 * 0.2)


def test_a_reading_that_cannot_change_the_decision_has_no_value_and_the_agent_stops():
    act = _action("flat")
    f = _forecast("flat", {U: 0.5, A: 0.5}, {U: 0.5, A: 0.5})
    plan = plan_measurement(("H1", "H2"), None, _legal([act]), lambda a, h: f, RULES, horizon=2, price=0.01)
    assert plan.chosen is None and plan.reason == "no_positive_value"


def test_lookahead_values_a_measurement_by_what_it_enables_next():
    # "probe" decides nothing itself but tells which of two follow-ups separates the hypotheses
    probe, left, right = _action("probe"), _action("left"), _action("right")

    def forecast(action, history):
        seen = dict(history).get("probe")
        if action.identifier == "probe":
            return _forecast("probe", {U: 0.5, A: 0.5}, {U: 0.5, A: 0.5})
        good = (seen == U and action.identifier == "left") or (seen == A and action.identifier == "right")
        if good:
            return _forecast(action.identifier, {M1: 1.0}, {M2: 1.0})
        return _forecast(action.identifier, {U: 1.0}, {U: 1.0})

    myopic = plan_measurement(("H1", "H2"), None, _legal([probe, left, right]), forecast, RULES, horizon=1)
    deep = plan_measurement(("H1", "H2"), None, _legal([probe, left, right]), forecast, RULES, horizon=2)
    assert myopic.chosen is None
    assert deep.chosen == "probe"
    assert deep.contingent == {U: "left", A: "right"}
    assert deep.value.p_correct == pytest.approx(1.0)


def test_belief_moves_only_by_bayes_rule_on_a_real_reading():
    f = _forecast("a", {U: 0.9, A: 0.1}, {U: 0.3, A: 0.7})
    b = update_belief({"H1": 0.5, "H2": 0.5}, f, U)
    assert b["H1"] == pytest.approx(0.45 / 0.6)
    assert update_belief(b, f, "a_label_nobody_forecast") == b


def test_a_refused_forecast_is_named_and_not_valued():
    good, bad = _action("good"), _action("bad")

    def forecast(action, history):
        if action.identifier == "bad":
            return OutcomeForecast("bad", refusal="outside_applicability_domain")
        return _forecast("good", {M1: 0.6, U: 0.4}, {M2: 0.6, U: 0.4})

    plan = plan_measurement(("H1", "H2"), None, _legal([good, bad], 1), forecast, RULES, horizon=1)
    assert plan.chosen == "good"
    assert plan.refusals == {"bad": "outside_applicability_domain"}
    only_bad = plan_measurement(("H1", "H2"), None, _legal([bad], 1), forecast, RULES, horizon=1)
    assert only_bad.chosen is None and only_bad.reason == "world_model_refused"


def test_baseline_anchor_keeps_the_expert_action_unless_the_gain_is_supported():
    expert, other = _action("expert"), _action("other")
    thin = {"expert": _forecast("expert", {M1: 0.5, A: 0.5}, {M2: 0.5, A: 0.5}, support=3),
            "other": _forecast("other", {M1: 0.6, A: 0.4}, {M2: 0.6, A: 0.4}, support=3)}
    plan = plan_measurement(("H1", "H2"), None, _legal([expert, other], 1), lambda a, h: thin[a.identifier], RULES,
                            horizon=1, baseline="expert", deviation_z=1.645)
    assert plan.chosen == "expert" and plan.anchor == "baseline_kept"
    rich = {k: _forecast(k, dict(v.branches[0].probabilities), dict(v.branches[1].probabilities), support=5000)
            for k, v in thin.items()}
    plan = plan_measurement(("H1", "H2"), None, _legal([expert, other], 1), lambda a, h: rich[a.identifier], RULES,
                            horizon=1, baseline="expert", deviation_z=1.645)
    assert plan.chosen == "other" and plan.anchor == "deviation_supported"


def test_wrong_risk_cap_stops_by_name_when_no_plan_is_within_it():
    act = _action("risky")
    f = _forecast("risky", {M1: 0.7, M2: 0.3}, {M2: 0.7, M1: 0.3}, support=10)
    plan = plan_measurement(("H1", "H2"), None, _legal([act], 1), lambda a, h: f, RULES, horizon=1, wrong_risk_cap=0.05)
    assert plan.chosen is None and plan.reason == "wrong_risk_cap"


def test_invalid_inputs_are_refused():
    act = _action("a")
    f = _forecast("a", {M1: 1.0}, {M2: 1.0})
    with pytest.raises(ValueError):
        plan_measurement(("H1",), None, _legal([act]), lambda a, h: f, RULES, horizon=1)
    with pytest.raises(ValueError):
        plan_measurement(("H1", "H2"), {"H1": -1.0, "H2": 2.0}, _legal([act]), lambda a, h: f, RULES, horizon=1)
    with pytest.raises(ValueError):
        plan_measurement(("H1", "H2"), None, _legal([act]), lambda a, h: f, RULES, horizon=1, wrong_risk_cap=1.5)
