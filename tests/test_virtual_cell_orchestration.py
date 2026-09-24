"""Virtual-cell predictions may rank actions but never satisfy a premise.

File summary
- Path: tests/test_virtual_cell_orchestration.py
- Purpose: Virtual-cell predictions may rank actions but never satisfy a premise.
- Core points: assertions here are contract tests, not biological results; each test pins one boundary that must not silently move.
- Interfaces: `test_orchestrator_checks_a_supported_virtual_cell_prediction()`, `test_orchestrator_builds_a_bound_prediction_request_and_uses_signal_only_to_break_a_tie()`
- Depends on: agent, maestro, virtual_cell
"""
from pathlib import Path

from agent.audit import RunLogger
from agent.context import ContextBuilder, TaskInterpreter
from agent.knowledge import EvidenceLedger
from agent.memory import MemoryStore
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import MechanismContrastPlanner
from agent.vision import VisualInspector
from maestro import EvidenceAction, FunctionalInterventionProfile, MAESTROAgent
from virtual_cell import (
    Intervention,
    Interval,
    IntervalKind,
    ModelCapabilities,
    PredictionRequest,
    QueryAssessment,
    QuerySupport,
    StatePrediction,
    SystemContext,
    VirtualCellQueryTemplate,
)

from tools.shared.stub_client import StubClient  # noqa: E402
class ApplicableWorldModel:
    def __init__(self):
        self.requests = []

    def capabilities(self):
        return ModelCapabilities("test", "model-1", "embedding", "condition", ("drug",), True, False, False, None)

    def assess_query(self, request):
        self.requests.append(request)
        return QueryAssessment(QuerySupport.SUPPORTED, (), (), self.capabilities())

    def predict(self, request):
        return StatePrediction(
            True, {"embedding_delta_l2": 1.0}, None, (),
            intervals={
                "embedding_delta_l2": Interval(
                    0.5, 1.5, kind=IntervalKind.CALIBRATED, level=0.9,
                    basis="held-out residuals for the declared test split",
                )
            },
            request_id=request.request_id, model_version=request.model_version,
            confidence=None, in_distribution=True,
            uncertainty_components={"fixture": "not independently calibrated"},
        )


def test_orchestrator_checks_a_supported_virtual_cell_prediction(tmp_path: Path):
    client = StubClient(
        [
            {
                "task_type": "mechanism_diagnosis", "research_question": "Resolve discrepancy.",
                "target_or_targets": ["TARGET"], "interventions": ["compound"],
                "biological_context": "cell line", "phenotype_endpoint": "viability",
                "supplied_evidence": [], "constraints": [], "missing_information": [], "needs_visual_review": False,
            },
            {
                "identifier": "contrast",
                "hypotheses": [
                    {"identifier": "a", "description": "A", "proposed_action": "continue"},
                    {"identifier": "b", "description": "B", "proposed_action": "revise_intervention"},
                ],
                "differing_assumptions": ["model readout"], "action_identifier": "model-action",
                "outcome_categories": ["a", "b"], "interpretation_boundaries": ["Prediction is not a measurement."],
            },
        ]
    )
    root = tmp_path / "log" / "20260910"
    memory = MemoryStore(root / "memory.sqlite")
    controller = MAESTROOrchestrator(
        interpreter=TaskInterpreter(client),
        context_builder=ContextBuilder(EvidenceLedger(root / "evidence.sqlite"), memory),
        planner=MechanismContrastPlanner(client),
        visual_inspector=VisualInspector(client, "vision"),
        memory=memory,
        logger=RunLogger(root),
        controller=MAESTROAgent(),
        virtual_cell=ApplicableWorldModel(),
    )
    request = PredictionRequest(
        "request-1", "case-1", "contrast", 1,
        Intervention("drug-label", "drug", ("TARGET",)),
        SystemContext("cell-a", "cell line", dataset_id="dataset", control_dataset_id="control"),
        ("embedding_delta_l2",), "model-1",
    )

    turn = controller.run(
        "Resolve discrepancy.",
        available_actions=(EvidenceAction(
            "model-action", "Model-guided assay.", 1.0, ("a", "b"),
            requires_virtual_prediction=True, prediction_readout="embedding_delta_l2",
            expected_outcomes={"a": "large_embedding_shift", "b": "small_embedding_shift"},
        ),),
        intervention_profile=FunctionalInterventionProfile(mode="inhibition"),
        prediction_request=request,
    )

    assert turn.prediction is not None and turn.prediction.applicable
    assert turn.prediction_assessment is not None
    assert turn.check is not None and turn.check.ready_for_mechanism_update


def test_orchestrator_builds_a_bound_prediction_request_and_uses_signal_only_to_break_a_tie(tmp_path: Path):
    client = StubClient(
        [
            {
                "task_type": "mechanism_diagnosis", "research_question": "Resolve discrepancy.",
                "target_or_targets": ["TARGET"], "interventions": ["compound"],
                "biological_context": "cell line", "phenotype_endpoint": "viability",
                "supplied_evidence": [], "constraints": [], "missing_information": [], "needs_visual_review": False,
            },
            {
                "identifier": "contrast", "hypotheses": [
                    {"identifier": "a", "description": "A", "proposed_action": "continue"},
                    {"identifier": "b", "description": "B", "proposed_action": "revise_intervention"},
                ],
                "differing_assumptions": ["model readout"], "action_identifier": "plain",
                "outcome_categories": ["a", "b"], "interpretation_boundaries": ["Prediction is not a measurement."],
            },
        ]
    )
    root = tmp_path / "log" / "20260910"
    memory = MemoryStore(root / "memory.sqlite")
    world_model = ApplicableWorldModel()
    controller = MAESTROOrchestrator(
        interpreter=TaskInterpreter(client),
        context_builder=ContextBuilder(EvidenceLedger(root / "evidence.sqlite"), memory),
        planner=MechanismContrastPlanner(client),
        visual_inspector=VisualInspector(client, "vision"),
        memory=memory,
        logger=RunLogger(root),
        controller=MAESTROAgent(),
        virtual_cell=world_model,
    )
    template = VirtualCellQueryTemplate(
        "registered-drug", "drug",
        SystemContext("cell-a", "cell line", dataset_id="dataset", control_dataset_id="control"),
        ("embedding_delta_l2",), "model-1",
    )
    plain = EvidenceAction(
        "plain", "Plain assay.", 1.0, ("a", "b"),
        expected_outcomes={"a": "outcome_a", "b": "outcome_b"},
    )
    model_guided = EvidenceAction(
        "model-guided", "Model-aligned assay.", 1.0, ("a", "b"),
        prediction_readout="embedding_delta_l2", prediction_relevance=1.0,
        expected_outcomes={"a": "outcome_a", "b": "outcome_b"},
    )

    turn = controller.run(
        "Resolve discrepancy.", available_actions=(plain, model_guided),
        intervention_profile=FunctionalInterventionProfile(mode="inhibition"),
        case_id="template-case", budget=1.0, virtual_cell_template=template,
    )

    assert tuple(action.identifier for action in turn.selected_actions) == ("model-guided",)
    assert world_model.requests[0].case_id == "template-case"
    assert world_model.requests[0].contrast_id == "contrast"
    assert world_model.requests[0].intervention.intended_targets == ("TARGET",)
