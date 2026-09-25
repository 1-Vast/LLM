"""The agent corrects its own contract violations and reasons with the virtual cell's answers.

File summary
- Path: tests/test_agent_world_model_integration.py
- Purpose: pin the agent-side and virtual-cell-integration behaviour added together:
  bounded planner self-correction, cross-round prediction reuse, the planning-only
  world-model briefing, registered hypotheses across a loop, and runtime configuration.
- Core points: assertions here are contract tests, not biological results; each test pins
  one boundary that must not silently move.
- Interfaces: pytest tests only
- Depends on: agent, maestro, virtual_cell, tools.shared
"""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest

from agent import llm as llm_module
from agent.audit import RunLogger
from agent.cases import CaseStore
from agent.cli import _hypotheses, main
from agent.configuration import ConfigurationError, MAESTROSettings
from agent.context import ContextBuilder, ContextPacket, TaskIntent, TaskInterpreter
from agent.knowledge import EvidenceLedger
from agent.llm import DeepSeekChatClient
from agent.memory import MemoryStore
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import MechanismContrastPlanner, PlannerContractError
from agent.template_client import TemplateCompleter
from agent.vision import VisualInspector
from agent.world_model_briefing import BRIEFING_HEADING, render_world_model_briefing, world_model_rows
from maestro import EvidenceAction, FunctionalInterventionProfile, MAESTROAgent
from maestro.models import (
    ContrastCheck,
    DevelopmentAction,
    EvidenceActionKind,
    MechanismContrast,
    MechanismHypothesis,
    NonDiscriminabilityReason,
)
from maestro.reliability import PredictionReliabilityLedger
from virtual_cell import (
    Intervention,
    Interval,
    IntervalKind,
    ModelCapabilities,
    PredictionCache,
    PredictionRequest,
    QueryAssessment,
    QuerySupport,
    StatePrediction,
    SystemContext,
    VirtualCellQueryTemplate,
)
from virtual_cell.cache import REUSE_NOTE_PREFIX

from tools.shared.stub_client import StubClient  # noqa: E402

TASK = {
    "task_type": "mechanism_diagnosis", "research_question": "Resolve discrepancy.",
    "target_or_targets": ["TARGET"], "interventions": ["compound"],
    "biological_context": "cell-a", "phenotype_endpoint": "viability",
    "supplied_evidence": [], "constraints": [], "missing_information": [], "needs_visual_review": False,
}
HYPOTHESES = [
    {"identifier": "a", "description": "A", "proposed_action": "continue"},
    {"identifier": "b", "description": "B", "proposed_action": "revise_intervention"},
]


def _plan(action: str, hypotheses=None) -> dict:
    return {
        "identifier": "contrast", "hypotheses": hypotheses if hypotheses is not None else HYPOTHESES,
        "differing_assumptions": ["model readout"], "action_identifier": action,
        "outcome_categories": ["a", "b"], "interpretation_boundaries": ["Prediction is not a measurement."],
    }


def _packet() -> ContextPacket:
    intent = TaskIntent("mechanism_diagnosis", "Question", (), (), None, None, (), (), (), False)
    return ContextPacket(intent, (), (), "public context")


class CountingWorldModel:
    """Answers registered labels only and counts real inferences."""

    name = "counting"

    def __init__(self, supported=("drug-known",)):
        self.supported = frozenset(supported)
        self.predictions = 0

    def capabilities(self):
        return ModelCapabilities("test", "model-1", "embedding", "condition", ("drug",), True, False, False, None)

    def assess_query(self, request):
        if request.intervention.identifier not in self.supported:
            return QueryAssessment(QuerySupport.UNSUPPORTED, (), ("unregistered perturbation",), self.capabilities())
        return QueryAssessment(QuerySupport.SUPPORTED, (), (), self.capabilities())

    def predict(self, request):
        self.predictions += 1
        return StatePrediction(
            True, {"embedding_delta_l2": 1.25}, None, ("fixture output",),
            intervals={
                "embedding_delta_l2": Interval(
                    1.0, 1.5, kind=IntervalKind.CALIBRATED, level=0.9, basis="fixture residuals"
                )
            },
            request_id=request.request_id, model_version=request.model_version,
            confidence=None, in_distribution=True, compute_cost=3.0,
            uncertainty_components={"fixture": "not independently calibrated"},
        )


