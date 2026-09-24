"""Test directed repair of a mechanism contrast and deferral.

File summary
- Path: tests/test_mechanism_contrast_repair.py
- Purpose: Test directed repair of a mechanism contrast and explicit deferral.
- Core points:
  - `repair_contrast` returns a catalog-bounded edit or an explicit deferral.
  - Confirms `observation_scope` limits an update to its interpretation premise.
- Interfaces: `test_*` functions
- Depends on: maestro, virtual_cell
"""
from maestro import (
    DevelopmentAction,
    EvidenceAction,
    EvidenceActionKind,
    EvidenceScope,
    FunctionalInterventionProfile,
    MAESTROAgent,
    MeasurementStatus,
    MechanismHypothesis,
    NonDiscriminabilityReason,
    RepairKind,
)
from virtual_cell import StatePrediction


def _hypotheses():
    return (
        MechanismHypothesis(
            "functional_gap", "Functional perturbation was incomplete.",
            DevelopmentAction.REVISE_INTERVENTION,
        ),
        MechanismHypothesis(
            "mode_mismatch", "Intervention modes are not equivalent.",
            DevelopmentAction.CHANGE_INTERVENTION_MODE,
        ),
    )


def test_missing_functional_precondition_repairs_with_registered_measurement():
    agent = MAESTROAgent()
    main_action = EvidenceAction(
        "survival", "Measure survival", 5.0, ("functional_gap", "mode_mismatch"),
        prerequisites=("functional:target_activity",),
    )
    functional_measurement = EvidenceAction(
        "target_activity", "Measure target activity", 2.0, ("functional_gap",),
        kind=EvidenceActionKind.FUNCTIONAL_MEASUREMENT,
    )
    contrast = agent.construct_contrast(
        "implementation-vs-mode", _hypotheses(), ("target activity",), (main_action,)
    )
    assert contrast is not None

    check = agent.check_contrast(
        contrast, FunctionalInterventionProfile(mode="inhibition")
    )

    assert NonDiscriminabilityReason.MISSING_FUNCTIONAL_MEASUREMENT in check.reasons
    assert not check.ready_for_mechanism_update
    assert agent.observation_scope(check) is EvidenceScope.INTERVENTION_IMPLEMENTATION
    repair = agent.repair_contrast(contrast, check, (functional_measurement,))
    assert repair.kind is RepairKind.ADD_FUNCTIONAL_MEASUREMENT
    assert repair.replacement_action is functional_measurement


def test_measured_precondition_allows_mechanism_update():
    agent = MAESTROAgent()
    action = EvidenceAction(
        "survival", "Measure survival", 5.0, ("functional_gap", "mode_mismatch"),
        prerequisites=("functional:target_activity",),
        expected_outcomes={"functional_gap": "survival_restored", "mode_mismatch": "survival_divergent"},
    )
    contrast = agent.construct_contrast("contrast", _hypotheses(), (), (action,))
    assert contrast is not None

    check = agent.check_contrast(
        contrast,
        FunctionalInterventionProfile(
            mode="inhibition",
            functional_states={"target_activity": MeasurementStatus.MEASURED},
        ),
    )

    assert check.ready_for_mechanism_update


def test_unsupported_virtual_cell_prediction_is_removed_from_the_plan():
    agent = MAESTROAgent()
    model_action = EvidenceAction(
        "model_guided", "Model-guided readout", 2.0, ("functional_gap", "mode_mismatch"),
        requires_virtual_prediction=True,
    )
    measured_action = EvidenceAction(
        "measured", "Measured readout", 3.0, ("functional_gap", "mode_mismatch"),
    )
    contrast = agent.construct_contrast("contrast", _hypotheses(), (), (model_action,))
    assert contrast is not None
    check = agent.check_contrast(
        contrast,
        FunctionalInterventionProfile(mode="inhibition"),
        StatePrediction(False, None, None, ("Out of domain",)),
    )

    repair = agent.repair_contrast(contrast, check, (measured_action,))

    assert NonDiscriminabilityReason.MODEL_UNSUPPORTED in check.reasons
    assert not check.ready_for_mechanism_update
    assert repair.kind is RepairKind.REMOVE_MODEL_DEPENDENCE
    assert repair.replacement_action is measured_action


def test_missing_development_actions_do_not_count_as_a_decision_separation():
    agent = MAESTROAgent()
    hypotheses = (
        MechanismHypothesis("a", "A"),
        MechanismHypothesis("b", "B"),
    )
    action = EvidenceAction("assay", "Assay", 1.0, ("a", "b"))
    contrast = agent.construct_contrast("contrast", hypotheses, (), (action,))
    assert contrast is not None

    check = agent.check_contrast(contrast, FunctionalInterventionProfile(mode="inhibition"))

    assert NonDiscriminabilityReason.DECISION_NOT_SEPARATED in check.reasons
    assert not check.ready_for_mechanism_update
