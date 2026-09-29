"""A revoked readout no longer certifies discrimination.

File summary
- Path: tests/test_discrimination_gate_revocation.py
- Purpose: close the third defect of the lawful-influence channel: the
  discrimination gate consulted the interval's own coverage claim and ignored
  the scored record of how that claim performed.
- Core points: assertions here are contract tests, not biological results; the
  pairs recorded into the ledger are synthetic misses.
- Interfaces: `test_three_consecutive_calibrated_misses_stop_certification()`,
  `test_the_guard_is_the_ledger_and_not_the_interval()`.
- Depends on: maestro, virtual_cell
"""
from maestro import EvidenceAction, FunctionalInterventionProfile, MAESTROAgent, MechanismHypothesis
from maestro.models import NonDiscriminabilityReason
from maestro.judgment import PredictionReliabilityLedger
from maestro.models import DevelopmentAction
from virtual_cell.interface import Interval, IntervalKind
from virtual_cell import StatePrediction

READOUT = "delta"
MODEL_VERSION = "m"


def _pair():
    return (
        MechanismHypothesis("h1", "Explanation one.", DevelopmentAction.CONTINUE),
        MechanismHypothesis("h2", "Explanation two.", DevelopmentAction.REVISE_INTERVENTION),
    )


def _action() -> EvidenceAction:
    return EvidenceAction(
        "model_assay", "Model-guided assay.", 1.0, ("h1", "h2"),
        requires_virtual_prediction=True, prediction_readout=READOUT,
        expected_outcomes={"h1": "large_shift", "h2": "small_shift"},
    )


def _contrast(agent: MAESTROAgent, action: EvidenceAction):
    contrast = agent.construct_contrast("contrast", _pair(), (), (action,))
    assert contrast is not None
    return contrast


def _prediction() -> StatePrediction:
    return StatePrediction(
        True, {READOUT: 2.0}, None, (),
        intervals={
            READOUT: Interval(
                0.0, 4.0, kind=IntervalKind.CALIBRATED, level=0.9, basis="held-out residuals"
            )
        },
        request_id="q", model_version=MODEL_VERSION,
    )


def _revoke(ledger: PredictionReliabilityLedger) -> None:
    """Three consecutive real values outside the declared interval."""

    for index in range(3):
        ledger.record_pair(
            model_version=MODEL_VERSION,
            readout=READOUT,
            predicted_value=2.0,
            realized_value=9.0,
            interval=(0.0, 4.0),
            result_id=f"r{index}",
        )
    summary = ledger.summarize(MODEL_VERSION, READOUT)
    assert summary.revoked, summary
    assert summary.weight == 0.0


def test_three_consecutive_calibrated_misses_stop_certification():
    agent = MAESTROAgent()
    contrast = _contrast(agent, _action())
    profile = FunctionalInterventionProfile(mode="drug")
    prediction = _prediction()
    ledger = PredictionReliabilityLedger()

    certified = agent.check_contrast(contrast, profile, prediction, ledger)
    assert certified.outcome_separated
    assert certified.ready_for_mechanism_update

    _revoke(ledger)

    revoked = agent.check_contrast(contrast, profile, prediction, ledger)
    assert not revoked.outcome_separated
    assert not revoked.ready_for_mechanism_update
    assert NonDiscriminabilityReason.MODEL_DISCRIMINATION_UNCALIBRATED in revoked.reasons


def test_the_guard_is_the_ledger_and_not_the_interval():
    """The same prediction certifies again the moment the ledger is withdrawn.

    Without this the test above would only prove that the interval stopped
    claiming coverage, which it did not: the band is unchanged throughout.
    """

    agent = MAESTROAgent()
    contrast = _contrast(agent, _action())
    profile = FunctionalInterventionProfile(mode="drug")
    prediction = _prediction()
    ledger = PredictionReliabilityLedger()
    _revoke(ledger)

    assert not agent.check_contrast(contrast, profile, prediction, ledger).outcome_separated
    # No ledger means no record to consult: the behaviour every caller had before
    # this argument existed, kept deliberately rather than made mandatory.
    assert agent.check_contrast(contrast, profile, prediction).outcome_separated
    assert agent.check_contrast(contrast, profile, prediction, None).outcome_separated

    # A provisional record -- fewer graded pairs than the ledger needs -- withholds
    # revocation instead of inventing one, so one miss certifies nothing away.
    thin = PredictionReliabilityLedger()
    thin.record_pair(
        model_version=MODEL_VERSION, readout=READOUT, predicted_value=2.0,
        realized_value=9.0, interval=(0.0, 4.0), result_id="only-one",
    )
    assert thin.summarize(MODEL_VERSION, READOUT).provisional
    assert agent.check_contrast(contrast, profile, prediction, thin).outcome_separated


def test_a_local_miss_run_survives_another_contexts_hits():
    """The consecutive-miss rule counts per context inside the scope.

    With one pooled sequence, another context's hit would break a failing
    context's run and a locally failing band would keep certifying. The pooled
    scope summary still exists and is what the gate consults; its scope string
    says it pools, and the miss run it reports is the worst local one.
    """

    ledger = PredictionReliabilityLedger()
    for index in range(3):
        ledger.record_pair(
            model_version=MODEL_VERSION, readout=READOUT,
            predicted_value=2.0, realized_value=9.0, interval=(0.0, 4.0),
            context_identifier="context_a", result_id=f"a{index}",
        )
        # Another context's hit between the misses: under one pooled sequence
        # this would break the run of context_a.
        ledger.record_pair(
            model_version=MODEL_VERSION, readout=READOUT,
            predicted_value=2.0, realized_value=2.0, interval=(0.0, 4.0),
            context_identifier="context_b", result_id=f"b{index}",
        )
    pooled = ledger.summarize(MODEL_VERSION, READOUT)
    assert pooled.scope.endswith("@all-contexts")
    assert pooled.revoked, pooled
    # Scoped to the healthy context, nothing is revoked.
    assert not ledger.summarize(MODEL_VERSION, READOUT, "context_b").revoked