def _request(request_id="r1", *, case_id="case-1", dose=None) -> PredictionRequest:
    return PredictionRequest(
        request_id, case_id, "contrast", 1,
        Intervention("drug-known", "drug", ("TARGET",), dose=dose, dose_unit="uM" if dose is not None else None),
        SystemContext("cell-a", "cell line", dataset_id="dataset", control_dataset_id="control"),
        ("embedding_delta_l2",), "model-1",
    )


def _controller(root: Path, client, *, world_model=None, repair=False, case_store=False, **kwargs):
    memory = MemoryStore(root / "memory.sqlite")
    return MAESTROOrchestrator(
        interpreter=TaskInterpreter(client),
        context_builder=ContextBuilder(EvidenceLedger(root / "evidence.sqlite"), memory),
        planner=MechanismContrastPlanner(client),
        visual_inspector=VisualInspector(client, "vision"),
        memory=memory,
        logger=RunLogger(root),
        controller=MAESTROAgent(),
        virtual_cell=world_model,
        enable_llm_repair=repair,
        case_store=CaseStore(root / "cases.sqlite") if case_store else None,
        **kwargs,
    )


def _events(root: Path, kind: str) -> list[dict]:
    lines = (root / "events.jsonl").read_text(encoding="utf-8").splitlines()
    return [record["payload"] for record in map(json.loads, lines) if record["kind"] == kind]


# --------------------------------------------------------------------------------------
# Planner self-correction
# --------------------------------------------------------------------------------------


def test_a_contract_violation_is_named_back_once_and_the_corrected_answer_is_used():
    three = _plan("assay", HYPOTHESES + [{"identifier": "c", "description": "C", "proposed_action": "stop"}])
    client = StubClient([three, _plan("assay")])
    planner = MechanismContrastPlanner(client)

    proposal = planner.propose(_packet(), (EvidenceAction("assay", "Assay", 1.0, ("a", "b")),))

    assert [item.identifier for item in proposal.hypotheses] == ["a", "b"]
    assert len(client.calls) == 2
    retry = client.calls[1][0]
    # The system prompt is unchanged, so a template completer still recognises the component.
    assert retry[0] == client.calls[0][0][0]
    assert retry[-2]["role"] == "assistant" and json.loads(retry[-2]["content"]) == three
    assert retry[-1]["role"] == "user" and retry[-1]["content"].startswith("CONTRACT_VIOLATION")
    assert "received 3" in retry[-1]["content"]
    assert planner.contract_violations == ["Mechanism planner must return exactly two hypotheses; received 3."]


def test_a_second_violation_still_raises_and_zero_retries_raise_at_once():
    bad = {"identifier": "x", "hypotheses": []}
    with pytest.raises(PlannerContractError, match="received 0"):
        MechanismContrastPlanner(StubClient([bad, bad])).propose(_packet(), ())
    client = StubClient([bad, _plan("assay")])
    with pytest.raises(PlannerContractError):
        MechanismContrastPlanner(client, contract_retries=0).propose(_packet(), ())
    assert len(client.calls) == 1
    with pytest.raises(ValueError):
        MechanismContrastPlanner(client, contract_retries=-1)


def test_registered_identifiers_are_named_in_the_violation():
    client = StubClient([_plan("assay"), _plan("assay", [dict(HYPOTHESES[0], identifier="x"), HYPOTHESES[1]])])
    with pytest.raises(PlannerContractError, match=r"expected \['fixed-a', 'fixed-b'\]"):
        MechanismContrastPlanner(client).propose(
            _packet(), (), required_hypothesis_identifiers=("fixed-a", "fixed-b")
        )


def test_a_repair_that_edits_an_outside_field_is_corrected_within_its_contract():
    outside = {"action_identifier": "b", "modified_fields": ["plan.cost"], "rationale": "cheaper"}
    inside = {"action_identifier": "b", "modified_fields": ["plan.action_identifier"], "rationale": "ok"}
    client = StubClient([outside, inside])
    contrast = MechanismContrast(
        "c", (MechanismHypothesis("a", "A"), MechanismHypothesis("b", "B")), (), None
    )
    check = ContrastCheck(False, False, False, False, (NonDiscriminabilityReason.INVALID_ACTION,))
    draft = MechanismContrastPlanner(client).propose_repair(_packet(), contrast, check, ())
    assert draft.action_identifier == "b"
    assert "plan.cost" in client.calls[1][0][-1]["content"]


