"""Panel invocation: abstentions, artifact integrity, gene-set refusal, ranking, receipts.

File summary
- Path: tests/test_virtual_cell_panel.py
- Purpose: pin the boundaries of the panel surface that invokes a weight-backed backend
  for analysis: an abstention is a row, an artifact is graded only against its own digest,
  an endpoint the coordinates cannot express is refused before scoring, a ranking never
  silently drops a condition, and a receipt is graded only against a declared criterion.
- Core points: assertions here are contract tests, not biological results.
- Interfaces: `test_panel_records_abstentions_and_bills_compute_separately()`,
  `test_artifact_reader_refuses_a_vector_that_does_not_match_its_digest()`,
  `test_gene_set_analysis_refuses_an_endpoint_the_coordinates_cannot_express()`,
  `test_gene_set_analysis_refuses_by_name_without_a_declared_pool()`,
  `test_ranking_keeps_unanswered_conditions_visible()`,
  `test_receipt_is_unscored_below_the_declared_minimum()`,
  `test_panel_spec_executes_and_requires_a_criterion_for_observations()`
- Depends on: virtual_cell
"""
import json
from pathlib import Path

import pytest

from virtual_cell import (
    BackgroundPool,
    ConditionPanel,
    GeneSet,
    Interval,
    IntervalKind,
    KnowledgeAnnotation,
    ModelCapabilities,
    PanelCondition,
    PanelCriterion,
    PanelRow,
    PanelRun,
    QueryAssessment,
    QuerySupport,
    SimulationCostLedger,
    StatePrediction,
    SupportLevel,
    SystemContext,
    execute_spec,
    load_panel_spec,
    rank_conditions,
    read_artifact_values,
    run_panel,
    score_panel_against_observations,
    score_panel_gene_sets,
)
from virtual_cell.artifacts import write_shift_artifact

READOUT = "embedding_delta_l2"


class _StubBackend:
    """A backend that answers the conditions it declares and refuses the rest."""

    name = "stub_backend"

    def __init__(self, supported: set[str]) -> None:
        self._supported = supported

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            model_identifier="stub",
            model_version="stub_v1",
            input_representation="none",
            perturbation_representation="registered condition label",
            supported_modes=("drug",),
            requires_matched_control=True,
            supports_dose=False,
            supports_time=False,
            calibration_basis=None,
        )

    def assess_query(self, request) -> QueryAssessment:
        if request.intervention.identifier in self._supported:
            return QueryAssessment(
                QuerySupport.SUPPORTED, (), (), self.capabilities(), SupportLevel.OBSERVED_SUPPORT
            )
        return QueryAssessment(
            QuerySupport.UNSUPPORTED, (), ("perturbation_unregistered",), self.capabilities()
        )

    def predict(self, request) -> StatePrediction:
        if request.intervention.identifier not in self._supported:
            raise AssertionError("predict must not run for a condition the backend refused")
        return StatePrediction(
            applicable=True,
            state_change={READOUT: 0.2},
            uncertainty=None,
            limitations=("planning-only stub prediction",),
            request_id=request.request_id,
            model_version="stub_v1",
            confidence=None,
            in_distribution=True,
            uncertainty_components={"measurement_noise": "unquantified in this stub"},
        )


def _panel(conditions: tuple[str, ...]) -> ConditionPanel:
    return ConditionPanel(
        panel_id="panel-1",
        context=SystemContext(
            identifier="NCI-H596",
            description="registered context",
            dataset_id="tahoe_c39",
            control_dataset_id="tahoe_c39",
        ),
        model_version="stub_v1",
        conditions=tuple(PanelCondition(identifier=name) for name in conditions),
        readouts=(READOUT,),
    )


def _artifact(tmp_path: Path, values: tuple[float, ...] = (1.0, 2.0, 3.0)) -> tuple[Path, str]:
    path = tmp_path / "condition.shift.json"
    digest = write_shift_artifact(
        path,
        request_id="panel-1.0",
        backend="stub_backend",
        model_version="stub_v1",
        endpoint="x_hvg_perturbation_shift",
        context_identifier="NCI-H596",
        perturbation="condition_a",
        control_label="vehicle",
        raw_vector=values,
        calibrated_vector=None,
        feature_names=("A", "B", "C"),
        feature_identity_sha256=None,
        provenance={"fitted_on": "test fixture"},
        limitations=("planning-only artifact",),
    )
    return path, digest


def _run_with_artifact(panel: ConditionPanel, path: Path, digest: str) -> PanelRun:
    row = PanelRow(
        condition="condition_a",
        request_id="panel-1.0",
        support="supported",
        applicable=True,
        in_distribution=True,
        validation_status="observed_support",
        values={READOUT: 1.0},
        artifact_ref=str(path),
        artifact_sha256=digest,
        artifact_digest_verified=True,
        compute_cost=0.1,
    )
    return PanelRun(panel=panel, rows=(row,), ledger=SimulationCostLedger())


