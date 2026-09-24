"""Regression tests for the six production-contract gaps of the 2026-09-13 follow-up review.

File summary
- Path: tests/test_production_contract_gaps.py
- Purpose: Pin the behaviour of the real virtual-cell entry point and of the biological contract objects, so a later change that reopens a reviewed gap fails here.
- Core points:
  - Each test was written before its fix and fails against the pre-fix code; the receipt of that state is D:/MAESTRO_pruned_log_20260914/20260913/real_path/contract_gaps/reproduction_before.json (the log consolidation of 2026-09-14 moved it; see log/INDEX.md).
  - Negative cases name the rejected condition; every section keeps at least one compatible positive path, so a fix cannot pass by refusing everything.
  - These are software tests: they establish admission, routing and labelling behaviour, never biological validity.
- Interfaces: pytest test functions
- Depends on: virtual_cell (state_adapter, applicability, biology, ladder, receipts, world_model), maestro.models, evaluation.cases
"""
from __future__ import annotations

import importlib.util
import math
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]

from evaluation.cases import EvidenceMenuItem, PublicCase, ReplayView, RevealedEvidence
from maestro.models import (
    BiologicalQuantity as Q,
    EvidenceAction,
    EvidenceKind,
    PremiseGrant,
    PremiseRequirement,
)
from virtual_cell import (
    CompositeWorldModel,
    Intervention,
    IntervalKind,
    LinearPerturbationBaseline,
    PerturbationTable,
    PredictionRequest,
    QuerySupport,
    StateAdapterConfig,
    StateCapabilityAdapter,
    SystemContext,
    UnavailableVirtualCellWorldModel,
    shuffled,
)
from virtual_cell.applicability import SupportLevel, SupportRecord, SupportRegistry
from virtual_cell.biology import (
    BridgeModel,
    ChainSegment,
    Connector,
    ConnectorKind,
    MeasurementModel,
    Observable,
    UNIT_CONVERSIONS,
)
from virtual_cell.ladder import DevelopmentMeanShiftBaseline
from virtual_cell.receipts import ValidationReceipt

from tools.shared.state_fixture import (  # noqa: E402
    CONTROL,
    DEFAULT_BASIS,
    DRUG_A,
    DRUG_B,
    SHIFT,
    adapter as _adapter,
    asset_sha256 as _sha256,
    joined as _joined,
    registration as _registration,
    request as _request,
    requires_asset_runtime as requires_runtime,
    write_asset as _write_asset,
)

CONTROL = "[('DMSO_TF', 0.0, 'uM')]"
DRUG_A = "[('drugA', 0.5, 'uM')]"
DRUG_B = "[('drugB', 0.5, 'uM')]"
SHIFT = "x_hvg_perturbation_shift"
HAVE_RUNTIME = all(importlib.util.find_spec(name) for name in ("anndata", "torch", "h5py"))


# --------------------------------------------------------------------------
# A. The real State entry point validates the query before prediction.
# --------------------------------------------------------------------------

requires_runtime = pytest.mark.skipif(not HAVE_RUNTIME, reason="anndata, torch and h5py are required to build the asset")


@requires_runtime
def test_entry_point_rejects_an_endpoint_the_checkpoint_does_not_serve(tmp_path):
    assessment = _adapter(tmp_path).assess_query(_request(readouts=("fitted_viability_auc",)))
    assert assessment.support is QuerySupport.UNSUPPORTED
    assert "readout_not_served:fitted_viability_auc" in _joined(assessment)


@requires_runtime
def test_entry_point_rejects_a_context_the_dataset_does_not_register(tmp_path):
    assessment = _adapter(tmp_path).assess_query(_request(context="A549"))
    assert assessment.support is QuerySupport.UNSUPPORTED
    assert "context_not_registered_for_dataset:A549" in _joined(assessment)


