"""Regression tests for the four foundational defects and the general contract.

File summary
- Path: tests/test_general_biological_contract.py
- Purpose: Pin the behaviour the biological contract requires, so a later change that reintroduces a defect fails here.
- Core points:
  - Each defect test was written before its fix and reproduces the counterexample, not the fix.
  - Contract tests are software tests: they establish admission and search behaviour, never biological validity.
  - Valid legacy behaviour is asserted alongside each new restriction, so a fix cannot pass by forbidding everything.
- Interfaces: pytest test functions
- Depends on: evaluation.feasibility, evaluation.planning, evaluation.cases, virtual_cell.applicability, virtual_cell.world_model, virtual_cell.biology
"""
from __future__ import annotations

import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

from evaluation.cases import EvidenceMenuItem, PublicCase, RevealedEvidence
from evaluation.feasibility import (
    effective_fields,
    enumerate_public_plans,
    granted_premises,
    legal_actions,
    plan_enumeration,
)
from evaluation.planning import (
    CompatibilityStatus,
    PlanConstraints,
    decision_ambiguity,
    hypothesis_compatibility,
    solve_exact,
)
from maestro.models import (
    BiologicalQuantity,
    EvidenceAction,
    EvidenceKind,
    PremiseRequirement,
)
from virtual_cell.applicability import SupportLevel, SupportRecord, SupportRegistry
from virtual_cell.biology import (
    ChainSegment,
    Connector,
    MeasurementModel,
    Observable,
)
from virtual_cell.interface import (
    Intervention,
    ModelCapabilities,
    PredictionRequest,
    QueryAssessment,
    QuerySupport,
    StatePrediction,
    SystemContext,
)
from virtual_cell.world_model import CompositeWorldModel


def _item(name: str, **kwargs) -> EvidenceMenuItem:
    return EvidenceMenuItem(EvidenceAction(name, f"action {name}", 1.0, ("hA", "hB"), **kwargs))


def _case(actions, budget: float, **kwargs) -> PublicCase:
    return PublicCase(
        identifier="fixture",
        provenance="synthetic contract fixture",
        evaluation_status="fixture",
        initial_evidence=(),
        hypotheses=({"identifier": "hA"}, {"identifier": "hB"}),
        actions=tuple(actions),
        budget=budget,
        context_identifier="ctx",
        **kwargs,
    )


def _record(name: str, outcome: str, fields: tuple[str, ...], **kwargs) -> RevealedEvidence:
    payload = {
        "context_identifier": "ctx",
        "time_hours": 24.0,
        "record_validated": True,
        "biological_quality": "passed",
        "evidence_kind": EvidenceKind.REAL_MEASUREMENT,
    }
    payload.update(kwargs)
    return RevealedEvidence(
        action_identifier=name,
        outcome=outcome,
        statement=f"record for {name}",
        source_id="fixture",
        conditions={},
        metrics={},
        record_count=3,
        biological_replicates=3,
        interpretation_fields=fields,
        limitations=(),
        **payload,
    )


# --------------------------------------------------------------------------
# Defect C: a truncated search must not certify an optimum.
# --------------------------------------------------------------------------


def test_truncated_enumeration_is_reported_as_incomplete():
    public = _case([_item(f"x{i}", expected_outcomes={}) for i in range(7)], 7.0)
    exhaustive = sum(math.perm(7, k) for k in range(8))
    result = plan_enumeration(public)
    assert len(result.plans) < exhaustive
    assert not result.complete
    assert result.limit == len(result.plans)


def test_complete_enumeration_is_reported_as_complete():
    public = _case([_item(f"x{i}", expected_outcomes={}) for i in range(3)], 3.0)
    result = plan_enumeration(public)
    assert result.complete
    assert len(result.plans) == sum(math.perm(3, k) for k in range(4))


def test_incomplete_search_does_not_claim_a_proven_optimum():
    public = _case([_item(f"x{i}", expected_outcomes={}) for i in range(7)], 7.0)
    solution = solve_exact(public, PlanConstraints(budget=7.0))
    assert solution.status == "FEASIBLE_INCOMPLETE"
    assert not solution.proven_optimal
    assert solution.gap == float("inf")
    assert not solution.search_complete


