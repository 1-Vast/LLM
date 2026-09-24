"""Behavioral regressions for the F08 admission contract and the F03 outcome mapping.

File summary
- Path: tests/test_f03_f08_remediation.py
- Purpose: Pin the acceptance behaviors of the F08 evidence-admission fix and the F03 outcome-separation fix.
- Core points:
  - Schema validity, biological quality, and evidence origin are separate gates.
  - Record counts never become independent experimental units.
  - Label coverage is not distinguishability; identical or undeclared declared outcomes are rejected.
  - A descriptive model spread cannot certify discrimination; complementary plans are assessed jointly.
- Interfaces: `test_*` functions
- Depends on: agent.cases, evaluation, maestro, virtual_cell
"""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from agent.cases import CaseStore, MeasurementResult
from agent.orchestrator import MAESTROOrchestrator
from evaluation import CaseRepository, ReplayEnvironment
from evaluation.cases import measurement_result_from_reveal
from maestro import (
    DevelopmentAction,
    EvidenceAction,
    EvidenceKind,
    EvidenceScope,
    FunctionalInterventionProfile,
    InterpretationTable,
    MAESTROAgent,
    MechanismHypothesis,
    NonDiscriminabilityReason,
    OutcomeRule,
)
from maestro.outcome import admit_evidence
from maestro.reliability import PredictionReliabilityLedger
from virtual_cell import Interval, IntervalKind, StatePrediction


ROOT = Path(__file__).resolve().parents[1]


def _synthetic():
    return next(
        item
        for item in CaseRepository(
            ROOT / "data/evaluation/cases/public", ROOT / "data/evaluation/cases/private"
        ).load()
        if item[0].public.identifier == "synthetic-functional-calibration-001"
    )


def _pair():
    return (
        MechanismHypothesis("h1", "Explanation one.", DevelopmentAction.CONTINUE),
        MechanismHypothesis("h2", "Explanation two.", DevelopmentAction.REVISE_INTERVENTION),
    )


def _contrast(agent, action, actions):
    contrast = agent.construct_contrast("contrast", _pair(), (), actions)
    assert contrast is not None
    return contrast


# --------------------------------------------------------------------------------------
# F08: one admission contract; validity is not biological quality
# --------------------------------------------------------------------------------------


def test_f08_failed_or_unknown_biological_quality_cannot_satisfy_a_prerequisite():
    case, outcomes = _synthetic()
    for quality in ("failed", "unknown"):
        degraded = dict(outcomes)
        degraded["functional_target_activity"] = replace(
            degraded["functional_target_activity"], biological_quality=quality
        )
        environment = ReplayEnvironment(case, degraded)
        environment.query("functional_target_activity")
        with pytest.raises(ValueError, match="unmet prerequisites"):
            environment.query("mode_matched_comparator")


def test_f08_a_derived_record_cannot_satisfy_a_biological_prerequisite():
    case, outcomes = _synthetic()
    derived = dict(outcomes)
    derived["functional_target_activity"] = replace(
        derived["functional_target_activity"], evidence_kind=EvidenceKind.DERIVED_ANALYSIS
    )
    environment = ReplayEnvironment(case, derived)
    environment.query("functional_target_activity")
    with pytest.raises(ValueError, match="unmet prerequisites"):
        environment.query("mode_matched_comparator")


def test_f08_record_count_never_becomes_independent_units_and_unknown_quality_is_not_a_pass():
    _, outcomes = _synthetic()
    outcome = replace(
        outcomes["functional_target_activity"],
        record_count=1000,
        biological_replicates=None,
        independent_units=None,
        biological_quality="unknown",
    )
    result = measurement_result_from_reveal(outcome, result_id=None)
    assert result.independent_units is None
    assert result.record_count == 1000
    assert result.quality_passed is False

    qualified = measurement_result_from_reveal(outcomes["functional_target_activity"], result_id=None)
    assert qualified.independent_units == 3
    assert qualified.quality_passed is True