@requires_runtime
def test_entry_point_rejects_an_unregistered_control_dataset(tmp_path):
    assessment = _adapter(tmp_path).assess_query(_request(control="NO_SUCH_CONTROL_DATASET"))
    assert assessment.support is QuerySupport.UNSUPPORTED
    assert "control_dataset_unregistered:NO_SUCH_CONTROL_DATASET" in _joined(assessment)


@requires_runtime
def test_entry_point_rejects_controls_from_a_different_asset(tmp_path):
    asset = _write_asset(tmp_path)
    other_directory = tmp_path / "other"
    other_directory.mkdir()
    other = _write_asset(other_directory)
    adapter = _adapter(
        tmp_path,
        datasets={"tiny": _registration("tiny", asset), "other": _registration("other", other)},
    )
    assessment = adapter.assess_query(_request(control="other"))
    assert assessment.support is QuerySupport.UNSUPPORTED
    assert "control_dataset_not_matched_to_input:other" in _joined(assessment)


@requires_runtime
def test_entry_point_rejects_an_input_schema_the_checkpoint_was_not_trained_on(tmp_path):
    assessment = _adapter(tmp_path, embedding_key="X_state").assess_query(_request())
    assert assessment.support is QuerySupport.UNSUPPORTED
    assert "input_schema_mismatch" in _joined(assessment)


@requires_runtime
def test_entry_point_rejects_an_asset_whose_bytes_no_longer_match_the_registration(tmp_path):
    """Reordering feature columns changes the bytes; a registered digest catches it."""

    asset = _write_asset(tmp_path)
    adapter = _adapter(tmp_path, datasets={"tiny": _registration("tiny", asset, sha256="0" * 64)})
    assessment = adapter.assess_query(_request())
    assert assessment.support is QuerySupport.UNSUPPORTED
    assert "dataset_asset_hash_mismatch:tiny" in _joined(assessment)


@requires_runtime
def test_entry_point_refuses_coordinate_names_verified_on_a_different_asset(tmp_path):
    """A column-reordered copy must not inherit the original file's gene names."""

    import json as json_module

    asset = _write_asset(tmp_path)
    names = tmp_path / "names.json"
    names.write_text(json_module.dumps({"dataset_sha256": "f" * 64, "feature_count": 8, "names": [f"g{i}" for i in range(8)]}), encoding="utf-8")
    registration = replace(_registration("tiny", asset), feature_names_path=names)
    assessment = _adapter(tmp_path, datasets={"tiny": registration}).assess_query(_request())
    assert assessment.support is QuerySupport.UNSUPPORTED
    assert "feature_identity_not_bound_to_asset:tiny" in _joined(assessment)


@requires_runtime
def test_entry_point_binds_the_declared_context_to_the_selected_rows(tmp_path):
    """A context registered for the asset but absent from the perturbation's rows is refused."""

    import json as json_module

    asset = _write_asset(tmp_path)
    # The basis has to agree for this test to reach the property it is about. Without a
    # bound identity file the adapter now refuses earlier, with `input_basis_unverified`,
    # which is correct behaviour and the wrong question.
    identity = tmp_path / "bound_identity.json"
    identity.write_text(
        json_module.dumps(
            {"dataset_sha256": _sha256(asset), "feature_count": 8, "names": list(DEFAULT_BASIS)}
        ),
        encoding="utf-8",
    )
    adapter = _adapter(
        tmp_path,
        datasets={
            "tiny": replace(
                _registration("tiny", asset, contexts=("NCI-H596", "A549")),
                feature_names_path=identity,
            )
        },
    )
    assessment = adapter.assess_query(_request(context="A549"))
    assert assessment.support is QuerySupport.UNSUPPORTED
    assert "no rows for the declared context" in _joined(assessment)


@requires_runtime
def test_a_compatible_query_stays_executable_and_its_validation_stays_unknown(tmp_path):
    assessment = _adapter(tmp_path).assess_query(_request())
    assert assessment.support is QuerySupport.SUPPORTED, _joined(assessment)
    assert assessment.validation_status is SupportLevel.UNKNOWN