def test_small_instance_still_proves_optimality():
    public = _case([_item("a", expected_outcomes={"hA": "high", "hB": "low"})], 1.0)
    solution = solve_exact(public, PlanConstraints(budget=1.0))
    assert solution.status == "OPTIMAL"
    assert solution.proven_optimal
    assert solution.gap == 0.0
    assert solution.search_complete


def test_enumerator_and_solver_limits_are_consistent():
    """The solver's own escalation threshold must be reachable by the enumerator."""

    from evaluation import planning as planning_module
    from evaluation import feasibility as feasibility_module

    assert planning_module.EXACT_ENUMERATION_LIMIT <= feasibility_module.DEFAULT_PLAN_LIMIT


# --------------------------------------------------------------------------
# Defect D: later conflicting evidence must not disappear.
# --------------------------------------------------------------------------


def test_conflicting_observations_are_reported_as_a_contradiction():
    separating = {"hA": "high", "hB": "low"}
    public = _case([_item(name, expected_outcomes=separating) for name in ("one", "two", "three")], 3.0)
    verdict = hypothesis_compatibility(public, {"one": "high", "two": "high", "three": "low"})
    assert verdict.status is CompatibilityStatus.CONTRADICTORY
    assert verdict.surviving == ()
    assert "three" in verdict.conflicting_actions
    assert not verdict.decided


def test_a_contradiction_is_not_scored_as_a_decided_contrast():
    separating = {"hA": "high", "hB": "low"}
    public = _case([_item(name, expected_outcomes=separating) for name in ("one", "two")], 2.0)
    contradictory = decision_ambiguity(public, {"one": "high", "two": "low"})
    decided = decision_ambiguity(public, {"one": "high", "two": "high"})
    assert decided == 1
    assert contradictory != 1, "a contradiction must not look like a resolved contrast"


def test_an_undeclared_outcome_is_unusable_rather_than_contradictory():
    public = _case([_item("one", expected_outcomes={"hA": "high", "hB": "low"})], 1.0)
    verdict = hypothesis_compatibility(public, {"one": "assay_failed"})
    assert verdict.status is CompatibilityStatus.UNUSABLE_MEASUREMENT
    assert "one" in verdict.unusable_actions
    assert not verdict.decided


def test_consistent_evidence_still_decides():
    separating = {"hA": "high", "hB": "low"}
    public = _case([_item(name, expected_outcomes=separating) for name in ("one", "two")], 2.0)
    verdict = hypothesis_compatibility(public, {"one": "high", "two": "high"})
    assert verdict.status is CompatibilityStatus.DECIDED
    assert verdict.surviving == ("hA",)
    assert verdict.decided


def test_no_observation_leaves_the_contrast_ambiguous():
    separating = {"hA": "high", "hB": "low"}
    public = _case([_item("one", expected_outcomes=separating)], 1.0)
    verdict = hypothesis_compatibility(public, {})
    assert verdict.status is CompatibilityStatus.AMBIGUOUS
    assert set(verdict.surviving) == {"hA", "hB"}


# --------------------------------------------------------------------------
# Defect B: premise admission must be bound to the quantity actually measured.
# --------------------------------------------------------------------------


def _typed_case():
    supplier = _item(
        "bulk_viability",
        quantity=BiologicalQuantity.VIABILITY,
        supplies=("target_engagement_confirmed",),
        expected_outcomes={},
    )
    dependant = _item(
        "engagement_followup",
        prerequisites=("target_engagement_confirmed",),
        quantity=BiologicalQuantity.PROXIMAL_ACTIVITY,
        expected_outcomes={},
    )
    registry = {
        "target_engagement_confirmed": PremiseRequirement(
            field="target_engagement_confirmed",
            quantity=BiologicalQuantity.TARGET_OCCUPANCY,
            entity="EGFR",
        )
    }
    return _case([supplier, dependant], 2.0, premise_registry=registry)


def test_a_misleading_field_name_does_not_discharge_a_typed_premise():
    public = _typed_case()
    observed = {"bulk_viability": _record("bulk_viability", "positive", ("target_engagement_confirmed",))}
    unlocked = {
        item.action.identifier
        for item in legal_actions(public, ("bulk_viability",), 1.0, effective_fields(observed), observed=observed)
    }
    assert "engagement_followup" not in unlocked


