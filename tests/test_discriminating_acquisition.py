"""Measurement choice by predicted discrimination, and the safety semantics around it.

File summary
- Path: tests/test_discriminating_acquisition.py
- Purpose: pin the repaired link from world-model output to the measurement MAESTRO buys. Each
  group states one failure the 2026-09-26 audit found in the old path: the power-aware selector
  dropped every world-model priority, per-hypothesis outcome forecasts could only reach a selector
  as one detection probability, a per-action query borrowed the template's exposure time, and a
  thinly supported forecast was deleted rather than discounted.
- Core points:
  - Counterexamples: a loud but non-separating action (magnitude trap), a costlier 72 h action that
    alone separates (late resolver), and equal correct-elimination odds with unequal wrong risk.
  - Runtime wiring: with power-aware selection on, changing only the action-level outcome
    forecasts changes the chosen action when discrimination selection is enabled, and nothing else
    about the case changes; magnitude alone still cannot move the power-aware choice (its keep
    rule was not met on 2026-09-26) and breaks only exact forecast ties.
  - Support: zero references refuse by name; one reference is served as visibly low-support,
    shrunk, and discounted by its wider interval.
  - Absence, prediction-derived records and failed QC still never remove a hypothesis.
  - The legacy selectors are characterised in the same tests, so each counterexample shows what
    the old path chose.
- Interfaces: pytest test functions
- Depends on: maestro.acquisition, maestro.outcome, maestro.selection, agent.orchestrator,
  agent.cases, virtual_cell
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from agent.audit import RunLogger
from agent.cases import CaseState, CaseStore, MeasurementResult
from agent.context import ContextBuilder, TaskInterpreter
from agent.knowledge import EvidenceLedger
from agent.memory import MemoryStore
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import MechanismContrastPlanner
from agent.template_client import TemplateCompleter
from agent.vision import VisualInspector
from maestro import EvidenceAction, FunctionalInterventionProfile, MAESTROAgent
from maestro.acquisition import (
    OutcomeBranch,
    OutcomeForecast,
    outcome_consequences,
    select_discriminating_action,
    select_expected_coverage,
)
from maestro.models import EvidenceKind, EvidenceScope, MechanismContrast, MechanismHypothesis, DevelopmentAction
from maestro.outcome import EvidenceState, InterpretationTable, OutcomeClass, OutcomeRule
from maestro.selection import BudgetedEvidenceSelector
from virtual_cell import (
    ModelCapabilities,
    QueryAssessment,
    QuerySupport,
    StatePrediction,
    SystemContext,
    VirtualCellQueryTemplate,
)

H1, H2 = "h1", "h2"
MATCH_H1, MATCH_H2 = "profile_matches_h1", "profile_matches_h2"
UNRESOLVED, ABSENT = "profile_unresolved", "no_detectable_response"
LABELS = (MATCH_H1, MATCH_H2, UNRESOLVED, ABSENT)
PROFILE = FunctionalInterventionProfile(mode="small_molecule")


def _rules(first: str = H1, second: str = H2) -> tuple[OutcomeRule, ...]:
    return (
        OutcomeRule("matches_first", MATCH_H1, frozenset({"response_detected", "profile_matches:first"}),
                    eliminates=frozenset({second}), scope=EvidenceScope.MECHANISM_CONTRAST),
        OutcomeRule("matches_second", MATCH_H2, frozenset({"response_detected", "profile_matches:second"}),
                    eliminates=frozenset({first}), scope=EvidenceScope.MECHANISM_CONTRAST),
        OutcomeRule("unresolved", UNRESOLVED, frozenset({"response_detected", "profile_unresolved"}),
                    scope=EvidenceScope.MEASUREMENT_FEASIBILITY),
        OutcomeRule("no_response", ABSENT, frozenset({"no_detectable_response"}),
                    scope=EvidenceScope.INTERVENTION_IMPLEMENTATION,
                    boundary="Absence cannot separate a failed perturbation from an inert mechanism."),
    )


CONSEQUENCES = outcome_consequences(_rules())


def _branch(hypothesis: str, *, correct: int = 0, wrong: int = 0, unresolved: int = 0, absent: int = 0,
            first: str = H1) -> OutcomeBranch:
    """Reference readings of one hypothesis, stated relative to it (correct removes the other one)."""

    support = correct + wrong + unresolved + absent
    own, other = (MATCH_H1, MATCH_H2) if hypothesis == first else (MATCH_H2, MATCH_H1)
    counts = {own: correct, other: wrong, UNRESOLVED: unresolved, ABSENT: absent}
    probabilities = {label: (counts[label] / support if support else 0.0) for label in LABELS}
    if not support:
        probabilities = {label: 0.25 for label in LABELS}
    return OutcomeBranch(hypothesis, probabilities, support)


def _forecast(identifier: str, first: OutcomeBranch, second: OutcomeBranch) -> OutcomeForecast:
    return OutcomeForecast(identifier, (first, second), basis="fixture: reference readings")


def _action(identifier: str, *, cost: float = 1.0, time_hours: float | None = 24.0) -> EvidenceAction:
    return EvidenceAction(identifier, f"{identifier} assay", cost, (H1, H2), time_hours=time_hours)


def _chosen(plan) -> str | None:
    return plan.plan.actions[0].identifier if plan.plan.actions else None


def _evaluation(plan, identifier: str):
    return next(item for item in plan.evaluations if item.action_identifier == identifier)


# ------------------------------------------------------------------------------------------ A


def test_a_loud_action_that_cannot_separate_loses_to_a_quiet_one_that_can():
    """Magnitude trap: the largest predicted response carries the same reading under both hypotheses."""

    loud, quiet = _action("loud"), _action("quiet")
    forecasts = {
        # A generic response that reads as H1 whichever hypothesis is true.
        "loud": _forecast("loud", _branch(H1, correct=2, unresolved=2), _branch(H2, wrong=2, unresolved=2)),
        "quiet": _forecast("quiet", _branch(H1, correct=3, absent=1), _branch(H2, correct=3, absent=1)),
    }
    priorities = {"loud": 50.0, "quiet": 1.0}

    plan = select_discriminating_action(frozenset({H1, H2}), (loud, quiet), PROFILE, 1.0, forecasts, CONSEQUENCES,
                                        action_priorities=priorities)

    assert _chosen(plan) == "quiet"
    assert _evaluation(plan, "loud").discrimination == pytest.approx(0.0)
    assert not _evaluation(plan, "loud").admissible
    assert plan.plan.rejection_reasons["loud"] == "wrong_elimination_risk_not_below_break_even"
    # The legacy selector reads only the magnitude and walks into the trap.
    legacy = BudgetedEvidenceSelector().select(frozenset({H1, H2}), (loud, quiet), PROFILE, 1.0,
                                               action_priorities=priorities)
    assert [action.identifier for action in legacy.actions] == ["loud"]


# ------------------------------------------------------------------------------------------ B


def test_a_costlier_late_measurement_that_alone_separates_can_be_chosen():
    """Late resolver: at 24 h both hypotheses read as absent or unresolved; at 72 h they separate."""

    early, late = _action("early", cost=6.0, time_hours=24.0), _action("late", cost=8.0, time_hours=72.0)
    forecasts = {
        "early": _forecast("early", _branch(H1, absent=3, unresolved=1), _branch(H2, absent=2, unresolved=2)),
        "late": _forecast("late", _branch(H1, correct=2), _branch(H2, correct=3, absent=1)),
    }

    plan = select_discriminating_action(frozenset({H1, H2}), (early, late), PROFILE, 8.0, forecasts, CONSEQUENCES)

    assert _chosen(plan) == "late"
    assert plan.plan.rejection_reasons["early"] == "no_reference_reading_eliminates_correctly"
    # Cost and exposure time are only consulted after discrimination; the legacy selector starts there.
    legacy = BudgetedEvidenceSelector().select(frozenset({H1, H2}), (early, late), PROFILE, 8.0)
    assert [action.identifier for action in legacy.actions] == ["early"]

    unaffordable = select_discriminating_action(frozenset({H1, H2}), (early, late), PROFILE, 6.0, forecasts,
                                                CONSEQUENCES)
    assert unaffordable.status == "no_admissible_action"
    assert unaffordable.plan.actions == ()
    assert unaffordable.plan.rejection_reasons["late"] == "exceeds_budget"


# ------------------------------------------------------------------------------------------ C


def test_equal_correct_odds_with_higher_wrong_risk_loses():
    safe_branches = (_branch(H1, correct=6, absent=4), _branch(H2, correct=6, absent=4))
    forecasts = {
        "a-risky": _forecast("a-risky", _branch(H1, correct=6, wrong=3, absent=1), _branch(H2, correct=6, wrong=3, absent=1)),
        "b-mild": _forecast("b-mild", _branch(H1, correct=6, wrong=1, absent=3), _branch(H2, correct=6, wrong=1, absent=3)),
        "c-safe": _forecast("c-safe", *safe_branches),
    }
    actions = tuple(_action(name) for name in forecasts)

    plan = select_discriminating_action(frozenset({H1, H2}), actions, PROFILE, 1.0, forecasts, CONSEQUENCES)

    assert _chosen(plan) == "c-safe"
    assert plan.plan.rejection_reasons["a-risky"] == "wrong_elimination_risk_not_below_break_even"
    mild = _evaluation(plan, "b-mild")
    assert mild.admissible, "a small wrong risk below the break-even stays admissible"
    assert plan.plan.rejection_reasons["b-mild"] == "lower_conservative_discrimination"
    assert _evaluation(plan, "c-safe").p_correct == pytest.approx(mild.p_correct)

    # Reduced to one detection probability, all three look identical and the label decides.
    reduced = tuple(
        EvidenceAction(name, name, 1.0, (H1, H2), detection_power=0.6) for name in forecasts
    )
    legacy = select_expected_coverage(frozenset({H1, H2}), reduced, PROFILE, 1.0)
    assert [action.identifier for action in legacy.plan.actions] == ["a-risky"]


# ------------------------------------------------------------------------------------------ support


def test_zero_references_refuse_by_name_and_a_missing_branch_is_named():
    forecasts = {
        "empty": _forecast("empty", _branch(H1, correct=2), _branch(H2)),
        "half": OutcomeForecast("half", (_branch(H1, correct=2),), basis="fixture"),
        "refused": OutcomeForecast("refused", (), basis="fixture", refusal="condition_not_in_reference_data:K562|72h"),
    }
    actions = (*(_action(name) for name in forecasts), _action("unforecast"))

    plan = select_discriminating_action(frozenset({H1, H2}), actions, PROFILE, 1.0, forecasts, CONSEQUENCES)

    reasons = plan.plan.rejection_reasons
    assert plan.status == "no_admissible_action"
    assert reasons["empty"] == "forecast_refused:no_reference_for_hypothesis:h2"
    assert reasons["half"] == "forecast_refused:forecast_missing_hypothesis:h2"
    assert reasons["refused"] == "forecast_refused:condition_not_in_reference_data:K562|72h"
    assert reasons["unforecast"] == "no_outcome_forecast"


def test_one_reference_is_served_low_support_shrunk_and_discounted_not_deleted():
    forecasts = {
        "one": _forecast("one", _branch(H1, correct=1), _branch(H2, correct=1)),
        "ten": _forecast("ten", _branch(H1, correct=10), _branch(H2, correct=10)),
        "flat": _forecast("flat", _branch(H1, absent=10), _branch(H2, absent=10)),
    }
    actions = tuple(_action(name) for name in forecasts)

    both = select_discriminating_action(frozenset({H1, H2}), actions, PROFILE, 1.0, forecasts, CONSEQUENCES)
    one, ten = _evaluation(both, "one"), _evaluation(both, "ten")
    assert _chosen(both) == "ten"
    assert one.admissible and one.low_support and one.support == 1
    assert not ten.low_support
    # The same observed frequency (every reference resolved correctly) is shrunk hard at one reference.
    assert one.p_correct == pytest.approx(0.5)
    assert ten.p_correct == pytest.approx(10.5 / 12.0)
    assert (one.discrimination - one.discrimination_lower) > (ten.discrimination - ten.discrimination_lower)
    assert one.discrimination_lower < ten.discrimination_lower

    # Without the well-supported option the one-reference action is still available, and chosen
    # over an action whose references never resolved anything.
    thin = select_discriminating_action(frozenset({H1, H2}), (actions[0], actions[2]), PROFILE, 1.0, forecasts,
                                        CONSEQUENCES)
    assert _chosen(thin) == "one"
    assert "low_support:one" in thin.assumptions


# ------------------------------------------------------------------------------------------ safety


def test_absence_is_never_credited_as_discrimination_even_when_the_distributions_differ():
    """Undetected under H1 and unresolved under H2 differ completely, and remove nothing."""

    forecasts = {"absence": _forecast("absence", _branch(H1, absent=5), _branch(H2, unresolved=5))}
    plan = select_discriminating_action(frozenset({H1, H2}), (_action("absence"),), PROFILE, 1.0, forecasts,
                                        CONSEQUENCES)
    evaluation = _evaluation(plan, "absence")
    assert CONSEQUENCES[ABSENT] == frozenset()
    assert evaluation.total_variation > 0.5
    assert evaluation.discrimination == pytest.approx(0.0)
    assert plan.status == "no_admissible_action"
    assert plan.plan.rejection_reasons["absence"] == "no_reference_reading_eliminates_correctly"

    contrast = _contrast()
    state = EvidenceState.open(contrast.hypotheses)
    interpretation = InterpretationTable(_rules()).interpret(
        _result(("no_detectable_response",)), contrast, PROFILE, contrast.plan)
    assert interpretation.eliminates == frozenset()
    assert state.apply(interpretation, _result(("no_detectable_response",))).candidates == frozenset({H1, H2})


def test_a_forecast_cannot_declare_what_a_reading_eliminates():
    """Consequences come from the registered rules; an unregistered label removes nothing."""

    invented = OutcomeForecast(
        "invented",
        (OutcomeBranch(H1, {"absence_retires_h2": 1.0}, 8), OutcomeBranch(H2, {ABSENT: 1.0}, 8)),
        basis="fixture",
    )
    plan = select_discriminating_action(frozenset({H1, H2}), (_action("invented"),), PROFILE, 1.0,
                                        {"invented": invented}, CONSEQUENCES)
    assert _evaluation(plan, "invented").p_correct < 0.1
    assert plan.status == "no_admissible_action"
    assert "forecast_label_not_registered:absence_retires_h2" in plan.assumptions


def test_prediction_derived_records_and_failed_qc_never_eliminate(tmp_path: Path):
    contrast = _contrast()
    table = InterpretationTable(_rules())
    fields = ("response_detected", "profile_matches:first")
    state = EvidenceState.open(contrast.hypotheses)

    predicted = _result(fields, evidence_kind=EvidenceKind.MODEL_PREDICTION)
    reading = table.interpret(predicted, contrast, PROFILE, contrast.plan)
    assert reading.outcome_class is OutcomeClass.NON_MEASUREMENT
    assert state.apply(reading, predicted).candidates == frozenset({H1, H2})

    failed = _result(fields, quality_passed=False)
    reading = table.interpret(failed, contrast, PROFILE, contrast.plan)
    assert reading.outcome_class is OutcomeClass.QUALITY_FAILED
    assert state.apply(reading, failed).candidates == frozenset({H1, H2})

    real = _result(fields)
    assert state.apply(table.interpret(real, contrast, PROFILE, contrast.plan), real).candidates == frozenset({H1})

    store = CaseStore(tmp_path / "cases.sqlite")
    store.open_case("qc", budget=10.0)
    store.record_plan("qc", (contrast.plan,), ready_to_measure=True, context_identifier=None)
    snapshot = store.import_measurement("qc", failed).snapshot
    assert snapshot.state is CaseState.RESULT_QC_FAILED


# ------------------------------------------------------------------------------------------ determinism


def test_ties_break_deterministically_and_a_rerun_is_identical():
    same = (_branch(H1, correct=3, absent=1), _branch(H2, correct=3, absent=1))
    forecasts = {name: _forecast(name, *same) for name in ("b", "a", "c")}
    actions = tuple(_action(name) for name in ("c", "b", "a"))

    first = select_discriminating_action(frozenset({H1, H2}), actions, PROFILE, 1.0, forecasts, CONSEQUENCES)
    again = select_discriminating_action(frozenset({H1, H2}), tuple(reversed(actions)), PROFILE, 1.0, forecasts,
                                         CONSEQUENCES)
    assert _chosen(first) == "a"
    assert first == again

    prioritised = select_discriminating_action(frozenset({H1, H2}), actions, PROFILE, 1.0, forecasts, CONSEQUENCES,
                                               action_priorities={"c": 2.0})
    assert _chosen(prioritised) == "c", "magnitude breaks only an exact tie"
    cheaper = select_discriminating_action(frozenset({H1, H2}), (*actions[:2], _action("a", cost=0.5)), PROFILE, 1.0,
                                           forecasts, CONSEQUENCES, action_priorities={"c": 2.0})
    assert _chosen(cheaper) == "a", "cost is consulted before magnitude"


def test_expected_coverage_breaks_exact_ties_by_prediction_but_never_buys_cost():
    equal = (EvidenceAction("a", "a", 1.0, (H1, H2)), EvidenceAction("b", "b", 1.0, (H1, H2)))
    assert [a.identifier for a in select_expected_coverage(frozenset({H1, H2}), equal, PROFILE, 1.0).plan.actions] == ["a"]
    ranked = select_expected_coverage(frozenset({H1, H2}), equal, PROFILE, 1.0, action_priorities={"b": 3.0})
    assert [a.identifier for a in ranked.plan.actions] == ["b"]

    priced = (EvidenceAction("cheap", "c", 1.0, (H1, H2)), EvidenceAction("dear", "d", 2.0, (H1, H2)))
    kept = select_expected_coverage(frozenset({H1, H2}), priced, PROFILE, 2.0, action_priorities={"dear": 9.0})
    assert [a.identifier for a in kept.plan.actions] == ["cheap"]


# ------------------------------------------------------------------------------------------ runtime wiring

CONTROL_LOW = "[('drugA', 0.5, 'uM')]"
CONTROL_HIGH = "[('drugA', 5.0, 'uM')]"
REALISED, NOT_REALISED = "response_realised", "response_not_realised"
TRIAGE = {
    "task_type": "mechanism_diagnosis",
    "research_question": "Is the transcriptional response of drugA realised in NCI-H596 at the tested exposure?",
    "target_or_targets": ["TARGET_A"], "interventions": ["drugA"], "biological_context": "NCI-H596",
    "phenotype_endpoint": "transcriptome shift", "supplied_evidence": [], "constraints": [],
    "missing_information": [], "evidence_gaps": ["proximal target activity"], "needs_visual_review": False,
}
PLAN = {
    "identifier": "realisation-contrast",
    "hypotheses": [
        {"identifier": REALISED, "description": "The exposure perturbs the transcriptome.",
         "proposed_action": "continue", "causal_factor": "unresolved"},
        {"identifier": NOT_REALISED, "description": "The exposure does not perturb the transcriptome.",
         "proposed_action": "revise_intervention", "causal_factor": "incomplete_perturbation"},
    ],
    "differing_assumptions": ["whether the exposure changes RNA abundance"],
    "action_identifier": "measure_low",
    "outcome_categories": ["response_detected", "no_detectable_response"],
    "interpretation_boundaries": ["An RNA-level response does not establish target engagement or viability."],
}
NO_REPAIR = {"action_identifier": None, "modified_fields": [], "rationale": "No catalog repair is needed.",
             "remaining_limitations": []}


class _LabelWorldModel:
    """Answers each exact label with a fixed number and refuses exposure times it was not built for."""

    name = "label_stub"

    def __init__(self, values, *, served_time: float | None = None):
        self.values = values
        self.served_time = served_time
        self.requests = []

    def capabilities(self):
        return ModelCapabilities("label_stub", "stub-1", "none", "label", ("drug",), True, False,
                                 self.served_time is not None, None)

    def _limitations(self, request):
        time = request.intervention.time_hours
        if self.served_time is not None and time is not None and time != self.served_time:
            return (f"time_not_supported:{time:g}h",)
        return ()

    def assess_query(self, request):
        self.requests.append(request)
        limitations = self._limitations(request)
        return QueryAssessment(QuerySupport.UNSUPPORTED if limitations else QuerySupport.SUPPORTED, (), limitations,
                               self.capabilities())

    def predict(self, request):
        limitations = self._limitations(request)
        if limitations:
            return StatePrediction(False, None, None, limitations, request_id=request.request_id, model_version="stub-1",
                                   in_distribution=False, abstain_reason=limitations[0])
        return StatePrediction(
            True, {"embedding_delta_l2": self.values[request.intervention.identifier]}, None, ("planning only",),
            request_id=request.request_id, model_version="stub-1", confidence=None, in_distribution=True,
            uncertainty_components={"all_sources": "unquantified in this fixture"},
        )


class _StubForecaster:
    name = "fixture_forecaster"

    def __init__(self, forecasts):
        self.forecasts = forecasts
        self.calls = []

    def forecast(self, contrast, actions, evidence):
        self.calls.append((contrast.identifier, tuple(action.identifier for action in actions)))
        return dict(self.forecasts)


def _runtime_actions(late_time: float | None = None) -> tuple[EvidenceAction, ...]:
    common = dict(
        cost=1.0, distinguishes=(REALISED, NOT_REALISED), supplies=("realization:transcript_response",),
        prediction_readout="embedding_delta_l2", prediction_relevance=1.0,
        expected_outcomes={REALISED: "response_detected", NOT_REALISED: "no_detectable_response"},
    )
    return (
        EvidenceAction("measure_low", "Transcriptome shift at 0.5 uM.", time_hours=24.0, **common),
        EvidenceAction("measure_high", "Transcriptome shift at 5 uM.", time_hours=late_time or 24.0, **common),
    )


def _runtime_rules() -> tuple[OutcomeRule, ...]:
    return (
        OutcomeRule("realised", "response_detected", frozenset({"realization:transcript_response:detected"}),
                    eliminates=frozenset({NOT_REALISED}), scope=EvidenceScope.MECHANISM_CONTRAST),
        OutcomeRule("absent", "no_detectable_response", frozenset({"no_detectable_response"}),
                    scope=EvidenceScope.INTERVENTION_IMPLEMENTATION),
    )


def _orchestrator(tmp_path: Path, world_model, **options) -> MAESTROOrchestrator:
    client = TemplateCompleter({"task_triage": TRIAGE, "contrast_planner": PLAN, "repair_planner": NO_REPAIR})
    root = tmp_path / "state"
    memory = MemoryStore(root / "memory.sqlite")
    return MAESTROOrchestrator(
        interpreter=TaskInterpreter(client),
        context_builder=ContextBuilder(EvidenceLedger(root / "evidence.sqlite"), memory),
        planner=MechanismContrastPlanner(client),
        visual_inspector=VisualInspector(client, "unused"),
        memory=memory,
        logger=RunLogger(root),
        controller=MAESTROAgent(),
        virtual_cell=world_model,
        power_aware_selection=options.pop("power_aware_selection", True),
        interpretation_table=InterpretationTable(_runtime_rules()),
        case_store=CaseStore(root / "cases.sqlite"),
        **options,
    )


def _template(time_hours: float | None = None) -> VirtualCellQueryTemplate:
    return VirtualCellQueryTemplate(
        CONTROL_LOW, "drug", SystemContext("NCI-H596", "fixture", dataset_id="tiny", control_dataset_id="tiny"),
        ("embedding_delta_l2",), "stub-1", action_interventions={"measure_low": CONTROL_LOW, "measure_high": CONTROL_HIGH},
        time_hours=time_hours,
    )


def _events(tmp_path: Path, kind: str) -> list[dict]:
    lines = (tmp_path / "state" / "events.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip() and json.loads(line)["kind"] == kind]


@pytest.mark.parametrize("values", [{CONTROL_LOW: 5.0, CONTROL_HIGH: 1.0}, {CONTROL_LOW: 1.0, CONTROL_HIGH: 5.0}])
def test_power_aware_coverage_keeps_magnitude_out_until_its_keep_rule_is_met(tmp_path, values):
    """Magnitude alone does not move the power-aware choice, and the log says so.

    Wiring it in as a tie-break failed its pre-registered keep rule on 2026-09-26 (tier A utility
    interval included zero; tier B wrong eliminations rose by 0.044), so the priorities stay logged
    and unused until an independent evaluation meets that rule.
    """

    profile = FunctionalInterventionProfile(mode="inhibition", context_identifier="NCI-H596", time_hours=24.0)
    turn = _orchestrator(tmp_path, _LabelWorldModel(values)).run(
        "Which exposure should be measured first?", available_actions=_runtime_actions(), intervention_profile=profile,
        case_id="wired", budget=1.0, virtual_cell_template=_template(),
    )
    assert tuple(action.identifier for action in turn.selected_actions) == ("measure_high",)
    completed = _events(tmp_path, "budget_selection_completed")[-1]["payload"]
    assert completed["selection_path"] == "expected_coverage"
    assert completed["prediction_priorities_used"] is False
    assert set(completed["prediction_action_priorities"]) == {"measure_low", "measure_high"}


@pytest.mark.parametrize("values, expected", [({CONTROL_LOW: 5.0, CONTROL_HIGH: 1.0}, "measure_low"),
                                              ({CONTROL_LOW: 1.0, CONTROL_HIGH: 5.0}, "measure_high")])
def test_magnitude_breaks_only_an_exact_forecast_tie_on_the_power_aware_path(tmp_path, values, expected):
    forecaster = _StubForecaster({"measure_low": _separating("measure_low"), "measure_high": _separating("measure_high")})
    profile = FunctionalInterventionProfile(mode="inhibition", context_identifier="NCI-H596", time_hours=24.0)
    turn = _orchestrator(tmp_path, _LabelWorldModel(values), outcome_forecaster=forecaster,
                         discrimination_selection=True).run(
        "Which exposure should be measured first?", available_actions=_runtime_actions(), intervention_profile=profile,
        case_id="tied", budget=1.0, virtual_cell_template=_template(),
    )
    assert tuple(action.identifier for action in turn.selected_actions) == (expected,)
    completed = _events(tmp_path, "budget_selection_completed")[-1]["payload"]
    assert completed["selection_path"] == "discrimination" and completed["prediction_priorities_used"] is True
    loser = "measure_high" if expected == "measure_low" else "measure_low"
    computed = _events(tmp_path, "discrimination_selection_computed")[-1]["payload"]
    assert computed["evaluations"][loser]["discrimination_lower"] == computed["evaluations"][expected]["discrimination_lower"]
    assert computed["rejection_reasons"][loser] == "smaller_predicted_response_at_equal_discrimination"


def _separating(identifier: str) -> OutcomeForecast:
    return OutcomeForecast(identifier, (
        OutcomeBranch(REALISED, {"response_detected": 0.75, "no_detectable_response": 0.25}, 8),
        OutcomeBranch(NOT_REALISED, {"response_detected": 0.0, "no_detectable_response": 1.0}, 8),
    ), basis="fixture")


def _flat(identifier: str) -> OutcomeForecast:
    return OutcomeForecast(identifier, (
        OutcomeBranch(REALISED, {"response_detected": 0.0, "no_detectable_response": 1.0}, 8),
        OutcomeBranch(NOT_REALISED, {"response_detected": 0.0, "no_detectable_response": 1.0}, 8),
    ), basis="fixture")


@pytest.mark.parametrize("separating, expected", [("measure_low", "measure_low"), ("measure_high", "measure_high")])
@pytest.mark.parametrize("power_aware", [False, True])
def test_power_aware_selection_follows_outcome_forecasts_when_enabled(tmp_path, separating, expected, power_aware):
    other = "measure_high" if separating == "measure_low" else "measure_low"
    forecaster = _StubForecaster({separating: _separating(separating), other: _flat(other)})
    profile = FunctionalInterventionProfile(mode="inhibition", context_identifier="NCI-H596", time_hours=24.0)
    # Equal magnitudes: only the forecasts differ between the two parametrisations.
    orchestrator = _orchestrator(tmp_path, _LabelWorldModel({CONTROL_LOW: 2.0, CONTROL_HIGH: 2.0}),
                                 outcome_forecaster=forecaster, discrimination_selection=True,
                                 power_aware_selection=power_aware)
    turn = orchestrator.run(
        "Which exposure should be measured first?", available_actions=_runtime_actions(), intervention_profile=profile,
        case_id="forecast", budget=1.0, virtual_cell_template=_template(),
    )
    assert tuple(action.identifier for action in turn.selected_actions) == (expected,)
    computed = _events(tmp_path, "discrimination_selection_computed")[-1]["payload"]
    assert computed["chosen"] == expected and computed["drives_selection"] is True
    assert computed["evaluations"][other]["reason"] == "no_reference_reading_eliminates_correctly"
    # Nothing but the plan moved: no hypothesis was removed and the case waits for a real result.
    assert orchestrator.evidence_state("forecast") is None or orchestrator.evidence_state("forecast").eliminated == frozenset()
    assert turn.case is not None and turn.case.state is CaseState.AWAITING_RESULT


@pytest.mark.parametrize("power_aware", [False, True])
def test_discrimination_deferral_blocks_execution_in_both_coverage_modes(tmp_path, power_aware):
    forecaster = _StubForecaster({identifier: _flat(identifier) for identifier in ("measure_low", "measure_high")})
    profile = FunctionalInterventionProfile(mode="inhibition", context_identifier="NCI-H596", time_hours=24.0)
    orchestrator = _orchestrator(tmp_path, _LabelWorldModel({CONTROL_LOW: 2.0, CONTROL_HIGH: 2.0}),
                                 outcome_forecaster=forecaster, discrimination_selection=True,
                                 power_aware_selection=power_aware)
    turn = orchestrator.run(
        "Which exposure should be measured first?", available_actions=_runtime_actions(), intervention_profile=profile,
        case_id="deferred", budget=1.0, virtual_cell_template=_template(),
    )
    assert turn.selected_actions == ()
    assert turn.case is not None and turn.case.state is CaseState.DEFERRED
    assert turn.case.stop_reason.startswith("acquisition_no_admissible_action:")
    computed = _events(tmp_path, "discrimination_selection_computed")[-1]["payload"]
    assert computed["status"] == "no_admissible_action" and computed["chosen"] is None
    assert orchestrator.evidence_state("deferred") is None or not orchestrator.evidence_state("deferred").eliminated


@pytest.mark.parametrize("power_aware", [False, True])
def test_partial_discrimination_choice_reaches_the_agent_check(tmp_path, power_aware):
    forecaster = _StubForecaster({"measure_low": _flat("measure_low"), "measure_high": _separating("measure_high")})
    profile = FunctionalInterventionProfile(mode="inhibition", context_identifier="NCI-H596", time_hours=24.0)
    actions = tuple(replace(action, distinguishes=(REALISED,)) for action in _runtime_actions())
    orchestrator = _orchestrator(tmp_path, _LabelWorldModel({CONTROL_LOW: 2.0, CONTROL_HIGH: 2.0}),
                                 outcome_forecaster=forecaster, discrimination_selection=True,
                                 power_aware_selection=power_aware)
    turn = orchestrator.run(
        "Which exposure should be measured first?", available_actions=actions, intervention_profile=profile,
        case_id="partial", budget=1.0, virtual_cell_template=_template(),
    )
    assert turn.contrast.plan.identifier == "measure_high"
    # The agent still checks the action's declared coverage before authorising execution.
    assert not turn.check.discriminable
    assert turn.selected_actions == ()
    assert turn.case.state is CaseState.DEFERRED
    completed = _events(tmp_path, "budget_selection_completed")[-1]["payload"]
    assert completed["selected_action_ids"] == ["measure_high"]
    assert completed["uncovered"] == [NOT_REALISED]


def test_outcome_forecasts_are_shadowed_unless_selection_is_enabled(tmp_path):
    forecaster = _StubForecaster({"measure_low": _separating("measure_low"), "measure_high": _flat("measure_high")})
    profile = FunctionalInterventionProfile(mode="inhibition", context_identifier="NCI-H596", time_hours=24.0)
    orchestrator = _orchestrator(tmp_path, _LabelWorldModel({CONTROL_LOW: 2.0, CONTROL_HIGH: 2.0}),
                                 outcome_forecaster=forecaster)
    turn = orchestrator.run(
        "Which exposure should be measured first?", available_actions=_runtime_actions(), intervention_profile=profile,
        case_id="shadow", budget=1.0, virtual_cell_template=_template(),
    )
    computed = _events(tmp_path, "discrimination_selection_computed")[-1]["payload"]
    assert computed["chosen"] == "measure_low" and computed["drives_selection"] is False
    assert tuple(action.identifier for action in turn.selected_actions) == ("measure_high",)
    with pytest.raises(ValueError):
        _orchestrator(tmp_path / "bad", None, discrimination_selection=True)


def test_a_per_action_query_states_the_action_own_exposure_time(tmp_path):
    """A 72 h action is queried at 72 h and refused by name; it never borrows the 24 h answer."""

    world_model = _LabelWorldModel({CONTROL_LOW: 1.0, CONTROL_HIGH: 5.0}, served_time=24.0)
    profile = FunctionalInterventionProfile(mode="inhibition", context_identifier="NCI-H596", time_hours=24.0)
    turn = _orchestrator(tmp_path, world_model).run(
        "Which exposure should be measured first?", available_actions=_runtime_actions(late_time=72.0),
        intervention_profile=profile, case_id="timed", budget=1.0, virtual_cell_template=_template(time_hours=24.0),
    )
    times = {request.request_id.rsplit(".", 1)[-1]: request.intervention.time_hours for request in world_model.requests}
    assert times == {"measure_low": 24.0, "measure_high": 72.0}
    assert turn.action_predictions["measure_high"].applicable is False
    assert "time_not_supported:72h" in turn.action_predictions["measure_high"].limitations
    priorities = _events(tmp_path, "budget_selection_completed")[-1]["payload"]["prediction_action_priorities"]
    assert "measure_high" not in priorities


def test_an_action_in_another_context_is_not_queried_with_the_template_context(tmp_path):
    world_model = _LabelWorldModel({CONTROL_LOW: 1.0, CONTROL_HIGH: 5.0})
    low, high = _runtime_actions()
    elsewhere = EvidenceAction(
        high.identifier, high.description, high.cost, high.distinguishes, time_hours=24.0,
        execution_context="MCF7", prediction_readout=high.prediction_readout, prediction_relevance=1.0,
    )
    profile = FunctionalInterventionProfile(mode="inhibition", context_identifier="NCI-H596", time_hours=24.0)
    _orchestrator(tmp_path, world_model).run(
        "Which exposure should be measured first?", available_actions=(low, elsewhere), intervention_profile=profile,
        case_id="elsewhere", budget=1.0, virtual_cell_template=_template(),
    )
    assert {request.request_id.rsplit(".", 1)[-1] for request in world_model.requests} == {"measure_low"}
    reasons = _events(tmp_path, "virtual_cell_query_not_built")[-1]["payload"]["reasons"]
    assert reasons == {"measure_high": "execution_context_differs_from_template:MCF7"}


# ------------------------------------------------------------------------------------------ helpers


def _contrast() -> MechanismContrast:
    action = EvidenceAction("assay", "Measure.", 1.0, (H1, H2), time_hours=24.0)
    return MechanismContrast(
        "c", (MechanismHypothesis(H1, "H1", DevelopmentAction.CONTINUE, causal_factor=H1),
              MechanismHypothesis(H2, "H2", DevelopmentAction.REVISE_ATTRIBUTION, causal_factor=H2)),
        ("mechanism class",), plan=action,
    )


def _result(fields, *, quality_passed: bool = True, evidence_kind: EvidenceKind = EvidenceKind.REAL_MEASUREMENT):
    return MeasurementResult(
        action_identifier="assay", statement="Observed profile.", source_id="fixture:assay", context_identifier=None,
        time_hours=24.0, independent_units=2, quality_passed=quality_passed, evidence_kind=evidence_kind,
        interpretation_fields=tuple(fields), result_id=f"fixture:{'-'.join(fields)}:{quality_passed}:{evidence_kind.value}",
    )