def test_panel_records_abstentions_and_bills_compute_separately():
    backend = _StubBackend({"condition_a"})
    run = run_panel(backend, _panel(("condition_a", "condition_b")))

    summary = run.summary()
    assert summary["conditions"] == 2
    assert summary["applicable"] == 1
    assert summary["abstained"] == 1
    assert summary["abstain_reasons"] == {"perturbation_unregistered": 1}
    assert summary["planning_only"] is True
    assert summary["is_measurement"] is False
    assert run.ledger.summary()["calls"] == {"stub_backend": 2}
    assert run.ledger.summary()["abstentions"] == {"stub_backend": 1}
    refused = run.rows_by_condition()["condition_b"]
    assert refused.applicable is False
    assert refused.evidence_kind == "model_prediction"
    assert refused.planning_only is True
    assert refused.artifact_ref is None


def test_artifact_reader_refuses_a_vector_that_does_not_match_its_digest(tmp_path: Path):
    path, _ = _artifact(tmp_path)
    values, meta = read_artifact_values(path)
    assert values == {"A": 1.0, "B": 2.0, "C": 3.0}
    assert meta["source"] == "raw"
    assert meta["resolved"] == 3

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["raw"]["values"][0] = 9.0
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="does not match its recorded vector digest"):
        read_artifact_values(path)


def test_gene_set_analysis_refuses_an_endpoint_the_coordinates_cannot_express(tmp_path: Path):
    panel = _panel(("condition_a",))
    path, digest = _artifact(tmp_path)
    run = _run_with_artifact(panel, path, digest)
    complete = GeneSet(
        identifier="complete", members=("A", "B"), source="test", source_sha256="0", rule="mean over members"
    )
    absent = GeneSet(
        identifier="absent", members=("A", "Z"), source="test", source_sha256="0", rule="mean over members"
    )
    # The declared sampling frame: the panel call site standardises against a pool it was
    # given, never against whatever coordinates the artifact happened to carry.
    pool = BackgroundPool(
        identifier="fixture_coordinates",
        members=("A", "B", "C"),
        source="test fixture artifacts",
        source_sha256="0" * 64,
        rule="the three coordinates of the fixture artifact",
    )
    scores = {
        item.gene_set_id: item
        for item in score_panel_gene_sets(run, (complete, absent), draws=50, background=pool)
    }

    assert scores["complete"].scored is True
    assert scores["complete"].raw == pytest.approx(1.5)
    assert scores["complete"].z is not None
    assert scores["complete"].background_pool_id == pool.identifier
    assert scores["complete"].background_pool_digest == pool.digest
    assert scores["absent"].scored is False
    assert scores["absent"].raw is None
    assert scores["absent"].refused_reason == "endpoint_not_representable_in_output_space:absent"


def test_gene_set_analysis_refuses_by_name_without_a_declared_pool(tmp_path: Path):
    """An expressible endpoint with no declared sampling frame is a named refusal."""

    panel = _panel(("condition_a",))
    path, digest = _artifact(tmp_path)
    run = _run_with_artifact(panel, path, digest)
    complete = GeneSet(
        identifier="complete", members=("A", "B"), source="test", source_sha256="0", rule="mean over members"
    )
    scores = {item.gene_set_id: item for item in score_panel_gene_sets(run, (complete,), draws=50)}
    assert scores["complete"].scored is False
    assert scores["complete"].raw is None
    assert scores["complete"].z is None
    assert scores["complete"].refused_reason == "background_pool_not_declared"


def test_ranking_keeps_unanswered_conditions_visible():
    panel = _panel(("condition_a", "condition_b", "condition_c"))
    rows = (
        PanelRow(
            condition="condition_b",
            request_id="panel-1.1",
            support="supported",
            applicable=True,
            in_distribution=True,
            validation_status="observed_support",
            values={READOUT: 0.2},
        ),
        PanelRow(
            condition="condition_a",
            request_id="panel-1.0",
            support="supported",
            applicable=True,
            in_distribution=True,
            validation_status="observed_support",
            values={READOUT: 0.2},
        ),
        PanelRow(
            condition="condition_c",
            request_id="panel-1.2",
            support="unsupported",
            applicable=False,
            in_distribution=False,
            validation_status="unknown",
            abstain_reason="perturbation_unregistered",
        ),
    )
    run = PanelRun(panel=panel, rows=rows, ledger=SimulationCostLedger())
    ranking = rank_conditions(run, READOUT, weight_of=lambda condition: 0.0 if condition == "condition_b" else 1.0)

    assert [entry.condition for entry in ranking.entries] == ["condition_a"]
    assert ranking.entries[0].rank == 1
    reasons = {item.condition: item.reason for item in ranking.not_ranked}
    assert reasons["condition_b"] == "weighted_out_by_reliability"
    assert reasons["condition_c"] == "perturbation_unregistered"


