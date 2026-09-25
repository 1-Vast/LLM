"""The typed decision model advises and is scored; it never becomes evidence.

File summary
- Path: tests/test_typed_decision_critic.py
- Purpose: pin the TypeSafe Jev integration end to end without a network call: question
  construction, fail-closed answer parsing, the advisory boundary, calibration revocation,
  and the orchestrator wiring.
- Core points: assertions here are contract tests, not biological results; each test pins one
  boundary that must not silently move. No test makes a provider request.
- Interfaces: pytest tests only
- Depends on: agent, maestro, tools.shared
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent import typesafe as typesafe_module
from agent.audit import RunLogger
from agent.context import ContextBuilder, TaskInterpreter
from agent.decision_critic import (
    NOT_LISTED,
    CriticThresholds,
    TypedDecisionCritic,
    contrast_questions,
    regulator_question,
)
from agent.knowledge import EvidenceLedger
from agent.memory import MemoryStore
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import ADVISORY_HEADING, MechanismContrastPlanner
from agent.typesafe import (
    JevEvaluation,
    QuestionKind,
    TypeSafeJevClient,
    TypeSafeSettings,
    TypedAnswer,
    TypedQuestion,
    choice,
    noul,
    score,
)
from agent.vision import VisualInspector
from maestro import EvidenceAction, FunctionalInterventionProfile, MAESTROAgent
from maestro.judgment import JudgmentLedger, JudgmentScope, TypedJudgment
from maestro.models import ContrastCheck, MechanismContrast, MechanismHypothesis, NonDiscriminabilityReason

from tools.shared.stub_client import StubClient  # noqa: E402

ACTIONS = (
    EvidenceAction("viability", "Viability readout.", 5.0, ("a", "b"),
                   expected_outcomes={"a": "low", "b": "high"}),
    EvidenceAction("activity", "Proximal target activity.", 2.0, ("a",)),
)
CONTRAST = MechanismContrast(
    "contrast",
    (MechanismHypothesis("a", "Incomplete perturbation."), MechanismHypothesis("b", "Mode mismatch.")),
    ("functional realization",),
    ACTIONS[0],
)


class RecordedJevClient:
    """Serves recorded answers and records the request; it never touches the network."""

    def __init__(self, answers, *, model="jev-1.13"):
        self._answers = answers
        self.model = model
        self.calls: list[tuple[str, tuple[TypedQuestion, ...]]] = []

    def evaluate(self, state, questions):
        self.calls.append((state, tuple(questions)))
        parsed = {
            question.identifier: TypedAnswer.parse(question, self._answers[question.identifier])
            for question in questions
            if question.identifier in self._answers
        }
        return JevEvaluation(self.model, typesafe_module.state_digest(state), parsed)


# --------------------------------------------------------------------------------------
# Questions
# --------------------------------------------------------------------------------------


def test_the_three_question_kinds_validate_their_own_limits():
    assert noul("q", "Yes or no?").payload() == {"type": "noul", "instructions": "Yes or no?"}
    assert choice("q", "Pick.", ("x", "y")).payload()["options"] == ["x", "y"]
    assert score("q", "Rate.", 5).payload()["scale"] == 5
    for bad in (
        lambda: choice("q", "Pick.", ("only",)),
        lambda: choice("q", "Pick.", ("x", "x")),
        lambda: score("q", "Rate.", 11),
        lambda: score("q", "Rate.", 1),
        lambda: TypedQuestion("q", QuestionKind.NOUL, "Yes?", options=("x", "y")),
        lambda: TypedQuestion("", QuestionKind.NOUL, "Yes?"),
    ):
        with pytest.raises(ValueError, match="invalid_question"):
            bad()
    assert choice("q", "Pick.", [f"o{i}" for i in range(255)])
    with pytest.raises(ValueError, match="invalid_question"):
        choice("q", "Pick.", [f"o{i}" for i in range(256)])


def test_choice_options_are_exactly_the_registered_action_identifiers():
    questions, notes = contrast_questions(CONTRAST, ACTIONS)
    best = next(q for q in questions if q.identifier == "best_separating_action")
    assert best.options == ("viability", "activity", NOT_LISTED)
    assert notes == ()
    # A refused action is not offered, and an oversized menu is truncated and says so.
    refused = ACTIONS + (EvidenceAction("unpriced", "No price.", -1.0, ("a",)),)
    assert "unpriced" not in next(
        q for q in contrast_questions(CONTRAST, refused)[0] if q.identifier == "best_separating_action"
    ).options
    big = tuple(EvidenceAction(f"a{i}", "x", 1.0, ("a",)) for i in range(300))
    _, big_notes = contrast_questions(CONTRAST, big)
    assert big_notes and big_notes[0].startswith("menu_truncated_for_choice:300")


def test_a_regulator_question_is_offered_only_with_candidates():
    assert regulator_question(()) is None
    question = regulator_question(("TP53", "MYC", "TP53"))
    assert question.options == ("TP53", "MYC", NOT_LISTED)


# --------------------------------------------------------------------------------------
# Fail-closed parsing
# --------------------------------------------------------------------------------------


def test_answers_parse_or_refuse_by_name_and_never_guess():
    yes_no = noul("q", "Yes?")
    assert TypedAnswer.parse(yes_no, {"probability": 0.8}).value is True
    assert TypedAnswer.parse(yes_no, {"probability": 0.2}).value is False
    assert TypedAnswer.parse(yes_no, {"value": True}).value is True
    refused = TypedAnswer.parse(yes_no, {"comment": "maybe"})
    assert not refused.usable and "noul_without_probability_or_boolean" in refused.refusal
    assert "keys=comment" in refused.refusal

    picker = choice("q", "Pick.", ("x", "y"))
    parsed = TypedAnswer.parse(picker, {"value": "x", "probabilities": {"x": 0.7, "y": 0.3}, "confidence": 0.6})
    assert parsed.value == "x" and parsed.probability == 0.7 and parsed.confidence == 0.6
    # With no explicit selection the highest-probability option is used, but an option that was
    # never offered is refused rather than accepted.
    assert TypedAnswer.parse(picker, {"probabilities": {"x": 0.2, "y": 0.8}}).value == "y"
    assert "unlisted_option" in TypedAnswer.parse(picker, {"probabilities": {"z": 1.0}}).refusal
    assert "outside_the_declared_options" in TypedAnswer.parse(picker, {"value": "z"}).refusal

    rating = score("q", "Rate.", 5)
    assert TypedAnswer.parse(rating, {"value": 4}).value == 4
    assert "score_outside_1_to_5" in TypedAnswer.parse(rating, {"value": 9}).refusal
    assert "score_without_a_number" in TypedAnswer.parse(rating, {"value": "high"}).refusal
    assert "answer_not_an_object" in TypedAnswer.parse(rating, [4]).refusal


def test_an_evaluation_refuses_malformed_envelopes_without_raising(monkeypatch, tmp_path):
    settings = TypeSafeSettings("secret-key", "https://example.org", "jev-1.13")
    client = TypeSafeJevClient(settings)
    question = noul("q", "Yes?")

    monkeypatch.setattr(TypeSafeJevClient, "_send", lambda self, body: {"unexpected": 1})
    assert "response_without_answers" in client.evaluate("state", [question]).refusal

    monkeypatch.setattr(TypeSafeJevClient, "_send", lambda self, body: {"answers": {}})
    missing = client.evaluate("state", [question])
    assert missing.refusals() == ("q:answer_missing_from_response",)

    def raising(self, body):
        raise typesafe_module.JevTransportError("the configured endpoint could not be reached")

    monkeypatch.setattr(TypeSafeJevClient, "_send", raising)
    assert client.evaluate("state", [question]).refusal.startswith("JevTransportError")
    assert client.evaluate("", [question]).refusal == "empty_state"
    assert client.evaluate("state", []).refusal == "no_questions"
    assert client.evaluate("state", [question, question]).refusal == "duplicate_question_identifier"


def test_settings_are_optional_redacted_and_build_the_evaluate_url(tmp_path: Path, monkeypatch):
    for name in ("TYPESAFE_API_KEY", "TYPESAFE_ENDPOINT", "TYPESAFE_MODEL", "TYPESAFE_TIMEOUT_SECONDS"):
        monkeypatch.delenv(name, raising=False)
    assert TypeSafeSettings.from_workspace(tmp_path) is None  # absent block disables the feature
    monkeypatch.setenv("TYPESAFE_API_KEY", "secret-key")
    assert TypeSafeSettings.from_workspace(tmp_path) is None  # a key with no model stays disabled
    monkeypatch.setenv("TYPESAFE_MODEL", "jev-1.13")
    settings = TypeSafeSettings.from_workspace(tmp_path)
    assert settings.evaluate_url == "https://api.typesafe.ai/v1/systemone"
    assert "secret-key" not in repr(settings)
    monkeypatch.setenv("TYPESAFE_ENDPOINT", "https://gateway.example.org/v1/systemone")
    assert TypeSafeSettings.from_workspace(tmp_path).evaluate_url == "https://gateway.example.org/v1/systemone"
    (tmp_path / ".env").write_text("TYPESAFE_API_KEY=from-file\nTYPESAFE_MODEL=jev-file\n", encoding="utf-8")
    assert TypeSafeSettings.from_workspace(tmp_path).model == "jev-1.13"  # environment wins over .env


def test_the_request_carries_the_key_in_a_header_and_never_in_the_body(monkeypatch):
    sent = {}

    class Reply:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return json.dumps({"model": "jev-1.13", "answers": {"q": {"probability": 0.9}}}).encode()

    def fake_urlopen(request, timeout):
        sent["url"] = request.full_url
        sent["headers"] = dict(request.headers)
        sent["body"] = json.loads(request.data)
        return Reply()

    monkeypatch.setattr(typesafe_module, "urlopen", fake_urlopen)
    client = TypeSafeJevClient(TypeSafeSettings("secret-key", "https://api.typesafe.ai", "jev-1.13"))
    result = client.evaluate("the state", [noul("q", "Yes?")])
    assert result.answers["q"].value is True
    assert sent["url"] == "https://api.typesafe.ai/v1/systemone"
    assert sent["headers"]["Authorization"] == "Bearer secret-key"
    assert "secret-key" not in json.dumps(sent["body"])
    assert sent["body"]["questions"]["q"] == {"type": "noul", "instructions": "Yes?"}
    assert sent["body"]["state"] == "the state"


# --------------------------------------------------------------------------------------
# The advisory boundary
# --------------------------------------------------------------------------------------


def test_a_judgment_is_model_output_and_can_never_be_promoted():
    judgment = TypedJudgment("q", JudgmentScope.PLAN_CRITIQUE, "noul", True, "jev-1.13", "d", probability=0.9)
    assert judgment.evidence_kind.value == "model_prediction"
    assert judgment.satisfies_premise is False
    assert judgment.eliminates_hypothesis is False
    assert judgment.is_measurement is False
    # The scope vocabulary has no mechanism-contrast member, so no judgment can name one.
    assert "mechanism" not in {scope.value for scope in JudgmentScope}
    with pytest.raises(ValueError, match="probability"):
        TypedJudgment("q", JudgmentScope.PLAN_CRITIQUE, "noul", True, "m", "d", probability=1.4)


def test_confident_answers_become_advisory_findings_and_weak_ones_do_not():
    critic = TypedDecisionCritic(RecordedJevClient({
        "decision_separation": {"probability": 0.05},
        "plan_discriminates": {"probability": 0.10},
        "boundary_stated": {"probability": 0.40},
        "evidence_sufficiency": {"value": 2},
        "best_separating_action": {"value": "activity", "probabilities": {"activity": 0.8, "viability": 0.2}},
    }))
    outcome = critic.review_plan(CONTRAST, ACTIONS)
    joined = "\n".join(outcome.findings)
    assert "do not lead to two different development decisions" in joined
    assert "would not separate the two explanations" in joined
    assert "prefers the registered action 'activity' over the planned 'viability'" in joined
    assert "2/5" in joined
    # p(no)=0.60 is below the 0.70 threshold, so the boundary question stays silent.
    assert "interpretation boundary" not in joined
    assert {j.question_id for j in outcome.judgments} == {
        "decision_separation", "plan_discriminates", "boundary_stated",
        "evidence_sufficiency", "best_separating_action",
    }
    assert all(j.evidence_kind.value == "model_prediction" for j in outcome.judgments)


def test_agreement_and_an_empty_menu_answer_produce_no_noise():
    critic = TypedDecisionCritic(RecordedJevClient({
        "decision_separation": {"probability": 0.95},
        "plan_discriminates": {"probability": 0.92},
        "boundary_stated": {"probability": 0.88},
        "evidence_sufficiency": {"value": 5},
        "best_separating_action": {"value": "viability", "probabilities": {"viability": 0.9}},
    }))
    assert critic.review_plan(CONTRAST, ACTIONS).findings == ()

    gap = TypedDecisionCritic(RecordedJevClient({
        "best_separating_action": {"value": NOT_LISTED, "probabilities": {NOT_LISTED: 0.9}},
    }))
    assert "capability gap" in gap.review_plan(CONTRAST, ACTIONS).findings[0]


def test_a_regulator_answer_is_labelled_a_hypothesis_not_a_finding():
    critic = TypedDecisionCritic(RecordedJevClient({
        "candidate_regulator": {"value": "TP53", "probabilities": {"TP53": 0.85}},
    }))
    outcome = critic.review_plan(CONTRAST, ACTIONS, regulator_candidates=("TP53", "MYC"))
    assert "hypothesis to test, not a causal finding" in outcome.findings[0]
    assert "no network edge is evidence" in outcome.findings[0]
    judgment = next(j for j in outcome.judgments if j.question_id == "candidate_regulator")
    assert judgment.scope is JudgmentScope.HYPOTHESIS_ADVISORY and judgment.satisfies_premise is False


def test_the_state_carries_repository_objects_and_the_non_evidence_boundary():
    client = RecordedJevClient({"decision_separation": {"probability": 0.9}})
    check = ContrastCheck(True, False, True, True, (NonDiscriminabilityReason.MISSING_PREREQUISITE,),
                          missing_prerequisites=("functional:target_activity",))
    TypedDecisionCritic(client).review_plan(
        CONTRAST, ACTIONS, check=check,
        topology={"executable_now": ["activity"], "unsupplied_premises": {}},
        world_model_rows=[{"action": "viability", "status": "predicted", "value": 1.25}],
        regulator_candidates=("TP53",),
    )
    state = client.calls[0][0]
    assert "never supply a measurement" in state
    assert "AVAILABLE_ACTIONS" in state and '"identifier":"viability"' in state
    assert "functional:target_activity" in state and "ACTION_TOPOLOGY" in state
    assert "planning-only model output, not measurements" in state
    assert "network edges are hypotheses" in state


def test_a_revoked_scope_is_recorded_but_stops_steering_the_plan():
    ledger = JudgmentLedger(minimum_records=3)
    for index in range(3):
        ledger.record_outcome(
            TypedJudgment(f"q{index}", JudgmentScope.PLAN_CRITIQUE, "noul", False, "jev-1.13",
                          f"digest{index}", probability=0.05),
            outcome=True, result_id=f"result-{index}",
        )
    assert ledger.is_revoked(JudgmentScope.PLAN_CRITIQUE, "jev-1.13")
    critic = TypedDecisionCritic(
        RecordedJevClient({"decision_separation": {"probability": 0.02}}), ledger=ledger
    )
    outcome = critic.review_plan(CONTRAST, ACTIONS)
    assert outcome.findings == () and outcome.suppressed_by_revocation
    assert outcome.judgments and outcome.judgments[0].question_id == "decision_separation"
    # Action ranking was never scored, so it keeps full weight and still speaks.
    assert ledger.weight(JudgmentScope.ACTION_RANKING, "jev-1.13") == 1.0


def test_thresholds_are_validated():
    for bad in ({"noul_probability": 0.2}, {"choice_probability": 1.5}, {"sufficiency_floor": 9}):
        with pytest.raises(ValueError, match="invalid_threshold"):
            CriticThresholds(**bad)


# --------------------------------------------------------------------------------------
# Orchestrator wiring
# --------------------------------------------------------------------------------------

TASK = {
    "task_type": "mechanism_diagnosis", "research_question": "Resolve discrepancy.",
    "target_or_targets": ["TARGET"], "interventions": ["compound"],
    "biological_context": "cell-a", "phenotype_endpoint": "viability",
    "supplied_evidence": [], "constraints": [], "missing_information": [], "needs_visual_review": False,
}
PLAN = {
    "identifier": "contrast",
    "hypotheses": [
        {"identifier": "a", "description": "A", "proposed_action": "continue"},
        {"identifier": "b", "description": "B", "proposed_action": "revise_intervention"},
    ],
    "differing_assumptions": ["x"], "action_identifier": "viability",
    "outcome_categories": ["a", "b"], "interpretation_boundaries": ["Not a mechanism."],
}
REPAIR = {"action_identifier": "activity", "modified_fields": ["plan.action_identifier"],
          "rationale": "Measure function first.", "remaining_limitations": []}


def _controller(root: Path, client, critic=None, **kwargs):
    memory = MemoryStore(root / "memory.sqlite")
    return MAESTROOrchestrator(
        interpreter=TaskInterpreter(client),
        context_builder=ContextBuilder(EvidenceLedger(root / "evidence.sqlite"), memory),
        planner=MechanismContrastPlanner(client),
        visual_inspector=VisualInspector(client, "vision"),
        memory=memory, logger=RunLogger(root), controller=MAESTROAgent(),
        decision_critic=critic, **kwargs,
    )


def test_findings_reach_the_repair_planner_and_the_run_record(tmp_path: Path):
    blocked = EvidenceAction("viability", "Viability.", 5.0, ("a", "b"),
                             prerequisites=("functional:target_activity",))
    functional = EvidenceAction("activity", "Activity.", 2.0, ("a",), supplies=("functional:target_activity",))
    client = StubClient([TASK, PLAN, REPAIR])
    critic = TypedDecisionCritic(RecordedJevClient({
        "best_separating_action": {"value": "activity", "probabilities": {"activity": 0.9}},
        "evidence_sufficiency": {"value": 1},
    }))
    controller = _controller(tmp_path, client, critic=critic, enable_llm_repair=True)

    turn = controller.run("Resolve.", available_actions=(blocked, functional),
                          intervention_profile=FunctionalInterventionProfile(mode="inhibition"))

    repair_prompt = client.calls[2][0][1]["content"]
    assert ADVISORY_HEADING in repair_prompt
    assert "prefers the registered action 'activity'" in repair_prompt
    assert "never a licence to name an action outside AVAILABLE_ACTIONS" in repair_prompt
    assert turn.decision_review["model_version"] == "jev-1.13"
    assert len(turn.decision_review["judgments"]) == 2
    events = [json.loads(line) for line in (tmp_path / "events.jsonl").read_text().splitlines()]
    review = next(e["payload"] for e in events if e["kind"] == "typed_decision_review")
    assert review["findings"] and review["judgments"][0]["evidence_kind"] == "model_prediction"


def test_the_critic_cannot_satisfy_a_premise_or_survive_a_provider_failure(tmp_path: Path):
    blocked = EvidenceAction("viability", "Viability.", 5.0, ("a", "b"),
                             prerequisites=("functional:target_activity",))
    functional = EvidenceAction("activity", "Activity.", 2.0, ("a",), supplies=("functional:target_activity",))

    class FailingClient:
        model = "jev-1.13"

        def evaluate(self, state, questions):
            return JevEvaluation(self.model, "digest", {}, refusal="JevTransportError:unreachable")

    controller = _controller(tmp_path, StubClient([TASK, PLAN]), critic=TypedDecisionCritic(FailingClient()))
    turn = controller.run("Resolve.", available_actions=(blocked, functional),
                          intervention_profile=FunctionalInterventionProfile(mode="inhibition"))
    # The round completed, the unmet premise is still unmet, and the failure is on the record
    # rather than being swallowed: a silent critic and an unreachable one must look different.
    assert turn.check is not None and not turn.check.ready_for_mechanism_update
    assert NonDiscriminabilityReason.MISSING_PREREQUISITE in turn.check.reasons
    assert turn.decision_review["refusals"] == ["JevTransportError:unreachable"]
    assert turn.decision_review["findings"] == [] and turn.decision_review["judgments"] == []

    saying_yes = TypedDecisionCritic(RecordedJevClient({
        "decision_separation": {"probability": 0.99},
        "evidence_sufficiency": {"value": 5},
    }))
    controller = _controller(tmp_path / "second", StubClient([TASK, PLAN]), critic=saying_yes)
    turn = controller.run("Resolve.", available_actions=(blocked, functional),
                          intervention_profile=FunctionalInterventionProfile(mode="inhibition"))
    assert NonDiscriminabilityReason.MISSING_PREREQUISITE in turn.check.reasons
    assert [action.identifier for action in turn.selected_actions] == ["activity"]


def test_without_a_typesafe_block_the_loop_is_unchanged(tmp_path: Path, monkeypatch):
    for name in ("TYPESAFE_API_KEY", "TYPESAFE_MODEL", "TYPESAFE_ENDPOINT"):
        monkeypatch.delenv(name, raising=False)
    assert TypeSafeSettings.from_workspace(tmp_path) is None
    controller = _controller(tmp_path, StubClient([TASK, PLAN]))
    turn = controller.run("Resolve.", available_actions=ACTIONS,
                          intervention_profile=FunctionalInterventionProfile(mode="inhibition"))
    assert controller.decision_critic is None and turn.decision_review == {}


def test_the_planner_accepts_a_caller_critique_in_the_same_back_prompt_loop():
    client = StubClient([PLAN, dict(PLAN, action_identifier="activity")])
    seen: list[str] = []

    def critique(proposal):
        seen.append(proposal.action_identifier)
        return ("A typed decision model prefers 'activity'.",) if proposal.action_identifier == "viability" else ()

    proposal = MechanismContrastPlanner(client).propose(
        __import__("agent.context", fromlist=["ContextPacket"]).ContextPacket(
            __import__("agent.context", fromlist=["TaskIntent"]).TaskIntent(
                "mechanism_diagnosis", "Q", (), (), None, None, (), (), (), False),
            (), (), "context"),
        ACTIONS, extra_critique=critique,
    )
    assert seen == ["viability", "activity"]
    assert proposal.action_identifier == "activity"
    assert client.calls[1][0][-1]["content"].startswith("CRITIC_FEEDBACK")
    assert "prefers 'activity'" in client.calls[1][0][-1]["content"]
