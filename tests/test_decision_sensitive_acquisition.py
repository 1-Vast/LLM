"""Decision-sensitive acquisition values terminal decisions, not forecast spread."""
from __future__ import annotations

import pytest

from maestro.acquisition import (
    OutcomeBranch,
    OutcomeForecast,
    decision_sensitivity,
    expected_terminal_decision_value,
    select_decision_sensitive_action,
)
from maestro.models import EvidenceAction, FunctionalInterventionProfile
from maestro.handoff import PolicyInput


def _forecast(identifier: str, h1: dict[str, float], h2: dict[str, float]) -> OutcomeForecast:
    return OutcomeForecast(
        identifier,
        (OutcomeBranch("H1", h1, 10), OutcomeBranch("H2", h2, 10)),
        basis="fixture",
    )


def test_uncertain_reading_with_no_terminal_effect_has_zero_value():
    forecast = _forecast("unhelpful", {"neutral": 0.5, "other": 0.5}, {"neutral": 0.5, "other": 0.5})
    consequences = {"neutral": frozenset(), "other": frozenset()}
    value = expected_terminal_decision_value({"H1", "H2"}, forecast, consequences)
    assert value.expected_value == 0.0
    assert value.decision_sensitivity == 0.0


def test_rule_conditioned_reading_changes_the_terminal_decision():
    forecast = _forecast("separating", {"supports_h1": 1.0}, {"supports_h2": 1.0})
    consequences = {"supports_h1": frozenset({"H2"}), "supports_h2": frozenset({"H1"})}
    value = expected_terminal_decision_value({"H1", "H2"}, forecast, consequences, measurement_cost=0.25)
    assert value.expected_value == 1.0
    assert value.decision_sensitivity == 1.0
    assert value.net_value == 0.75


def test_selector_chooses_decision_sensitive_action_after_cost():
    actions = (
        EvidenceAction("unhelpful", "No decision effect", 0.1, ("H1", "H2")),
        EvidenceAction("separating", "Separates hypotheses", 0.25, ("H1", "H2")),
    )
    forecasts = {
        "unhelpful": _forecast("unhelpful", {"neutral": 1.0}, {"neutral": 1.0}),
        "separating": _forecast("separating", {"supports_h1": 1.0}, {"supports_h2": 1.0}),
    }
    consequences = {
        "neutral": frozenset(), "supports_h1": frozenset({"H2"}), "supports_h2": frozenset({"H1"})
    }
    plan = select_decision_sensitive_action(
        frozenset({"H1", "H2"}), actions, FunctionalInterventionProfile("small_molecule"), 1.0,
        forecasts, consequences,
    )
    assert plan.status == "selected"
    assert plan.chosen is not None and plan.chosen.action_identifier == "separating"


def test_selector_can_keep_assay_days_as_budget_cost_and_use_utility_price():
    action = EvidenceAction("separating", "Separates hypotheses", 6.0, ("H1", "H2"))
    forecast = {"separating": _forecast("separating", {"supports_h1": 1.0}, {"supports_h2": 1.0})}
    plan = select_decision_sensitive_action(
        frozenset({"H1", "H2"}), (action,), FunctionalInterventionProfile("small_molecule"), 6.0,
        forecast, {"supports_h1": frozenset({"H2"}), "supports_h2": frozenset({"H1"})},
        measurement_costs={"separating": 0.25},
    )
    assert plan.chosen is not None and plan.chosen.cost == 0.25


def test_policy_input_has_only_public_prediction_state():
    action = EvidenceAction("a", "A", 1.0, ("H1", "H2"))
    view = PolicyInput(
        visible_evidence=("observed",), legal_actions=(action,), budget=1.0,
        calibrated_action_distributions={"a": {"neutral": 1.0}}, provenance={"model": "fixture"},
    )
    assert view.action_ids == ("a",)
    assert not hasattr(view, "hidden_truth")
    assert not hasattr(view, "mechanism_annotation")


def test_policy_input_rejects_evaluator_fields_even_when_constructed_directly():
    with pytest.raises(ValueError, match="evaluator-only"):
        PolicyInput(visible_evidence=({"truth": "H1"},), budget=1.0)