def test_the_template_completer_serves_the_corrected_answer_to_the_same_component():
    three = _plan("assay", HYPOTHESES + [{"identifier": "c", "description": "C", "proposed_action": "stop"}])
    completer = TemplateCompleter({"contrast_planner": [three, _plan("assay")]}, repeat_last=False)
    proposal = MechanismContrastPlanner(completer).propose(_packet(), ())
    assert len(proposal.hypotheses) == 2
    assert [call["component"] for call in completer.calls] == ["contrast_planner", "contrast_planner"]


# --------------------------------------------------------------------------------------
# Prediction reuse
# --------------------------------------------------------------------------------------


def test_an_identical_query_is_reused_with_new_lineage_and_no_compute():
    cache = PredictionCache()
    model = CountingWorldModel()
    first = _request("r1")
    assessment = model.assess_query(first)
    prediction = model.predict(first)
    assert cache.store(first, "counting", assessment, prediction)

    hit = cache.lookup(_request("r2", case_id="another-case"), "counting")
    assert hit is not None
    _, reused, origin = hit
    assert origin == "r1"
    assert reused.request_id == "r2"
    assert reused.compute_cost == 0.0
    assert reused.state_change == prediction.state_change
    assert reused.limitations[-1].startswith(REUSE_NOTE_PREFIX + "r1")
    assert reused.contract_valid

    # A different model input, or a different backend, is a different query.
    assert cache.lookup(_request("r3", dose=1.0), "counting") is None
    assert cache.lookup(_request("r4"), "other-backend") is None
    assert cache.stats() == {"entries": 1, "hits": 1, "misses": 2}


def test_abstentions_invalid_requests_and_mismatched_lineage_are_never_stored():
    cache = PredictionCache(max_entries=1)
    request = _request("r1")
    abstention = StatePrediction(
        False, None, None, ("refused",), request_id="r1", model_version="model-1", abstain_reason="query_unsupported",
        compute_cost=0.0,
    )
    assessment = CountingWorldModel().assess_query(request)
    assert not cache.store(request, "counting", assessment, abstention)
    borrowed = CountingWorldModel().predict(_request("other"))
    assert not cache.store(request, "counting", assessment, borrowed)
    assert cache.key_for(replace(request, readouts=()), "counting") is None
    # Bounded: the oldest entry makes room for the newest.
    assert cache.store(request, "counting", assessment, CountingWorldModel().predict(request))
    newer = _request("r2", dose=2.0)
    assert cache.store(newer, "counting", assessment, CountingWorldModel().predict(newer))
    assert cache.lookup(_request("r5"), "counting") is None
    assert cache.lookup(_request("r6", dose=2.0), "counting") is not None
    with pytest.raises(ValueError):
        PredictionCache(max_entries=0)


def _template() -> VirtualCellQueryTemplate:
    return VirtualCellQueryTemplate(
        "drug-known", "drug",
        SystemContext("cell-a", "cell line", dataset_id="dataset", control_dataset_id="control"),
        ("embedding_delta_l2",), "model-1",
        action_interventions={"model-guided": "drug-known", "plain": "drug-unknown"},
    )


def _actions() -> tuple[EvidenceAction, ...]:
    plain = EvidenceAction(
        "plain", "Plain assay.", 1.0, ("a", "b"), expected_outcomes={"a": "outcome_a", "b": "outcome_b"},
    )
    model_guided = EvidenceAction(
        "model-guided", "Model-aligned assay.", 1.0, ("a", "b"),
        prediction_readout="embedding_delta_l2", prediction_relevance=1.0,
        expected_outcomes={"a": "outcome_a", "b": "outcome_b"},
    )
    return plain, model_guided


