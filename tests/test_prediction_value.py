"""What a revocable prediction is worth, and what the contract's rules cost.

File summary
- Path: tests/test_prediction_value.py
- Purpose: pin the secondary-core measurement. Each assertion states one measured fact
  about a declared finite model: where a prediction changes the plan it is worth exactly
  the plan change and no more, where it does not change the plan it is worth nothing, a
  wrong prediction costs what a right one earns, a refused prediction is exactly the
  no-model arm, and revocation stops paying without making the predictor better.
- Interfaces: pytest test functions
- Depends on: evaluation.prediction_value, maestro.reliability
"""
import pytest

from evaluation.prediction_value import (
    CHEAP,
    READOUT,
    ContextPrediction,
    arm_rows,
    branch_family,
    contract_effect,
    no_model_prediction,
    prediction_influence,
    revocation_trace,
    value_map,
    with_predicted_qualification,
)
from maestro.reliability import PredictionReliabilityLedger


def _informed(qualification: float, **kwargs) -> ContextPrediction:
    return ContextPrediction(
        context_identifier="context",
        qualification=qualification,
        interval=(max(0.0, qualification - 0.1), 1.0),
        **kwargs,
    )


def test_a_prediction_is_worth_the_plan_change_it_gets_right():
    """Context A: the prediction moves the plan from the reliable to the cheap supplier."""

    truth = branch_family(identifier="truth_a", qualification=0.9)
    informed = arm_rows(truth, _informed(0.9), fallback=0.5)
    absent = arm_rows(truth, no_model_prediction(), fallback=0.5)
    assert informed["plan_changed"] is True
    assert absent["plan_changed"] is False
    assert absent["expected_loss_under_truth"] == pytest.approx(3.5)
    assert informed["expected_loss_under_truth"] == pytest.approx(2.75)


def test_a_prediction_that_does_not_move_the_plan_is_worth_exactly_nothing():
    """Context B: the class-correct plan is the reliable supplier either way."""

    truth = branch_family(identifier="truth_b", qualification=0.3)
    informed = arm_rows(truth, _informed(0.3), fallback=0.5)
    absent = arm_rows(truth, no_model_prediction(), fallback=0.5)
    assert informed["plan_changed"] is False
    assert informed["expected_loss_under_truth"] == pytest.approx(
        absent["expected_loss_under_truth"]
    )


def test_a_wrong_prediction_costs_what_a_right_one_earns():
    """The asymmetry claim, measured on the symmetric family rather than asserted."""

    effect = contract_effect()
    assert effect["value_of_a_correct_prediction"] == pytest.approx(0.375)
    assert effect["harm_of_a_wrong_prediction"] == pytest.approx(0.375)
    assert effect["informed_plan_change_rate"] == pytest.approx(0.5)


def test_a_refused_prediction_is_exactly_the_no_model_arm():
    """An uncalibrated claim cannot change the plan, so it cannot change the loss."""

    effect = contract_effect()
    for row in effect["contexts"].values():
        assert row["refused_uncalibrated"] == pytest.approx(row["no_model"])
    uncalibrated = ContextPrediction(context_identifier="context", qualification=0.9)
    assert uncalibrated.claims_coverage is False
    assert prediction_influence(uncalibrated, fallback=0.5, require_coverage=True) == pytest.approx(0.5)
    assert prediction_influence(uncalibrated, fallback=0.5, require_coverage=False) == pytest.approx(0.9)
    # A coverage-claiming prediction is exactly what the refusal rule lets through.
    assert prediction_influence(_informed(0.9), fallback=0.5, require_coverage=True) == pytest.approx(0.9)


def test_an_abstaining_or_out_of_scope_model_reads_as_no_model():
    abstaining = ContextPrediction(
        context_identifier="context",
        qualification=0.9,
        interval=(0.8, 1.0),
        applicable=False,
        abstain_reason="endpoint_not_representable_in_output_space",
    )
    assert prediction_influence(abstaining, fallback=0.5) == pytest.approx(0.5)
    truth = branch_family(identifier="truth", qualification=0.9)
    assert arm_rows(truth, abstaining, fallback=0.5)["prediction_refused"] is True


