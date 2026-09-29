"""Closing the loop: decision-value action selection and append-only case updates.

File summary
- Path: src/maestro/case_update.py
- Purpose: connect the case memory to action selection and to the append-only update that follows
  a real result, reusing the existing MAESTRO decision-value machinery rather than duplicating it.
- Core points:
  - Actions are ranked by expected terminal decision value with hypothesis discrimination, cost,
    detection power, prerequisite cost, ambiguity risk and model/adaptation uncertainty as named
    terms - never by predicted magnitude, embedding similarity or case count alone.
  - The recommendation is branching: each possible reading maps to its evidence update, hypothesis
    update and next action; an ambiguous reading routes to an orthogonal assay or QC action; an
    invalid experiment updates no biological hypothesis.
  - Result qualification keeps `reliable_but_inconclusive`, `unreliable`, `not_measured`,
    `negative` and `qualified` apart. Only a qualified real measurement updates hypotheses, through
    the registered rules; a QC failure updates nothing.
  - `ingest_result` supersedes the episode (never edits it), records the hypothesis update and
    grades the forecast the system gave the realised reading as a calibration entry.
- Interfaces: `OutcomeQualification`, `qualify_result`, `rank_actions_by_decision_value`,
  `ActionRanking`, `branching_interpretation_plan`, `ingest_result`, `IngestResult`
- Depends on: maestro.case_memory, maestro.acquisition (decision-value helpers), maestro.directional
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

from .acquisition import OutcomeForecast, expected_terminal_decision_value
from .case_memory import (
    BranchingPlan,
    CalibrationEntry,
    CandidateAction,
    EpisodeStore,
    HypothesisUpdate,
    RealMeasurement,
    ScientificEpisode,
    ScientificMeasurementStatus,
)


class OutcomeQualification(str, Enum):
    """What one real result is allowed to mean. Distinct states, never collapsed."""

    QUALIFIED = "qualified"
    RELIABLE_BUT_INCONCLUSIVE = "reliable_but_inconclusive"
    NEGATIVE = "negative"
    UNRELIABLE = "unreliable"
    NOT_MEASURED = "not_measured"


def qualify_result(measurement: RealMeasurement, *, qc_passed: bool, detected: bool | None,
                   eliminated: Sequence[str] = ()) -> OutcomeQualification:
    """The qualification of one real result from its status, QC and what it eliminated."""

    if measurement.status in (ScientificMeasurementStatus.NOT_PLANNED,
                              ScientificMeasurementStatus.PLANNED_MISSING):
        return OutcomeQualification.NOT_MEASURED
    if measurement.status is ScientificMeasurementStatus.QC_FAILED or not qc_passed:
        return OutcomeQualification.UNRELIABLE
    if measurement.status is ScientificMeasurementStatus.UNDETECTED or detected is False:
        return OutcomeQualification.NEGATIVE
    if measurement.status is ScientificMeasurementStatus.QUALIFIED and eliminated:
        return OutcomeQualification.QUALIFIED
    return OutcomeQualification.RELIABLE_BUT_INCONCLUSIVE


@dataclass(frozen=True)
class ActionRanking:
    action_id: str
    expected_terminal_decision_value: float
    hypothesis_discrimination: float
    measurement_cost: float
    detection_power: float | None
    prerequisite_cost: float
    ambiguity_risk: float
    model_uncertainty: float
    adaptation_uncertainty: float
    net_value: float
    admissible: bool
    reason: str


def _discrimination(forecast: OutcomeForecast) -> float:
    """Log-likelihood spread between hypothesis branches of one forecast (nats)."""

    import math

    if forecast.refusal is not None or len(forecast.branches) < 2:
        return 0.0
    best = []
    for branch in forecast.branches:
        if branch.probabilities:
            best.append(max(branch.probabilities.values()))
    if len(best) < 2 or min(best) <= 0:
        return 0.0
    return abs(math.log(best[0]) - math.log(best[1]))


def rank_actions_by_decision_value(
    candidates: Sequence[str],
    actions: Sequence[CandidateAction],
    forecasts: Mapping[str, OutcomeForecast],
    consequences: Mapping[str, frozenset],
    *,
    prior: Mapping[str, float] | None = None,
    wrong_decision_loss: float = 2.0,
    defer_loss: float = 1.0,
    price_per_well: float = 0.02,
    prerequisite_costs: Mapping[str, float] | None = None,
    adaptation_uncertainties: Mapping[str, float] | None = None,
) -> tuple[ActionRanking, ...]:
    """Rank candidate actions by net expected terminal decision value, with named terms.

    Uses `maestro.acquisition.expected_terminal_decision_value` for the value term; every other
    term is reported, not folded away, so the ranking can be audited term by term.
    """

    prerequisite_costs = prerequisite_costs or {}
    adaptation_uncertainties = adaptation_uncertainties or {}
    rankings: list[ActionRanking] = []
    for action in actions:
        forecast = forecasts.get(action.action_id)
        if forecast is None or forecast.refusal is not None:
            rankings.append(ActionRanking(
                action.action_id, 0.0, 0.0, action.cost_wells * price_per_well,
                action.detection_power, float(prerequisite_costs.get(action.action_id, 0.0)),
                1.0, 1.0, float(adaptation_uncertainties.get(action.action_id, 0.0)),
                -1e9, False,
                (forecast.refusal if forecast is not None else "no_forecast")))
            continue
        value = expected_terminal_decision_value(
            candidates, forecast, consequences, prior=prior,
            wrong_decision_loss=wrong_decision_loss, defer_loss=defer_loss,
            measurement_cost=action.cost_wells * price_per_well)
        discrimination = _discrimination(forecast)
        ambiguity_risk = float(forecast.branches[0].probabilities.get("ambiguous", 0.0)
                               + forecast.branches[0].probabilities.get("unresolved", 0.0)) \
            if forecast.branches else 1.0
        low_support = min((b.support for b in forecast.branches), default=0)
        model_uncertainty = 1.0 if low_support < 6 else 0.0
        pre_cost = float(prerequisite_costs.get(action.action_id, 0.0))
        adapt_unc = float(adaptation_uncertainties.get(action.action_id, 0.0))
        net = value.net_value - pre_cost - 0.5 * model_uncertainty - 0.5 * adapt_unc
        rankings.append(ActionRanking(
            action.action_id, value.expected_value, discrimination,
            action.cost_wells * price_per_well, action.detection_power, pre_cost,
            ambiguity_risk, model_uncertainty, adapt_unc, net, True, ""))
    rankings.sort(key=lambda r: (-r.net_value, r.action_id))
    return tuple(rankings)


def branching_interpretation_plan(
    action: CandidateAction,
    outcome_labels: Sequence[str],
    *,
    orthogonal_action: str | None = None,
) -> BranchingPlan:
    """The registered per-outcome plan of one action.

    Every decisive reading maps to `update:<label>` (update evidence, update hypotheses, choose the
    registered follow-up). Ambiguous routes to an orthogonal assay or QC action; an invalid
    experiment updates no biological hypothesis.
    """

    on_outcome = {label: f"update:{label}" for label in outcome_labels}
    on_ambiguous = (f"orthogonal:{orthogonal_action}" if orthogonal_action
                    else "orthogonal_assay_or_qc_action")
    return BranchingPlan(action.action_id, on_outcome, on_ambiguous,
                         "invalid:no_biological_hypothesis_update")


@dataclass(frozen=True)
class IngestResult:
    episode: ScientificEpisode
    qualification: OutcomeQualification
    eliminated: tuple[str, ...]
    calibration: CalibrationEntry | None


def ingest_result(
    store: EpisodeStore,
    episode: ScientificEpisode,
    measurement: RealMeasurement,
    *,
    qc_passed: bool,
    detected: bool | None,
    contrast: tuple[str, str],
    eliminated: Sequence[str] = (),
    forecast_probability: float | None = None,
    model_version: str = "",
) -> IngestResult:
    """Close the loop for one real result, append-only.

    - not measured / QC failed: no hypothesis update, the episode is not superseded for hypotheses;
    - undetected: recorded as a negative reading, nothing eliminated;
    - qualified: the registered elimination is recorded and the episode gains a new version;
    - the probability the system gave the realised reading is stored as a calibration entry.
    """

    qualification = qualify_result(measurement, qc_passed=qc_passed, detected=detected,
                                   eliminated=eliminated)
    changes: dict = {}
    updates = list(episode.hypothesis_updates)
    eliminated_tuple: tuple[str, ...] = ()
    calibration = None
    if qualification is OutcomeQualification.QUALIFIED:
        eliminated_tuple = tuple(eliminated)
        updates.append(HypothesisUpdate(measurement.action_id, contrast, "real_result",
                                        eliminated_tuple, True, "qualified real measurement"))
    elif qualification in (OutcomeQualification.NEGATIVE, OutcomeQualification.RELIABLE_BUT_INCONCLUSIVE):
        updates.append(HypothesisUpdate(measurement.action_id, contrast, "real_result",
                                        (), False, qualification.value))
    if updates or qualification in (OutcomeQualification.UNRELIABLE, OutcomeQualification.NOT_MEASURED):
        changes["hypothesis_updates"] = tuple(updates)
    if forecast_probability is not None and measurement.outcome_label is not None:
        calibration = CalibrationEntry(model_version, measurement.action_id,
                                       float(forecast_probability),
                                       1.0 if qualification is OutcomeQualification.QUALIFIED else 0.0,
                                       "reading_probability", episode.digest)
        changes["calibration_history"] = tuple(episode.calibration_history) + (calibration,)
    measurements = {m.action_id: m for m in episode.real_measurements}
    measurements[measurement.action_id] = measurement
    changes["real_measurements"] = tuple(measurements.values())
    new_episode = store.supersede(episode, **changes)
    return IngestResult(new_episode, qualification, eliminated_tuple, calibration)