def test_the_matching_quantity_does_discharge_the_premise():
    supplier = _item(
        "occupancy_assay",
        quantity=BiologicalQuantity.TARGET_OCCUPANCY,
        supplies=("target_engagement_confirmed",),
        entity="EGFR",
        expected_outcomes={},
    )
    dependant = _item(
        "engagement_followup",
        prerequisites=("target_engagement_confirmed",),
        expected_outcomes={},
    )
    registry = {
        "target_engagement_confirmed": PremiseRequirement(
            field="target_engagement_confirmed",
            quantity=BiologicalQuantity.TARGET_OCCUPANCY,
            entity="EGFR",
        )
    }
    public = _case([supplier, dependant], 2.0, premise_registry=registry)
    observed = {"occupancy_assay": _record("occupancy_assay", "positive", ("target_engagement_confirmed",))}
    unlocked = {
        item.action.identifier
        for item in legal_actions(public, ("occupancy_assay",), 1.0, effective_fields(observed), observed=observed)
    }
    assert "engagement_followup" in unlocked


def test_a_bridge_estimate_does_not_discharge_a_direct_measurement_premise():
    supplier = _item(
        "rna_to_protein_bridge",
        quantity=BiologicalQuantity.PROTEIN_ABUNDANCE,
        quantity_is_estimated=True,
        supplies=("protein_present",),
        entity="EGFR",
        expected_outcomes={},
    )
    dependant = _item("protein_followup", prerequisites=("protein_present",), expected_outcomes={})
    registry = {
        "protein_present": PremiseRequirement(
            field="protein_present",
            quantity=BiologicalQuantity.PROTEIN_ABUNDANCE,
            entity="EGFR",
            require_direct_measurement=True,
        )
    }
    public = _case([supplier, dependant], 2.0, premise_registry=registry)
    observed = {"rna_to_protein_bridge": _record("rna_to_protein_bridge", "positive", ("protein_present",))}
    unlocked = {
        item.action.identifier
        for item in legal_actions(public, ("rna_to_protein_bridge",), 1.0, effective_fields(observed), observed=observed)
    }
    assert "protein_followup" not in unlocked


def test_a_wrong_entity_does_not_discharge_the_premise():
    supplier = _item(
        "occupancy_assay",
        quantity=BiologicalQuantity.TARGET_OCCUPANCY,
        supplies=("target_engagement_confirmed",),
        entity="MET",
        expected_outcomes={},
    )
    dependant = _item("engagement_followup", prerequisites=("target_engagement_confirmed",), expected_outcomes={})
    registry = {
        "target_engagement_confirmed": PremiseRequirement(
            field="target_engagement_confirmed",
            quantity=BiologicalQuantity.TARGET_OCCUPANCY,
            entity="EGFR",
        )
    }
    public = _case([supplier, dependant], 2.0, premise_registry=registry)
    observed = {"occupancy_assay": _record("occupancy_assay", "positive", ("target_engagement_confirmed",))}
    unlocked = {
        item.action.identifier
        for item in legal_actions(public, ("occupancy_assay",), 1.0, effective_fields(observed), observed=observed)
    }
    assert "engagement_followup" not in unlocked


def test_a_record_from_another_context_does_not_discharge_a_context_bound_premise():
    supplier = _item(
        "occupancy_assay",
        quantity=BiologicalQuantity.TARGET_OCCUPANCY,
        supplies=("target_engagement_confirmed",),
        entity="EGFR",
        expected_outcomes={},
    )
    dependant = _item("engagement_followup", prerequisites=("target_engagement_confirmed",), expected_outcomes={})
    registry = {
        "target_engagement_confirmed": PremiseRequirement(
            field="target_engagement_confirmed",
            quantity=BiologicalQuantity.TARGET_OCCUPANCY,
            entity="EGFR",
            context_identifier="ctx",
        )
    }
    public = _case([supplier, dependant], 2.0, premise_registry=registry)
    observed = {
        "occupancy_assay": _record(
            "occupancy_assay", "positive", ("target_engagement_confirmed",), context_identifier="other_line"
        )
    }
    unlocked = {
        item.action.identifier
        for item in legal_actions(public, ("occupancy_assay",), 1.0, effective_fields(observed), observed=observed)
    }
    assert "engagement_followup" not in unlocked


