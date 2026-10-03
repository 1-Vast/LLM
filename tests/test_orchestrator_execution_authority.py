"""Only the current persisted, affordable plan may reach a result provider."""
from dataclasses import replace
from pathlib import Path

import pytest

from tests.fixtures.orchestration import TASK, _action, _controller, _plan
from agent.memory import CaseState
from agent.orchestrator import MAESTROOrchestrator
from maestro import EvidenceAction, FunctionalInterventionProfile
from maestro.acquisition import OutcomeBranch, OutcomeForecast
from maestro.models import EvidenceActionKind, EvidenceScope, MechanismContrast, MechanismHypothesis, MeasurementStatus, PremiseGrant
from maestro.outcome import InterpretationTable, MeasuredPremise, OutcomeRule
from tests.fixtures.stub_client import StubClient


@pytest.mark.parametrize("budget", [0.0, 0.5])
def test_overbudget_action_never_reaches_the_result_provider(tmp_path: Path, budget):
    controller = _controller(tmp_path, [TASK, _plan("assay")])
    calls = []

    def provider(action, turn):
        calls.append(action.identifier)
        return None

    loop = controller.run_case_loop(
        "Resolve discrepancy.", available_actions=(_action(),),
        intervention_profile=FunctionalInterventionProfile(mode="inhibition"),
        result_provider=provider, case_id="bounded", budget=budget,
    )

    assert calls == []
    assert loop.turns[0].selected_actions == ()
    assert controller._case_store.snapshot("bounded").state is CaseState.DEFERRED


def test_budget_blocks_execution_even_without_a_case_store(tmp_path: Path):
    controller = _controller(tmp_path, [TASK, _plan("assay")], case_store=False)
    turn = controller.run(
        "Resolve discrepancy.", available_actions=(_action(),),
        intervention_profile=FunctionalInterventionProfile(mode="inhibition"), budget=0.5,
    )
    assert turn.selected_actions == ()


def test_repair_measurement_is_subject_to_the_same_execution_budget(tmp_path: Path):
    controller = _controller(tmp_path, [TASK, _plan("mode-comparison")])
    functional = EvidenceAction(
        "functional", "Measure target activity.", 2.0, ("a",), kind=EvidenceActionKind.FUNCTIONAL_MEASUREMENT,
    )
    mode = EvidenceAction(
        "mode-comparison", "Compare modes.", 3.0, ("a", "b"), prerequisites=("functional:target_activity",),
    )
    turn = controller.run(
        "Resolve discrepancy.", available_actions=(functional, mode),
        intervention_profile=FunctionalInterventionProfile(mode="drug", context_identifier="cell-a"),
        case_id="repair", budget=1.0,
    )
    assert turn.repair is not None
    assert turn.selected_actions == ()
    assert turn.case.state is CaseState.DEFERRED


def test_replanning_cannot_execute_a_different_action_while_a_plan_is_pending(tmp_path: Path):
    controller = _controller(tmp_path, [TASK, _plan("first"), TASK, _plan("second")])
    first = controller.run(
        "Resolve discrepancy.", available_actions=(_action("first"),),
        intervention_profile=FunctionalInterventionProfile(mode="inhibition"), case_id="pending", budget=2.0,
    )
    second = controller.run(
        "Try another assay.", available_actions=(_action("second"),),
        intervention_profile=FunctionalInterventionProfile(mode="inhibition"), case_id="pending", budget=2.0,
    )

    assert first.selected_actions == (_action("first"),)
    assert second.selected_actions == ()
    assert second.case.state is CaseState.AWAITING_RESULT
    assert second.case.plan_version == first.case.plan_version
    assert "awaiting" in second.response.lower()
    assert controller.evidence_state("pending") is None


def test_pending_case_loop_waits_without_calling_a_new_result_provider(tmp_path: Path):
    controller = _controller(tmp_path, [TASK, _plan("first"), TASK, _plan("second")])
    controller.run(
        "Resolve discrepancy.", available_actions=(_action("first"),),
        intervention_profile=FunctionalInterventionProfile(mode="inhibition"), case_id="pending", budget=2.0,
    )
    calls = []
    loop = controller.run_case_loop(
        "Try another assay.", available_actions=(_action("second"),),
        intervention_profile=FunctionalInterventionProfile(mode="inhibition"),
        result_provider=lambda action, turn: calls.append(action.identifier), case_id="pending", budget=2.0,
    )
    assert calls == []
    assert loop.stop_reason == "awaiting_result"


