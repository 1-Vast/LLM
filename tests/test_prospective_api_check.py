"""Offline checks for the fresh, bounded post-fix API experiment."""
from copy import deepcopy

import pytest

from research.dual_core_live.benchmark import PROMPT as ORIGINAL_PROMPT
from research.dual_core_live.live_api import digest, validate_proposal
from research.dual_core_live.prospective_check import (
    FAMILIES, PROMPT, SEED, cluster_estimate, expected_action, generated_cards, score,
)
from research.dual_core_live.support_contract import FORECAST_SUPPORT_CONTRACT, gate_supported_proposal


def test_fresh_generated_population_and_prompt_are_frozen_without_outcomes():
    cards = generated_cards()
    assert SEED == 20261002 and len(cards) == 8
    assert len({card["id"] for card in cards}) == 8
    assert len({card["independent_unit"] for card in cards}) == 8
    assert {family: sum(card["family"] == family for card in cards) for family in FAMILIES} == dict.fromkeys(FAMILIES, 2)
    assert digest(cards) == digest(generated_cards())
    assert PROMPT == ORIGINAL_PROMPT
    assert all(not card["evidence"] and "outcomes" not in card and "truth" not in card for card in cards)


@pytest.mark.parametrize("family", FAMILIES)
def test_nonpositive_and_unsupported_measurements_refuse_without_repair(family):
    card = next(card for card in generated_cards() if card["family"] == family)
    proposal = {"action": card["actions"][0]["id"], "terminal_authorized": False}
    before = digest(card)
    base = validate_proposal(card, proposal)
    assert base["accepted"]
    gate = gate_supported_proposal(card, proposal, FORECAST_SUPPORT_CONTRACT)
    if family == "positive_supported":
        assert gate["accepted"] and gate["action"] == proposal["action"]
    else:
        assert not gate["accepted"] and gate["action"] == "defer"
        assert gate["reason"] == "forecast_support_refusal"
        assert score(card, base)["support_violation"]
        assert not score(card, gate)["support_violation"]
        assert score(card, gate)["objective_adherent"]
    assert digest(card) == before


def test_defer_is_legal_but_fails_positive_objective_when_supported_action_exists():
    card = next(card for card in generated_cards() if card["family"] == "positive_supported")
    proposal = {"action": "defer", "terminal_authorized": False}
    gate = gate_supported_proposal(card, proposal, FORECAST_SUPPORT_CONTRACT)
    assert gate["accepted"] and score(card, gate)["legal"]
    assert not score(card, gate)["objective_adherent"]
    assert expected_action(card) != "defer"


def test_absent_contract_retains_legal_no_forecast_compatibility():
    card = deepcopy(next(card for card in generated_cards() if card["family"] == "missing_forecast"))
    del card["forecast_support_contract"]
    proposal = {"action": card["actions"][0]["id"], "terminal_authorized": False}
    gated = gate_supported_proposal(card, proposal)
    base = validate_proposal(card, proposal)
    assert {key: gated[key] for key in base} == base
    assert gated["violations"] == ()


def test_single_family_interval_is_unavailable_instead_of_zero_width():
    result = cluster_estimate({"only_family": [0, 1]})
    assert result["mean"] == .5 and result["ci"] is None
    assert result["interval_status"] == "insufficient_independent_clusters"


def test_family_average_does_not_count_variant_volume_as_independent_replication():
    result = cluster_estimate({"many_variants": [0] * 20, "few_variants": [1]})
    assert result["mean"] == .5 and result["clusters"] == 2
    assert result["ci"] == [0.0, 1.0]