def test_untyped_legacy_fields_keep_working_and_are_reported_as_untyped():
    """A case with no premise registry must behave exactly as before."""

    supplier = _item("legacy_supplier", supplies=("some_field",), expected_outcomes={})
    dependant = _item("legacy_dependant", prerequisites=("some_field",), expected_outcomes={})
    public = _case([supplier, dependant], 2.0)
    observed = {"legacy_supplier": _record("legacy_supplier", "positive", ("some_field",))}
    unlocked = {
        item.action.identifier
        for item in legal_actions(public, ("legacy_supplier",), 1.0, effective_fields(observed), observed=observed)
    }
    assert "legacy_dependant" in unlocked
    grants = granted_premises(public, observed)
    assert grants["some_field"][0].is_typed is False


def test_the_planner_rejects_a_route_whose_declaration_cannot_discharge_the_premise():
    """No viability result would ever satisfy an occupancy premise, so do not plan one."""

    public = _typed_case()
    plans = enumerate_public_plans(public)
    assert ("bulk_viability",) in plans
    assert ("bulk_viability", "engagement_followup") not in plans


def test_a_planned_premise_is_a_bet_that_the_assay_qualifies():
    """The planner is optimistic about the result, never about the meaning.

    A correctly typed supplier is planned as if its record will qualify. If the
    record then fails its biological quality check, the dependent action becomes
    illegal. That gap between a selected prerequisite and a satisfied premise is
    what the repair step exists to close.
    """

    supplier = _item(
        "occupancy_assay",
        quantity=BiologicalQuantity.TARGET_OCCUPANCY,
        supplies=("target_engagement_confirmed",),
        entity="EGFR",
        expected_outcomes={},
    )
    dependant = _item("engagement_followup", prerequisites=("target_engagement_confirmed",), expected_outcomes={})
    registry = {
        "target_engagement_confirmed": PremiseRequirement(
            field="target_engagement_confirmed",
            quantity=BiologicalQuantity.TARGET_OCCUPANCY,
            entity="EGFR",
        )
    }
    public = _case([supplier, dependant], 2.0, premise_registry=registry)

    assert ("occupancy_assay", "engagement_followup") in enumerate_public_plans(public)

    failed = {
        "occupancy_assay": _record(
            "occupancy_assay",
            "positive",
            ("target_engagement_confirmed",),
            biological_quality="failed",
        )
    }
    executable = {
        item.action.identifier
        for item in legal_actions(public, ("occupancy_assay",), 1.0, effective_fields(failed), observed=failed)
    }
    assert "engagement_followup" not in executable


# --------------------------------------------------------------------------
# Defect A: joint validation domains, not the cross product of margins.
# --------------------------------------------------------------------------


def _joint_rows():
    return [
        {"context_id": "A375", "perturbation": "trametinib", "dose": 0.01, "time_hours": 2.0, "readout": "phospho"},
        {"context_id": "A375", "perturbation": "trametinib", "dose": 5.0, "time_hours": 72.0, "readout": "viability"},
    ]


def test_an_unobserved_cross_product_is_not_in_distribution():
    registry = SupportRegistry.from_table(_joint_rows())
    verdict = registry.assess(
        context_id="A375", perturbation="trametinib", mode="drug", dose=5.0, time_hours=2.0, readouts=("viability",)
    )
    assert not verdict.in_distribution
    assert verdict.level is SupportLevel.EXECUTABLE_UNCALIBRATED
    assert verdict.reasons


def test_an_observed_joint_slice_is_observed_support_not_validation():
    """Revised 2026-09-13 (follow-up review, finding D).

    This test previously asserted VALIDATED for a slice derived from a table of
    rows, which is the defect the review reproduced: writing rows down measures
    no held-out error. Validation now needs a receipt; see
    tests/test_production_contract_gaps.py.
    """

    registry = SupportRegistry.from_table(_joint_rows())
    verdict = registry.assess(
        context_id="A375", perturbation="trametinib", mode="drug", dose=5.0, time_hours=72.0, readouts=("viability",)
    )
    assert verdict.in_distribution
    assert verdict.level is SupportLevel.OBSERVED_SUPPORT
    assert not verdict.validated


