"""End-to-end orchestrator behaviour from task to logged decision.

File summary
- Path: tests/test_orchestrator.py
- Purpose: End-to-end orchestrator behaviour from task to logged decision.
- Core points: assertions here are contract tests, not biological results; each test pins one boundary that must not silently move.
- Interfaces: `test_orchestrator_keeps_missing_functional_precondition_out_of_mechanism_update()`, `test_visual_inspector_sends_local_image_in_user_content_only()`, `test_visual_review_is_a_planner_context_partition_not_evidence()`, `test_knowledge_base_ingests_source_chunks_without_marking_them_measured()`, `test_orchestrator_routes_a_supplied_dataset_through_a_registered_tool()`, `test_orchestrator_keeps_a_llm_repair_only_after_deterministic_recheck()`
- Depends on: agent, maestro
"""
from pathlib import Path

from maestro.contrast import MAESTROAgent
from agent.audit import RunLogger
from agent.context import ContextBuilder, TaskIntent, TaskInterpreter
from agent.knowledge import EvidenceLedger, EvidenceStatus, KnowledgeBase
from agent.memory import MemoryStore
from maestro.models import (
    EvidenceAction,
    EvidenceActionKind,
    FunctionalInterventionProfile,
    NonDiscriminabilityReason,
    RepairKind,
)
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import MechanismContrastPlanner
from agent.tool_runtime import ToolRouter
from agent.vision import VisualInspection, VisualInspector

from tools.shared.stub_client import StubClient  # noqa: E402
def test_orchestrator_keeps_missing_functional_precondition_out_of_mechanism_update(
    tmp_path: Path,
):
    client = StubClient(
        [
            {
                "task_type": "mechanism_diagnosis",
                "research_question": "Explain a genetic-pharmacological mismatch.",
                "target_or_targets": ["TARGET"],
                "interventions": ["compound"],
                "biological_context": "cell line",
                "phenotype_endpoint": "viability",
                "supplied_evidence": ["Genetic perturbation reduced viability."],
                "constraints": [],
                "missing_information": [],
                "needs_visual_review": False,
            },
            {
                "identifier": "implementation-vs-mode",
                "hypotheses": [
                    {
                        "identifier": "functional_gap",
                        "description": "Target activity was not sufficiently changed.",
                        "proposed_action": "revise_intervention",
                    },
                    {
                        "identifier": "mode_mismatch",
                        "description": "The two perturbation modes are not equivalent.",
                        "proposed_action": "change_intervention_mode",
                    },
                ],
                "differing_assumptions": ["target activity in the phenotype time window"],
                "action_identifier": "viability_readout",
                "outcome_categories": ["functional change insufficient", "functional change measured"],
                "interpretation_boundaries": ["An absent phenotype does not alone invalidate the target."],
            },
        ]
    )
    log_root = tmp_path / "log" / "20260910"
    memory = MemoryStore(log_root / "memory.sqlite")
    controller = MAESTROOrchestrator(
        interpreter=TaskInterpreter(client),
        context_builder=ContextBuilder(EvidenceLedger(log_root / "evidence.sqlite"), memory),
        planner=MechanismContrastPlanner(client),
        visual_inspector=VisualInspector(client, "vision-model"),
        memory=memory,
        logger=RunLogger(log_root),
        controller=MAESTROAgent(),
    )
    viability = EvidenceAction(
        "viability_readout",
        "Measure viability after intervention.",
        5.0,
        ("functional_gap", "mode_mismatch"),
        prerequisites=("functional:target_activity",),
    )
    target_activity = EvidenceAction(
        "target_activity",
        "Measure proximal target activity.",
        2.0,
        ("functional_gap",),
        kind=EvidenceActionKind.FUNCTIONAL_MEASUREMENT,
    )

    turn = controller.run(
        "Genetic loss is lethal, but the compound is negative.",
        available_actions=(viability, target_activity),
        intervention_profile=FunctionalInterventionProfile(mode="inhibition"),
        session_id="test-session",
    )

    assert turn.check is not None
    assert NonDiscriminabilityReason.MISSING_FUNCTIONAL_MEASUREMENT in turn.check.reasons
    assert turn.repair is not None
    assert turn.repair.kind is RepairKind.ADD_FUNCTIONAL_MEASUREMENT
    assert (log_root / "events.jsonl").is_file()
    assert (log_root / "experiments.jsonl").is_file()


def test_visual_inspector_sends_local_image_in_user_content_only(tmp_path: Path):
    image = tmp_path / "plot.png"
    image.write_bytes(b"not-a-real-png-but-a-local-test-fixture")
    client = StubClient(
        [
            {
                "observations": ["A two-group plot is visible."],
                "quality_concerns": ["Axis units are not visible."],
                "decision_relevance": "Request the underlying measurements before updating a mechanism.",
                "limitations": ["The image does not establish causality."],
            }
        ]
    )

    result = VisualInspector(client, "vision-model").inspect((image,), question="Inspect the plot.")

    assert result[0].observations == ("A two-group plot is visible.",)
    message = client.calls[0][0][1]
    assert message["role"] == "user"
    assert message["content"][1]["type"] == "image_url"
    assert client.calls[0][1]["model"] == "vision-model"


def test_visual_review_is_a_planner_context_partition_not_evidence(tmp_path: Path):
    builder = ContextBuilder(EvidenceLedger(tmp_path / "evidence.sqlite"), MemoryStore(tmp_path / "memory.sqlite"))
    packet = builder.build(
        TaskIntent("mechanism_diagnosis", "Explain a mismatch.", (), (), None, None, (), (), (), True)
    )
    reviewed = builder.add_visual_reviews(
        packet,
        (
            VisualInspection(
                tmp_path / "plot.png",
                ("Two groups are visible.",),
                (),
                "Check the underlying measurements.",
                ("No causal conclusion follows.",),
            ),
        ),
    )

    assert "VISUAL REVIEW (not measured evidence)" in reviewed.rendered
    assert reviewed.visual_reviews
    assert reviewed.evidence == ()


