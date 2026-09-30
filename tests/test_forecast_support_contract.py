"""The optional support rule is planning-only and falls back to defer."""
from copy import deepcopy

import pytest

from research.dual_core_live.live_api import validate_proposal
from research.dual_core_live.support_contract import (
    FORECAST_SUPPORT_CONTRACT, gate_supported_proposal, support_violations,
)


def card():
    return {"remaining_budget": 3, "qualified_prerequisites": [], "attempted_actions": [],
            "actions": [{"id": "measure", "cost": 2, "forecast_available": True,
                         "one_step_net_utility": 0.1}], "evidence": [], "forecasts": []}


PROPOSAL = {"action": "measure", "terminal_authorized": False}


@pytest.mark.parametrize("value,reason", [
    (None, "forecast_utility_invalid"), ("0.1", "forecast_utility_invalid"),
    (True, "forecast_utility_invalid"), (float("nan"), "forecast_utility_nonfinite"),
    (float("inf"), "forecast_utility_nonfinite"),
    (-float("inf"), "forecast_utility_nonfinite"),
    (10 ** 1000, "forecast_utility_nonfinite"),
    (0, "forecast_utility_nonpositive"), (-0.1, "forecast_utility_nonpositive"),
])
def test_invalid_or_nonpositive_forecast_defers_without_replacement(value, reason):
    state = card()
    state["actions"][0]["one_step_net_utility"] = value
    state["actions"].append({"id": "better", "cost": 1, "forecast_available": True,
                             "one_step_net_utility": 0.8})
    assert support_violations(state, PROPOSAL, FORECAST_SUPPORT_CONTRACT) == (reason,)
    result = gate_supported_proposal(state, PROPOSAL, FORECAST_SUPPORT_CONTRACT)
    assert result == {"accepted": False, "action": "defer", "reason": "forecast_support_refusal",
                      "violations": (reason,)}


@pytest.mark.parametrize("available", [None, False, 1, "true"])
def test_available_forecast_must_be_explicitly_true(available):
    state = card()
    state["actions"][0]["forecast_available"] = available
    assert support_violations(state, PROPOSAL, FORECAST_SUPPORT_CONTRACT) == ("forecast_unavailable",)


def test_missing_forecast_fields_report_without_guessing():
    state = card()
    del state["actions"][0]["forecast_available"]
    del state["actions"][0]["one_step_net_utility"]
    assert support_violations(state, PROPOSAL, FORECAST_SUPPORT_CONTRACT) == (
        "forecast_unavailable", "forecast_utility_missing")
    assert gate_supported_proposal(state, PROPOSAL, FORECAST_SUPPORT_CONTRACT)["action"] == "defer"


def test_no_explicit_contract_preserves_legal_no_forecast_planning():
    state = card()
    del state["actions"][0]["forecast_available"]
    del state["actions"][0]["one_step_net_utility"]
    assert support_violations(state, PROPOSAL) == ()
    result = gate_supported_proposal(state, PROPOSAL)
    assert {key: result[key] for key in ("accepted", "action", "reason")} == validate_proposal(state, PROPOSAL)
    assert result["accepted"] and result["action"] == "measure"
    bad = {"action": "new", "terminal_authorized": False}
    assert gate_supported_proposal(state, bad)["action"] is None


@pytest.mark.parametrize("blocked", ["budget", "attempted", "prerequisite"])
def test_a_positive_forecast_does_not_override_action_legality(blocked):
    state = card()
    if blocked == "budget":
        state["remaining_budget"] = 1
    elif blocked == "attempted":
        state["attempted_actions"] = ["measure"]
    else:
        state["actions"][0]["prerequisites"] = ["qualified_measurement"]
        state["forecasts"] = [{"supplies": ["qualified_measurement"]}]
    assert support_violations(state, PROPOSAL, FORECAST_SUPPORT_CONTRACT) == ("action_not_currently_legal",)
    assert gate_supported_proposal(state, PROPOSAL, FORECAST_SUPPORT_CONTRACT)["action"] == "defer"


@pytest.mark.parametrize("value", [0.1, 1])
def test_supported_positive_action_passes_without_ranking_or_mutation(value):
    state = card()
    state["actions"][0]["one_step_net_utility"] = value
    state["actions"].append({"id": "higher", "cost": 1, "forecast_available": True,
                             "one_step_net_utility": 2})
    proposal, contract = deepcopy(PROPOSAL), deepcopy(FORECAST_SUPPORT_CONTRACT)
    before = deepcopy((state, proposal, contract))
    assert support_violations(state, proposal, contract) == ()
    result = gate_supported_proposal(state, proposal, contract)
    assert result["accepted"] and result["action"] == "measure"
    assert (state, proposal, contract) == before
    assert state["evidence"] == []


def test_explicit_defer_needs_no_forecast_and_grants_no_terminal_authority():
    state = card()
    state["actions"] = []
    proposal = {"action": "defer", "terminal_authorized": False}
    assert gate_supported_proposal(state, proposal, FORECAST_SUPPORT_CONTRACT)["accepted"]
    proposal["terminal_authorized"] = True
    assert support_violations(state, proposal, FORECAST_SUPPORT_CONTRACT) == ("proposal_cannot_authorize_terminal",)
    result = gate_supported_proposal(state, proposal, FORECAST_SUPPORT_CONTRACT)
    assert not result["accepted"] and result["action"] == "defer"


@pytest.mark.parametrize("proposal", ["measure", {}, {"action": "measure"}])
def test_malformed_proposal_cannot_be_made_valid_by_support(proposal):
    result = gate_supported_proposal(card(), proposal, FORECAST_SUPPORT_CONTRACT)
    assert not result["accepted"] and result["action"] == "defer" and result["violations"]


@pytest.mark.parametrize("contract", [
    {"forecast_required": True}, {"forecast_required": 1, "fallback": "defer"},
    {"forecast_required": True, "fallback": "optimal"},
])
def test_an_unrecognized_contract_does_not_guess_a_fallback(contract):
    result = gate_supported_proposal(card(), PROPOSAL, contract)
    assert result == {"accepted": False, "action": None, "reason": "invalid_support_contract",
                      "violations": ("invalid_support_contract",)}


def test_a_support_refusal_does_not_mutate_inputs_or_invent_a_forecast():
    state = card()
    state["actions"][0]["forecast_available"] = False
    del state["actions"][0]["one_step_net_utility"]
    proposal, contract = deepcopy(PROPOSAL), deepcopy(FORECAST_SUPPORT_CONTRACT)
    before = deepcopy((state, proposal, contract))
    assert support_violations(state, proposal, contract)
    assert (state, proposal, contract) == before
    assert gate_supported_proposal(state, proposal, contract)["action"] == "defer"
    assert (state, proposal, contract) == before