def test_an_unregistered_axis_is_unknown_not_merely_out_of_range():
    registry = SupportRegistry.from_table(_joint_rows())
    verdict = registry.assess(
        context_id="HUVEC", perturbation="trametinib", mode="drug", dose=5.0, time_hours=72.0, readouts=("viability",)
    )
    assert verdict.level is SupportLevel.UNKNOWN


def test_an_unsupported_readout_is_incompatible():
    registry = SupportRegistry.from_table(_joint_rows())
    verdict = registry.assess(
        context_id="A375", perturbation="trametinib", mode="drug", dose=5.0, time_hours=72.0, readouts=("occupancy",)
    )
    assert verdict.level is SupportLevel.INCOMPATIBLE


def test_declared_interpolation_is_honoured_only_on_the_declared_axis():
    rows = [
        {"context_id": "A375", "perturbation": "trametinib", "dose": 0.1, "time_hours": 6.0, "readout": "viability"},
        {"context_id": "A375", "perturbation": "trametinib", "dose": 10.0, "time_hours": 6.0, "readout": "viability"},
    ]
    registry = SupportRegistry.from_table(rows, interpolate_over=("dose",))
    inside = registry.assess(
        context_id="A375", perturbation="trametinib", mode="drug", dose=1.0, time_hours=6.0, readouts=("viability",)
    )
    assert inside.in_distribution
    off_axis = registry.assess(
        context_id="A375", perturbation="trametinib", mode="drug", dose=1.0, time_hours=24.0, readouts=("viability",)
    )
    assert not off_axis.in_distribution


def test_an_explicitly_declared_range_record_is_still_honoured():
    """A hand-declared range is a deliberate claim and must not be rejected."""

    registry = SupportRegistry(
        [
            SupportRecord(
                context_id="A549",
                perturbations=frozenset({"drug_p"}),
                modes=frozenset({"drug"}),
                readouts=frozenset({"viability"}),
                dose_range=(0.0, 100.0),
            )
        ]
    )
    assert registry.assess(context_id="A549", perturbation="drug_p", mode="drug", dose=10.0).in_distribution


# --------------------------------------------------------------------------
# Defect E: the backend catalog, and composition only through a connector.
# --------------------------------------------------------------------------


class _Rung:
    def __init__(self, name: str, readout: str, quantity: BiologicalQuantity):
        self.name = name
        self._readout = readout
        self.quantity = quantity

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            model_identifier=self.name,
            model_version=f"{self.name}-v1",
            input_representation="fixture",
            perturbation_representation="fixture",
            supported_modes=("drug",),
            requires_matched_control=False,
            supports_dose=False,
            supports_time=False,
            calibration_basis=None,
        )

    def assess_query(self, request: PredictionRequest) -> QueryAssessment:
        supported = self._readout in request.readouts
        return QueryAssessment(
            support=QuerySupport.SUPPORTED if supported else QuerySupport.UNSUPPORTED,
            missing_inputs=(),
            limitations=() if supported else (f"{self.name} does not serve {request.readouts}",),
            capabilities=self.capabilities(),
        )

    def predict(self, request: PredictionRequest) -> StatePrediction:
        return StatePrediction(
            applicable=True,
            state_change={self._readout: 1.0},
            uncertainty=0.1,
            limitations=(),
            request_id=request.request_id,
            model_version=self.capabilities().model_version,
            confidence=0.5,
            in_distribution=True,
        )


def _request(readout: str) -> PredictionRequest:
    return PredictionRequest(
        request_id="fixture.request",
        case_id="fixture",
        contrast_id="k1",
        plan_version=1,
        intervention=Intervention("trametinib", "drug", ("MAP2K1",)),
        context=SystemContext("A375", "fixture context"),
        readouts=(readout,),
        model_version="viability_rung-v1" if readout == "viability" else "rung_one-v1",
    )


def test_the_composite_exposes_every_backend_not_only_the_first():
    composite = CompositeWorldModel(
        [
            _Rung("transcript_rung", "rna", BiologicalQuantity.RNA_ABUNDANCE),
            _Rung("viability_rung", "viability", BiologicalQuantity.VIABILITY),
        ]
    )
    catalog = composite.catalog()
    assert [entry.model_identifier for entry in catalog] == ["transcript_rung", "viability_rung"]


