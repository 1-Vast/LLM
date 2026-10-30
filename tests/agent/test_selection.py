"""Budgeted evidence selection and visible uncovered prerequisites."""
from maestro import EvidenceAction, FunctionalInterventionProfile, MAESTROAgent


def test_budgeted_selector_chooses_complementary_actions_when_single_full_action_is_over_budget():
    actions = (
        EvidenceAction("A", "Cover p1 and p2", 2.0, ("p1", "p2")),
        EvidenceAction("B", "Cover p3", 3.0, ("p3",)),
        EvidenceAction("C", "Cover all", 6.0, ("p1", "p2", "p3")),
    )

    plan = MAESTROAgent.select_budgeted_evidence(
        frozenset({"p1", "p2", "p3"}), actions, FunctionalInterventionProfile(mode="inhibition"), 5.0
    )

    assert tuple(action.identifier for action in plan.actions) == ("A", "B")
    assert plan.covered == {"p1", "p2", "p3"}
    assert plan.total_cost == 5.0