def test_a_second_round_reuses_the_first_rounds_inference(tmp_path: Path):
    client = StubClient([TASK, _plan("plain"), TASK, _plan("plain")])
    world_model = CountingWorldModel()
    controller = _controller(tmp_path, client, world_model=world_model)
    profile = FunctionalInterventionProfile(mode="inhibition")

    first = controller.run("Resolve.", available_actions=_actions(), intervention_profile=profile,
                           case_id="case", virtual_cell_template=_template(), session_id="round-1")
    second = controller.run("Resolve.", available_actions=_actions(), intervention_profile=profile,
                            case_id="case", virtual_cell_template=_template(), session_id="round-2")

    assert world_model.predictions == 1
    reused = second.action_predictions["model-guided"]
    assert reused.request_id == second.action_prediction_requests["model-guided"].request_id == "round-2.model-guided"
    assert reused.compute_cost == 0.0
    assert first.action_predictions["model-guided"].compute_cost == 3.0
    row = next(item for item in second.world_model_rows if item.action == "model-guided")
    assert row.reused_from_request == "round-1.model-guided"
    assert "1 reused from an identical earlier query" in second.response

    fresh = _controller(tmp_path / "off", StubClient([TASK, _plan("plain"), TASK, _plan("plain")]),
                        world_model=(counted := CountingWorldModel()), reuse_predictions=False)
    for session in ("s1", "s2"):
        fresh.run("Resolve.", available_actions=_actions(), intervention_profile=profile,
                  case_id="case", virtual_cell_template=_template(), session_id=session)
    assert counted.predictions == 2


# --------------------------------------------------------------------------------------
# Planning-only briefing
# --------------------------------------------------------------------------------------


def test_the_repair_planner_sees_predictions_and_abstentions_labelled_as_planning_only(tmp_path: Path):
    blocked = EvidenceAction(
        "model-guided", "Model-aligned viability assay.", 5.0, ("a", "b"),
        prerequisites=("functional:target_activity",),
        prediction_readout="embedding_delta_l2", prediction_relevance=1.0,
        expected_outcomes={"a": "outcome_a", "b": "outcome_b"},
    )
    functional = EvidenceAction(
        "plain", "Proximal target activity.", 2.0, ("a",), kind=EvidenceActionKind.FUNCTIONAL_MEASUREMENT,
    )
    repair = {"action_identifier": "plain", "modified_fields": ["plan.action_identifier"],
              "rationale": "Measure function first.", "remaining_limitations": ["Still unmeasured."]}
    client = StubClient([TASK, _plan("model-guided"), repair])
    controller = _controller(tmp_path, client, world_model=CountingWorldModel(), repair=True)

    turn = controller.run("Resolve.", available_actions=(blocked, functional),
                          intervention_profile=FunctionalInterventionProfile(mode="inhibition"),
                          case_id="case", virtual_cell_template=_template())

    content = client.calls[2][0][1]["content"]
    section = content[content.index(BRIEFING_HEADING):]
    rows = {row["action"]: row for row in map(json.loads, section.splitlines()[BRIEFING_HEADING.count("\n") + 1:])}
    assert rows["model-guided"]["status"] == "predicted"
    assert rows["model-guided"]["value"] == 1.25
    assert rows["model-guided"]["interval"] == [1.0, 1.5]
    assert rows["model-guided"]["interval_claims_coverage"] is True
    assert rows["model-guided"]["reliability_weight"] == 1.0
    assert rows["plain"]["status"] == "abstained"
    assert rows["plain"]["abstain_reason"] == "query_unsupported"
    # The briefing informs the proposal; it never becomes a satisfied premise: the gated
    # action stays blocked and the step executed is the functional measurement.
    assert turn.check is not None and not turn.check.ready_for_mechanism_update
    assert [action.identifier for action in turn.selected_actions] == ["plain"]
    assert "Virtual cell: 1 of 2 action queries answered" in turn.response
    assert "abstained on plain" in turn.response


def test_a_revoked_readout_is_reported_with_zero_weight():
    ledger = PredictionReliabilityLedger()
    for index in range(6):
        ledger.record_pair(
            model_version="model-1", readout="embedding_delta_l2", predicted_value=1.25, realized_value=9.0,
            interval=(1.0, 1.5), context_identifier="cell-a", source_cluster=f"s{index}", result_id=f"x{index}",
        )
    model = CountingWorldModel()
    request = _request("r1")
    action = _actions()[1]
    rows = world_model_rows(
        (action,), {action.identifier: request}, {action.identifier: model.assess_query(request)},
        {action.identifier: model.predict(request)}, ledger,
    )
    assert rows[0].reliability_revoked is True and rows[0].reliability_weight == 0.0
    assert render_world_model_briefing(()) == ""