def test_eligibility_not_list_order_selects_the_backend():
    composite = CompositeWorldModel(
        [
            _Rung("transcript_rung", "rna", BiologicalQuantity.RNA_ABUNDANCE),
            _Rung("viability_rung", "viability", BiologicalQuantity.VIABILITY),
        ]
    )
    eligible = composite.eligible_backends(_request("viability"))
    assert [entry.name for entry in eligible] == ["viability_rung"]
    composite.predict(_request("viability"))
    assert composite.last_rung == "viability_rung"


def test_disagreeing_backends_are_preserved_rather_than_averaged():
    composite = CompositeWorldModel(
        [
            _Rung("rung_one", "rna", BiologicalQuantity.RNA_ABUNDANCE),
            _Rung("rung_two", "rna", BiologicalQuantity.RNA_ABUNDANCE),
        ]
    )
    predictions = composite.predict_all(_request("rna"))
    assert len(predictions) == 2
    assert {name for name, _ in predictions} == {"rung_one", "rung_two"}


def test_a_connector_refuses_to_bridge_unmatched_quantities():
    transcript = Observable(
        name="EGFR_rna",
        quantity=BiologicalQuantity.RNA_ABUNDANCE,
        entity="EGFR",
        units="log2_tpm",
        assay="rnaseq",
        measurement_model=MeasurementModel(observation="identity", noise="normal"),
    )
    survival = Observable(
        name="cell_viability",
        quantity=BiologicalQuantity.VIABILITY,
        entity="cell",
        units="fraction_of_control",
        assay="ctg",
        measurement_model=MeasurementModel(observation="identity", noise="normal"),
    )
    connector = Connector(
        identifier="rna_to_viability",
        source=transcript,
        target=survival,
        segment=ChainSegment.RESPONSE_TO_OBSERVATION,
        validation_basis=None,
    )
    problems = connector.qualification_errors()
    assert "quantity_mismatch" in problems
    assert "units_mismatch" in problems
    assert "no_validation_basis" in problems
    assert not connector.qualified


def test_a_free_text_basis_no_longer_qualifies_a_simulation_as_a_blot():
    """Revised 2026-09-13 (follow-up review, finding E).

    This test previously asserted that a simulated observable and a western
    blot observable qualified as connected because a basis string was present.
    They differ in assay, and a nonempty text field is not a validation result.
    """

    source = Observable(
        name="EGFR_protein_predicted",
        quantity=BiologicalQuantity.PROTEIN_ABUNDANCE,
        entity="EGFR",
        units="log2_intensity",
        assay="simulated",
        measurement_model=MeasurementModel(observation="identity", noise="normal"),
        context_identifier="A375",
        time_hours=24.0,
    )
    target = Observable(
        name="EGFR_protein_measured",
        quantity=BiologicalQuantity.PROTEIN_ABUNDANCE,
        entity="EGFR",
        units="log2_intensity",
        assay="wb",
        measurement_model=MeasurementModel(observation="identity", noise="normal"),
        context_identifier="A375",
        time_hours=24.0,
    )
    connector = Connector(
        identifier="sim_to_measured",
        source=source,
        target=target,
        segment=ChainSegment.RESPONSE_TO_OBSERVATION,
        validation_basis="held-out residuals, 42 independent units",
    )
    assert "assay_mismatch" in connector.qualification_errors()
    assert not connector.qualified


def test_an_identity_between_two_records_of_the_same_measurement_qualifies():
    from dataclasses import replace as dataclass_replace

    from virtual_cell.biology import ConnectorKind

    blot = Observable(
        name="EGFR_protein_western",
        quantity=BiologicalQuantity.PROTEIN_ABUNDANCE,
        entity="EGFR",
        units="log2_intensity",
        assay="wb",
        measurement_model=MeasurementModel(observation="identity", noise="normal"),
        context_identifier="A375",
        time_hours=24.0,
    )
    connector = Connector(
        identifier="blot_record_to_blot_record",
        source=blot,
        target=dataclass_replace(blot),
        segment=ChainSegment.RESPONSE_TO_OBSERVATION,
        kind=ConnectorKind.IDENTITY,
    )
    assert connector.qualification_errors() == ()
    assert connector.qualified