def test_f08_unknown_independent_units_are_not_statistically_usable(tmp_path: Path):
    action = EvidenceAction("assay", "Measure.", 1.0, ("h1", "h2"))
    result = MeasurementResult(
        "assay", "Observed.", "source", None, None, None, True,
        interpretation_fields=("functional:target_activity:insufficient",),
    )
    agent = MAESTROAgent()
    contrast = _contrast(agent, action, (action,))
    table = InterpretationTable(
        [OutcomeRule(identifier="r", outcome_label="r", matched_fields=frozenset({"functional:target_activity:insufficient"}))]
    )
    interpretation = table.interpret(result, contrast, FunctionalInterventionProfile(mode="drug"), action)
    admission = admit_evidence(interpretation, result, independent_units=result.independent_units)
    assert not admission.admissible
    assert admission.statistically_usable is False
    assert not interpretation.can_update_mechanism

    known = replace(result, independent_units=3)
    interpretation = table.interpret(known, contrast, FunctionalInterventionProfile(mode="drug"), action)
    admission = admit_evidence(interpretation, known, independent_units=known.independent_units)
    assert admission.admissible
    assert admission.statistically_usable is True


def test_f08_imported_verdict_survives_persistence_and_idempotent_reimport(tmp_path: Path):
    store = CaseStore(tmp_path / "cases.sqlite")
    action = EvidenceAction("assay", "Measure.", 1.0, ("h1",), time_hours=24.0)
    store.open_case("case", budget=2.0)
    store.record_plan("case", (action,), ready_to_measure=True, context_identifier=None)
    result = MeasurementResult("assay", "Observed.", "source", None, 24.0, None, False, result_id="r1")
    imported = store.import_measurement("case", result)
    assert imported.created
    repeated = store.import_measurement("case", result)
    assert not repeated.created

    reopened = CaseStore(tmp_path / "cases.sqlite")
    again = reopened.import_measurement("case", result)
    assert not again.created


# --------------------------------------------------------------------------------------
# F03: label coverage is not distinguishability
# --------------------------------------------------------------------------------------


def test_f03_identical_declared_outcomes_reject_distinguishability():
    agent = MAESTROAgent()
    action = EvidenceAction(
        "assay", "Assay.", 1.0, ("h1", "h2"),
        expected_outcomes={"h1": "same_reading", "h2": "same_reading"},
    )
    check = agent.check_contrast(
        _contrast(agent, action, (action,)), FunctionalInterventionProfile(mode="drug")
    )
    assert NonDiscriminabilityReason.OUTCOME_NOT_SEPARATED in check.reasons
    assert not check.outcome_separated
    assert not check.ready_for_mechanism_update


def test_f03_an_undeclared_outcome_mapping_is_not_distinguishable():
    agent = MAESTROAgent()
    action = EvidenceAction("assay", "Assay.", 1.0, ("h1", "h2"))
    check = agent.check_contrast(
        _contrast(agent, action, (action,)), FunctionalInterventionProfile(mode="drug")
    )
    assert NonDiscriminabilityReason.OUTCOME_MAPPING_UNDECLARED in check.reasons
    assert not check.ready_for_mechanism_update
    assert agent.observation_scope(check) is EvidenceScope.PLAN_LIMITATION


def test_f03_differing_declared_outcomes_separate_the_pair():
    agent = MAESTROAgent()
    action = EvidenceAction(
        "assay", "Assay.", 1.0, ("h1", "h2"),
        expected_outcomes={"h1": "reading_one", "h2": "reading_two"},
    )
    check = agent.check_contrast(
        _contrast(agent, action, (action,)), FunctionalInterventionProfile(mode="drug")
    )
    assert check.outcome_separated
    assert check.ready_for_mechanism_update