def test_an_unregistered_llm_repair_is_logged_rather_than_silently_dropped(tmp_path: Path):
    blocked = EvidenceAction("viability", "Viability.", 5.0, ("a", "b"), prerequisites=("functional:target_activity",))
    functional = EvidenceAction(
        "activity", "Activity.", 2.0, ("a",), kind=EvidenceActionKind.FUNCTIONAL_MEASUREMENT,
    )
    invented = {"action_identifier": "invented_assay", "modified_fields": ["plan.action_identifier"],
                "rationale": "Invented.", "remaining_limitations": []}
    client = StubClient([TASK, _plan("viability"), invented, invented])
    controller = _controller(tmp_path, client, repair=True)
    turn = controller.run("Resolve.", available_actions=(blocked, functional),
                          intervention_profile=FunctionalInterventionProfile(mode="inhibition"))
    assert turn.llm_repair is None
    # The critic named the unregistered action once; the repeated answer is then refused by name.
    assert client.calls[3][0][-1]["content"].startswith("CRITIC_FEEDBACK")
    assert "'invented_assay' is not in AVAILABLE_ACTIONS" in client.calls[3][0][-1]["content"]
    assert _events(tmp_path, "llm_repair_not_applicable") == [
        {"action_identifier": "invented_assay", "reason": "unregistered_action"}
    ]
    assert _events(tmp_path, "planner_critic_feedback")[0]["component"] == "repair_planner"


def test_a_corrected_contract_violation_is_on_the_run_record(tmp_path: Path):
    three = _plan("plain", HYPOTHESES + [{"identifier": "c", "description": "C", "proposed_action": "stop"}])
    client = StubClient([TASK, three, _plan("plain")])
    controller = _controller(tmp_path, client)
    turn = controller.run("Resolve.", available_actions=_actions(),
                          intervention_profile=FunctionalInterventionProfile(mode="inhibition"))
    assert turn.contrast is not None
    events = _events(tmp_path, "planner_contract_violation")
    assert events and events[0]["component"] == "contrast_planner"


# --------------------------------------------------------------------------------------
# Registered hypotheses across a loop
# --------------------------------------------------------------------------------------


def test_registered_hypotheses_keep_a_reworded_plan_from_ending_the_loop(tmp_path: Path):
    from tools.shared.biological_fixture import PLAN, contract, orchestrator, results

    actions, table, profile = contract()
    changed = {**PLAN, "hypotheses": [{**item, "description": item["description"] + " Reworded."}
                                      for item in PLAN["hypotheses"]]}
    registered = tuple(
        MechanismHypothesis(item["identifier"], item["description"], DevelopmentAction(item["proposed_action"]),
                            item["causal_factor"])
        for item in PLAN["hypotheses"]
    )
    agent = orchestrator(tmp_path, table=table, plans=[PLAN, changed, changed, changed])
    supplied = results()
    loop = agent.run_case_loop(
        "Check definitions", available_actions=actions, intervention_profile=profile,
        result_provider=lambda action, turn: supplied[action.identifier],
        case_id="definitions", budget=5.0, max_rounds=4, expected_hypotheses=registered,
    )
    assert loop.stop_reason != "hypothesis_definition_changed"
    assert len(loop.turns) >= 2
    assert all(turn.contrast.hypotheses == registered for turn in loop.turns)


# --------------------------------------------------------------------------------------
# Configuration, CLI and transport
# --------------------------------------------------------------------------------------

_PROVIDER = {
    "DEEPSEEK_API_KEY": "secret-key", "DEEPSEEK_BASE_URL": "https://example.org/v1/",
    "DEEPSEEK_MODEL": "model", "DEEPSEEK_VISION_MODEL": "vision",
}


def test_exported_settings_suffice_without_a_dotenv_file(tmp_path: Path, monkeypatch):
    for name, value in _PROVIDER.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("MAESTRO_LOG_DIRECTORY", "runs/today")
    settings = MAESTROSettings.from_workspace(tmp_path)
    assert settings.base_url == "https://example.org/v1"
    assert settings.log_directory == tmp_path / "runs" / "today"
    assert "secret-key" not in repr(settings)

    monkeypatch.delenv("MAESTRO_LOG_DIRECTORY")
    assert MAESTROSettings.from_workspace(tmp_path).log_directory == tmp_path / "log" / "20260910"
    monkeypatch.delenv("DEEPSEEK_API_KEY")
    with pytest.raises(ConfigurationError, match="DEEPSEEK_API_KEY"):
        MAESTROSettings.from_workspace(tmp_path)