@requires_runtime
def test_a_registered_receipt_without_a_verified_holdout_is_not_reported_as_validated(tmp_path):
    receipt = ValidationReceipt(
        receipt_id="retrospective-c39",
        endpoint=SHIFT,
        context_identifier="NCI-H596",
        model_version="state-test",
        split="drug-held-out cross-fitting",
        acceptance_criterion="paired squared error below the development-mean baseline",
        metric="paired_mse_difference",
        value=-0.0001,
        passed=True,
        holdout_verified=False,
    )
    assessment = _adapter(tmp_path, validation_receipts=(receipt,)).assess_query(_request())
    assert assessment.support is QuerySupport.SUPPORTED, _joined(assessment)
    assert assessment.validation_status is SupportLevel.RETROSPECTIVE_UNVERIFIED_HOLDOUT


# --------------------------------------------------------------------------
# B. The production adapter satisfies the rung protocol composite routing reads.
# --------------------------------------------------------------------------


def _baseline(context: str = "NCI-H596", dataset: str = "tiny") -> DevelopmentMeanShiftBaseline:
    return DevelopmentMeanShiftBaseline.fit(
        {DRUG_B: np.full(8, 0.2), "[('drugC', 0.5, 'uM')]": np.full(8, 0.4)},
        development_conditions=(DRUG_B, "[('drugC', 0.5, 'uM')]"),
        feature_names=tuple(f"gene{i}" for i in range(8)),
        context_identifier=context,
        dataset_id=dataset,
        fitted_on="synthetic development conditions",
    )


def test_the_state_adapter_exposes_a_rung_name(tmp_path):
    checkpoint = tmp_path / "final.ckpt"
    config = tmp_path / "config.yaml"
    checkpoint.write_bytes(b"x")
    config.write_text("x", encoding="utf-8")
    adapter = StateCapabilityAdapter(StateAdapterConfig(checkpoint, config, "state-test"))
    assert isinstance(adapter.name, str) and "state-test" in adapter.name


@requires_runtime
def test_composite_routing_runs_with_the_production_adapter_and_a_computed_baseline(tmp_path):
    adapter = _adapter(tmp_path)
    baseline = _baseline()
    composite = CompositeWorldModel([adapter, baseline])
    report = composite.routing_report(_request(readouts=("development_mean_only",)))
    assert report["registered_backends"] == [adapter.name, baseline.name]
    assert adapter.name in report["ineligible"]


def test_a_composite_refuses_a_rung_without_a_name_at_construction():
    class Nameless:
        def capabilities(self):
            raise AssertionError("never reached")

    with pytest.raises(ValueError, match="name"):
        CompositeWorldModel([Nameless()])


def test_wrapped_and_unavailable_models_have_names():
    table = PerturbationTable(("A549",) * 4, ("p",) * 4, ("drug",) * 4, (0.0, 1.0, 10.0, 100.0), (24.0,) * 4,
                              ("viability",), {"viability": (1.0, 0.9, 0.7, 0.5)})
    assert shuffled(LinearPerturbationBaseline(table)).name.endswith(":shuffled")
    assert UnavailableVirtualCellWorldModel().name == "unavailable"


def test_the_computed_baseline_refuses_a_condition_it_was_fitted_on():
    assessment = _baseline().assess_query(_request(label=DRUG_B, version=_baseline().name))
    assert assessment.support is QuerySupport.UNSUPPORTED
    assert "query_condition_in_fitting_partition" in _joined(assessment)


def test_the_computed_baseline_serves_a_held_out_condition_with_its_fitted_vector():
    baseline = _baseline()
    prediction = baseline.predict(_request(label=DRUG_A, version=baseline.name))
    assert prediction.applicable and prediction.contract_valid
    assert math.isclose(prediction.state_change["embedding_delta_l2"], float(np.linalg.norm(np.full(8, 0.3))), rel_tol=1e-9)


