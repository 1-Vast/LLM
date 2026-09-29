"""A result that arrives outside the case loop is still reconciled.

File summary
- Path: tests/test_single_shot_reconciliation.py
- Purpose: close the second half of the second defect: `import_measurement` and
  `record_revealed_result` score the prediction they were planned against, so a
  ledger fed only by those callers is no longer permanently empty.
- Core points: assertions here are contract tests, not biological results; the
  prediction and the result are both fixtures.
- Interfaces: `test_a_single_shot_import_scores_the_prediction()`,
  `test_reimporting_the_same_result_is_ignored_once()`,
  `test_unqualified_and_mismatched_results_are_not_scored()`.
- Depends on: agent, maestro, virtual_cell
"""
import json
from pathlib import Path

from agent.memory import RunLogger
from agent.memory import CaseStore, MeasurementResult
from agent.context import ContextBuilder, TaskInterpreter
from agent.knowledge import EvidenceLedger
from agent.memory import MemoryStore
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import MechanismContrastPlanner
from agent.llm import VisualInspector
from maestro import EvidenceAction, FunctionalInterventionProfile, MAESTROAgent
from maestro.models import EvidenceKind
from maestro.judgment import PredictionReliabilityLedger
from virtual_cell.interface import Interval, IntervalKind, ModelCapabilities, QueryAssessment, QuerySupport, SystemContext, VirtualCellQueryTemplate
from virtual_cell import StatePrediction

from tests.fixtures.stub_client import StubClient  # noqa: E402

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
READOUT = "embedding_delta_l2"
ACTION = "model-guided"


class FixtureWorldModel:
    """One registered condition, answered with a coverage-claiming interval."""

    name = "fixture"

    def capabilities(self):
        return ModelCapabilities("test", "model-1", "embedding", "condition", ("drug",), True, False, False, None)

    def assess_query(self, request):
        return QueryAssessment(QuerySupport.SUPPORTED, (), (), self.capabilities())

    def predict(self, request):
        return StatePrediction(
            True, {READOUT: 1.25}, None, ("fixture output",),
            intervals={READOUT: Interval(1.0, 1.5, kind=IntervalKind.CALIBRATED, level=0.9, basis="fixture residuals")},
            request_id=request.request_id, model_version=request.model_version,
            confidence=None, in_distribution=True, compute_cost=1.0,
            uncertainty_components={"fixture": "not independently calibrated"},
        )


def _plan(action: str = ACTION) -> dict:
    return {
        "identifier": "contrast", "hypotheses": HYPOTHESES,
        "differing_assumptions": ["model readout"], "action_identifier": action,
        "outcome_categories": ["a", "b"], "interpretation_boundaries": ["Prediction is not a measurement."],
    }


def _action() -> EvidenceAction:
    return EvidenceAction(
        ACTION, "Model-aligned assay.", 1.0, ("a", "b"),
        prediction_readout=READOUT, prediction_relevance=1.0,
        expected_outcomes={"a": "outcome_a", "b": "outcome_b"},
    )


def _template() -> VirtualCellQueryTemplate:
    return VirtualCellQueryTemplate(
        "drug-known", "drug",
        SystemContext("cell-a", "cell line", dataset_id="dataset", control_dataset_id="control"),
        (READOUT,), "model-1",
        action_interventions={ACTION: "drug-known"},
    )


def _controller(root: Path) -> tuple[MAESTROOrchestrator, PredictionReliabilityLedger]:
    client = StubClient([TASK, _plan()])
    memory = MemoryStore(root / "memory.sqlite")
    ledger = PredictionReliabilityLedger()
    controller = MAESTROOrchestrator(
        interpreter=TaskInterpreter(client),
        context_builder=ContextBuilder(EvidenceLedger(root / "evidence.sqlite"), memory),
        planner=MechanismContrastPlanner(client),
        visual_inspector=VisualInspector(client, "vision"),
        memory=memory,
        logger=RunLogger(root),
        controller=MAESTROAgent(),
        virtual_cell=FixtureWorldModel(),
        case_store=CaseStore(root / "cases.sqlite"),
        reliability=ledger,
    )
    return controller, ledger