def test_f03_a_descriptive_model_spread_cannot_certify_discrimination():
    agent = MAESTROAgent()
    action = EvidenceAction(
        "model_assay", "Model-guided assay.", 1.0, ("h1", "h2"),
        requires_virtual_prediction=True, prediction_readout="delta",
        expected_outcomes={"h1": "large_shift", "h2": "small_shift"},
    )
    contrast = _contrast(agent, action, (action,))
    descriptive = StatePrediction(
        True, {"delta": 2.0}, 0.5, (),
        intervals={"delta": Interval(0.0, 4.0, basis="spread of the statistic")},
        request_id="q", model_version="m",
    )
    check = agent.check_contrast(contrast, FunctionalInterventionProfile(mode="drug"), descriptive)
    assert NonDiscriminabilityReason.MODEL_DISCRIMINATION_UNCALIBRATED in check.reasons
    assert not check.ready_for_mechanism_update

    calibrated = StatePrediction(
        True, {"delta": 2.0}, None, (),
        intervals={"delta": Interval(0.0, 4.0, kind=IntervalKind.CALIBRATED, level=0.9, basis="held-out residuals")},
        request_id="q", model_version="m",
    )
    check = agent.check_contrast(contrast, FunctionalInterventionProfile(mode="drug"), calibrated)
    assert check.outcome_separated
    assert check.ready_for_mechanism_update


def test_f03_complementary_actions_do_not_form_a_joint_mapping_without_a_shared_coordinate():
    agent = MAESTROAgent()
    left = EvidenceAction("left", "Left arm.", 1.0, ("h1",), expected_outcomes={"h1": "reading_one"})
    right = EvidenceAction("right", "Right arm.", 1.0, ("h2",), expected_outcomes={"h2": "reading_two"})
    joint = EvidenceAction(
        "joint", "Joint readout.", 1.0, ("h1", "h2"),
        expected_outcomes={"h1": "reading_one", "h2": "reading_two"},
    )
    contrast = agent.construct_contrast("contrast", _pair(), (), (joint,))
    assert contrast is not None
    bundled = replace(contrast, plan=left, additional_plans=(right,))
    check = agent.check_contrast(bundled, FunctionalInterventionProfile(mode="drug"))
    assert not check.outcome_separated
    assert not check.ready_for_mechanism_update
    assert NonDiscriminabilityReason.OUTCOME_MAPPING_INCOMPLETE in check.reasons


# --------------------------------------------------------------------------------------
# Interval semantics in prediction scoring
# --------------------------------------------------------------------------------------


class _SilentLogger:
    def event(self, *args, **kwargs):
        pass

    def experiment(self, *args, **kwargs):
        pass


def _scoring_controller() -> MAESTROOrchestrator:
    controller = object.__new__(MAESTROOrchestrator)
    controller._reliability = PredictionReliabilityLedger()
    controller._logger = _SilentLogger()
    return controller


def _result_for_scoring() -> MeasurementResult:
    return MeasurementResult(
        "act", "Observed.", "source", None, None, 3, True, metrics={"delta": "5.0"}
    )


def test_scalar_uncertainty_is_recorded_as_descriptive_and_never_graded():
    controller = _scoring_controller()
    turn = SimpleNamespace(
        prediction=StatePrediction(True, {"delta": 1.0}, 0.5, (), request_id="q", model_version="m"),
        session_id="s",
    )
    action = EvidenceAction("act", "Assay.", 1.0, ("h1", "h2"), prediction_readout="delta")
    controller._score_prediction(turn, action, _result_for_scoring())
    entry = controller._reliability.records[-1]
    assert entry.interval is None
    assert entry.descriptive_interval == (0.5, 1.5)
    assert entry.interval_hit is None
    summary = controller._reliability.summarize("m", "delta")
    assert summary.miss_rate is None


def test_a_calibrated_interval_is_graded_for_coverage():
    controller = _scoring_controller()
    turn = SimpleNamespace(
        prediction=StatePrediction(
            True, {"delta": 1.0}, None, (),
            intervals={"delta": Interval(0.5, 1.5, kind=IntervalKind.CALIBRATED, level=0.9, basis="held-out residuals")},
            request_id="q", model_version="m",
        ),
        session_id="s",
    )
    action = EvidenceAction("act", "Assay.", 1.0, ("h1", "h2"), prediction_readout="delta")
    controller._score_prediction(turn, action, _result_for_scoring())
    entry = controller._reliability.records[-1]
    assert entry.interval == (0.5, 1.5)
    assert entry.interval_hit is False