def test_an_observable_will_not_equate_rna_with_protein():
    """Revised 2026-09-13 (follow-up review, finding C): both observables now
    state their context and time, because an observable that leaves them unknown
    is no longer interchangeable with anything, including another copy of itself."""

    rna = Observable(
        name="EGFR_rna",
        quantity=BiologicalQuantity.RNA_ABUNDANCE,
        entity="EGFR",
        units="log2_tpm",
        assay="rnaseq",
        measurement_model=MeasurementModel(observation="identity", noise="normal"),
        context_identifier="A375",
        time_hours=24.0,
    )
    protein = Observable(
        name="EGFR_protein",
        quantity=BiologicalQuantity.PROTEIN_ABUNDANCE,
        entity="EGFR",
        units="log2_tpm",
        assay="wb",
        measurement_model=MeasurementModel(observation="identity", noise="normal"),
        context_identifier="A375",
        time_hours=24.0,
    )
    assert not rna.interchangeable_with(protein)
    assert rna.interchangeable_with(rna)


def test_the_same_entity_at_a_different_site_is_not_the_same_observable():
    total = Observable(
        name="EGFR_total",
        quantity=BiologicalQuantity.PROTEIN_ABUNDANCE,
        entity="EGFR",
        units="log2_intensity",
        assay="ms",
        measurement_model=MeasurementModel(observation="identity", noise="normal"),
    )
    phospho = Observable(
        name="EGFR_pY992",
        quantity=BiologicalQuantity.PROTEIN_ABUNDANCE,
        entity="EGFR",
        site="Y992",
        units="log2_intensity",
        assay="ms",
        measurement_model=MeasurementModel(observation="identity", noise="normal"),
    )
    assert not total.interchangeable_with(phospho)


@pytest.mark.parametrize(
    "segment",
    [
        ChainSegment.INTENDED_TO_REALIZED,
        ChainSegment.REALIZED_TO_RESPONSE,
        ChainSegment.RESPONSE_TO_OBSERVATION,
        ChainSegment.OBSERVATION_TO_DECISION,
    ],
)
def test_every_chain_segment_is_nameable(segment):
    assert segment.value


# --------------------------------------------------------------------------
# Scale calibration: a magnitude correction that knows where it came from.
# --------------------------------------------------------------------------


def test_a_fitted_scale_refuses_a_different_endpoint_and_context():
    from virtual_cell.calibration import fit_scale

    calibration = fit_scale(
        [[1.0, 2.0], [2.0, 4.0]],
        [[4.0, 8.0], [8.0, 16.0]],
        endpoint="x_hvg_perturbation_shift",
        context_identifier="NCI-H596",
        fitted_on="development drugs only",
        independent_units=190,
    )
    assert abs(calibration.scale - 0.25) < 1e-9
    assert calibration.shrinks
    assert calibration.applies_to(endpoint="x_hvg_perturbation_shift", context_identifier="NCI-H596")
    assert not calibration.applies_to(endpoint="fitted_viability_auc", context_identifier="NCI-H596")
    assert not calibration.applies_to(endpoint="x_hvg_perturbation_shift", context_identifier="A549")
    with pytest.raises(ValueError):
        calibration.apply([1.0], endpoint="fitted_viability_auc", context_identifier="NCI-H596")


def test_a_scale_cannot_be_fitted_from_identically_zero_predictions():
    from virtual_cell.calibration import fit_scale

    with pytest.raises(ValueError):
        fit_scale(
            [[1.0, 2.0]],
            [[0.0, 0.0]],
            endpoint="e",
            context_identifier=None,
            fitted_on="fixture",
            independent_units=1,
        )


# --------------------------------------------------------------------------
# Backend eligibility is decided on declarations, with named reasons.
# --------------------------------------------------------------------------


def _transcript_observable():
    # Context and time are declared (revised 2026-09-13, finding C): a request
    # that does not say which context and exposure it asks about is unresolved.
    return Observable(
        name="x_hvg_shift",
        quantity=BiologicalQuantity.RNA_ABUNDANCE,
        entity="transcriptome_hvg_2000",
        units="x_hvg_units",
        assay="scrnaseq_pseudobulk",
        measurement_model=MeasurementModel(observation="mean_minus_vehicle", noise="normal"),
        context_identifier="NCI-H596",
        time_hours=24.0,
    )