def test_a_prediction_never_edits_the_evidence_problem():
    """Only the declared branch parameter of the planner's view may move."""

    truth = branch_family(identifier="truth", qualification=0.9)
    planning = with_predicted_qualification(truth, 0.3)
    assert planning.hypotheses == truth.hypotheses
    assert planning.decisions == truth.decisions
    assert planning.loss == truth.loss
    assert planning.budget == truth.budget
    assert planning.prior == truth.prior
    assert [a.identifier for a in planning.actions] == [a.identifier for a in truth.actions]
    for original, changed in zip(truth.actions, planning.actions):
        assert original.cost == changed.cost
        assert original.prerequisites == changed.prerequisites
        assert original.supplies == changed.supplies
        if original.identifier == CHEAP:
            assert changed.outcome_model != original.outcome_model
        else:
            assert changed.outcome_model == original.outcome_model
    # The truth is untouched by the prediction that was applied to the planner's view.
    assert truth.action(CHEAP).outcome_model["realised"]["qualified"] == pytest.approx(0.9)


def test_revocation_stops_paying_for_a_miscalibrated_predictor():
    """Three consecutive missed intervals revoke; the loss recovered is the latency's price."""

    trace = revocation_trace()
    assert [row["weight_before"] for row in trace["cases"]] == [1.0, 1.0, 1.0, 0.0, 0.0]
    assert trace["revocation_latency_cases"] == 4
    assert trace["total_loss_if_always_trusted"] == pytest.approx(21.25)
    assert trace["total_loss_with_revocation"] == pytest.approx(19.75)
    assert trace["loss_recovered_by_revocation"] == pytest.approx(1.5)


def test_revocation_does_not_make_the_predictor_better():
    """Before it revokes, the ledger pays the full price: it is a bound, not a fix."""

    trace = revocation_trace()
    trusted = [row["expected_loss_if_always_trusted"] for row in trace["cases"]]
    with_revocation = [row["expected_loss_under_truth"] for row in trace["cases"]]
    assert with_revocation[:3] == pytest.approx(trusted[:3])
    assert with_revocation[3:] < trusted[3:]


def test_a_revoked_scope_is_reported_and_keeps_the_evidence_ledger_untouched():
    ledger = PredictionReliabilityLedger(minimum_records=3, revoke_after_consecutive_misses=3)
    for _ in range(3):
        ledger.record_pair(
            model_version="m",
            readout=READOUT,
            predicted_value=0.9,
            realized_value=0.3,
            interval=(0.8, 1.0),
            context_identifier="context",
        )
    summary = ledger.summarize("m", READOUT, "context")
    assert summary.revoked is True
    assert summary.weight == 0.0
    assert summary.consecutive_misses == 3
    assert len(ledger.records) == 3


def test_a_branch_parameter_outside_the_unit_interval_is_refused():
    with pytest.raises(ValueError):
        branch_family(identifier="impossible", qualification=1.5)
    truth = branch_family(identifier="truth", qualification=0.5)
    with pytest.raises(ValueError):
        with_predicted_qualification(truth, -0.1)
    with pytest.raises(ValueError):
        prediction_influence(_informed(0.9), fallback=0.5, weight=1.5)


def test_a_claim_that_leaves_the_plan_alone_cannot_move_the_loss():
    """The scope condition, asserted on every cell of the grid rather than on one instance."""

    table = value_map()
    informative = 0
    for cell in table["cells"]:
        if not cell["plan_changed"]:
            assert cell["value"] == 0.0, cell
        else:
            informative += 1
            assert cell["value"] > 0.0, cell
        if not cell["wrong_claim_plan_changed"]:
            assert cell["harm"] == 0.0, cell
    assert informative == table["plan_changing_cells"]
    assert 0 < informative < table["total_cells"]
