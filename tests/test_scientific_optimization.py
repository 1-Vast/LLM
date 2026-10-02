"""Software regressions, not evidence that a model predicts biology correctly."""
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from agent.planner import MechanismContrastPlanner, PlannerContractError
from maestro.outcome import InterpretationTable, OutcomeClass, OutcomeRule
from maestro import FunctionalInterventionProfile
from tests.fixtures.stub_client import StubClient
from tests.fixtures.learned_response import registered_model
from tests.test_outcome_decision import _contrast, _result
from virtual_cell.interface import IntervalKind, safe_predict
from virtual_cell.learned_response import LearnedTranscriptWorldModel
from virtual_cell.biology import GeneSet


def panel(members=("ENSG1",)):
    return GeneSet("target_rna", members, "frozen software fixture", "a" * 64, "mean RNA shift")


def test_signed_readouts_separate_equal_magnitude_opposite_responses():
    from virtual_cell.learned_response import transcript_readouts

    positive = np.array([[2., -2.], [3., -3.], [1., -1.]])
    names = ("transcript_shift_rms", "rna_gene:ENSG1", "rna_set:target_rna")
    a, bands = transcript_readouts(positive, ("ENSG1", "ENSG2"), names, (panel(),))
    b, _ = transcript_readouts(-positive, ("ENSG1", "ENSG2"), names, (panel(),))
    assert a["transcript_shift_rms"] == b["transcript_shift_rms"]
    assert a["rna_gene:ENSG1"] == a["rna_set:target_rna"] == 2.
    assert b["rna_set:target_rna"] == -2.
    assert bands["rna_set:target_rna"].low == 1.
    assert bands["rna_set:target_rna"].high == 3.
    assert all(x.kind is IntervalKind.DESCRIPTIVE and not x.claims_coverage for x in bands.values())


@pytest.mark.parametrize("samples", [np.array([[np.nan, 1.]]), np.ones((3, 3)), np.empty((0, 2))])
def test_invalid_transcript_ensemble_cannot_produce_readouts(samples):
    from virtual_cell.learned_response import transcript_readouts

    with pytest.raises(ValueError, match="invalid_transcript_ensemble"):
        transcript_readouts(samples, ("ENSG1", "ENSG2"), ("transcript_shift_rms",))


def test_gene_set_with_missing_genes_is_not_silently_restricted(registered_model):
    model, request = registered_model
    enriched = LearnedTranscriptWorldModel(model.directory, model.registrations, gene_sets=(panel(("ABSENT",)),))
    request = replace(request, model_version=enriched.model_version, readouts=("rna_set:target_rna",))
    assessment, prediction = safe_predict(enriched, request)
    assert not prediction.applicable
    assert "readout_missing_genes:rna_set:target_rna" in assessment.limitations


def test_gene_set_membership_changes_served_model_identity(registered_model):
    model, _ = registered_model
    a = LearnedTranscriptWorldModel(model.directory, model.registrations, gene_sets=(panel(),))
    b = LearnedTranscriptWorldModel(model.directory, model.registrations, gene_sets=(panel(("ENSG2",)),))
    assert a.model_version != b.model_version


def test_served_readouts_keep_unknown_calibration_and_exact_vehicle(registered_model):
    model, request = registered_model
    model = LearnedTranscriptWorldModel(model.directory, model.registrations, gene_sets=(panel(),))
    request = replace(request, model_version=model.model_version,
                      readouts=("rna_gene:ENSG1", "rna_set:target_rna"))
    _, predicted = safe_predict(model, request)
    assert predicted.applicable and predicted.contract_errors() == ()
    assert set(predicted.state_change) == set(request.readouts)
    assert predicted.confidence is None and predicted.in_distribution is None
    assert predicted.calibration_basis is None
    assert all(not x.claims_coverage for x in predicted.intervals.values())
    _, vehicle = safe_predict(model, replace(request, intervention=replace(request.intervention, dose=0)))
    assert all(value == 0 for value in vehicle.state_change.values())
    assert all(x.low == x.high == 0 for x in vehicle.intervals.values())


def test_nonfinite_model_output_is_a_named_refusal(registered_model, monkeypatch):
    model, request = registered_model
    monkeypatch.setattr(model.models[0], "predict", lambda *args: np.array([[np.nan]]))
    _, prediction = safe_predict(model, request)
    assert not prediction.applicable
    assert prediction.abstain_reason == "nonfinite_transcript_prediction"


def test_duplicate_hypothesis_ids_are_rejected_before_constructing_a_contrast():
    response = {"hypotheses": [
        {"identifier": "same", "description": "exposure insufficient", "proposed_action": "revise_intervention"},
        {"identifier": "same", "description": "mode mismatch", "proposed_action": "change_intervention_mode"},
    ]}
    planner = MechanismContrastPlanner(StubClient([response]), contract_retries=0)
    with pytest.raises(PlannerContractError, match="distinct"):
        planner.propose(SimpleNamespace(rendered="test"), ())


@pytest.mark.parametrize("field", ["identifier", "description"])
def test_missing_hypothesis_definition_is_not_replaced_by_a_fabricated_default(field):
    hypotheses = [{"identifier": "a", "description": "A"}, {"identifier": "b", "description": "B"}]
    hypotheses[0][field] = " "
    planner = MechanismContrastPlanner(StubClient([{"hypotheses": hypotheses}]), contract_retries=0)
    with pytest.raises(PlannerContractError, match=field):
        planner.propose(SimpleNamespace(rendered="test"), ())


def test_conflicting_interpretation_rules_cannot_choose_truth_by_registration_order():
    observation = _result()
    contrast = _contrast()
    first = OutcomeRule("first", "a", matched_fields=frozenset(observation.interpretation_fields),
                        eliminates=frozenset({"incomplete_perturbation"}))
    second = replace(first, identifier="second", outcome_label="b", eliminates=frozenset({"mode_non_equivalence"}))
    for rules in ((first, second), (second, first)):
        interpretation = InterpretationTable(rules).interpret(
            observation, contrast, FunctionalInterventionProfile("drug", context_identifier="cell-a"))
        assert interpretation.outcome_class is OutcomeClass.AMBIGUOUS
        assert interpretation.outcome_label == "ambiguous_registered_rules"
        assert not interpretation.eliminates and not interpretation.authorized_fields
        assert not interpretation.can_update_mechanism


def test_duplicate_rule_ids_are_not_a_valid_registration():
    rule = OutcomeRule("same", "a")
    with pytest.raises(ValueError, match="unique"):
        InterpretationTable((rule, replace(rule, outcome_label="b")))