def test_knowledge_base_ingests_source_chunks_without_marking_them_measured(tmp_path: Path):
    knowledge = KnowledgeBase(tmp_path / "knowledge.sqlite")

    records = knowledge.ingest_text(
        "First source paragraph.\n\nSecond source paragraph.",
        source="source-a",
        context="defined cell context",
        chunk_size=200,
    )

    assert len(records) == 1
    assert records[0].status is EvidenceStatus.RETRIEVED
    assert knowledge.retrieve("second source", limit=1)[0].source == "source-a"


def test_orchestrator_routes_a_supplied_dataset_through_a_registered_tool(tmp_path: Path):
    dataset = tmp_path / "assay.csv"
    dataset.write_text("compound,ic50\nA,12.5\nB,\n", encoding="utf-8")
    client = StubClient(
        [
            {
                "task_type": "analysis_planning",
                "research_question": "Profile the supplied assay table.",
                "target_or_targets": ["TARGET"],
                "interventions": ["compound"],
                "biological_context": "cell line",
                "phenotype_endpoint": "IC50",
                "supplied_evidence": [],
                "constraints": [],
                "missing_information": [],
                "needs_visual_review": False,
            },
            {
                "tool_id": "data_profile",
                "dataset_id": "dataset_1",
                "arguments": {},
                "rationale": "Schema inspection is needed before any targeted analysis.",
            },
            {"tool_id": None},
            {
                "identifier": "implementation-vs-mode",
                "hypotheses": [
                    {
                        "identifier": "functional_gap",
                        "description": "Target activity was not sufficiently changed.",
                        "proposed_action": "revise_intervention",
                    },
                    {
                        "identifier": "mode_mismatch",
                        "description": "The two perturbation modes are not equivalent.",
                        "proposed_action": "change_intervention_mode",
                    },
                ],
                "differing_assumptions": ["target activity in the phenotype time window"],
                "action_identifier": "viability_readout",
                "outcome_categories": ["functional change insufficient", "functional change measured"],
                "interpretation_boundaries": ["An absent phenotype does not alone invalidate the target."],
            },
        ]
    )
    log_root = tmp_path / "log" / "20260910"
    memory = MemoryStore(log_root / "memory.sqlite")
    controller = MAESTROOrchestrator(
        interpreter=TaskInterpreter(client),
        context_builder=ContextBuilder(EvidenceLedger(log_root / "evidence.sqlite"), memory),
        planner=MechanismContrastPlanner(client),
        visual_inspector=VisualInspector(client, "vision-model"),
        memory=memory,
        logger=RunLogger(log_root),
        controller=MAESTROAgent(),
        tool_router=ToolRouter(client, Path(__file__).resolve().parents[1] / "tools"),
    )
    action = EvidenceAction("viability_readout", "Measure viability.", 5.0, ("functional_gap", "mode_mismatch"))

    turn = controller.run(
        "Profile the assay data before planning.",
        available_actions=(action,),
        intervention_profile=FunctionalInterventionProfile(mode="inhibition"),
        dataset_paths=(dataset,),
    )

    assert turn.tool_executions[0].tool_id == "data_profile"
    assert turn.tool_executions[0].dataset_path == dataset.resolve()
    assert "DATASET TOOL OUTPUT" in client.calls[3][0][1]["content"]
    assert "tool:data_profile:assay.csv" in client.calls[3][0][1]["content"]


def test_orchestrator_keeps_a_llm_repair_only_after_deterministic_recheck(tmp_path: Path):
    client = StubClient(
        [
            {
                "task_type": "mechanism_diagnosis",
                "research_question": "Resolve the discrepancy.",
                "target_or_targets": ["TARGET"],
                "interventions": ["compound"],
                "biological_context": "cell line",
                "phenotype_endpoint": "viability",
                "supplied_evidence": [],
                "constraints": [],
                "missing_information": [],
                "needs_visual_review": False,
            },
            {
                "identifier": "contrast",
                "hypotheses": [
                    {"identifier": "a", "description": "A", "proposed_action": "continue"},
                    {"identifier": "b", "description": "B", "proposed_action": "revise_intervention"},
                ],
                "differing_assumptions": ["model-supported readout"],
                "action_identifier": "model_action",
                "outcome_categories": ["a", "b"],
                "interpretation_boundaries": ["Prediction does not replace measurement."],
            },
            {
                "action_identifier": "measured_action",
                "modified_fields": ["plan.action_identifier"],
                "rationale": "Use the registered measurement without an unsupported prediction.",
                "remaining_limitations": ["A real result is still required."],
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
        enable_llm_repair=True,
    )
    model_action = EvidenceAction(
        "model_action", "Model-guided assay.", 1.0, ("a", "b"), requires_virtual_prediction=True
    )
    measured_action = EvidenceAction(
        "measured_action", "Measured assay.", 2.0, ("a", "b"),
        expected_outcomes={"a": "outcome_a", "b": "outcome_b"},
    )

    turn = controller.run(
        "Resolve this discrepancy.",
        available_actions=(model_action, measured_action),
        intervention_profile=FunctionalInterventionProfile(mode="inhibition"),
    )

    assert turn.llm_repair is not None
    assert turn.llm_repair.action_identifier == "measured_action"
    assert turn.contrast is not None
    assert turn.contrast.plan is not None
    assert turn.contrast.plan.identifier == "measured_action"
    assert turn.check is not None
    assert turn.check.ready_for_mechanism_update
    assert turn.repair is None