def test_the_cli_reports_an_unconfigured_provider_without_a_traceback(tmp_path: Path, monkeypatch, capsys):
    for name in (*_PROVIDER, "MAESTRO_LOG_DIRECTORY"):
        monkeypatch.delenv(name, raising=False)
    actions = tmp_path / "actions.json"
    actions.write_text(json.dumps([{"identifier": "a", "description": "A", "cost": 1, "distinguishes": ["x", "y"]}]))
    profile = tmp_path / "profile.json"
    profile.write_text(json.dumps({"mode": "inhibition"}))
    monkeypatch.setattr(sys, "argv", [
        "maestro", "Question", "--actions", str(actions), "--profile", str(profile),
        "--workspace", str(tmp_path), "--virtual-cell", "none",
    ])
    assert main() == 2
    assert "ConfigurationError" in capsys.readouterr().err


def test_cli_hypotheses_are_two_distinct_registered_definitions():
    parsed = _hypotheses([
        {"identifier": "a", "description": "A", "proposed_action": "continue", "causal_factor": "unresolved"},
        {"identifier": "b", "description": "B", "proposed_action": "stop"},
    ])
    assert parsed[0].proposed_action is DevelopmentAction.CONTINUE and parsed[1].causal_factor is None
    with pytest.raises(ValueError):
        _hypotheses([{"identifier": "a", "description": "A"}])
    with pytest.raises(ValueError):
        _hypotheses([{"identifier": "a", "description": "A"}, {"identifier": "a", "description": "B"}])