@pytest.mark.parametrize("budget", [True, float("nan"), float("inf"), -1.0])
def test_invalid_budget_is_rejected_before_planning(tmp_path: Path, budget):
    controller = _controller(tmp_path, [])
    with pytest.raises(ValueError, match="Budget"):
        controller.run(
            "Resolve discrepancy.", available_actions=(_action(),),
            intervention_profile=FunctionalInterventionProfile(mode="inhibition"), budget=budget,
        )


@pytest.mark.parametrize("active, expected", [(False, "first"), (True, "second")])
def test_workspace_factory_reaches_the_forecaster_in_shadow_and_active_modes(tmp_path, monkeypatch, active, expected):
    for name in ("DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL", "DEEPSEEK_MODEL", "DEEPSEEK_VISION_MODEL"):
        monkeypatch.setenv(name, "fixture")

    class Forecaster:
        name = "factory_fixture"

        def __init__(self):
            self.calls = []

        def forecast(self, contrast, actions, evidence):
            self.calls.append((contrast.identifier, tuple(action.identifier for action in actions), evidence))
            return {
                "first": OutcomeForecast("first", (
                    OutcomeBranch("a", {"unresolved": 1.0}, 8),
                    OutcomeBranch("b", {"unresolved": 1.0}, 8),
                )),
                "second": OutcomeForecast("second", (
                    OutcomeBranch("a", {"matches_a": 1.0}, 8),
                    OutcomeBranch("b", {"matches_b": 1.0}, 8),
                )),
            }

    forecaster = Forecaster()
    rules = InterpretationTable((
        OutcomeRule("a", "matches_a", frozenset({"matches_a"}), eliminates=frozenset({"b"}),
                    scope=EvidenceScope.MECHANISM_CONTRAST),
        OutcomeRule("b", "matches_b", frozenset({"matches_b"}), eliminates=frozenset({"a"}),
                    scope=EvidenceScope.MECHANISM_CONTRAST),
        OutcomeRule("unresolved", "unresolved", frozenset({"unresolved"})),
    ))
    controller = MAESTROOrchestrator.from_workspace(
        tmp_path, state_directory=tmp_path / "state", client=StubClient([TASK, _plan("first")]),
        enable_virtual_cell=False, enable_decision_critic=False, interpretation_table=rules,
        outcome_forecaster=forecaster, discrimination_selection=active,
    )
    turn = controller.run(
        "Resolve discrepancy.", available_actions=(_action("first"), _action("second")),
        intervention_profile=FunctionalInterventionProfile(mode="inhibition"), case_id="factory", budget=1.0,
    )

    assert forecaster.calls == [("contrast", ("first", "second"), None)]
    assert tuple(action.identifier for action in turn.selected_actions) == (expected,)
    assert turn.case.state is CaseState.AWAITING_RESULT
    assert controller.evidence_state("factory") is None


@pytest.mark.parametrize("change, expected", [
    ({}, "second"),
    ({"quality_passed": False}, "first"),
    ({"independent_units": 1}, "first"),
    ({"context_identifier": "other"}, "first"),
    ({"time_hours": 48.0}, "first"),
    ({"conditions": {"sample": "other"}}, "first"),
])
def test_only_sufficiently_measured_same_condition_premise_is_removed_from_selection(tmp_path, change, expected):
    controller = _controller(tmp_path, [])
    controller._selection_strategy = "expected_coverage"
    controller._interpretation_table = InterpretationTable((
        OutcomeRule("premise", "measured", frozenset({"premise"}), action_identifier="first",
                    scope=EvidenceScope.INTERVENTION_IMPLEMENTATION, minimum_independent_units=3),
    ))
    first = replace(_action("first"), supplies=("premise",), execution_context="cell-a", time_hours=24.0,
                    expected_conditions={"sample": "original"})
    second = replace(_action("second"), prerequisites=("premise",))
    contrast = MechanismContrast("contrast", (MechanismHypothesis("a", "A"), MechanismHypothesis("b", "B")),
                                (), second)
    grant = PremiseGrant("premise", "first", context_identifier="cell-a", time_hours=24.0, quality_passed=True)
    if "quality_passed" in change or "context_identifier" in change or "time_hours" in change:
        grant = replace(grant, **change)
    premise = MeasuredPremise(
        grant, "real", change.get("independent_units", 3), EvidenceScope.INTERVENTION_IMPLEMENTATION,
        change.get("conditions", {"sample": "original"}),
    )
    profile = FunctionalInterventionProfile(
        mode="inhibition", context_identifier="cell-a", measured_fields={"premise": MeasurementStatus.MEASURED},
    )
    selection = controller._select_budgeted_actions(
        contrast, (first, second), profile, None, 1.0, "selection", prior_evidence=(premise,),
    )
    assert tuple(action.identifier for action in selection.actions) == (expected,)