# --------------------------------------------------------------------------
# C. Quantity compatibility, interchangeability and direct-measurement admission.
# --------------------------------------------------------------------------


def _flow() -> Observable:
    return Observable(
        "EGFR_pY1068_flow", Q.PROTEIN_ABUNDANCE, "EGFR", "ratio_to_isotype", "phospho_flow_cytometry",
        MeasurementModel("median_fluorescence_ratio_to_isotype", "lognormal"),
        site="Y1068", context_identifier="ACH-000628", time_hours=1.0,
    )


def test_a_different_assay_is_the_same_quantity_but_not_interchangeable():
    flow = _flow()
    western = replace(flow, name="EGFR_pY1068_western", assay="western_blot",
                      measurement_model=MeasurementModel("densitometry_ratio_to_total", "lognormal"))
    assert flow.same_quantity_as(western)
    assert not flow.interchangeable_with(western)
    assert {"assay_mismatch", "measurement_model_mismatch"} <= set(flow.mismatches(western))


def test_a_prediction_is_not_interchangeable_with_a_measurement():
    flow = _flow()
    predicted = replace(flow, name="EGFR_pY1068_predicted", measured=False)
    assert not flow.interchangeable_with(predicted)
    assert "measurement_status_mismatch" in flow.mismatches(predicted)
    assert "estimate_offered_for_direct_measurement" in predicted.direct_measurement_gaps(flow)


def test_missing_context_and_time_are_named_unresolved_conditions():
    flow = _flow()
    unplaced = replace(flow, name="EGFR_pY1068_unplaced", context_identifier=None, time_hours=None)
    assert not flow.interchangeable_with(unplaced)
    assert {"context_unresolved", "time_unresolved"} <= set(flow.unresolved_conditions(unplaced))


def test_a_fully_qualified_observable_remains_interchangeable_with_itself():
    flow = _flow()
    assert flow.interchangeable_with(replace(flow))
    assert flow.direct_measurement_gaps(flow) == ()


def test_a_premise_requiring_units_and_context_names_them_when_the_grant_lacks_them():
    requirement = PremiseRequirement("abundance:target_rna", Q.RNA_ABUNDANCE, entity="MET",
                                     units="log2_tpm_plus_1", context_identifier="ACH-000628")
    bare = PremiseGrant("abundance:target_rna", "rna_assay", Q.RNA_ABUNDANCE, entity="MET", quality="passed", quality_passed=True)
    reasons = requirement.unmet_reasons(bare)
    assert "units_undeclared" in reasons
    assert "context_undeclared" in reasons
    complete = replace(bare, units="log2_tpm_plus_1", context_identifier="ACH-000628")
    assert requirement.unmet_reasons(complete) == ()


# --------------------------------------------------------------------------
# D. Representability, observed support, evaluated performance, calibration.
# --------------------------------------------------------------------------


_ROWS = [{"context_id": "A549", "perturbation": "drug_p", "mode": "drug", "dose": 10.0, "time_hours": 24.0, "readout": "viability"}]


def _assess(registry: SupportRegistry):
    return registry.assess(context_id="A549", perturbation="drug_p", mode="drug", dose=10.0, time_hours=24.0, readouts=("viability",))


def test_training_rows_give_observed_support_not_validation():
    verdict = _assess(SupportRegistry.from_table(_ROWS, source="training rows only; no held-out evaluation"))
    assert verdict.in_distribution
    assert verdict.level is SupportLevel.OBSERVED_SUPPORT
    assert not verdict.validated


def _receipt(**overrides) -> ValidationReceipt:
    values = dict(
        receipt_id="eval-001", endpoint="viability", context_identifier="A549", model_version=None,
        split="held-out compounds", acceptance_criterion="MAE at most 0.1 on held-out compounds",
        metric="mae", value=0.07, passed=True, holdout_verified=True,
    )
    values.update(overrides)
    return ValidationReceipt(**values)


