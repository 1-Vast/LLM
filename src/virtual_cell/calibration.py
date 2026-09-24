"""Calibration scoring and the world-model exit conditions.

File summary
- Path: src/virtual_cell/calibration.py
- Purpose: score prediction intervals and probabilities against real values so
  calibration is judged before accuracy, as the reference design requires.
- Core points:
  - Reports interval coverage, mean width, Brier and log score.
  - Stratifies by mode, dose and time, where extrapolation failures hide.
  - Implements the pre-registered exit conditions for withdrawing a model.
- Interfaces: `CalibrationPair`, `CalibrationReport`, `score`, `stratify`,
  `compare_models`, `evaluate_exit_conditions`.
- Depends on: src/virtual_cell/interface.py
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite, log
from typing import Callable, Mapping, Sequence


@dataclass(frozen=True)
class CalibrationPair:
    """One declared prediction scored against the real value that arrived."""

    predicted: float
    low: float
    high: float
    observed: float
    strata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CalibrationReport:
    """Calibration, not accuracy: does the stated uncertainty match reality?"""

    pairs: int
    interval_coverage: float | None
    mean_interval_width: float | None
    mean_absolute_error: float | None
    brier_score: float | None = None
    log_score: float | None = None
    nominal_level: float | None = None

    @property
    def enough_pairs(self) -> bool:
        return self.pairs >= 5

    @property
    def under_confident(self) -> bool:
        return (
            self.interval_coverage is not None
            and self.nominal_level is not None
            and self.interval_coverage > self.nominal_level + 0.15
        )

    @property
    def over_confident(self) -> bool:
        return (
            self.interval_coverage is not None
            and self.nominal_level is not None
            and self.interval_coverage < self.nominal_level - 0.15
        )


def brier_score(probability: float, outcome: float) -> float:
    """Squared error of a declared probability against a 0/1 outcome."""

    return (probability - outcome) ** 2


def log_score(probability: float, outcome: float, *, epsilon: float = 1e-6) -> float:
    """Logarithmic score; clipped so a confident miss cannot produce infinity."""

    clamped = min(max(probability, epsilon), 1.0 - epsilon)
    if outcome >= 0.5:
        return -log(clamped)
    return -log(1.0 - clamped)


DEFAULT_NOMINAL_LEVEL = 0.9


def score(
    pairs: Sequence[CalibrationPair],
    *,
    probability_of: Callable[[CalibrationPair], float] | None = None,
    nominal_level: float = DEFAULT_NOMINAL_LEVEL,
) -> CalibrationReport:
    """Score a set of pairs; returns an empty report when nothing is scorable."""

    scorable = [
        pair
        for pair in pairs
        if all(isfinite(float(value)) for value in (pair.predicted, pair.low, pair.high, pair.observed))
    ]
    if not scorable:
        return CalibrationReport(0, None, None, None)
    hits = sum(1 for pair in scorable if pair.low <= pair.observed <= pair.high)
    width = sum(pair.high - pair.low for pair in scorable) / len(scorable)
    error = sum(abs(pair.predicted - pair.observed) for pair in scorable) / len(scorable)
    brier_values: list[float] = []
    log_values: list[float] = []
    if probability_of is not None:
        for pair in scorable:
            probability = float(probability_of(pair))
            if isfinite(probability):
                brier_values.append(brier_score(probability, 1.0 if pair.observed >= 0.5 else 0.0))
                log_values.append(log_score(probability, 1.0 if pair.observed >= 0.5 else 0.0))
    return CalibrationReport(
        pairs=len(scorable),
        interval_coverage=hits / len(scorable),
        mean_interval_width=width,
        mean_absolute_error=error,
        brier_score=(sum(brier_values) / len(brier_values)) if brier_values else None,
        log_score=(sum(log_values) / len(log_values)) if log_values else None,
        nominal_level=nominal_level,
    )


def stratify(pairs: Sequence[CalibrationPair], key: str) -> dict[str, CalibrationReport]:
    """Stratify by mode, dose bucket or time, where extrapolation failures hide."""

    buckets: dict[str, list[CalibrationPair]] = {}
    for pair in pairs:
        buckets.setdefault(str(pair.strata.get(key, "unspecified")), []).append(pair)
    return {name: score(items) for name, items in sorted(buckets.items())}


def compare_models(
    candidate: Mapping[str, CalibrationReport],
    reference: Mapping[str, CalibrationReport],
) -> dict[str, str]:
    """Per-stratum comparison; used by the module-swap ablation."""

    verdicts: dict[str, str] = {}
    for name in sorted(set(candidate) | set(reference)):
        left = candidate.get(name)
        right = reference.get(name)
        if left is None or right is None or not left.enough_pairs or not right.enough_pairs:
            verdicts[name] = "insufficient_pairs"
            continue
        if left.interval_coverage is None or right.interval_coverage is None:
            verdicts[name] = "unscorable"
            continue
        if left.over_confident and not right.over_confident:
            verdicts[name] = "candidate_over_confident"
        elif right.over_confident and not left.over_confident:
            verdicts[name] = "reference_over_confident"
        elif left.mean_absolute_error is not None and right.mean_absolute_error is not None:
            verdicts[name] = (
                "candidate_better" if left.mean_absolute_error < right.mean_absolute_error else "reference_better"
            )
        else:
            verdicts[name] = "unscorable"
    return verdicts


def evaluate_exit_conditions(
    report: CalibrationReport,
    *,
    minimum_pairs: int = 10,
    maximum_over_confidence_gap: float = 0.20,
) -> tuple[str, ...]:
    """Return the pre-registered reasons for withdrawing a world model.

    Conditions are evaluated in the same order for every model; they are never
    tuned after seeing which model wins.
    """

    reasons: list[str] = []
    if report.pairs < minimum_pairs:
        reasons.append("insufficient_scored_predictions")
        return tuple(reasons)
    if report.interval_coverage is None or report.nominal_level is None:
        reasons.append("no_interval_coverage")
        return tuple(reasons)
    gap = report.nominal_level - report.interval_coverage
    if gap > maximum_over_confidence_gap:
        reasons.append("over_confident_intervals")
    if report.over_confident:
        reasons.append("interval_coverage_below_nominal")
    return tuple(reasons)


@dataclass(frozen=True)
class ScaleCalibration:
    """A fitted rescaling of a predictor's output, with the domain it was fitted on.

    A model can point in the right direction and still be the wrong size. When
    it is, the useful correction is one number, and the important thing about
    that number is where it came from: a scale fitted on one endpoint, context
    and split says nothing about another.

    ``scale`` is the least-squares multiplier of the predicted vector onto the
    observed one. A value far below 1 means the prediction should be shrunk:
    most of its length does not lie along the truth, so using it at face value
    costs more squared error than predicting no change.
    """

    scale: float
    endpoint: str
    context_identifier: str | None
    fitted_on: str
    independent_units: int
    residual_scale: float | None = None
    limitations: tuple[str, ...] = ()
    # What the scale was fitted *through*. A scale fitted on one checkpoint,
    # input schema or control protocol says nothing about another, so each
    # declared binding must be matched exactly by the query it is applied to.
    model_version: str | None = None
    input_schema: str | None = None
    control_protocol: str | None = None
    development_partition_sha256: str | None = None

    @property
    def shrinks(self) -> bool:
        return self.scale < 1.0

    def binding_mismatches(
        self,
        *,
        endpoint: str,
        context_identifier: str | None,
        model_version: str | None = None,
        input_schema: str | None = None,
        control_protocol: str | None = None,
    ) -> tuple[str, ...]:
        """Every binding the query fails, named; a declared binding left unstated fails."""

        problems: list[str] = []
        if endpoint != self.endpoint:
            problems.append("endpoint_mismatch")
        if self.context_identifier is not None and context_identifier != self.context_identifier:
            problems.append("context_mismatch")
        for name, declared, offered in (
            ("model_version", self.model_version, model_version),
            ("input_schema", self.input_schema, input_schema),
            ("control_protocol", self.control_protocol, control_protocol),
        ):
            if declared is None:
                continue
            if offered is None:
                problems.append(f"{name}_unstated")
            elif offered != declared:
                problems.append(f"{name}_mismatch")
        return tuple(problems)

    def applies_to(
        self,
        *,
        endpoint: str,
        context_identifier: str | None,
        model_version: str | None = None,
        input_schema: str | None = None,
        control_protocol: str | None = None,
    ) -> bool:
        """Whether this calibration may be used for the requested query at all."""

        return not self.binding_mismatches(
            endpoint=endpoint,
            context_identifier=context_identifier,
            model_version=model_version,
            input_schema=input_schema,
            control_protocol=control_protocol,
        )

    def apply(
        self,
        values: Sequence[float],
        *,
        endpoint: str,
        context_identifier: str | None,
        model_version: str | None = None,
        input_schema: str | None = None,
        control_protocol: str | None = None,
    ) -> tuple[float, ...]:
        """Rescale a prediction, refusing outside the domain the scale was fitted on."""

        problems = self.binding_mismatches(
            endpoint=endpoint,
            context_identifier=context_identifier,
            model_version=model_version,
            input_schema=input_schema,
            control_protocol=control_protocol,
        )
        if problems:
            raise ValueError(
                f"Scale calibration for '{self.endpoint}' does not apply to "
                f"'{endpoint}' in context '{context_identifier}': {', '.join(problems)}."
            )
        return tuple(self.scale * float(value) for value in values)


def fit_scale(
    observed: Sequence[Sequence[float]],
    predicted: Sequence[Sequence[float]],
    *,
    endpoint: str,
    context_identifier: str | None,
    fitted_on: str,
    independent_units: int,
    model_version: str | None = None,
    input_schema: str | None = None,
    control_protocol: str | None = None,
    development_partition_sha256: str | None = None,
) -> ScaleCalibration:
    """Least-squares multiplier taking predictions onto observations.

    The caller is responsible for passing development data only. This function
    cannot tell development from test, so the ``fitted_on`` string is required:
    a calibration whose provenance is not stated cannot be audited. The optional
    bindings make the scale refuse any query that differs in checkpoint, input
    schema or control protocol from the ones it was fitted through.
    """

    if len(observed) != len(predicted):
        raise ValueError("Observed and predicted must be paired.")
    if not observed:
        raise ValueError("A scale needs at least one paired observation.")
    numerator = 0.0
    denominator = 0.0
    for truth, guess in zip(observed, predicted):
        if len(truth) != len(guess):
            raise ValueError("Paired vectors must have the same length.")
        numerator += sum(float(a) * float(b) for a, b in zip(truth, guess))
        denominator += sum(float(b) * float(b) for b in guess)
    if denominator == 0.0:
        raise ValueError("Predictions are identically zero; no scale is identifiable.")
    return ScaleCalibration(
        scale=numerator / denominator,
        endpoint=endpoint,
        context_identifier=context_identifier,
        fitted_on=fitted_on,
        independent_units=independent_units,
        model_version=model_version,
        input_schema=input_schema,
        control_protocol=control_protocol,
        development_partition_sha256=development_partition_sha256,
        limitations=(
            "A scale corrects magnitude only. It does not make an uncalibrated prediction "
            "a measurement, and it carries no coverage claim.",
        ),
    )
