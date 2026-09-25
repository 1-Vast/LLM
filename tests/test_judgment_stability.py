"""Reproducibility of a judgment source is measurable before any outcome exists.

File summary
- Path: tests/test_judgment_stability.py
- Purpose: pin the boundary that a source which answers differently each time loses influence
  without waiting for a biological outcome, and that not having asked twice is treated as the
  absence of evidence it is, rather than as evidence of unreliability.
- Core points:
  - Agreement is the unbiased collision probability and is computed on the decision-relevant
    value, so two yes answers at different confidences agree.
  - A measured unstable scope is suppressed; an unmeasured one speaks, labelled.
  - Repeated answers aggregate by mean for a yes/no question and by mode for a choice.
- Interfaces: pytest test functions
- Depends on: maestro.stability, agent.decision_critic
"""
from __future__ import annotations

import pytest

from agent import typesafe as typesafe_module
from agent.decision_critic import TypedDecisionCritic
from agent.typesafe import JevEvaluation, TypedAnswer, TypedQuestion
from maestro.judgment import JudgmentLedger, JudgmentScope
from maestro.models import (
    DevelopmentAction,
    EvidenceAction,
    MechanismContrast,
    MechanismHypothesis,
)
from maestro.stability import (
    RELIABLE_REPEATS,
    RepeatedJudgment,
    StabilityLedger,
    StabilityVerdict,
    canonical_value,
    effective_weight,
)

RANKING = JudgmentScope.ACTION_RANKING
CRITIQUE = JudgmentScope.PLAN_CRITIQUE


def _repeat(values, *, scope=RANKING, kind="choice", probabilities=()):
    return RepeatedJudgment(
        question_id="best_separating_action",
        scope=scope,
        kind=kind,
        model_version="jev-1.13",
        state_digest="digest",
        values=tuple(values),
        probabilities=tuple(probabilities),
    )


class SequenceJevClient:
    """Serves one recorded answer set per call, so repeats can disagree on purpose."""

    def __init__(self, answer_sets, *, model="jev-1.13"):
        self._answer_sets = list(answer_sets)
        self.model = model
        self.calls = 0

    def evaluate(self, state, questions):
        answers = self._answer_sets[min(self.calls, len(self._answer_sets) - 1)]
        self.calls += 1
        parsed = {
            question.identifier: TypedAnswer.parse(question, answers[question.identifier])
            for question in questions
            if question.identifier in answers
        }
        return JevEvaluation(self.model, typesafe_module.state_digest(state), parsed)


def _contrast(planned: str = "viability") -> MechanismContrast:
    return MechanismContrast(
        identifier="contrast",
        hypotheses=(
            MechanismHypothesis("h1", "First.", DevelopmentAction.CONTINUE, "a"),
            MechanismHypothesis("h2", "Second.", DevelopmentAction.REVISE_INTERVENTION, "b"),
        ),
        differing_assumptions=("which one holds",),
        plan=EvidenceAction(planned, "Planned action.", 1.0, ("h1", "h2")),
        outcome_categories=("x", "y"),
    )


def _actions():
    return (
        EvidenceAction("viability", "Planned action.", 1.0, ("h1", "h2")),
        EvidenceAction("activity", "Rival action.", 1.0, ("h1", "h2")),
    )


# --------------------------------------------------------------------------------------
# Measurement
# --------------------------------------------------------------------------------------


def test_agreement_is_the_chance_that_asking_again_returns_the_same_answer():
    """The unbiased collision estimator, checked against its closed form on exact counts."""

    # Four calls, three of one answer and one of another: agreeing pairs 3*2=6 of 4*3=12.
    assert _repeat(("a", "a", "a", "b")).agreement == pytest.approx(0.5)
    # Perfect agreement and total disagreement are the two ends.
    assert _repeat(("a", "a", "a", "a")).agreement == pytest.approx(1.0)
    assert _repeat(("a", "b", "c", "d")).agreement == pytest.approx(0.0)
    # One observation is not a measurement of a rate.
    assert _repeat(("a",)).agreement is None
    assert _repeat(("a",)).verdict is StabilityVerdict.UNMEASURED


def test_agreement_is_judged_on_the_value_that_can_change_a_decision():
    """Two confident yes answers agree; comparing raw floats would call every source unstable."""

    assert canonical_value("noul", True) == canonical_value("noul", True)
    assert canonical_value("score", 3) == canonical_value("score", 3.0)
    assert canonical_value("choice", "rna_low") != canonical_value("choice", "rna_high")
    same = _repeat(("true", "true", "true"), kind="noul", probabilities=(0.94, 0.77, 0.98))
    assert same.agreement == pytest.approx(1.0)
    # The spread is still reported, because it is the Brier penalty repetition can remove.
    assert same.probability_variance == pytest.approx(0.0124333, abs=1e-6)
    assert same.averaging_gain(4) == pytest.approx(same.probability_variance * 0.75, abs=1e-6)


def test_the_measured_flip_from_the_live_run_reads_as_unstable():
    """The 2026-09-25 observation: one ranking question, two identical calls, two answers."""

    observed = _repeat(("proximal_activity", "orthogonal_rescue"))
    assert observed.agreement == pytest.approx(0.0)
    assert observed.flip_rate == pytest.approx(1.0)
    assert observed.verdict is StabilityVerdict.UNSTABLE