def _record(receipt: ValidationReceipt | None) -> SupportRegistry:
    return SupportRegistry([SupportRecord(
        context_id="A549", perturbations=frozenset({"drug_p"}), modes=frozenset({"drug"}),
        readouts=frozenset({"viability"}), dose_range=(1.0, 100.0), time_range=(24.0, 24.0),
        evaluations=(receipt,) if receipt is not None else (),
    )])


def test_an_identifiable_accepted_receipt_on_a_verified_holdout_validates():
    verdict = _assess(_record(_receipt()))
    assert verdict.level is SupportLevel.VALIDATED and verdict.validated


@pytest.mark.parametrize(
    "overrides, level, problem",
    [
        ({"acceptance_criterion": ""}, SupportLevel.OBSERVED_SUPPORT, "acceptance_criterion_missing"),
        ({"receipt_id": ""}, SupportLevel.OBSERVED_SUPPORT, "receipt_id_missing"),
        ({"split": ""}, SupportLevel.OBSERVED_SUPPORT, "split_missing"),
        ({"endpoint": "rna"}, SupportLevel.OBSERVED_SUPPORT, "receipt_endpoint_mismatch"),
        ({"passed": False}, SupportLevel.EVALUATED_BELOW_ACCEPTANCE, None),
        ({"passed": None}, SupportLevel.OBSERVED_SUPPORT, "acceptance_not_evaluated"),
        ({"holdout_verified": False}, SupportLevel.RETROSPECTIVE_UNVERIFIED_HOLDOUT, None),
    ],
)
def test_a_receipt_validates_only_when_it_is_identifiable_accepted_and_held_out(overrides, level, problem):
    verdict = _assess(_record(_receipt(**overrides)))
    assert verdict.level is level
    assert not verdict.validated
    if problem is not None:
        assert problem in verdict.receipt_problems


def test_a_ladder_rung_does_not_claim_coverage_from_its_training_residuals():
    table = PerturbationTable(("A549",) * 4, ("drug_p",) * 4, ("drug",) * 4, (0.0, 1.0, 10.0, 100.0), (24.0,) * 4,
                              ("viability",), {"viability": (1.0, 0.95, 0.8, 0.6)})
    model = LinearPerturbationBaseline(table)
    prediction = model.predict(PredictionRequest(
        "ladder", "case", "contrast", 1, Intervention("drug_p", "drug", (), dose=10.0, time_hours=24.0),
        SystemContext("A549", "test", dataset_id="d", control_dataset_id="d"), ("viability",), model.model_version,
    ))
    interval = prediction.intervals["viability"]
    assert interval.kind is IntervalKind.DESCRIPTIVE
    assert not interval.claims_coverage


# --------------------------------------------------------------------------
# E. Identity, deterministic conversion and learned bridge are different operations.
# --------------------------------------------------------------------------


def _tpm() -> Observable:
    return Observable("MET_rna_tpm", Q.RNA_ABUNDANCE, "MET", "TPM", "bulk_rnaseq",
                      MeasurementModel("transcripts_per_million", "lognormal"),
                      context_identifier="ACH-000628", time_applicable=False)


def test_an_exact_unit_conversion_qualifies_and_executes():
    source = _tpm()
    target = replace(source, name="MET_rna_log2tpm1", units="log2_tpm_plus_1",
                     measurement_model=MeasurementModel("log2(TPM+1)", "normal"))
    connector = Connector("tpm_to_log2", source, target, ChainSegment.RESPONSE_TO_OBSERVATION,
                          kind=ConnectorKind.DETERMINISTIC_CONVERSION, conversion=UNIT_CONVERSIONS[("TPM", "log2_tpm_plus_1")])
    assert connector.qualification_errors() == ()
    assert math.isclose(connector.apply(3.0), 2.0)
    assert not connector.output_is_estimate


