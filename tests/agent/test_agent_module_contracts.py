"""Agent boundary regressions: purchases, condition binding and durable tool context."""
from dataclasses import replace
import json
from types import SimpleNamespace

import numpy as np
import pytest

from agent.context import ContextBuilder, TaskIntent
from agent.discovery import DiscoverySpec, run_discovery
from agent.knowledge import EvidenceLedger
from agent.memory import MemoryScope, MemoryStore, RunLogger
from agent.prediction import PredictionCoordinator
from agent.tool_runtime import ToolExecution, ToolExecutionState, ToolReceipt
from maestro.models import EvidenceAction, EvidenceKind, MechanismContrast
from virtual_cell.interface import SystemContext, VirtualCellQueryTemplate
from tests.fixtures.world_model import ApplicableWorldModel


def _world():
    return SimpleNamespace(rows=np.arange(10), screen=SimpleNamespace(threshold=0.5),
                           posterior=lambda i, v: (np.arange(10), np.ones(10)),
                           p_hit=lambda mean, var: mean)


@pytest.mark.parametrize("indices", [[-1], [10], [True], [0.9], ["0"], [[0]], [0, 1, 2], [0, 0]])
def test_invalid_purchase_is_rejected_before_measurement(indices):
    calls = []
    planner = SimpleNamespace(choose=lambda available, measured, values, k: indices)
    with pytest.raises(ValueError):
        run_discovery(_world(), lambda i: calls.append(i) or np.ones(len(i)),
                      DiscoverySpec(budget_fraction=0.4, rounds=2, terminal="exploit"), planner=planner)
    assert calls == []


def test_numpy_integer_choices_preserve_budget_and_identity():
    planner = SimpleNamespace(choose=lambda available, measured, values, k: np.flatnonzero(available)[:k])
    report = run_discovery(_world(), lambda i: i.astype(float),
                           DiscoverySpec(budget_fraction=0.4, rounds=2, terminal="exploit"), planner=planner)
    assert report.purchases == [[0, 1], [2, 3]]
    assert report.labels == {0: 0.0, 1: 1.0, 2: 2.0, 3: 3.0}
    assert sum(map(len, report.purchases)) == report.budget


@pytest.mark.parametrize("changes", [{"rounds": True}, {"rounds": 2.5}, {"kappa": True},
                                    {"budget_fraction": True}, {"alpha": np.nan}, {"alpha": 1},
                                    {"delta": np.nan}, {"delta": 0}])
def test_invalid_discovery_configuration_precedes_external_measurement(changes):
    calls = []
    with pytest.raises(ValueError):
        run_discovery(_world(), lambda i: calls.append(i) or np.ones(len(i)), DiscoverySpec(**changes))
    assert calls == []


@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
def test_nonfinite_measurement_cannot_become_a_hit(value):
    with pytest.raises(ValueError, match="finite"):
        run_discovery(_world(), lambda i: np.full(len(i), value),
                      DiscoverySpec(budget_fraction=0.4, rounds=2, terminal="exploit"))


@pytest.mark.parametrize("scores", [np.full(10, np.nan), np.full(10, np.inf), np.ones(10, bool),
                                  np.ones(9), np.ones(11), np.ones((10, 1))])
def test_invalid_ranking_is_rejected_before_measurement(scores):
    calls = []
    with pytest.raises(ValueError, match="scores"):
        run_discovery(_world(), lambda i: calls.append(i) or np.ones(len(i)),
                      DiscoverySpec(budget_fraction=0.4, rounds=2, terminal="exploit"),
                      planner=SimpleNamespace(scores=lambda indices, values: scores))
    assert calls == []


@pytest.mark.parametrize("scores", [np.array([0, 1], dtype=np.uint64),
                                  np.array([np.iinfo(np.int64).min, 0], dtype=np.int64),
                                  np.array([2**63, 2**63 + 1], dtype=np.uint64)])
def test_integer_ranking_does_not_wrap_when_sorted_descending(scores):
    from agent.discovery import _top

    assert _top(scores, np.ones(2, dtype=bool), 1, np.random.default_rng(0)).tolist() == [1]