def test_enough_agreeing_repeats_earn_the_right_to_decide():
    ledger = StabilityLedger()
    assert not ledger.may_decide(RANKING, "jev-1.13"), "an unmeasured ranking has earned nothing"
    ledger.record(_repeat(("a",) * RELIABLE_REPEATS))
    summary = ledger.summarize(RANKING, "jev-1.13")
    assert summary.verdict is StabilityVerdict.STABLE
    assert summary.weight == pytest.approx(1.0)
    assert summary.may_decide


def test_too_few_repeats_are_reported_as_insufficient_rather_than_stable():
    """Three agreeing calls do not establish stability; the verdict says so instead of rounding up."""

    ledger = StabilityLedger()
    ledger.record(_repeat(("a", "a", "a")))
    summary = ledger.summarize(RANKING, "jev-1.13")
    assert summary.agreement == pytest.approx(1.0)
    assert summary.verdict is StabilityVerdict.INSUFFICIENT
    assert not summary.may_decide


def test_an_unstable_scope_is_revoked_with_no_outcome_and_the_brier_ledger_still_silent():
    """The point of the whole construct: revocation that does not wait for a measurement."""

    stability, calibration = StabilityLedger(), JudgmentLedger()
    stability.record(_repeat(("a", "b", "a", "b", "a", "b", "a", "b")))
    assert stability.is_revoked(RANKING, "jev-1.13")
    assert stability.weight(RANKING, "jev-1.13") == 0.0
    # The Brier ledger has been given nothing to grade and correctly claims nothing.
    assert not calibration.is_revoked(RANKING, "jev-1.13")
    assert calibration.summarize(RANKING, "jev-1.13").provisional
    assert effective_weight(calibration.weight(RANKING, "jev-1.13"), 0.0) == 0.0


def test_effective_weight_is_the_weaker_test_and_refuses_a_bad_fraction():
    assert effective_weight(1.0, 0.4) == pytest.approx(0.4)
    assert effective_weight(0.3, 0.9) == pytest.approx(0.3)
    for bad in (-0.1, 1.5, float("nan")):
        with pytest.raises(ValueError):
            effective_weight(1.0, bad)


# --------------------------------------------------------------------------------------
# What the critic does with it
# --------------------------------------------------------------------------------------


def test_an_unchecked_preference_is_still_said_and_said_as_unchecked():
    """Absence of evidence is named, not silently converted into suppression."""

    client = SequenceJevClient([{
        "best_separating_action": {"value": "activity", "probabilities": {"activity": 0.9}},
    }])
    outcome = TypedDecisionCritic(client).review_plan(_contrast(), _actions())
    assert client.calls == 1
    ranking = [item for item in outcome.findings if "activity" in item]
    assert ranking, "the preference must still reach the planner"
    assert "Reproducibility unchecked" in ranking[0]
    assert not outcome.suppressed_by_revocation


def test_a_measured_flip_suppresses_the_preference_within_one_review():
    """Two calls, two answers: the ranking is withheld and the disagreement is on the record."""

    client = SequenceJevClient([
        {"best_separating_action": {"value": "activity", "probabilities": {"activity": 0.9}}},
        {"best_separating_action": {"value": "viability", "probabilities": {"viability": 0.9}}},
    ])
    critic = TypedDecisionCritic(client)
    outcome = critic.review_plan(_contrast(), _actions(), repeats=2)

    assert client.calls == 2
    assert outcome.repeats == 2
    assert not [item for item in outcome.findings if "prefers the registered action" in item]
    assert outcome.suppressed_by_revocation
    assert critic.stability.is_revoked(RANKING, "jev-1.13")
    # The judgment is still recorded: withheld influence, not withheld history.
    assert [item for item in outcome.judgments if item.question_id == "best_separating_action"]
    rows = [row for row in outcome.stability if row.get("question_id") == "best_separating_action"]
    assert rows and rows[0]["flip_rate"] == pytest.approx(1.0)


def test_repeated_yes_no_answers_are_averaged_and_choices_take_the_mode():
    """The averaging law decides the aggregation: means for probabilities, modes for labels."""

    sets = [
        {"decision_separation": {"value": True, "probability": 0.9},
         "best_separating_action": {"value": "activity", "probabilities": {"activity": 0.8}}},
        {"decision_separation": {"value": True, "probability": 0.7},
         "best_separating_action": {"value": "activity", "probabilities": {"activity": 0.6}}},
        {"decision_separation": {"value": True, "probability": 0.8},
         "best_separating_action": {"value": "viability", "probabilities": {"viability": 0.6}}},
    ]
    critic = TypedDecisionCritic(SequenceJevClient(sets))
    outcome = critic.review_plan(_contrast(), _actions(), repeats=3)

    separation = next(i for i in outcome.judgments if i.question_id == "decision_separation")
    assert separation.value is True
    assert separation.probability == pytest.approx(0.8)  # the mean of 0.9, 0.7, 0.8
    ranking = next(i for i in outcome.judgments if i.question_id == "best_separating_action")
    assert ranking.value == "activity"  # two of three calls, not the last one


def test_one_evaluation_behaves_exactly_as_before():
    """The default costs one call and records no stability, so existing callers are unchanged."""

    client = SequenceJevClient([{"decision_separation": {"value": True, "probability": 0.9}}])
    critic = TypedDecisionCritic(client)
    outcome = critic.review_plan(_contrast(), _actions())
    assert client.calls == 1 and outcome.repeats == 1
    assert critic.stability.records == ()
    assert not outcome.suppressed_by_revocation


def test_repeats_must_be_at_least_one():
    critic = TypedDecisionCritic(SequenceJevClient([{}]))
    with pytest.raises(ValueError):
        critic.review_plan(_contrast(), _actions(), repeats=0)