def _result(*, context_identifier: str = "cell-a", quality_passed: bool = True,
            result_id: str | None = None) -> MeasurementResult:
    return MeasurementResult(
        ACTION, "Observed.", "source-a", context_identifier, None, 3, quality_passed,
        metrics={READOUT: "1.2"}, result_id=result_id, evidence_kind=EvidenceKind.REAL_MEASUREMENT,
    )


def _events(root: Path, kind: str) -> list[dict]:
    lines = (root / "events.jsonl").read_text(encoding="utf-8").splitlines()
    return [record["payload"] for record in map(json.loads, lines) if record["kind"] == kind]


def test_a_single_shot_import_scores_the_prediction(tmp_path: Path):
    controller, ledger = _controller(tmp_path)
    turn = controller.run(
        "Resolve.", available_actions=(_action(),),
        intervention_profile=FunctionalInterventionProfile(mode="inhibition"),
        case_id="case", virtual_cell_template=_template(), session_id="s1",
    )
    assert [action.identifier for action in turn.selected_actions] == [ACTION]

    controller.import_measurement("case", _result())

    scored = _events(tmp_path, "prediction_reliability_scored")
    assert len(scored) == 1, scored
    assert scored[0]["weight"] == 1.0
    assert scored[0]["provisional"] is True
    # The graded pair is the one thing the ledger could never build before: an
    # interval and a real value in the same record.
    assert len([entry for entry in ledger.records if entry.interval_hit is not None]) == 1
    assert ledger.records[0].interval_hit is True


def test_reimporting_the_same_result_is_ignored_once(tmp_path: Path):
    controller, ledger = _controller(tmp_path)
    controller.run(
        "Resolve.", available_actions=(_action(),),
        intervention_profile=FunctionalInterventionProfile(mode="inhibition"),
        case_id="case", virtual_cell_template=_template(), session_id="s1",
    )
    imported = controller.import_measurement("case", _result())
    assert imported.created

    from dataclasses import replace

    controller.import_measurement("case", _result(result_id=imported.result_id))

    assert len(_events(tmp_path, "prediction_reliability_scored")) == 1
    ignored = _events(tmp_path, "prediction_reliability_duplicate_ignored")
    assert len(ignored) == 1, ignored
    assert len(ledger.records) == 1


def test_an_authorized_reveal_is_reconciled_without_a_case(tmp_path: Path):
    # A reveal carries no case, so it resolves through the action it belongs to.
    controller, ledger = _controller(tmp_path)
    controller.run(
        "Resolve.", available_actions=(_action(),),
        intervention_profile=FunctionalInterventionProfile(mode="inhibition"),
        case_id="case", virtual_cell_template=_template(), session_id="s1",
    )
    controller.record_revealed_result(_result())

    assert len(_events(tmp_path, "prediction_reliability_scored")) == 1
    assert len(ledger.records) == 1

    # A reveal that failed its own quality control is not a realisation of anything.
    fresh, fresh_ledger = _controller(tmp_path / "reveal")
    fresh.run(
        "Resolve.", available_actions=(_action(),),
        intervention_profile=FunctionalInterventionProfile(mode="inhibition"),
        case_id="case", virtual_cell_template=_template(), session_id="s1",
    )
    fresh.record_revealed_result(_result(quality_passed=False))
    assert fresh_ledger.records == ()


def test_unqualified_and_mismatched_results_are_not_scored(tmp_path: Path):
    controller, ledger = _controller(tmp_path / "qc")
    controller.run(
        "Resolve.", available_actions=(_action(),),
        intervention_profile=FunctionalInterventionProfile(mode="inhibition"),
        case_id="case", virtual_cell_template=_template(), session_id="s1",
    )
    controller.import_measurement("case", _result(quality_passed=False))
    assert _events(tmp_path / "qc", "prediction_reliability_scored") == []
    assert _events(tmp_path / "qc", "prediction_reliability_duplicate_ignored") == []
    assert ledger.records == ()

    elsewhere, other_ledger = _controller(tmp_path / "context")
    elsewhere.run(
        "Resolve.", available_actions=(_action(),),
        intervention_profile=FunctionalInterventionProfile(mode="inhibition"),
        case_id="case", virtual_cell_template=_template(), session_id="s1",
    )
    elsewhere.import_measurement("case", _result(context_identifier="another-cell"))
    assert _events(tmp_path / "context", "prediction_reliability_scored") == []
    assert other_ledger.records == ()
