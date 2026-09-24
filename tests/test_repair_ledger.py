"""Bounded repair loop, cycle detection, and the repair ledger.

File summary
- Path: tests/test_repair_ledger.py
- Purpose: Test the bounded repair loop, cycle detection, and ledger accounting.
- Core points:
  - `RepairController` stops on repetition or no progress; `RepairLedger` records each edit.
  - Adoption is separated from `gap_resolved`, scored only by a later real result.
- Interfaces: `test_*` functions
- Depends on: maestro
"""
from maestro import (
    ContrastCheck,
    EvidenceAction,
    EvidenceActionKind,
    FunctionalInterventionProfile,
    MAESTROAgent,
    MechanismContrast,
    MechanismHypothesis,
    NonDiscriminabilityReason,
    RepairController,
    RepairKind,
    RepairLedger,
)


def _contrast(plan: EvidenceAction | None) -> MechanismContrast:
    return MechanismContrast(
        identifier="contrast",
        hypotheses=(
            MechanismHypothesis("a", "Explanation A."),
            MechanismHypothesis("b", "Explanation B."),
        ),
        differing_assumptions=("implementation",),
        plan=plan,
    )


def _actions() -> tuple[EvidenceAction, ...]:
    return (
        EvidenceAction("functional", "Measure activity.", 1.0, ("a",), kind=EvidenceActionKind.FUNCTIONAL_MEASUREMENT),
        EvidenceAction("comparator", "Compare modes.", 2.0, ("a", "b"), prerequisites=("functional:target_activity",)),
    )


def _profile() -> FunctionalInterventionProfile:
    return FunctionalInterventionProfile(mode="drug", context_identifier="cell-a")


def test_repair_stops_when_the_plan_is_already_ready():
    plan = EvidenceAction("both", "Covers both.", 1.0, ("a", "b"))
    contrast = _contrast(plan)
    check = ContrastCheck(True, True, True, True, (), outcome_separated=True)
    outcome = RepairController(MAESTROAgent()).run(contrast, check, _actions(), _profile())
    assert outcome.stop_reason == "ready"
    assert outcome.records == ()


def test_repair_adopts_the_edit_that_removes_a_failure_and_records_its_expected_gain():
    contrast = _contrast(_actions()[1])
    check = ContrastCheck(
        executable=True,
        prerequisites_satisfied=False,
        discriminable=True,
        decision_separating=True,
        reasons=(NonDiscriminabilityReason.MISSING_FUNCTIONAL_MEASUREMENT,),
        missing_prerequisites=("functional:target_activity",),
    )
    agent = MAESTROAgent()
    outcome = RepairController(agent).run(contrast, check, _actions(), _profile())
    assert outcome.proposal is not None
    assert outcome.proposal.kind is RepairKind.ADD_FUNCTIONAL_MEASUREMENT
    assert outcome.records[0].adopted
    assert outcome.records[0].resolved_reasons == (
        NonDiscriminabilityReason.MISSING_FUNCTIONAL_MEASUREMENT,
    )
    assert outcome.records[0].expected_gain


def test_repair_stops_without_progress_rather_than_repeating_the_same_edit():
    class StuckAgent(MAESTROAgent):
        def check_contrast(self, contrast, profile, prediction=None):  # noqa: D102
            return ContrastCheck(
                executable=True,
                prerequisites_satisfied=False,
                discriminable=True,
                decision_separating=True,
                reasons=(NonDiscriminabilityReason.MISSING_FUNCTIONAL_MEASUREMENT,),
                missing_prerequisites=("functional:target_activity",),
            )

    contrast = _contrast(_actions()[1])
    check = ContrastCheck(
        executable=True,
        prerequisites_satisfied=False,
        discriminable=True,
        decision_separating=True,
        reasons=(NonDiscriminabilityReason.MISSING_FUNCTIONAL_MEASUREMENT,),
    )
    outcome = RepairController(StuckAgent()).run(contrast, check, _actions(), _profile())
    assert outcome.stop_reason == "no_progress"
    assert len(outcome.records) == 1
    assert not outcome.records[0].adopted


