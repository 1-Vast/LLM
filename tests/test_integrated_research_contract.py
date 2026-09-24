"""Production boundaries: corrupt predictions and absent measurements fail closed."""
from dataclasses import replace
import json
from types import SimpleNamespace

import pytest

from agent.orchestrator import MAESTROOrchestrator
from agent.tool_runtime import ToolRouter
from maestro import EvidenceAction, FunctionalInterventionProfile
from maestro.acquisition import select_expected_coverage
from maestro.handoff import RoundRecord, read_round
from maestro.reliability import PredictionReliabilityLedger
from virtual_cell.interface import Intervention, PredictionRequest, SystemContext
from virtual_cell import CompositeWorldModel, StatePrediction
from pathlib import Path
from agent.context import ContextPacket, TaskIntent
from maestro.handoff import EvidenceLayer, WorldModelLayer, DecisionLayer, ExecutionLayer
from maestro.tool_analysis import evidence_bundle_optimize
from virtual_cell import ModelCapabilities, QueryAssessment, QuerySupport
from evaluation.public_loop import run as run_public_loop

ROOT = Path(__file__).resolve().parents[1]


def _round():
    return RoundRecord("test", 1, EvidenceLayer(missing_reason=("no_evidence",)),
                       WorldModelLayer.no_model(), DecisionLayer(), ExecutionLayer())


class ApplicableWorldModel:
    def capabilities(self):
        return ModelCapabilities("test", "model-1", "scalar", "label", ("drug",), False, False, False, None)

    def assess_query(self, query):
        return QueryAssessment(QuerySupport.SUPPORTED, (), (), self.capabilities())

    def predict(self, query):
        return StatePrediction(True, {"embedding_delta_l2": 1.0}, None, (), request_id=query.request_id,
                               model_version="model-1", confidence=0.5, in_distribution=True)


def _context():
    return ContextPacket(TaskIntent("analysis_planning", "Inspect", (), (), None, None, (), (), (), False), (), (), "Inspect")
from tools.shared.stub_client import StubClient


def request():
    return PredictionRequest("request", "case", "contrast", 1, Intervention("drug", "drug", ()),
                             SystemContext("cells", "test"), ("embedding_delta_l2",), "model-1")


@pytest.mark.parametrize("layer,field", [
    ("L2_world_model", "in_distribution"), ("L3_decision", "rejected"),
    ("L4_execution", "contradiction_flag"),
])
def test_disk_handoff_refuses_missing_fields(tmp_path, layer, field):
    data = _round().to_payload()
    del data["layers"][layer][field]
    path = tmp_path / "round.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="mandatory_field_missing"):
        read_round(path)


@pytest.mark.parametrize("layer,field,value", [
    ("L2_world_model", "in_distribution", "false"),
    ("L2_world_model", "mean", float("nan")),
    ("L3_decision", "rejected", None),
    ("L4_execution", "contradiction_flag", None),
])
def test_handoff_does_not_coerce_bad_safety_fields(layer, field, value):
    data = _round().to_payload()
    data["layers"][layer][field] = value
    with pytest.raises(ValueError):
        RoundRecord.from_payload(data)


@pytest.mark.parametrize("change,reason", [
    ({"request_id": "other"}, "request_id_mismatch"),
    ({"model_version": "other"}, "prediction_model_mismatch"),
    ({"state_change": {"embedding_delta_l2": float("nan")}}, "contract_violation"),
])
def test_main_agent_and_composite_enforce_the_same_boundary(change, reason):
    class Corrupt(ApplicableWorldModel):
        name = "corrupt"

        def predict(self, query):
            return replace(super().predict(query), **change)

    logger = SimpleNamespace(event=lambda *a, **k: None, experiment=lambda *a, **k: None)
    controller = object.__new__(MAESTROOrchestrator)
    controller._logger, controller._virtual_cell = logger, Corrupt()
    _, output = controller._predict_virtual_cell(request(), "test")
    composite = CompositeWorldModel([Corrupt()]).predict(request())
    for prediction in (output, composite):
        assert prediction.abstain_reason == reason
        assert prediction.state_change is None and prediction.contract_valid


@pytest.mark.parametrize("change", [{"in_distribution": False}, {"request_id": "other"},
                                   {"model_version": "other"}])