def _backend():
    from virtual_cell.biology import BackendDescription

    return BackendDescription(
        name="transcript_backend",
        model_identifier="arc_state",
        model_version="v1",
        segments=(ChainSegment.REALIZED_TO_RESPONSE,),
        observables=(_transcript_observable(),),
        supported_modalities=("drug",),
        supports_combinations=False,
    )


def test_a_backend_names_each_reason_it_is_ineligible():
    viability = Observable(
        name="viability",
        quantity=BiologicalQuantity.VIABILITY,
        entity="cell_population",
        units="fitted_auc",
        assay="ctg",
        measurement_model=MeasurementModel(observation="identity", noise="normal"),
    )
    reasons = _backend().ineligibility_reasons(
        observable=viability,
        modality="crispr_knockout",
        combination=True,
        segment=ChainSegment.OBSERVATION_TO_DECISION,
    )
    assert set(reasons) == {
        "quantity_not_served",
        "modality_unsupported",
        "combination_unsupported",
        "segment_not_implemented",
    }


def test_a_matching_request_has_no_ineligibility_reasons():
    assert _backend().ineligibility_reasons(
        observable=_transcript_observable(),
        modality="drug",
        combination=False,
        segment=ChainSegment.REALIZED_TO_RESPONSE,
    ) == ()


def test_a_served_quantity_with_wrong_qualifiers_is_distinguished_from_an_unserved_one():
    other_units = replace_observable_units(_transcript_observable(), "counts")
    reasons = _backend().ineligibility_reasons(observable=other_units)
    assert reasons == ("observable_qualifier_mismatch",)


def replace_observable_units(observable: Observable, units: str) -> Observable:
    from dataclasses import replace as dataclass_replace

    return dataclass_replace(observable, units=units)


def test_a_selectivity_observable_without_a_comparator_is_marked_incomplete():
    lonely = Observable(
        name="selectivity",
        quantity=BiologicalQuantity.SELECTIVITY,
        entity="EGFR",
        units="ratio",
        assay="panel",
        measurement_model=MeasurementModel(observation="identity", noise="normal"),
    )
    assert "selectivity_without_comparator" in lonely.limitations


def test_an_intervention_separates_intent_from_realised_effect():
    from maestro.models import MeasurementStatus
    from virtual_cell.biology import CompositeIntervention, InterventionComponent

    inhibitor = InterventionComponent(
        identifier="compound_a",
        modality="small_molecule_inhibitor",
        intended_targets=("EGFR", "MET"),
        realized_effects={"EGFR": MeasurementStatus.MEASURED},
    )
    assert inhibitor.unverified_targets == ("MET",)
    combination = CompositeIntervention("combo", (inhibitor,))
    assert not combination.is_combination
    assert combination.unverified_targets == ("MET",)


# --------------------------------------------------------------------------
# The decision state separates three independent facts.
# --------------------------------------------------------------------------


def test_the_view_reports_readiness_menu_state_and_missing_premises_separately():
    from evaluation.cases import ReplayView

    """Revised 2026-09-13 (follow-up review, finding F).

    The second half of this test previously asserted that a call declaring no
    requirement was ready to decide. With nothing declared there is nothing to
    be ready for, so that state is now unresolved; missing premises are named
    with the typed reason rather than by field name alone.
    """

    public = _typed_case()
    view = ReplayView(case=public, remaining_budget=public.budget, revealed=(), queried_actions=())
    state = view.decision_state(required_premises=("target_engagement_confirmed",))
    assert state["decision_ready"] is False
    assert state["required_missing_premises"] == ("target_engagement_confirmed:not_supplied",)
    assert state["additional_evidence_available"] is True

    undeclared = view.decision_state()
    assert undeclared["decision_ready"] is False
    assert undeclared["readiness"] == "unresolved"
    assert undeclared["additional_evidence_available"] is True, (
        "readiness and an open menu remain independent facts"
    )


def test_a_blocked_action_names_the_premise_that_blocks_it():
    from evaluation.cases import ReplayView

    public = _typed_case()
    record = _record("bulk_viability", "positive", ("target_engagement_confirmed",))
    view = ReplayView(
        case=public,
        remaining_budget=public.budget - 1.0,
        revealed=(record,),
        queried_actions=("bulk_viability",),
    )
    blocked = view.blocked_actions()
    assert "engagement_followup" in blocked
    assert any("quantity_mismatch" in reason for reason in blocked["engagement_followup"])