def test_repair_detects_a_cycle_between_two_edits():
    """Every edit removes one failure and reintroduces the other, so the loop must stop."""

    class AlternatingAgent(MAESTROAgent):
        def __init__(self):
            self.calls = 0

        def check_contrast(self, contrast, profile, prediction=None):  # noqa: D102
            self.calls += 1
            if self.calls % 2 == 1:
                return ContrastCheck(True, False, True, True, (NonDiscriminabilityReason.MISSING_FUNCTIONAL_MEASUREMENT,))
            return ContrastCheck(True, True, False, True, (NonDiscriminabilityReason.NO_DISCRIMINATING_ACTION,))

    contrast = _contrast(_actions()[1])
    check = ContrastCheck(
        executable=True,
        prerequisites_satisfied=True,
        discriminable=False,
        decision_separating=True,
        reasons=(NonDiscriminabilityReason.NO_DISCRIMINATING_ACTION,),
    )
    outcome = RepairController(AlternatingAgent(), max_attempts=3).run(
        contrast, check, _actions(), _profile()
    )
    assert outcome.stop_reason == "repair_cycle_detected"
    assert [record.kind for record in outcome.records] == [
        RepairKind.CHANGE_READOUT_OR_TIME,
        RepairKind.ADD_FUNCTIONAL_MEASUREMENT,
        RepairKind.CHANGE_READOUT_OR_TIME,
    ]
    assert not outcome.records[-1].adopted


def test_ledger_scores_adopted_repairs_against_real_results():
    ledger = RepairLedger()
    contrast = _contrast(_actions()[1])
    check = ContrastCheck(
        executable=True,
        prerequisites_satisfied=False,
        discriminable=True,
        decision_separating=True,
        reasons=(NonDiscriminabilityReason.MISSING_FUNCTIONAL_MEASUREMENT,),
    )
    outcome = RepairController(MAESTROAgent()).run(
        contrast, check, _actions(), _profile(), ledger=ledger
    )
    assert outcome.records and outcome.records[0].adopted
    assert ledger.success_rate() is None
    ledger.resolve(outcome.records[0].attempt, True)
    assert ledger.scored_count == 1
    assert ledger.success_rate() == 1.0
    assert ledger.adopted_count >= 1
    trajectory = ledger.trajectory()
    assert trajectory[0]["gap_resolved"] is True
    assert trajectory[0]["triggered_by"] == ["missing_functional_measurement"]
    assert trajectory[0]["expected_gain"]


def test_ledger_distinguishes_adopted_from_resolved():
    ledger = RepairLedger()
    class NoRepairAgent(MAESTROAgent):
        def repair_contrast(self, contrast, check, available_actions):  # noqa: D102
            from maestro import RepairProposal, RepairKind

            return RepairProposal(
                kind=RepairKind.DEFER,
                replacement_action=None,
                modified_fields=(),
                triggered_by=tuple(check.reasons),
                interpretation_boundary="No registered repair exists.",
            )

    contrast = _contrast(_actions()[1])
    check = ContrastCheck(
        executable=True,
        prerequisites_satisfied=False,
        discriminable=True,
        decision_separating=True,
        reasons=(NonDiscriminabilityReason.MISSING_PREREQUISITE,),
    )
    outcome = RepairController(NoRepairAgent()).run(
        contrast, check, _actions(), _profile(), ledger=ledger
    )
    assert outcome.stop_reason == "no_registered_repair"
    assert outcome.proposal is not None
    assert ledger.adopted_count == 0
    assert ledger.scored_count == 0


def test_zero_attempts_disables_repair_entirely():
    contrast = _contrast(_actions()[1])
    check = ContrastCheck(
        executable=True,
        prerequisites_satisfied=False,
        discriminable=True,
        decision_separating=True,
        reasons=(NonDiscriminabilityReason.MISSING_FUNCTIONAL_MEASUREMENT,),
    )
    outcome = RepairController(MAESTROAgent(), max_attempts=0).run(
        contrast, check, _actions(), _profile()
    )
    assert outcome.proposal is None
    assert outcome.records == ()
    assert outcome.stop_reason == "max_attempts_reached"