def test_safe_score_order_preserves_float_ties_and_random_state():
    from agent.discovery import _top

    scores = np.array([0.5, 0.5, 0.7, -0.5])
    original_rng, safe_rng = np.random.default_rng(3), np.random.default_rng(3)
    expected = np.lexsort((original_rng.random(4), -scores))
    assert _top(scores, np.ones(4, dtype=bool), 4, safe_rng).tolist() == expected.tolist()
    assert original_rng.random() == safe_rng.random()


@pytest.mark.parametrize("value", [True, "1.0", 1 + 0j])
def test_nonnumeric_measurement_is_not_coerced_into_a_hit(value):
    with pytest.raises(ValueError, match="finite numeric"):
        run_discovery(_world(), lambda i: np.full(len(i), value),
                      DiscoverySpec(budget_fraction=0.4, rounds=2, terminal="exploit"))


def _intent():
    return TaskIntent("analysis_planning", "Resolve TARGET conditions", ("TARGET",), ("drug",),
                      "cell-a", "RNA", (), (), (), False)


def _template():
    return VirtualCellQueryTemplate("drug", "drug", SystemContext("cell-a", "cell line"),
                                    ("embedding_delta_l2",), "model-1", dose=0.05, dose_unit="uM", time_hours=6)


@pytest.mark.parametrize("mapped", [False, True])
@pytest.mark.parametrize("template_time", [None, 6])
def test_template_binds_registered_action_conditions(tmp_path, mapped, template_time):
    action = EvidenceAction("assay", "Assay", 1, (), time_hours=24,
                            expected_conditions={"dose_uM": "5"})
    template = replace(_template(), action_interventions={"assay": "drug"} if mapped else {}, time_hours=template_time)
    model = ApplicableWorldModel()
    answers = PredictionCoordinator(model, RunLogger(tmp_path)).query(
        MechanismContrast("contrast", (), (), action, (), ()), _intent(), None, "case", "session", (action,),
        prediction_request=None, template=template)
    assert len(model.requests) == 1
    request = answers.requests["assay"]
    assert (request.intervention.dose, request.intervention.dose_unit, request.intervention.time_hours) == (5, "uM", 24)
    assert answers.predictions["assay"].applicable


@pytest.mark.parametrize("changes,reason", [
    ({"execution_context": "cell-b"}, "action_query_context_mismatch"),
    ({"expected_conditions": {"plate": "plate-6"}}, "unexpressible_action_conditions:plate"),
    ({"time_hours": 24, "expected_conditions": {"exposure_hours": "48"}}, "action_query_time_mismatch"),
    ({"expected_conditions": {"intervention": "other-drug"}}, "action_query_intervention_mismatch"),
])
def test_shared_template_refuses_unbound_conditions_with_audit_reason(tmp_path, changes, reason):
    action = replace(EvidenceAction("assay", "Assay", 1, ()), **changes)
    model = ApplicableWorldModel()
    answers = PredictionCoordinator(model, RunLogger(tmp_path)).query(
        MechanismContrast("contrast", (), (), action, (), ()), _intent(), None, "case", "session", (action,),
        prediction_request=None, template=_template())
    assert answers.requests == {} and model.requests == []
    event = json.loads((tmp_path / "events.jsonl").read_text().strip())
    assert event["payload"]["reasons"] == {"assay": reason}


def test_explicit_request_is_not_rewritten_to_fit_an_action(tmp_path):
    action = EvidenceAction("assay", "Assay", 1, (), time_hours=24,
                            expected_conditions={"dose_uM": "5"})
    request = _template().build(request_id="explicit", case_id="case", contrast_id="contrast",
                                plan_version=1, intended_targets=("TARGET",))
    model = ApplicableWorldModel()
    answers = PredictionCoordinator(model, RunLogger(tmp_path)).query(
        MechanismContrast("contrast", (), (), action, (), ()), _intent(), None, "case", "session", (action,),
        prediction_request=request, template=None)
    assert answers.requests == {} and model.requests == []


