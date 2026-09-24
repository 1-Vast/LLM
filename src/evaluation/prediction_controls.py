"""Module-swap controls for the one prediction input the replay path consumes.

File summary
- Path: src/evaluation/prediction_controls.py
- Purpose: give report section 37's shuffled-prediction row, and the remove-the-model
  control of section 29, a concrete arm on the frozen packages, where the only
  prediction-like input a replay policy reads is each action's declared
  ``prediction_value``.
- Core points:
  - The controls change the ranking input and nothing else: legality, cost, budget and
    the terminal interpretation rule are the unshuffled policy's own.
  - The shuffle is a seeded derangement over a case's available actions, so every
    available action carries a value declared for another one; a case where that moves
    no number is reported by `is_identity`, never assumed away.
  - A declared value is a case author's score, not a trained model. A verdict reached
    with these controls is a verdict about that input only.
- Interfaces: `SHUFFLE_SEED`, `ShuffledPredictionValuePolicy`, `RemovedPredictionValuePolicy`,
  `shuffled_assignment`, `is_identity`, `with_prediction_values`
- Depends on: evaluation.baselines, evaluation.cases
"""
from __future__ import annotations

from dataclasses import replace
from random import Random
from typing import Mapping

from .baselines import MAESTROCorePolicy, PredictionValuePolicy
from .cases import PublicCase, ReplayView

SHUFFLE_SEED = 20260914
_MAX_DRAWS = 10_000


def with_prediction_values(view: ReplayView, values: Mapping[str, float]) -> ReplayView:
    """The same view with some declared prediction values replaced, and nothing else changed."""

    actions = tuple(
        replace(item, prediction_value=float(values[item.action.identifier]))
        if item.action.identifier in values
        else item
        for item in view.case.actions
    )
    return replace(view, case=replace(view.case, actions=actions))


def shuffled_assignment(case: PublicCase, *, seed: int = SHUFFLE_SEED) -> Mapping[str, float]:
    """Reassign the available actions' declared values by a seeded derangement.

    Positions are deranged, so no available action keeps its own slot. Unavailable actions
    keep their values: moving a value onto an action that can never run would change how
    much value the policy can act on, not only where it sits.
    """

    available = sorted(
        (item for item in case.actions if item.available), key=lambda item: item.action.identifier
    )
    values = [item.prediction_value for item in available]
    count = len(values)
    if count < 2:
        return {item.action.identifier: item.prediction_value for item in available}
    rng = Random(f"{seed}:{case.identifier}")
    order = list(range(count))
    for _ in range(_MAX_DRAWS):
        rng.shuffle(order)
        if all(position != index for index, position in enumerate(order)):
            break
    else:  # pragma: no cover - a derangement of two or more positions is found almost surely
        order = list(range(1, count)) + [0]
    return {item.action.identifier: values[order[index]] for index, item in enumerate(available)}


def is_identity(case: PublicCase, *, seed: int = SHUFFLE_SEED) -> bool:
    """Whether the shuffle leaves every available action with the value it declared."""

    original = {item.action.identifier: item.prediction_value for item in case.actions if item.available}
    return dict(shuffled_assignment(case, seed=seed)) == original


class ShuffledPredictionValuePolicy(PredictionValuePolicy):
    """Section 37 row six for the declared-value heuristic: the same policy, values moved.

    If this arm acquires the same evidence and reaches the same verdicts as the
    unshuffled heuristic, the declared values did not change what the policy bought.
    """

    name = "prediction_value_shuffled"

    def __init__(self, *, seed: int = SHUFFLE_SEED):
        self._seed = seed

    def next_action(self, view: ReplayView) -> str | None:
        return super().next_action(with_prediction_values(view, shuffled_assignment(view.case, seed=self._seed)))


class ShuffledPredictionFullSystemPolicy(MAESTROCorePolicy):
    """Section 37 row six for the full system: the same loop, its prediction input deranged.

    The row asks whether the full system's behaviour depends on the prediction input being
    the right way round. On a package whose full system reads no prediction, this arm is
    expected to match the unshuffled one exactly - and that identity is the measurement, not
    a failure of the control: it says the input is not in the loop, which is what audit
    finding F14 claims and what a shuffle over an unread input can show.
    """

    name = "maestro_core_shuffled_predictions"

    def __init__(self, *args, seed: int = SHUFFLE_SEED, **kwargs):
        super().__init__(*args, **kwargs)
        self._seed = seed

    def next_action(self, view: ReplayView) -> str | None:
        return super().next_action(
            with_prediction_values(view, shuffled_assignment(view.case, seed=self._seed))
        )


class RemovedPredictionValuePolicy(PredictionValuePolicy):
    """The remove-the-model control: every declared prediction value reads as zero.

    The ranking then falls back to the heuristic's own tie-break, cheapest first and then
    by identifier, so the arm is the same selector with its prediction input switched off.
    """

    name = "prediction_value_removed"

    def next_action(self, view: ReplayView) -> str | None:
        return super().next_action(
            with_prediction_values(view, {item.action.identifier: 0.0 for item in view.case.actions})
        )
