"""The live research runner cannot promote provider output to evidence."""
from copy import deepcopy

import pytest

from research.dual_core_live.live_api import (
    RecordedDeepSeek, RecordedJev, SMOKE_CARDS, assert_no_credentials, digest,
    legal_actions, validate_proposal,
)
from agent.decision_critic import TypeSafeSettings, noul
from agent.llm import MAESTROSettings


def test_budget_prerequisite_and_repeat_constraints_apply_together():
    card = deepcopy(SMOKE_CARDS[0])
    assert legal_actions(card) == ["m1"]
    card["attempted_actions"] = ["m1"]
    assert legal_actions(card) == []
    card["remaining_budget"] = 4
    assert legal_actions(card) == []
    card["qualified_prerequisites"] = ["target_activity"]
    assert legal_actions(card) == ["m2"]


def test_a_legal_proposal_cannot_authorize_a_terminal():
    card = SMOKE_CARDS[0]
    assert validate_proposal(card, {"action": "m1", "terminal_authorized": False})["accepted"]
    assert not validate_proposal(card, {"action": "m1", "terminal_authorized": True})["accepted"]
    assert not validate_proposal(card, {"action": "m1"})["accepted"]
    assert not validate_proposal(card, {"action": "new_action", "terminal_authorized": False})["accepted"]


def test_forecasts_do_not_supply_prerequisites_or_change_evidence():
    card = deepcopy(SMOKE_CARDS[1])
    before = digest(card["evidence"])
    assert legal_actions(card) == []
    assert validate_proposal(card, {"action": "defer", "terminal_authorized": False})["accepted"]
    assert digest(card["evidence"]) == before
    assert not card["qualified_prerequisites"]


def test_credentials_are_rejected_before_artifact_write():
    assert_no_credentials({"response": "safe"}, ("secret-key",))
    with pytest.raises(RuntimeError, match="Credential detected"):
        assert_no_credentials({"response": "echo secret-key"}, ("secret-key",))


def test_a_malformed_proposal_is_refused_without_guessing():
    assert validate_proposal(SMOKE_CARDS[0], "m1")["reason"] == "proposal_not_object"


def test_the_recorder_uses_existing_deepseek_protocol_without_logging_auth(monkeypatch, tmp_path):
    from agent import llm
    import json

    payload = {"model": "served-version", "choices": [{"message": {"content": '{"action":"m1","terminal_authorized":false}'},
                                                       "finish_reason": "stop"}], "usage": {"total_tokens": 9}}

    class Reply:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return json.dumps(payload).encode()

    monkeypatch.setattr(llm, "urlopen", lambda request, timeout: Reply())
    client = RecordedDeepSeek(MAESTROSettings("private-deepseek-key", "https://example.invalid", "deepseek-flash", "vision", tmp_path))
    proposal, response = client.complete_json([{"role": "user", "content": "Choose JSON."}], max_tokens=160)
    exchange = client.exchanges[0]
    assert response.model == "served-version" and proposal["action"] == "m1"
    assert exchange["response_sha256"] == digest(payload)
    assert exchange["request_sha256"] == digest(exchange["request"])
    assert_no_credentials(exchange, ("private-deepseek-key",))


def test_the_jev_recorder_retains_typed_answers_and_safe_envelope(monkeypatch):
    from agent import decision_critic
    import json

    payload = {"model": "served-jev", "answers": {"measured": {"type": "noul", "noul": 0.1}},
               "usage": {"input_tokens": 10, "output_tokens": 2}}

    class Reply:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return json.dumps(payload).encode()

    monkeypatch.setattr(decision_critic, "urlopen", lambda request, timeout: Reply())
    client = RecordedJev(TypeSafeSettings("private-jev-key", "https://example.invalid", "jev-latest"))
    result = client.evaluate("Forecast only.", [noul("measured", "Is an actual measurement present?")])
    assert result.answers["measured"].value is False
    assert client.exchanges[0]["response_sha256"] == digest(payload)
    assert_no_credentials(client.exchanges[0], ("private-jev-key",))


def test_preregistered_review_population_contains_four_distinct_defect_classes():
    from agent.model_audit import ModelAuditAgent
    from research.dual_core_live.benchmark import defect_cards, general_cards
    cards = general_cards()
    reviews, labels = defect_cards(cards)
    assert len(cards) == 24 and len(reviews) == 48 and sum(labels.values()) == 24
    auditor = ModelAuditAgent()
    findings = {}
    for key, card in reviews.items():
        before = digest(card)
        report = auditor.review(card, card["proposal"])
        assert bool(report.findings) is labels[key]
        assert digest(card) == before
        for finding in report.findings:
            findings[finding.code] = findings.get(finding.code, 0) + 1
    assert findings == {"terminal_authority_claim": 6, "illegal_action": 6, "malformed_proposal": 12}


def test_biological_population_is_frozen_by_identifier_hash_without_reading_truth():
    from research.dual_core_live.benchmark import choose_population
    population = choose_population()
    assert len(population) == 12
    for task in {p["task"] for p in population}:
        rows = [p for p in population if p["task"] == task]
        assert len(rows) == 6 and len({p["compound"] for p in rows}) == 6
        assert {p["fold"] for p in rows} == {0, 1, 2, 3, 4}
        assert all("truth" not in p and "outcomes" not in p for p in rows)


def test_unit_weighted_interval_endpoints_do_not_overweight_large_units():
    from research.dual_core_live.benchmark import unit_estimate
    result = unit_estimate({"large": [0.0] * 20, "small": [1.0]})
    assert result["units"] == 2 and result["mean"] == 0.5


def test_registered_replay_adapter_purchases_before_exposing_observations(tmp_path):
    from research.dual_core_live.benchmark import best_action, choose_population, run_biology
    population = choose_population()
    probe = [next(p for p in population if p["task"] == task and p["fold"] == 0)
             for task in ("sciplex3_B", "l1000_LT")]
    calls = []

    def recorded_offline_proposal(card, call_id):
        assert "truth" not in card and "outcomes" not in card
        assert all(s["action"] in card["attempted_actions"] for s in card["evidence"])
        calls.append((call_id, card))
        proposal = {"action": best_action(card), "terminal_authorized": False}
        return proposal, validate_proposal(card, proposal)

    rows = run_biology({"biological_population": probe}, tmp_path, recorded_offline_proposal)
    assert len(rows) == 6 and len(calls) <= 4
    assert all(not row["forecast_in_final_evidence"] for row in rows)
    assert all(row["net_utility"] == row["utility"] - 0.02 * row["measurements"] for row in rows)
    assert all(row["coverage"]["point_identified"] for row in rows)