@pytest.mark.parametrize("changes", [{"case_id": "other-case"}, {"contrast_id": "other-contrast"},
                                    {"plan_version": 99}])
def test_explicit_query_must_belong_to_current_plan_before_inference(tmp_path, changes):
    action = EvidenceAction("assay", "Assay", 1, (), time_hours=6,
                            expected_conditions={"dose_uM": "0.05"})
    request = _template().build(request_id="explicit", case_id="case", contrast_id="contrast",
                                plan_version=1, intended_targets=("TARGET",))
    model = ApplicableWorldModel()
    answers = PredictionCoordinator(model, RunLogger(tmp_path)).query(
        MechanismContrast("contrast", (), (), action, (), ()), _intent(), None, "case", "session", (action,),
        prediction_request=replace(request, **changes), template=None)
    assert answers.requests == {} and model.requests == []
    event = json.loads((tmp_path / "events.jsonl").read_text().strip())
    assert event["payload"]["reasons"] == {"assay": "explicit_query_plan_identity_mismatch"}


def _execution(tmp_path):
    return ToolExecution("source-resolver", tmp_path / "sources.json", ("TARGET source found.",),
                         ("Metadata only; not measured RNA.",), (), "Resolve exact source", EvidenceKind.RETRIEVED_SOURCE,
                         ToolReceipt("receipt-1", ToolExecutionState.COMMITTED, (ToolExecutionState.COMMITTED,),
                                     "input-hash", "tool-hash", {"condition": "drug"}, "session", 0, "output-hash"),
                         {"source_plate": "plate-6"})


def test_tool_context_survives_same_case_rebuild_without_cross_case_leak(tmp_path):
    builder = ContextBuilder(EvidenceLedger(tmp_path / "e.sqlite"), MemoryStore(tmp_path / "m.sqlite"))
    packet = builder.build(_intent(), memory_scope=MemoryScope(case_id="case-a"))
    execution = _execution(tmp_path)
    packet = builder.add_tool_execution(packet, execution, case_id="case-a")
    packet = builder.add_tool_execution(packet, execution, case_id="case-a")
    rebuilt = builder.build(_intent(), memory_scope=MemoryScope(case_id="case-a"))
    assert len(packet.evidence) == len(rebuilt.evidence) == 1
    record = rebuilt.evidence[0]
    assert record.case_id == "case-a" and record.partition == "case"
    assert record.evidence_kind is EvidenceKind.RETRIEVED_SOURCE
    assert record.payload["receipt"]["input_sha256"] == "input-hash"
    assert record.payload["tool_payload"] == {"source_plate": "plate-6"}
    assert "Metadata only" in rebuilt.rendered
    assert builder.build(_intent(), memory_scope=MemoryScope(case_id="case-b")).evidence == ()
    assert builder.build(_intent()).evidence == ()
    with pytest.raises(ValueError, match="identifier conflict"):
        builder.add_tool_execution(packet, replace(execution, observations=("changed",)), case_id="case-a")


def test_orchestrator_binds_tool_projection_to_its_durable_case(tmp_path, monkeypatch):
    from tests.fixtures.orchestration import TASK, _controller
    from maestro.models import FunctionalInterventionProfile

    # A clarification turn still owns the tools it already executed; no measurement plan is needed.
    controller = _controller(tmp_path, [dict(TASK, missing_information=["existing_observation"])])
    execution = _execution(tmp_path)
    monkeypatch.setattr(controller, "_run_dataset_tool", lambda *args: (execution,))
    turn = controller.run("Resolve TARGET conditions", available_actions=(),
                          intervention_profile=FunctionalInterventionProfile(mode="drug"), case_id="case-a")
    assert turn.tool_executions == (execution,)
    rebuilt = controller._context_builder.build(_intent(), memory_scope=MemoryScope(case_id="case-a"))
    assert len(rebuilt.evidence) == 1 and rebuilt.evidence[0].case_id == "case-a"
    assert controller._context_builder.build(_intent(), memory_scope=MemoryScope(case_id="case-b")).evidence == ()