def test_a_conversion_cannot_change_what_is_measured():
    source = _tpm()
    target = replace(source, name="EGFR_rna_log2tpm1", entity="EGFR", units="log2_tpm_plus_1")
    connector = Connector("wrong_entity", source, target, ChainSegment.RESPONSE_TO_OBSERVATION,
                          kind=ConnectorKind.DETERMINISTIC_CONVERSION, conversion=UNIT_CONVERSIONS[("TPM", "log2_tpm_plus_1")])
    assert "entity_mismatch" in connector.qualification_errors()


def test_a_conversion_whose_units_do_not_match_its_ports_is_refused():
    source = _tpm()
    target = replace(source, name="MET_rna_percent", units="percent")
    connector = Connector("mismatched", source, target, ChainSegment.RESPONSE_TO_OBSERVATION,
                          kind=ConnectorKind.DETERMINISTIC_CONVERSION, conversion=UNIT_CONVERSIONS[("TPM", "log2_tpm_plus_1")])
    assert "conversion_units_mismatch" in connector.qualification_errors()


def _shift() -> Observable:
    return Observable(SHIFT, Q.RNA_ABUNDANCE, "transcriptome_hvg_2000", "log1p_normalized_counts", "scrnaseq_pseudobulk",
                      MeasurementModel("mean_treated_minus_mean_vehicle", "normal"), context_identifier="NCI-H596",
                      time_hours=24.0, measured=False)


def _auc(measured: bool = False) -> Observable:
    return Observable("prism_auc", Q.VIABILITY, "cell_population", "fitted_auc", "prism_secondary",
                      MeasurementModel("area_under_dose_response", "normal"), context_identifier="NCI-H596",
                      time_hours=120.0, measured=measured)


def test_an_unvalidated_transcript_to_viability_bridge_is_refused():
    bridge = BridgeModel("ridge_shift_to_auc", artifact_sha256="a" * 64, function=lambda value: 1.0 - 0.1 * value)
    connector = Connector("shift_to_auc", _shift(), _auc(), ChainSegment.RESPONSE_TO_OBSERVATION,
                          kind=ConnectorKind.LEARNED_BRIDGE, bridge=bridge, validation_basis="a correlation was reported")
    errors = connector.qualification_errors()
    assert "no_validation_receipt" in errors
    assert not connector.qualified
    with pytest.raises(ValueError):
        connector.apply(1.0)


def test_a_bridge_cannot_declare_its_output_a_measurement():
    bridge = BridgeModel("ridge_shift_to_auc", artifact_sha256="a" * 64, function=lambda value: 1.0 - 0.1 * value)
    receipt = ValidationReceipt(receipt_id="bridge-eval", endpoint="prism_auc", context_identifier="NCI-H596", model_version=None,
                                split="held-out compounds", acceptance_criterion="MAE at most 0.05", metric="mae", value=0.04,
                                passed=True, holdout_verified=True)
    connector = Connector("shift_to_auc", _shift(), _auc(measured=True), ChainSegment.RESPONSE_TO_OBSERVATION,
                          kind=ConnectorKind.LEARNED_BRIDGE, bridge=bridge, validation=receipt)
    assert "bridge_output_declared_as_measurement" in connector.qualification_errors()


def test_a_validated_bridge_yields_an_estimate_that_cannot_discharge_a_direct_measurement():
    bridge = BridgeModel("ridge_shift_to_auc", artifact_sha256="a" * 64, function=lambda value: 1.0 - 0.1 * value)
    receipt = ValidationReceipt(receipt_id="bridge-eval", endpoint="prism_auc", context_identifier="NCI-H596", model_version=None,
                                split="held-out compounds", acceptance_criterion="MAE at most 0.05", metric="mae", value=0.04,
                                passed=True, holdout_verified=True)
    connector = Connector("shift_to_auc", _shift(), _auc(), ChainSegment.RESPONSE_TO_OBSERVATION,
                          kind=ConnectorKind.LEARNED_BRIDGE, bridge=bridge, validation=receipt)
    assert connector.qualification_errors() == ()
    assert connector.output_is_estimate
    assert math.isclose(connector.apply(2.0), 0.8)
    assert "estimate_offered_for_direct_measurement" in connector.target.direct_measurement_gaps(_auc(measured=True))