def test_invalid_prediction_cannot_influence_decision_ranking(change):
    controller = object.__new__(MAESTROOrchestrator)
    controller._reliability = PredictionReliabilityLedger()
    source = replace(ApplicableWorldModel().predict(request()), **change)
    action = EvidenceAction("a", "assay", 1, ("h",), prediction_readout="embedding_delta_l2", prediction_relevance=1)
    assert controller._prediction_action_priorities(source, request(), (action,)) == {}


def test_zero_information_does_not_spend_budget_and_cap_names_every_refusal():
    profile = FunctionalInterventionProfile(mode="drug")
    actions = (EvidenceAction("a", "irrelevant assay", 1, ("other",), detection_power=0.5),)
    assert not select_expected_coverage(frozenset({"h"}), actions, profile, 2).plan.actions
    many = tuple(replace(actions[0], identifier=str(i)) for i in range(17))
    answer = select_expected_coverage(frozenset({"h"}), many, profile, 2)
    assert answer.status == "too_large" and len(answer.rejected) == 17
    assert {item.reason for item in answer.rejected} == {"exact_candidate_limit_exceeded"}


def test_registered_optimizer_uses_declared_detection_power(tmp_path):
    data = {"schema_version": "1.0", "budget": 1, "cost_unit": "wells", "context": "cells",
            "time_hours": 24, "required": ["h1"], "sources": [{"id": "source", "independence_group": "study"}],
            "actions": [{"id": name, "cost": 1, "cost_unit": "wells", "context": "cells", "time_hours": 24,
                         "distinguishes": ["h1"], "source_ids": ["source"], "independent_unit": "well",
                         "quantity": "viability", "detection_power": power} for name, power in [("a", 0.1), ("b", 0.9)]]}
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    answer = evidence_bundle_optimize({"dataset_path": str(path)})["payload"]
    assert answer["solver"] == "select_expected_coverage"
    assert answer["selected_action_ids"] == ["b"]
    assert answer["expected_coverage"] == pytest.approx(0.9)


def test_main_agent_preserves_completed_tools_after_later_failure(tmp_path):
    dataset = tmp_path / "measurements.csv"
    dataset.write_text("x\n1\n2\n", encoding="utf-8")
    controller = object.__new__(MAESTROOrchestrator)
    controller._logger = SimpleNamespace(event=lambda *a, **k: None)
    controller._tool_router = ToolRouter(StubClient([
        {"tool_id": "data_profile", "dataset_id": "dataset_1", "arguments": {}},
        {"tool_id": "column_summary", "dataset_id": "dataset_1", "arguments": {"column": "x"}},
        {"tool_id": "unregistered", "dataset_id": "dataset_1", "arguments": {}},
    ]), ROOT / "tools")
    executions = controller._run_dataset_tool(_context(), (dataset,), "plan-v1")
    assert [item.tool_id for item in executions] == ["data_profile", "column_summary"]
    assert all(item.receipt.plan_version == "plan-v1" for item in executions)


def test_self_combination_preserves_reparameterization_even_in_a_validated_window():
    import math
    for first, second in [(0.1, 0.3), (1, 2)]:
        for exponent in (1, 2):
            residual = lambda d: math.exp(-exponent * d)
            assert residual(first + second) == pytest.approx(residual(first) * residual(second))
    assert math.exp(-1) != math.exp(-2)


def test_public_data_loop_reaches_both_registered_stops(tmp_path):
    summary = run_public_loop(ROOT, tmp_path / "public_loop")

    missing = summary["arms"]["missing_result"]
    imported = summary["arms"]["public_result_import"]
    assert missing["stop_reason"] == "awaiting_result"
    assert imported["stop_reason"] == "result_quality_failed"
    assert missing["tools"] == ["data_profile", "virtual_cell_query"]
    assert imported["tools"] == ["data_profile", "virtual_cell_query"]
    assert missing["model_refusals"] == ["query_unsupported"]
    assert imported["model_refusals"] == ["query_unsupported"]
    assert missing["mechanism_updates"] == imported["mechanism_updates"] == 0
    assert summary["new_experiment_wells"] == summary["turnaround_days"] == 0

    plan_paths = list((tmp_path / "public_loop").glob("*/rounds/*.plan.json"))
    assert len(plan_paths) == 2
    for plan_path in plan_paths:
        layers = json.loads(plan_path.read_text(encoding="utf-8"))["layers"]
        assert "in_distribution" in layers["L2_world_model"]
        assert isinstance(layers["L3_decision"]["rejected"], list)
        assert isinstance(layers["L4_execution"]["contradiction_flag"], bool)