def test_receipt_is_unscored_below_the_declared_minimum():
    panel = _panel(("condition_a",))
    rows = tuple(
        PanelRow(
            condition=condition,
            request_id=f"panel-1.{index}",
            support="supported",
            applicable=True,
            in_distribution=True,
            validation_status="observed_support",
            values={READOUT: 0.2},
            intervals={
                READOUT: Interval(
                    low=0.18, high=0.22, kind=IntervalKind.CALIBRATED, level=0.9, basis="declared residual"
                )
            },
        )
        for index, condition in enumerate(("condition_a", "condition_b", "condition_c"))
    )
    run = PanelRun(panel=panel, rows=rows, ledger=SimulationCostLedger())
    observations = {"condition_a": 0.21}
    strict = PanelCriterion(
        endpoint=READOUT,
        metric="mean_absolute_error",
        direction="below",
        threshold=0.05,
        minimum_pairs=3,
        split="declared_panel",
        acceptance_criterion="mean absolute error below 0.05 on three declared pairs",
    )
    unscored = score_panel_against_observations(run, observations, strict)
    assert unscored.passed is None
    assert unscored.value is None
    assert unscored.independent_units == 1
    assert unscored.holdout_verified is False
    assert "acceptance_not_evaluated" in unscored.problems()

    relaxed = PanelCriterion(
        endpoint=READOUT,
        metric="mean_absolute_error",
        direction="below",
        threshold=0.05,
        minimum_pairs=1,
        split="declared_panel",
        acceptance_criterion="mean absolute error below 0.05 on one declared pair",
    )
    graded = score_panel_against_observations(run, observations, relaxed)
    assert graded.passed is True
    assert graded.value == pytest.approx(0.01, abs=1e-9)
    assert graded.identifiable is True
    assert graded.validates(endpoint=READOUT, context_identifier="NCI-H596") is False

    failing = PanelCriterion(
        endpoint=READOUT,
        metric="mean_absolute_error",
        direction="below",
        threshold=0.001,
        minimum_pairs=1,
        split="declared_panel",
        acceptance_criterion="mean absolute error below 0.001 on one declared pair",
    )
    assert score_panel_against_observations(run, observations, failing).passed is False


def test_panel_spec_executes_and_requires_a_criterion_for_observations(tmp_path: Path):
    spec = {
        "panel_id": "panel-1",
        "context": {"identifier": "NCI-H596", "dataset_id": "tahoe_c39", "control_dataset_id": "tahoe_c39"},
        "model_version": "stub_v1",
        "readouts": [READOUT],
        "conditions": [{"identifier": "condition_a"}],
        "observations": {"condition_a": 0.21},
        "criterion": {
            "endpoint": READOUT,
            "metric": "mean_absolute_error",
            "direction": "below",
            "threshold": 0.05,
            "minimum_pairs": 1,
            "split": "declared_panel",
            "acceptance_criterion": "mean absolute error below 0.05 on one declared pair",
        },
    }
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec), encoding="utf-8")

    payload = execute_spec(_StubBackend({"condition_a"}), path)
    assert payload["schema"] == "maestro.virtual_cell.panel.v1"
    assert payload["is_measurement"] is False
    assert payload["summary"]["applicable"] == 1
    assert payload["rows"][0]["evidence_kind"] == "model_prediction"
    assert payload["receipt"]["split"] == "declared_panel"
    assert payload["receipt"]["passed"] is True
    assert payload["ranking"]["entries"][0]["condition"] == "condition_a"

    del spec["criterion"]
    path.write_text(json.dumps(spec), encoding="utf-8")
    with pytest.raises(ValueError, match="without the criterion"):
        load_panel_spec(path)


def test_knowledge_annotations_must_be_sourced_and_are_never_premises(tmp_path: Path):
    with pytest.raises(ValueError, match="annotation_source_digest_missing"):
        ConditionPanel(
            panel_id="panel-1",
            context=SystemContext(identifier="NCI-H596", description="registered context"),
            model_version="stub_v1",
            conditions=(PanelCondition(identifier="condition_a"),),
            readouts=(READOUT,),
            annotations=(KnowledgeAnnotation("EGFR inhibition blocks MAPK output", "reactome", ""),),
        )

    spec = {
        "panel_id": "panel-1",
        "context": {"identifier": "NCI-H596", "dataset_id": "tahoe_c39", "control_dataset_id": "tahoe_c39"},
        "model_version": "stub_v1",
        "readouts": [READOUT],
        "conditions": [{"identifier": "condition_a"}],
        "annotations": [
            {
                "statement": "EGFR inhibition blocks MAPK output",
                "source_id": "reactome:R-HSA-5675221",
                "source_digest": "9c2a5097591e01ee8f5b10ffc39a4b5028dab9b55164f440b3a1584e8c0516eb",
                "relation": "supports",
                "quantity": "rna_abundance",
            }
        ],
    }
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec), encoding="utf-8")

    payload = execute_spec(_StubBackend({"condition_a"}), path)
    annotation = payload["knowledge_annotations"][0]
    assert annotation["evidence_kind"] == "retrieved_source"
    assert annotation["can_satisfy_a_premise"] is False
    assert annotation["source_digest"].startswith("9c2a5097")