def test_an_identity_connector_between_different_assays_is_refused():
    flow = _flow()
    western = replace(flow, name="EGFR_pY1068_western", assay="western_blot")
    connector = Connector("flow_is_western", flow, western, ChainSegment.RESPONSE_TO_OBSERVATION,
                          kind=ConnectorKind.IDENTITY, validation_basis="free text")
    assert "assay_mismatch" in connector.qualification_errors()


# --------------------------------------------------------------------------
# F. Readiness is tied to declared, typed requirements, not to menu state.
# --------------------------------------------------------------------------


def _typed_view(*, supplier_quantity: Q, remaining: float = 1.0, observed: bool = True) -> ReplayView:
    supplier = EvidenceMenuItem(EvidenceAction(
        "supplier", "supplier", 1.0, ("hA", "hB"), quantity=supplier_quantity, entity="EGFR",
        supplies=("target_engagement_confirmed",), expected_outcomes={"hA": "engaged", "hB": "not_engaged"},
    ))
    dependant = EvidenceMenuItem(EvidenceAction(
        "followup", "follow-up", 1.0, ("hA", "hB"), prerequisites=("target_engagement_confirmed",),
    ))
    case = PublicCase(
        identifier="f", provenance="synthetic", evaluation_status="fixture", initial_evidence=(),
        hypotheses=({"identifier": "hA"}, {"identifier": "hB"}), actions=(supplier, dependant), budget=2.0,
        context_identifier="ctx",
        premise_registry={"target_engagement_confirmed": PremiseRequirement(
            "target_engagement_confirmed", Q.TARGET_OCCUPANCY, entity="EGFR", context_identifier="ctx")},
    )
    record = RevealedEvidence(
        action_identifier="supplier", outcome="engaged", statement="record", source_id="fixture", context_identifier="ctx",
        time_hours=24.0, conditions={}, metrics={}, record_count=3, biological_replicates=3, record_validated=True,
        biological_quality="passed", interpretation_fields=("target_engagement_confirmed",), limitations=(),
        evidence_kind=EvidenceKind.REAL_MEASUREMENT,
    )
    return ReplayView(case=case, remaining_budget=remaining, revealed=(record,) if observed else (),
                      queried_actions=("supplier",) if observed else ())


def test_no_declared_requirement_is_not_readiness():
    state = _typed_view(supplier_quantity=Q.TARGET_OCCUPANCY, observed=False).decision_state()
    assert state["decision_ready"] is False
    assert state["readiness"] == "unresolved"
    assert "no_decision_requirements_declared" in state["readiness_reasons"]


def test_an_exhausted_menu_is_not_a_conclusion():
    state = _typed_view(supplier_quantity=Q.TARGET_OCCUPANCY, remaining=0.0, observed=False).decision_state(
        required_premises=("target_engagement_confirmed",)
    )
    assert state["decision_ready"] is False
    assert state["additional_evidence_available"] is False
    assert state["readiness"] == "unresolved"


def test_a_record_named_for_a_premise_but_measuring_another_quantity_does_not_make_a_decision_ready():
    state = _typed_view(supplier_quantity=Q.VIABILITY).decision_state(required_premises=("target_engagement_confirmed",))
    assert state["decision_ready"] is False
    assert any("quantity_mismatch" in item for item in state["required_missing_premises"])


def test_a_correctly_typed_record_makes_the_declared_requirement_ready_while_evidence_remains():
    state = _typed_view(supplier_quantity=Q.TARGET_OCCUPANCY).decision_state(required_premises=("target_engagement_confirmed",))
    assert state["decision_ready"] is True
    assert state["readiness"] == "ready"
    assert state["additional_evidence_available"] is True
    assert state["evidence_status"] == "decided"
