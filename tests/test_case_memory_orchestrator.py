"""End-to-end tests: user state -> forecasts, the gated pipeline, the orchestrator path, the tool.

File summary
- Path: tests/test_case_memory_orchestrator.py
- Purpose: prove the case memory works through the real production seams, not only as isolated
  modules: (1) the same action under two different user states forecasts differently when the
  feature arm carries state; (2) the gated pipeline runs compiler -> graph -> retriever ->
  forecaster -> decision-value ranking -> branching plan; (3) the orchestrator keeps its default
  behaviour with the flag off and uses the case-memory forecaster through discrimination
  selection with the flag on; (4) the runtime tool honours its contract and its typed refusals.
- Depends on: src/maestro/*case_memory*, src/agent/{orchestrator,case_memory_wiring}.py,
  tools/case_memory/tool.py, the fixture style of tests/test_discriminating_acquisition.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.memory import RunLogger
from agent.memory import CaseStore
from agent.context import ContextBuilder, TaskInterpreter
from agent.knowledge import EvidenceLedger
from agent.memory import MemoryStore
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import MechanismContrastPlanner
from agent.llm import TemplateCompleter
from agent.llm import VisualInspector
from maestro import MAESTROAgent
from maestro import case_memory as CM
from maestro import case_update as MP
from maestro import adaptive_retrieval as DR
from maestro import hypothesis_forecast as HF
from maestro.acquisition import OutcomeBranch, outcome_consequences
from maestro.models import (
    EvidenceAction,
    EvidenceScope,
    FunctionalInterventionProfile,
)
from maestro.outcome import InterpretationTable, OutcomeRule

_PROFILE = FunctionalInterventionProfile(mode="small_molecule", context_identifier="NCI-H596",
                                         time_hours=24.0)

from tests.fixtures.case_memory_forecasting import (
    H1, H2, _actions, _compiled_problem, _contrast, _episode, _state, _store,
)


# -------------------------------------------------------------------------------- user state
def test_the_same_action_forecasts_differently_under_two_user_states(monkeypatch):
    """Directional information reaches the forecast: opposite states weight opposite precedents."""

    monkeypatch.setenv("MAESTRO_CASE_MEMORY_ENABLED", "1")
    positive = _episode("ep-pos", +1)
    negative = CM.episode_from_dict({**CM.episode_to_dict(_episode("ep-neg", -1, ())),
                                     "hypothesis_updates": []})
    store = _store((positive, negative))
    forecaster = HF.CaseMemoryOutcomeForecaster(store, feature_arm=DR.FeatureArm.COMBINED)
    action = _actions()[0]
    up = forecaster.forecast(_contrast(), (action,), None, _state(+1))[action.identifier]
    down = forecaster.forecast(_contrast(), (action,), None, _state(-1))[action.identifier]
    assert up != down
    same_up = forecaster.forecast(_contrast(), (action,), None, _state(+1))[action.identifier]
    assert same_up == up  # cache identity includes the user state, not a random draw


def test_scalar_arm_is_state_blind_where_the_combined_arm_is_not(monkeypatch):
    monkeypatch.setenv("MAESTRO_CASE_MEMORY_ENABLED", "1")
    store = _store((_episode("ep-pos", +1), _episode("ep-neg", -1, ())))
    action = _actions()[0]
    scalar = HF.CaseMemoryOutcomeForecaster(store, feature_arm=DR.FeatureArm.SCALAR)
    up = scalar.forecast(_contrast(), (action,), None, _state(+1))[action.identifier]
    down = scalar.forecast(_contrast(), (action,), None, _state(-1))[action.identifier]
    assert up == down


def test_forecast_prefers_realised_case_measurements_over_heuristic_mapping(monkeypatch):
    monkeypatch.setenv("MAESTRO_CASE_MEMORY_ENABLED", "1")
    episodes = []
    for i in range(6):
        episode = _episode(f"measured-{i}", +1)
        data = CM.episode_to_dict(episode)
        data["real_measurements"] = [{
            "action_id": "measure_low", "status": "qualified", "outcome_label": "match_h1",
            "conditioning_hypothesis": H1, "contrast": [H1, H2],
            "independent_units": 1, "source": "fixture-real-result",
        }]
        episodes.append(CM.episode_from_dict(data))
    episodes.append(_episode("other-stratum", +1))
    forecast = HF.CaseMemoryOutcomeForecaster(_store(episodes)).forecast(
        _contrast(), (_actions()[0],), None)["measure_low"]
    realised = forecast.branch_for(H1)
    assert realised is not None
    assert "observed_label_frequencies" in forecast.basis
    assert realised.probabilities[f"match_{H1}"] > realised.probabilities[f"match_{H2}"]


# -------------------------------------------------------------------------------- pipeline


def test_the_gated_pipeline_runs_end_to_end_in_research_mode():
    store = _store([_episode(f"ep-{i}", +1) for i in range(6)])
    compiled = _compiled_problem()
    actions = _actions()
    rules = (
        OutcomeRule("realised", "match_h1", frozenset({"response_detected"}),
                    eliminates=frozenset({H2}), scope=EvidenceScope.MECHANISM_CONTRAST),
        OutcomeRule("not_realised", "match_h2", frozenset({"no_response"}),
                    eliminates=frozenset({H1}), scope=EvidenceScope.MECHANISM_CONTRAST),
    )
    candidates = (CM.CandidateAction("measure_low", "low dose", "readout_measurement", 8.0, 2.0, "x"),
                  CM.CandidateAction("measure_high", "high dose", "readout_measurement", 8.0, 2.0, "x"))
    result = MP.run_case_memory_path(
        compiled, store, _contrast(), actions, None,
        candidate_actions=candidates, consequences=outcome_consequences(rules),
        research_mode=True)
    assert result.activated, [f"{f.gate}:{f.detail}" for f in result.gate_failures]
    assert result.forecasts["measure_low"]["calibration_status"] == "uncalibrated"
    assert result.rankings and result.branching_plans
    assert all(p.on_invalid == "invalid:no_biological_hypothesis_update" for p in result.branching_plans)


def test_the_pipeline_refuses_when_the_flag_is_off(monkeypatch):
    monkeypatch.delenv("MAESTRO_CASE_MEMORY_ENABLED", raising=False)
    store = _store([_episode(f"ep-{i}", +1) for i in range(6)])
    result = MP.run_case_memory_path(_compiled_problem(), store, _contrast(), _actions(), None)
    assert not result.activated and result.refusal == "case_memory_disabled"
    assert result.gate_failures[0].gate == "feature_flag"


def test_the_pipeline_names_the_support_gate_when_precedents_are_thin(monkeypatch):
    monkeypatch.setenv("MAESTRO_CASE_MEMORY_ENABLED", "1")
    store = _store([_episode("ep-0", +1)])
    result = MP.run_case_memory_path(_compiled_problem(), store, _contrast(), _actions(), None)
    assert not result.activated
    assert any(f.gate == "support" for f in result.gate_failures)


# -------------------------------------------------------------------------------- orchestrator
TRIAGE = {
    "task_type": "mechanism_diagnosis",
    "research_question": "Is the transcriptional response of drugA realised in NCI-H596?",
    "target_or_targets": ["TARGET_A"], "interventions": ["drugA"], "biological_context": "NCI-H596",
    "phenotype_endpoint": "transcriptome shift", "supplied_evidence": [], "constraints": [],
    "missing_information": [], "evidence_gaps": ["proximal target activity"], "needs_visual_review": False,
}
PLAN = {
    "identifier": "realisation-contrast",
    "hypotheses": [
        {"identifier": H1, "description": "The exposure perturbs the transcriptome.",
         "proposed_action": "continue", "causal_factor": "unresolved"},
        {"identifier": H2, "description": "The exposure does not perturb the transcriptome.",
         "proposed_action": "revise_intervention", "causal_factor": "incomplete_perturbation"},
    ],
    "differing_assumptions": ["whether the exposure changes RNA abundance"],
    "action_identifier": "measure_low",
    "outcome_categories": ["response_detected", "no_detectable_response"],
    "interpretation_boundaries": ["An RNA-level response does not establish target engagement."],
}
NO_REPAIR = {"action_identifier": None, "modified_fields": [], "rationale": "none",
             "remaining_limitations": []}


class _UnavailableWorldModel:
    name = "unavailable_stub"

    def capabilities(self):
        from virtual_cell.interface import ModelCapabilities
        return ModelCapabilities("stub", "stub-1", "none", "none", (), True, False, False, None)

    def assess_query(self, request):
        from virtual_cell.interface import QueryAssessment, QuerySupport
        return QueryAssessment(QuerySupport.UNSUPPORTED, (), ("no model",), self.capabilities())

    def predict(self, request):
        from virtual_cell import StatePrediction
        return StatePrediction(False, None, None, ("no model",), request_id=request.request_id,
                               model_version="stub-1", abstain_reason="model_unavailable")


def _runtime_rules() -> tuple[OutcomeRule, ...]:
    return (
        OutcomeRule("realised", "response_detected", frozenset({"realization:transcript_response:detected"}),
                    eliminates=frozenset({H2}), scope=EvidenceScope.MECHANISM_CONTRAST),
        OutcomeRule("absent", "no_detectable_response", frozenset({"no_detectable_response"}),
                    scope=EvidenceScope.INTERVENTION_IMPLEMENTATION),
    )


def _orchestrator(tmp_path: Path, **options) -> MAESTROOrchestrator:
    client = TemplateCompleter({"task_triage": TRIAGE, "contrast_planner": PLAN, "repair_planner": NO_REPAIR})
    root = tmp_path / "state"
    memory = MemoryStore(root / "memory.sqlite")
    return MAESTROOrchestrator(
        interpreter=TaskInterpreter(client),
        context_builder=ContextBuilder(EvidenceLedger(root / "evidence.sqlite"), memory),
        planner=MechanismContrastPlanner(client),
        visual_inspector=VisualInspector(client, "unused"),
        memory=memory, logger=RunLogger(root), controller=MAESTROAgent(),
        virtual_cell=_UnavailableWorldModel(),
        interpretation_table=InterpretationTable(_runtime_rules()),
        case_store=CaseStore(root / "cases.sqlite"),
        **options,
    )


def _runtime_actions() -> tuple[EvidenceAction, ...]:
    common = dict(cost=1.0, distinguishes=(H1, H2), supplies=("realization:transcript_response",),
                  expected_outcomes={H1: "response_detected", H2: "no_detectable_response"})
    return (EvidenceAction("measure_low", "low dose", time_hours=24.0, **common),
            EvidenceAction("measure_high", "high dose", time_hours=24.0, **common))


def _events(tmp_path: Path, kind: str) -> list[dict]:
    lines = (tmp_path / "state" / "events.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip() and json.loads(line)["kind"] == kind]


def test_orchestrator_default_behaviour_is_unchanged_with_the_flag_off(tmp_path, monkeypatch):
    """With the flag unset, the environment wiring yields no forecaster and coverage stays in charge."""

    monkeypatch.delenv("MAESTRO_CASE_MEMORY_ENABLED", raising=False)
    from agent.planner import forecaster_from_environment
    assert forecaster_from_environment() is None
    turn = _orchestrator(tmp_path, outcome_forecaster=forecaster_from_environment()).run(
        "Which exposure should be measured first?", available_actions=_runtime_actions(),
        intervention_profile=_PROFILE, case_id="wired-off", budget=1.0)
    assert turn.selected_actions
    assert not _events(tmp_path, "discrimination_selection_computed")
    completed = _events(tmp_path, "budget_selection_completed")[-1]["payload"]
    assert completed["selection_path"] in ("budgeted", "expected_coverage")


def test_orchestrator_uses_the_case_memory_forecaster_with_the_flag_on(tmp_path, monkeypatch):
    """With the flag on and support present, discrimination selection consumes the memory forecasts."""

    monkeypatch.setenv("MAESTRO_CASE_MEMORY_ENABLED", "1")
    store = _store([_episode(f"ep-{i}", +1) for i in range(6)])
    forecaster = HF.CaseMemoryOutcomeForecaster(store, outcome_mode="attempted_experiment")
    turn = _orchestrator(tmp_path, outcome_forecaster=forecaster,
                         discrimination_selection=True).run(
        "Which exposure should be measured first?", available_actions=_runtime_actions(),
        intervention_profile=_PROFILE, case_id="wired-on", budget=1.0)
    computed = _events(tmp_path, "discrimination_selection_computed")
    assert computed, "the discrimination path never ran"
    assert turn.selected_actions
    forecast = forecaster.forecast(_contrast(), _runtime_actions(), None)["measure_low"]
    assert forecast.evidence_kind.value == "model_prediction" and forecast.refusal is None


# -------------------------------------------------------------------------------- tool contract
def _problem_file(tmp_path: Path, store: CM.EpisodeStore | None, **overrides) -> Path:
    store_path = ""
    if store is not None:
        store_path = tmp_path / "episodes.jsonl.gz"
        store.path = store_path
        store._flush()
    payload = {
        "problem_id": "user-1", "user_question": "mechanism?", "evaluation": True,
        "hypotheses": [H1, H2], "assay": "readout_measurement", "biological_system": "",
        "measurement_type": "", "control_design": "vehicle", "intervention_type": "compound",
        "context": {"cell_line": "NCI-H596", "time_h": 24.0, "dose_nM": 500.0},
        "signed_feature_delta": {"EGR1": 2.0},
        "episode_store": str(store_path),
        "actions": [{"action_id": "measure_low", "description": "low dose", "assay": "readout_measurement",
                     "cost_wells": 8.0, "duration_days": 2.0, "readout": "x",
                     "consequences": {"match_h1": [H2], "match_h2": [H1]}}],
    }
    payload.update(overrides)
    path = tmp_path / "problem.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _tool():
    from tools.case_memory import tool
    return tool


def test_tool_returns_the_full_contract_for_a_valid_problem(tmp_path):
    store = _store([_episode(f"ep-{i}", +1) for i in range(6)])
    problem = _problem_file(tmp_path, store)
    receipt = _tool().run({"dataset_path": str(problem), "research_mode": True})
    assert receipt["status"] == "ok" and receipt["mode"] == "research_evaluation"
    observation = receipt["observations"][0]
    assert observation["calibration_status"] == "uncalibrated"
    assert observation["applicable"] and observation["branches"]
    branch = observation["branches"][0]
    assert abs(sum(branch["probabilities"].values()) - 1.0) < 1e-6 and branch["support"] >= 1
    assert set(branch["probabilities"]) == {"match_h1", "match_h2", "unresolved", "absent"}
    assert receipt["retrieval"][H1]["precedents"]
    assert receipt["action_ranking"] and receipt["branching_interpretation_plan"]


def test_tool_refuses_a_problem_without_a_control(tmp_path):
    problem = _problem_file(tmp_path, None, control_design="")
    receipt = _tool().run({"dataset_path": str(problem), "research_mode": True})
    assert receipt["status"] == "refused" and receipt["reason"] == "missing_control"


def test_tool_abstains_with_insufficient_support(tmp_path):
    problem = _problem_file(tmp_path, CM.EpisodeStore())
    receipt = _tool().run({"dataset_path": str(problem), "research_mode": True})
    assert receipt["status"] == "abstained" and receipt["reason"] == "insufficient_outcome_support"
    assert receipt["calibration_status"] == "uncalibrated"


def test_tool_marks_low_support_branches_instead_of_hiding_them(tmp_path):
    store = _store([_episode("ep-0", +1)])
    problem = _problem_file(tmp_path, store)
    receipt = _tool().run({"dataset_path": str(problem), "research_mode": True})
    assert receipt["status"] == "ok"
    branches = receipt["observations"][0]["branches"]
    assert all(b["low_support"] for b in branches)


def test_tool_refuses_when_the_case_memory_is_disabled(tmp_path, monkeypatch):
    monkeypatch.delenv("MAESTRO_CASE_MEMORY_ENABLED", raising=False)
    store = _store([_episode(f"ep-{i}", +1) for i in range(6)])
    problem = _problem_file(tmp_path, store)
    receipt = _tool().run({"dataset_path": str(problem)})
    assert receipt["status"] == "refused" and receipt["reason"] == "case_memory_disabled"


def test_tool_production_mode_succeeds_only_with_the_flag(tmp_path, monkeypatch):
    monkeypatch.setenv("MAESTRO_CASE_MEMORY_ENABLED", "1")
    store = _store([_episode(f"ep-{i}", +1) for i in range(6)])
    problem = _problem_file(tmp_path, store)
    receipt = _tool().run({"dataset_path": str(problem)})
    assert receipt["status"] == "ok" and receipt["mode"] == "production"


def test_tool_research_mode_never_impersonates_a_production_answer(tmp_path):
    store = _store([_episode(f"ep-{i}", +1) for i in range(6)])
    problem = _problem_file(tmp_path, store, evaluation=False)
    receipt = _tool().run({"dataset_path": str(problem), "research_mode": True})
    assert receipt["status"] == "refused"
    assert receipt["reason"] == "research_mode_requires_evaluation_payload"


def test_tool_refuses_malformed_input(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    receipt = _tool().run({"dataset_path": str(bad), "research_mode": True})
    assert receipt["status"] == "refused" and receipt["reason"] == "malformed_input"
    assert _tool().run({"dataset_path": str(tmp_path / "absent.json")})["reason"] == "dataset_path_missing"