def test_a_rate_limited_request_waits_as_long_as_the_provider_asks(tmp_path: Path, monkeypatch):
    delays: list[float] = []
    headers = Message()
    headers["Retry-After"] = "7"
    attempts = iter([HTTPError("https://example.org", 429, "slow down", headers, None)])

    class Reply:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return json.dumps({"choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}]}).encode()

    def fake_urlopen(request, timeout):
        error = next(attempts, None)
        if error is not None:
            raise error
        return Reply()

    monkeypatch.setattr(llm_module, "urlopen", fake_urlopen)
    monkeypatch.setattr(llm_module, "sleep", delays.append)
    client = DeepSeekChatClient(MAESTROSettings("k", "https://example.org", "model", "vision", tmp_path))
    assert client.complete([]).content == "{}"
    assert delays == [7.0]


# --------------------------------------------------------------------------------------
# Critic back-prompting and compact rendering
# --------------------------------------------------------------------------------------

SAME_DECISION = [dict(HYPOTHESES[0]), dict(HYPOTHESES[1], proposed_action="continue")]


def test_the_critic_back_prompts_a_plan_that_cannot_separate_a_decision():
    client = StubClient([_plan("assay", SAME_DECISION), _plan("assay")])
    planner = MechanismContrastPlanner(client)
    proposal = planner.propose(_packet(), (EvidenceAction("assay", "Assay", 1.0, ("a", "b")),))
    assert {item.proposed_action for item in proposal.hypotheses} == {
        DevelopmentAction.CONTINUE, DevelopmentAction.REVISE_INTERVENTION
    }
    feedback = client.calls[1][0][-1]["content"]
    assert feedback.startswith("CRITIC_FEEDBACK") and "distinct development actions" in feedback
    assert planner.critic_findings and not planner.contract_violations


def test_a_critic_finding_left_after_the_budget_is_returned_for_the_controller_to_judge():
    client = StubClient([_plan("invented", SAME_DECISION), _plan("invented", SAME_DECISION)])
    proposal = MechanismContrastPlanner(client).propose(
        _packet(), (EvidenceAction("assay", "Assay", 1.0, ("a", "b")),)
    )
    # Soft: no exception, and the deterministic check still sees exactly what the model said.
    assert proposal.action_identifier == "invented"
    assert len(client.calls) == 2
    assert "'invented' is not in AVAILABLE_ACTIONS" in client.calls[1][0][-1]["content"]
    single = StubClient([_plan("invented", SAME_DECISION)])
    MechanismContrastPlanner(single, contract_retries=0).propose(_packet(), (EvidenceAction("assay", "A", 1.0, ("a",)),))
    assert len(single.calls) == 1


def test_registered_definitions_are_never_critiqued():
    registered = (MechanismHypothesis("a", "A", DevelopmentAction.DEFER), MechanismHypothesis("b", "B", DevelopmentAction.DEFER))
    client = StubClient([_plan("assay", SAME_DECISION)])
    proposal = MechanismContrastPlanner(client).propose(
        _packet(), (EvidenceAction("assay", "Assay", 1.0, ("a", "b")),),
        required_hypothesis_identifiers=("a", "b"), expected_hypotheses=registered,
    )
    assert proposal.hypotheses == registered and len(client.calls) == 1


def test_the_catalogue_omits_undeclared_fields_but_keeps_every_declaration():
    from dataclasses import asdict

    from agent.planner import render_catalogue, render_contrast
    from tools.shared.biological_fixture import contract

    actions, _, _ = contract()
    unbound = replace(actions[0], context_bound=False, prediction_relevance=0.0)
    rendered = json.loads(render_catalogue((unbound,) + actions[1:]))
    assert rendered[0]["context_bound"] is False and rendered[0]["prediction_relevance"] == 0.0
    assert "readout" not in rendered[0] and "interpretation_gate" not in rendered[0]
    assert rendered[2]["prerequisites"] == list(actions[2].prerequisites)
    full = json.dumps([asdict(action) for action in actions], allow_nan=False)
    assert len(render_catalogue(actions)) < 0.8 * len(full)

    contrast = MechanismContrast(
        "c", (MechanismHypothesis("a", "A"), MechanismHypothesis("b", "B")), (), actions[2],
        additional_plans=actions[:1],
    )
    payload = json.loads(render_contrast(contrast))
    assert payload["plan"] == "comparator" and payload["additional_plans"] == ["engagement"]
    assert payload["hypotheses"] == [{"identifier": "a", "description": "A"}, {"identifier": "b", "description": "B"}]


# --------------------------------------------------------------------------------------
# Parallel, deduplicated dispatch
# --------------------------------------------------------------------------------------


class SlowWorldModel(CountingWorldModel):
    """Every inference takes a fixed wall time; the counter is thread-safe."""

    name = "slow"

    def __init__(self, delay: float):
        super().__init__(supported=("drug-1", "drug-2", "drug-3"))
        import threading

        self._lock = threading.Lock()
        self._delay = delay
        self.labels: list[str] = []

    def predict(self, request):
        import time

        time.sleep(self._delay)
        with self._lock:
            self.labels.append(request.intervention.identifier)
        return super().predict(request)


def _parallel_case(root: Path, workers: int):
    import time

    labels = {"a1": "drug-1", "a2": "drug-2", "a3": "drug-3", "a4": "drug-1"}
    actions = tuple(
        EvidenceAction(name, "Assay.", 1.0, ("a", "b"), prediction_readout="embedding_delta_l2",
                       prediction_relevance=1.0, expected_outcomes={"a": "x", "b": "y"})
        for name in labels
    )
    template = replace(_template(), action_interventions=labels)
    model = SlowWorldModel(0.15)
    controller = _controller(root, StubClient([TASK, _plan("a1")]), world_model=model,
                             max_parallel_predictions=workers)
    started = time.perf_counter()
    turn = controller.run("Resolve.", available_actions=actions,
                          intervention_profile=FunctionalInterventionProfile(mode="inhibition"),
                          case_id="case", virtual_cell_template=template, session_id="s")
    return turn, model, time.perf_counter() - started


def test_distinct_queries_run_concurrently_once_each_and_log_in_request_order(tmp_path: Path):
    turn, model, elapsed = _parallel_case(tmp_path / "parallel", 3)
    sequential_turn, sequential_model, sequential_elapsed = _parallel_case(tmp_path / "sequential", 1)

    # a4 asks exactly what a1 asked: one inference, answered for both.
    assert sorted(model.labels) == ["drug-1", "drug-2", "drug-3"]
    assert sorted(sequential_model.labels) == ["drug-1", "drug-2", "drug-3"]
    assert turn.action_predictions["a4"].limitations[-1].startswith(REUSE_NOTE_PREFIX + "s.a1")
    assert elapsed < sequential_elapsed
    # Same answers and the same run record, whichever way inference was dispatched.
    assert turn.action_predictions.keys() == sequential_turn.action_predictions.keys()
    assert [row.as_payload() for row in turn.world_model_rows] == [
        row.as_payload() for row in sequential_turn.world_model_rows
    ]
    completed = [
        json.loads(line)["payload"]["request_id"]
        for line in (tmp_path / "parallel" / "experiments.jsonl").read_text().splitlines()
        if json.loads(line)["kind"] == "virtual_cell_prediction_completed"
    ]
    assert completed == ["s.a1", "s.a2", "s.a3"]
    with pytest.raises(ValueError):
        _controller(tmp_path / "bad", StubClient([]), max_parallel_predictions=0)
