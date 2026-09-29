"""Hypothesis-conditional, history-aware virtual-cell forecasts (production contract).

File summary
- Path: src/virtual_cell/conditional_forecast.py
- Purpose: the typed forecast object a registered model returns when a `PredictionRequest` asks for
  hypothesis-conditional or history-aware predictions, and the cache identity those forecasts need.
- Core points:
  - `ConditionalStatePrediction` carries one branch per hypothesis with predicted readouts,
    directional effects, intervals, support counts, applicability, calibration status, model
    version, provenance and an explicit abstain reason. A branch a model cannot support is an
    abstention with a named reason, never a fabricated distribution.
  - The object is planning-only: it has no method that touches evidence state, and the validator
    refuses a conditional forecast that claims to be a measurement.
  - `conditional_cache_key` includes the request's intervention, context, readouts, model version,
    backend AND the hypotheses, history, observation context and forecast mode - the four inputs
    the plain `PredictionCache` deliberately strips, because a conditional forecast changes when
    they change. Abstentions are never cached, following the `PredictionCache` precedent.
  - Calibrated and descriptive intervals stay distinct through `interface.Interval`; the validator
    enforces the same rules as `StatePrediction.contract_errors`.
- Interfaces: `HypothesisBranch`, `ConditionalStatePrediction`, `conditional_cache_key`,
  `validate_conditional`, `FORECAST_MODES`
- Depends on: virtual_cell.interface (Interval, PredictionRequest), standard library
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from math import isfinite
from typing import Mapping

from .interface import FORECAST_MODES, Interval, IntervalKind, PredictionRequest

__all__ = ["HypothesisBranch", "ConditionalStatePrediction", "conditional_cache_key",
           "validate_conditional", "FORECAST_MODES", "CALIBRATION_STATUSES"]

CALIBRATION_STATUSES = ("uncalibrated", "calibrated", "not_applicable")


@dataclass(frozen=True)
class HypothesisBranch:
    """The forecast for one hypothesis of one action."""

    hypothesis_id: str
    predicted_readouts: Mapping[str, float] = field(default_factory=dict)
    directional_effects: Mapping[str, int] = field(default_factory=dict)
    """readout -> expected direction (-1, 0, +1); absent when the model does not forecast direction."""
    intervals: Mapping[str, Interval] = field(default_factory=dict)
    support: int = 0
    abstain_reason: str | None = None


@dataclass(frozen=True)
class ConditionalStatePrediction:
    """A hypothesis-conditional forecast, or a typed abstention from one."""

    action_identifier: str
    applicable: bool
    branches: tuple[HypothesisBranch, ...] = ()
    calibration_status: str = "uncalibrated"
    model_version: str = ""
    provenance: Mapping[str, str] = field(default_factory=dict)
    abstain_reason: str | None = None
    request_id: str | None = None
    compute_cost: float = 1.0


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_conditional(prediction: ConditionalStatePrediction) -> tuple[str, ...]:
    """Named contract violations of a conditional forecast; empty means valid."""

    errors: list[str] = []
    if not _text(prediction.action_identifier):
        errors.append("invalid_action_identifier")
    if type(prediction.applicable) is not bool:
        errors.append("invalid_applicable")
    if prediction.calibration_status not in CALIBRATION_STATUSES:
        errors.append("invalid_calibration_status")
    if not _text(prediction.model_version):
        errors.append("invalid_model_version")
    if not (isfinite(prediction.compute_cost) and prediction.compute_cost >= 0):
        errors.append("invalid_compute_cost")
    if not isinstance(prediction.provenance, Mapping) or not all(
            _text(k) and _text(v) for k, v in prediction.provenance.items()):
        errors.append("invalid_provenance")
    branch_ids = [b.hypothesis_id for b in prediction.branches]
    if len(set(branch_ids)) != len(branch_ids):
        errors.append("duplicate_branch_hypothesis")
    if prediction.applicable:
        if prediction.abstain_reason is not None:
            errors.append("applicable_with_abstain_reason")
        if not prediction.branches:
            errors.append("applicable_without_branches")
    else:
        if not _text(prediction.abstain_reason):
            errors.append("abstain_reason_missing")
        if prediction.branches:
            errors.append("abstention_contains_prediction")
    for branch in prediction.branches:
        if not _text(branch.hypothesis_id):
            errors.append("invalid_branch_hypothesis_id")
        if branch.abstain_reason is not None and (branch.predicted_readouts or branch.intervals):
            errors.append(f"branch_abstention_contains_prediction:{branch.hypothesis_id}")
        if type(branch.support) is not int or branch.support < 0:
            errors.append(f"invalid_branch_support:{branch.hypothesis_id}")
        for name, value in branch.predicted_readouts.items():
            if not _text(name) or not isfinite(value):
                errors.append(f"invalid_branch_readout:{branch.hypothesis_id}:{name}")
        for name, direction in branch.directional_effects.items():
            if direction not in (-1, 0, 1):
                errors.append(f"invalid_branch_direction:{branch.hypothesis_id}:{name}")
        for name, interval in branch.intervals.items():
            if not isinstance(interval, Interval):
                errors.append(f"invalid_branch_interval:{branch.hypothesis_id}:{name}")
                continue
            if not isfinite(interval.low) or not isfinite(interval.high) or interval.low > interval.high:
                errors.append(f"invalid_branch_interval:{branch.hypothesis_id}:{name}")
            if interval.kind is IntervalKind.CALIBRATED:
                if interval.level is None or not 0.0 < interval.level < 1.0 or not _text(interval.basis):
                    errors.append(f"invalid_calibrated_interval:{branch.hypothesis_id}:{name}")
            elif interval.level is not None:
                errors.append(f"descriptive_interval_claims_a_level:{branch.hypothesis_id}:{name}")
    return tuple(dict.fromkeys(errors))


def conditional_cache_key(request: PredictionRequest, backend: str) -> str | None:
    """Cache identity of a conditional forecast.

    Everything the plain prediction cache uses plus the four conditional inputs - hypotheses,
    history, observation context and forecast mode - because the forecast changes when any of
    them changes. Returns None for an invalid request; abstentions are never cached by callers,
    following the `PredictionCache` precedent.
    """

    if not isinstance(request, PredictionRequest) or request.validation_errors():
        return None
    identity = request.to_dict()
    for tracking in ("request_id", "case_id", "contrast_id", "plan_version"):
        identity.pop(tracking, None)
    identity["backend"] = backend
    text = json.dumps(identity, sort_keys=True, allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
