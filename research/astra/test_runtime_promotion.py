"""Production promotion contracts; all observations are software fixtures."""
from dataclasses import replace
import json
from unittest.mock import Mock

import pytest

from agent.memory import CaseState
from maestro.models import FunctionalInterventionProfile
from tests.test_orchestrator_execution_authority import TASK, _action, _controller, _plan
from tests.test_virtual_cell_orchestration import ApplicableWorldModel
from virtual_cell.interface import SystemContext, VirtualCellQueryTemplate


def template(actions):
    return VirtualCellQueryTemplate(
        "registered-drug", "drug", SystemContext("cell-a", "fixture cells", dataset_id="dataset", control_dataset_id="control"),
        ("embedding_delta_l2",), "model-1",
        action_interventions={a.identifier: "drug-" + a.identifier for a in actions},
    )


def events(root, kind):
    return [row["payload"] for row in map(json.loads, (root / "events.jsonl").read_text().splitlines())
            if row["kind"] == kind]


def test_waiting_skips_interpreter_context_tools_planner_model_and_review(tmp_path):
    core = _controller(tmp_path, [])
    action = _action()
    core._case_store.open_case("case", budget=2)
    before = core._case_store.record_plan("case", (action,), ready_to_measure=True,
                                          context_identifier="cell-a")
    for name in ("_interpreter", "_context_builder", "_planner", "_visual_inspector", "_virtual_cell", "_decision_critic", "_tool_router"):
        setattr(core, name, Mock(side_effect=AssertionError("must not be called while waiting")))
    result = core.run("unchanged task", available_actions=(action,),
                      intervention_profile=FunctionalInterventionProfile("fixture"), case_id="case", budget=2)
    assert result.case == before
    assert result.case.state is CaseState.AWAITING_RESULT
    assert not result.selected_actions
    assert not result.contrast
    for name in ("_interpreter", "_context_builder", "_planner", "_visual_inspector", "_virtual_cell", "_decision_critic", "_tool_router"):
        assert not getattr(core, name).mock_calls


def test_budget_and_execution_prerequisites_filtered_before_model(tmp_path):
    legal = _action("legal")
    expensive = replace(_action("expensive"), cost=3)
    blocked = replace(_action("blocked"), prerequisites=("missing",))
    actions = (legal, expensive, blocked)
    core = _controller(tmp_path, [TASK, _plan("legal")])
    world = ApplicableWorldModel()
    core._virtual_cell = world
    turn = core.run("task", available_actions=actions,
                    intervention_profile=FunctionalInterventionProfile("fixture"),
                    case_id="case", budget=1, virtual_cell_template=template(actions))
    assert [r.intervention.identifier for r in world.requests] == ["drug-legal"]
    assert set(turn.action_prediction_requests) == {"legal"}
    audit = events(tmp_path, "virtual_cell_candidates_filtered")[0]
    assert audit["rejected"] == {"expensive": "unaffordable", "blocked": "missing_prerequisites:missing"}


def test_interpretation_gate_is_not_an_execution_prerequisite(tmp_path):
    action = replace(_action(), interpretation_gate="unmeasured_gate")
    core = _controller(tmp_path, [TASK, _plan(action.identifier)])
    world = ApplicableWorldModel()
    core._virtual_cell = world
    core.run("task", available_actions=(action,),
             intervention_profile=FunctionalInterventionProfile("fixture"),
             case_id="case", budget=1, virtual_cell_template=template((action,)))
    assert len(world.requests) == 1


@pytest.mark.parametrize("blocked_by", ["budget", "prerequisite"])
def test_single_explicit_query_for_blocked_plan_does_not_run(tmp_path, blocked_by):
    action = replace(_action(), cost=2) if blocked_by == "budget" else replace(_action(), prerequisites=("missing",))
    core = _controller(tmp_path, [TASK, _plan(action.identifier)])
    world = ApplicableWorldModel()
    core._virtual_cell = world
    query = template((action,)).build(request_id="query", case_id="case", contrast_id="contrast",
                                      plan_version=1, intended_targets=("TARGET",))
    core.run("task", available_actions=(action,),
             intervention_profile=FunctionalInterventionProfile("fixture"),
             budget=1, prediction_request=query)
    assert not world.requests


def test_legal_evidence_action_survives_unavailable_model(tmp_path):
    from virtual_cell.interface import UnavailableVirtualCellWorldModel
    action = _action()
    core = _controller(tmp_path, [TASK, _plan(action.identifier)])
    core._virtual_cell = UnavailableVirtualCellWorldModel()
    turn = core.run("task", available_actions=(action,),
                    intervention_profile=FunctionalInterventionProfile("fixture"), budget=1,
                    virtual_cell_template=template((action,)))
    assert turn.selected_actions == (action,)
    assert not turn.prediction.applicable


def test_final_identity_audit_marks_review_as_stale_without_another_call(tmp_path):
    from agent.decision_critic import CritiqueOutcome
    legal, expensive = _action("legal"), replace(_action("expensive"), cost=3)
    core = _controller(tmp_path, [TASK, _plan("expensive")])
    core._decision_critic = Mock()
    core._review_plan = Mock(return_value=CritiqueOutcome(model_version="fixture-review"))
    turn = core.run("task", available_actions=(legal, expensive),
                    intervention_profile=FunctionalInterventionProfile("fixture"), budget=1)
    core._review_plan.assert_called_once()
    assert turn.selected_actions == (legal,)
    audit = events(tmp_path, "final_plan_audit")[0]
    assert audit["reviewed_action_ids"] == ["expensive"]
    assert audit["submitted_action_ids"] == ["legal"]
    assert audit["review_matches_submitted_plan"] is False
    assert turn.decision_review["review_matches_submitted_plan"] is False


def test_expected_coverage_logs_response_as_diagnostic(tmp_path):
    action = _action()
    core = _controller(tmp_path, [TASK, _plan(action.identifier)])
    core._power_aware_selection = True
    core._virtual_cell = ApplicableWorldModel()
    turn = core.run("task", available_actions=(action,),
                    intervention_profile=FunctionalInterventionProfile("fixture"), budget=1,
                    virtual_cell_template=template((action,)))
    usage = events(tmp_path, "prediction_usage")[0]
    assert usage["selection_source"] == "expected_coverage"
    assert usage["response_priority_use"] == "diagnostic_only"
    assert turn.selected_actions == (action,)
