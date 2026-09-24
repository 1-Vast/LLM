"""Contract tests for the section 37 row arms and the blind adjudication.

File summary
- Path: tests/test_section37_rows.py
- Purpose: pin what the two new rows and the adjudication protocol do: an outcome model
  fitted on a development split, a value-of-information selector that refuses to buy what it
  cannot use, an LLM arm whose hypothesis bookkeeping is enforced rather than requested, and
  an adjudication packet that carries evidence but no one's answer.
- Core points: assertions here are contract tests, not biological results, and no test makes a
  provider call.
- Interfaces: one test per contract, named for the contract it pins.
- Depends on: evaluation.voi_arm, evaluation.llm_rows, evaluation.adjudication,
  evaluation.provider_spend, evaluation.cases, agent.llm
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[1]

from evaluation.adjudication import adjudication_packet, agreement, mechanical_verdict  # noqa: E402
from evaluation.cases import CaseRepository, ReplayEnvironment  # noqa: E402
from evaluation.llm_rows import ExplicitHypothesesLLMPolicy  # noqa: E402
from evaluation.provider_spend import RATES, SpendLedger, price_usage  # noqa: E402
from evaluation.voi_arm import (  # noqa: E402
    SimpleModelVOIPolicy,
    expected_value_of_information,
    fit_action_reliability,
)

HYPOTHESES = [
    {
        "identifier": "insufficient_functional_perturbation",
        "description": "The intervention did not perturb the target.",
        "development_action": "revise_intervention",
    },
    {
        "identifier": "genetic_pharmacological_mode_non_equivalence",
        "description": "The modes are not equivalent.",
        "development_action": "change_intervention_mode",
    },
]


def _package(tmp_path: Path, *, case_id: str = "case-1", comparator_outcome: str = "comparator_active"):
    """A one-case package on disk: a separating readout and a non-separating retrieval."""

    public = {
        "identifier": case_id,
        "provenance": "test",
        "evaluation_status": "test_case",
        "initial_evidence": [
            {"identifier": "premise", "statement": "A discordance.", "source_id": "release:premise"}
        ],
        "context_identifier": "ACH-000551:K562",
        "budget": 3.0,
        "hypotheses": HYPOTHESES,
        "actions": [
            {
                "identifier": "mode_matched_comparator",
                "description": "A second compound's curve.",
                "cost": 1.0,
                "distinguishes": [item["identifier"] for item in HYPOTHESES],
                "kind": "mode_matched_comparator",
                "quantity": "viability",
                "expected_outcomes": {
                    "insufficient_functional_perturbation": "comparator_active",
                    "genetic_pharmacological_mode_non_equivalence": "comparator_inactive",
                },
            },
            {
                "identifier": "target_abundance_rna",
                "description": "RNA abundance.",
                "cost": 1.0,
                "distinguishes": [item["identifier"] for item in HYPOTHESES],
                "kind": "rna_abundance_measurement",
                "quantity": "rna_abundance",
                "expected_outcomes": {
                    "insufficient_functional_perturbation": "target_expressed",
                    "genetic_pharmacological_mode_non_equivalence": "target_expressed",
                },
            },
        ],
        "limitations": ["A test fixture."],
    }
    private = {
        "case_id": case_id,
        "results": [
            {
                "action_identifier": "mode_matched_comparator",
                "outcome": comparator_outcome,
                "statement": "A comparator curve.",
                "source_id": "release:comparator",
                "context_identifier": "ACH-000551:K562",
                "record_validated": True,
                "biological_quality": "passed",
                "evidence_kind": "real_measurement",
                "interpretation_fields": ["functional:mode_comparator"],
            },
            {
                "action_identifier": "target_abundance_rna",
                "outcome": "target_expressed",
                "statement": "An abundance record.",
                "source_id": "release:abundance",
                "context_identifier": "ACH-000551:K562",
                "record_validated": True,
                "biological_quality": "passed",
                "evidence_kind": "real_measurement",
                "interpretation_fields": ["abundance:target_rna"],
            },
        ],
        "final_test": [
            {
                "identifier": "held-back-binding",
                "statement": "An independent binding record.",
                "source_id": "release:binding",
                "outcome": "listed_as_target",
                "confirms": ["change_intervention_mode"],
                "contradicts": [],
                "record_validated": True,
                "biological_quality": "passed",
                "evidence_kind": "real_measurement",
            }
        ],
        "scoring": {
            "decision_rules": [
                {
                    "decision": "revise_intervention",
                    "required_outcomes": {"mode_matched_comparator": "comparator_active"},
                    "require_biological_quality": True,
                },
                {
                    "decision": "change_intervention_mode",
                    "required_outcomes": {"mode_matched_comparator": "comparator_inactive"},
                    "require_biological_quality": True,
                },
            ],
            "critical_actions": [],
        },
    }
    (tmp_path / "public").mkdir(parents=True, exist_ok=True)
    (tmp_path / "private").mkdir(parents=True, exist_ok=True)
    (tmp_path / "public" / f"{case_id}.json").write_text(json.dumps(public), encoding="utf-8")
    (tmp_path / "private" / f"{case_id}.results.json").write_text(json.dumps(private), encoding="utf-8")
    return CaseRepository(tmp_path / "public", tmp_path / "private").load()


def test_reliability_is_fitted_on_the_development_split_only(tmp_path):
    cases = _package(tmp_path)
    fitted = fit_action_reliability(cases, development_cases=("case-1",))
    # One development observation, both actions returning a declared outcome, smoothed towards
    # the declaration with the module's one-observation prior: (1 + 1) / (1 + 2).
    assert fitted["mode_matched_comparator"] == pytest.approx(2 / 3)
    assert fitted["target_abundance_rna"] == pytest.approx(2 / 3)
    assert fit_action_reliability(cases, development_cases=()) == {}


def test_value_of_information_is_the_loss_a_reading_would_remove(tmp_path):
    cases = _package(tmp_path)
    case, outcomes = cases[0]
    view = ReplayEnvironment(case, outcomes).view()
    separating = case.public.action("mode_matched_comparator")
    flat = case.public.action("target_abundance_rna")
    # A perfectly reliable separating readout takes the decision from deferral (4.0) to a
    # correct act (0.0); a readout declared identical under both explanations removes nothing.
    assert expected_value_of_information(view, separating, 1.0) == pytest.approx(4.0)
    assert expected_value_of_information(view, separating, 0.6) < 4.0
    assert expected_value_of_information(view, flat, 1.0) == pytest.approx(0.0)


def test_the_voi_arm_buys_what_pays_for_itself_and_refuses_what_does_not(tmp_path):
    cases = _package(tmp_path)
    case, outcomes = cases[0]
    view = ReplayEnvironment(case, outcomes).view()
    buying = SimpleModelVOIPolicy(reliability={"mode_matched_comparator": 1.0, "target_abundance_rna": 1.0})
    assert buying.next_action(view) == "mode_matched_comparator"
    # With the separating readout barely better than chance its value no longer covers its
    # cost, and refusing to buy is the value-of-information answer rather than a failure.
    refusing = SimpleModelVOIPolicy(reliability={"mode_matched_comparator": 0.51, "target_abundance_rna": 0.51})
    assert refusing.next_action(view) is None


@pytest.mark.parametrize(
    "payload, code",
    [
        ({"value_of_information": {}, "action": None}, "posterior_does_not_cover_the_registered_explanations"),
        (
            {
                "posterior": {"insufficient_functional_perturbation": 0.5, "genetic_pharmacological_mode_non_equivalence": 0.2},
                "value_of_information": {"mode_matched_comparator": 1.0, "target_abundance_rna": 0.0},
            },
            "posterior_not_normalised:0.700000",
        ),
        (
            {
                "posterior": {"insufficient_functional_perturbation": 0.5, "genetic_pharmacological_mode_non_equivalence": 0.5},
                "value_of_information": {"mode_matched_comparator": 1.0},
            },
            "value_of_information_does_not_cover_the_offered_actions",
        ),
        (
            {
                "posterior": {"insufficient_functional_perturbation": 0.5, "genetic_pharmacological_mode_non_equivalence": 0.5},
                "value_of_information": {"mode_matched_comparator": 1.0, "target_abundance_rna": 0.0},
                "action": "an_action_that_is_not_offered",
            },
            "action_not_executable:an_action_that_is_not_offered",
        ),
    ],
)
def test_the_explicit_hypotheses_contract_is_enforced_by_name(payload, code):
    registered = {item["identifier"] for item in HYPOTHESES}
    allowed = {"mode_matched_comparator", "target_abundance_rna"}
    assert ExplicitHypothesesLLMPolicy._contract_refusal(payload, registered, allowed) == code


def test_a_contract_satisfying_turn_is_accepted_and_priced(tmp_path):
    cases = _package(tmp_path)
    case, outcomes = cases[0]
    view = ReplayEnvironment(case, outcomes).view()

    class Stub:
        def complete_json(self, messages, **kwargs):
            payload = {
                "posterior": {
                    "insufficient_functional_perturbation": 0.5,
                    "genetic_pharmacological_mode_non_equivalence": 0.5,
                },
                "value_of_information": {"mode_matched_comparator": 3.0, "target_abundance_rna": 0.0},
                "action": "mode_matched_comparator",
                "rationale": "The comparator separates the two explanations.",
            }
            usage = {"prompt_tokens": 1000, "prompt_cache_miss_tokens": 1000, "completion_tokens": 500}
            return payload, SimpleNamespace(model="stub", usage=usage, finish_reason="stop")

    ledger = SpendLedger(path=tmp_path / "spend.json", ceiling_usd=5.0, prior_total_usd=0.0)
    policy = ExplicitHypothesesLLMPolicy(Stub(), ledger=ledger)
    assert policy.next_action(view) == "mode_matched_comparator"
    assert policy.turns[0]["refusal"] is None
    assert ledger.entries and ledger.entries[0].charged_usd == pytest.approx(
        (1000 * 0.3 + 500 * 1.2) / 1_000_000
    )


def test_the_ceiling_is_refused_before_the_call_not_after(tmp_path):
    ledger = SpendLedger(path=tmp_path / "spend.json", ceiling_usd=1.0, prior_total_usd=0.999)
    with pytest.raises(ValueError, match="provider_ceiling_exceeded"):
        ledger.reserve("row4:case-1", 0.01)
    assert price_usage({"prompt_cache_hit_tokens": 1_000_000}) == pytest.approx(float(RATES["input_cache_hit"]))


def test_an_adjudication_packet_carries_the_evidence_and_no_ones_answer(tmp_path):
    cases = _package(tmp_path)
    case, outcomes = cases[0]
    packet = adjudication_packet(case, outcomes)
    text = json.dumps(packet)
    assert "decision_rules" not in text and "licensing" not in text
    assert {record["identifier"] for record in packet["results_obtained"]} == {
        "mode_matched_comparator",
        "target_abundance_rna",
    }
    assert packet["results_held_back_from_everyone"][0]["identifier"] == "held-back-binding"
    assert [item["development_action"] for item in packet["explanations"]] == [
        "revise_intervention",
        "change_intervention_mode",
    ]


def test_the_mechanical_verdict_is_the_frozen_rules_with_every_record_revealed(tmp_path):
    cases = _package(tmp_path, comparator_outcome="comparator_inactive")
    case, outcomes = cases[0]
    assert mechanical_verdict(case, outcomes) == ("change_intervention_mode",)


def test_a_long_adjudication_leaves_its_finished_cases_behind(tmp_path):
    """A run that stops half way must still be evidence, so each case is written as it lands."""

    from evaluation.adjudication import adjudicate_package

    _package(tmp_path)

    class Stub:
        def complete_json(self, messages, **kwargs):
            payload = {
                "supported_decisions": ["defer"],
                "ruled_out": [],
                "minimum_evidence": ["mode_matched_comparator"],
                "rationale": "The comparator record does not isolate either explanation.",
            }
            usage = {"prompt_tokens": 800, "prompt_cache_miss_tokens": 800, "completion_tokens": 400}
            return payload, SimpleNamespace(model="stub", usage=usage, finish_reason="stop")

    ledger = SpendLedger(path=tmp_path / "spend.json", ceiling_usd=5.0, prior_total_usd=0.0)
    progress = tmp_path / "progress.json"
    payload = adjudicate_package(
        public_directory=tmp_path / "public",
        private_directory=tmp_path / "private",
        client=Stub(),
        ledger=ledger,
        progress_path=progress,
    )
    assert progress.is_file(), "no progress file was written during the run"
    recorded = json.loads(progress.read_text(encoding="utf-8"))
    assert recorded["cases_done"] == recorded["cases_total"] == 1
    assert recorded["verdicts"]["case-1"]["supported_decisions"] == ["defer"]
    assert (tmp_path / "spend.json").is_file(), "the priced ledger was not written as the run progressed"
    assert payload["agreement"]["cases_compared"] == 1
    assert payload["mechanical_digest"]


def test_resuming_re_reviews_only_the_cases_that_failed(tmp_path):
    """A provider failure must cost one case, not the whole package, on the next attempt."""

    from evaluation.adjudication import adjudicate_package

    _package(tmp_path)
    calls: list[int] = []

    class CountingStub:
        def complete_json(self, messages, **kwargs):
            calls.append(1)
            payload = {
                "supported_decisions": ["change_intervention_mode"],
                "ruled_out": [],
                "minimum_evidence": ["mode_matched_comparator"],
                "rationale": "A fresh review.",
            }
            usage = {"prompt_tokens": 500, "prompt_cache_miss_tokens": 500, "completion_tokens": 300}
            return payload, SimpleNamespace(model="stub", usage=usage, finish_reason="stop")

    clean = {
        "case-1": {
            "supported_decisions": ["defer"],
            "ruled_out": [],
            "minimum_evidence": ["mode_matched_comparator"],
            "rationale": "Recorded by an earlier run.",
            "refusal": None,
        }
    }
    payload = adjudicate_package(
        public_directory=tmp_path / "public",
        private_directory=tmp_path / "private",
        client=CountingStub(),
        resume_from=clean,
    )
    assert calls == [], "a clean recorded verdict was paid for a second time"
    assert payload["reused_from_an_earlier_run"] == ["case-1"]
    assert payload["reviewed_now"] == 0
    assert payload["reviewer_verdicts"]["case-1"]["rationale"] == "Recorded by an earlier run."

    refused = {"case-1": dict(clean["case-1"], refusal="provider_failure:LLMProtocolError")}
    payload = adjudicate_package(
        public_directory=tmp_path / "public",
        private_directory=tmp_path / "private",
        client=CountingStub(),
        resume_from=refused,
    )
    assert calls == [1], "a refused verdict was not re-reviewed"
    assert payload["reviewed_now"] == 1
    assert payload["reviewer_verdicts"]["case-1"]["supported_decisions"] == ["change_intervention_mode"]


def test_a_reply_without_usable_text_names_which_shape_it_was(monkeypatch):
    """Three ways a reply can carry no text call for three different responses, so each is named."""

    import json as json_module

    from agent import llm as llm_module

    settings = SimpleNamespace(
        api_key="not-a-real-key",
        base_url="https://example.invalid",
        chat_model="stub-model",
        timeout_seconds=1.0,
        max_tokens=100,
    )
    client = llm_module.DeepSeekChatClient(settings)

    def reply(body):
        def _send(self, request):  # noqa: ANN001 - test double for one private method
            return json_module.loads(json_module.dumps(body))

        return _send

    monkeypatch.setattr(llm_module.DeepSeekChatClient, "_send", reply({"choices": []}))
    with pytest.raises(llm_module.LLMProtocolError) as empty:
        client.complete([{"role": "user", "content": "x"}])
    assert getattr(empty.value, "code", None) == "no_choice_returned"

    monkeypatch.setattr(
        llm_module.DeepSeekChatClient,
        "_send",
        reply({"choices": [{"finish_reason": "stop", "message": {"reasoning": "thought only"}}], "usage": {}}),
    )
    with pytest.raises(llm_module.LLMProtocolError) as reasoning_only:
        client.complete([{"role": "user", "content": "x"}])
    assert getattr(reasoning_only.value, "code", None) == "message_without_text_content"
    assert "message_keys=['reasoning']" in str(reasoning_only.value)


def test_a_fenced_or_padded_reply_is_still_one_decision(tmp_path):
    """A code fence is presentation, not a different answer; anything unparseable still raises."""

    from agent.llm import json_object_from_text

    payload = {"decision": "defer", "evidence_ids": []}
    assert json_object_from_text(json.dumps(payload)) == payload
    assert json_object_from_text("```json\n" + json.dumps(payload) + "\n```") == payload
    assert json_object_from_text("```\n" + json.dumps(payload) + "\n```") == payload
    assert json_object_from_text(
        "Here is my answer:\n" + json.dumps(payload) + "\nI hope this helps."
    ) == payload
    with pytest.raises(json.JSONDecodeError):
        json_object_from_text("I cannot answer that.")


def test_agreement_reports_kappa_and_every_disagreement(tmp_path):
    from evaluation.adjudication import ReviewerVerdict

    mechanical = {"a": ("revise_intervention",), "b": ("change_intervention_mode",), "c": ("defer",)}
    reviewer = {
        "a": ReviewerVerdict("a", ("revise_intervention",), (), (), ""),
        "b": ReviewerVerdict("b", ("defer",), (), (), "The evidence does not isolate a cause."),
        "c": ReviewerVerdict("c", ("defer",), (), (), ""),
    }
    result = agreement(
        mechanical,
        reviewer,
        registered_actions=("revise_intervention", "change_intervention_mode", "defer"),
    )
    assert result["cases_compared"] == 3
    assert result["cases_in_full_agreement"] == 2
    assert result["disputed_cases"] == ["b"]
    assert result["disagreements"][0]["mechanical"] == ["change_intervention_mode"]
    assert result["cohens_kappa"] is not None
