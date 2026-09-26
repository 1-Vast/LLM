"""Independent counterexamples for cost accounting and planning-only conditioning."""
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import policy as Q

FIRST = ("A549", 6.0, 10000.0)
SECOND = ("A549", 24.0, 10000.0)
OTHER = ("MCF7", 24.0, 10000.0)
UNRESOLVED, ABSENT = Q.P.V.UNRESOLVED, Q.P.V.ABSENT
SETTING = Q.P.Setting("fixture", (FIRST, SECOND, OTHER), (FIRST, SECOND), lambda key: 1.0, 2.0)


def forecast(first, second):
    branches = {}
    for hypothesis, values in (("H1", first), ("H2", second)):
        correct, wrong, absent = values
        good = Q.P.LABELS[0 if hypothesis == "H1" else 1]
        bad = Q.P.LABELS[1 if hypothesis == "H1" else 0]
        branches[hypothesis] = SimpleNamespace(
            p_correct=correct, p_wrong=wrong, value_variance=0.0, wrong_upper95=wrong,
            probabilities={good: correct, bad: wrong, ABSENT: absent,
                           UNRESOLVED: 1.0 - correct - wrong - absent},
            local_support=10, parent_support=0, basis="test", prior_strength=0.0,
        )
    return SimpleNamespace(refusal=None, branches=branches)


def test_first_reading_changes_planning_weights_and_charges_expected_second_assay():
    class Model:
        def forecast(self, action, h1, h2, source=None, observed_label=None):
            if action == FIRST:
                return forecast((0.0, 0.0, 0.9), (0.0, 0.0, 0.1))
            if source is None:
                return forecast((0.0, 0.0, 1.0), (0.0, 0.0, 1.0))
            if observed_label == ABSENT:
                return forecast((1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
            return forecast((0.0, 0.0, 1.0), (0.0, 0.0, 1.0))

    chosen, note = Q.choose(Model(), [FIRST, SECOND], "H1", "H2", [], 2.0, SETTING, 0.1)
    assert chosen == FIRST
    assert note["expected_terminal_correct"] == pytest.approx(0.45)
    assert note["expected_terminal_wrong"] == pytest.approx(0.05)
    assert note["expected_measurements"] == pytest.approx(1.5)
    assert note["expected_net"] == pytest.approx(0.2)
    executed = [{"key": FIRST, "outcome": "undetected", "qc": True}]
    chosen, note = Q.choose(Model(), [SECOND], "H1", "H2", executed, 1.0, SETTING, 0.1)
    assert chosen == SECOND
    assert note["planning_hypothesis_weights"] == pytest.approx({"H1": 0.9, "H2": 0.1})
    assert note["expected_net"] == pytest.approx(0.6)
    # A high price makes the same two-stage experiment unprofitable.
    chosen, _ = Q.choose(Model(), [FIRST, SECOND], "H1", "H2", [], 2.0, SETTING, 0.3)
    assert chosen is None


def test_mixed_unknown_and_nonpositive_continuations_do_not_claim_all_value_is_nonpositive():
    class Model:
        def forecast(self, action, h1, h2, source=None, observed_label=None):
            if action == OTHER:
                return SimpleNamespace(refusal="no_target_references:H2", branches={})
            return forecast((0.0, 0.0, 1.0), (0.0, 0.0, 1.0))

    executed = [{"key": FIRST, "outcome": "undetected", "qc": True}]
    chosen, note = Q.choose(Model(), [SECOND, OTHER], "H1", "H2", executed, 1.0, SETTING, 0.02)
    assert chosen is None
    assert note["reason"] == "value_unknown"
    assert note["unknown_forecasts"] == {Q.P.C.action_id(OTHER): "no_target_references:H2"}


def test_mutually_exclusive_followups_share_the_same_remaining_budget():
    class Model:
        def forecast(self, action, h1, h2, source=None, observed_label=None):
            if action == FIRST:
                return forecast((0.0, 0.0, 0.5), (0.0, 0.0, 0.5))
            if source == FIRST and ((observed_label == ABSENT and action == SECOND)
                                    or (observed_label == UNRESOLVED and action == OTHER)):
                return forecast((0.9, 0.0, 0.1), (0.9, 0.0, 0.1))
            return forecast((0.0, 0.0, 1.0), (0.0, 0.0, 1.0))

    chosen, note = Q.choose(Model(), list(SETTING.keys), "H1", "H2", [], 2.0, SETTING, 0.1)
    assert chosen == FIRST
    assert note["planned_followups"] == {ABSENT: Q.P.C.action_id(SECOND), UNRESOLVED: Q.P.C.action_id(OTHER)}
    assert note["expected_terminal_correct"] == pytest.approx(0.9)
    assert note["expected_terminal_wrong"] == pytest.approx(0.0)
    assert note["expected_measurements"] == pytest.approx(2.0)
    assert note["expected_net"] == pytest.approx(0.7)
