"""Decision-level admission of a world model: consult it only where a perfect one would matter.

A better forecast need not change a decision. MAESTRO's record shows RNA error falling while the
selection made with it stayed the same, because the decision had no headroom or because its
endpoint was only loosely tied to the forecast readout. This contract asks two questions before a
world-model forecast may influence selection for an endpoint, and answers each by name:

* **Bridge** -- is the forecast readout tied to the decision endpoint by pairs measured in the
  same culture unit, at the same dose and time? A cross-assay or cross-dose pairing is
  ``BRIDGE_NOT_SAME_UNIT``.
* **Ceiling** -- on reference contexts, scored leave-one-context-out, does a *perfect* forecast
  (the observed response used in its place) beat the best cheap prior by at least the declared
  minimum useful benefit? Otherwise ``WM_CEILING_BELOW_MUB``.

Admission is necessary, not sufficient: it licenses evaluating the actual forecast against the
cheap prior on unseen contexts; it never certifies that the forecast realises the ceiling.

When the decision endpoint lies at a later time or in another assay than the forecast readout,
``plan_measure_or_predict`` replaces the same-unit rule. It compares interval estimates, scored on
reference units in the decision's own domain, of what a measured early state and what the world
model's forecast of it add to the cheap prior.

Record (2026-10-10, ``research/astra/phenotype_anchor_20261010``): for Tahoe relative-survival
selectivity, the reference ceiling was r 0.530 against 0.527 for basal-similarity transfer. The
gate refused (``WM_CEILING_BELOW_MUB``). On five checkpoint-held-out lines the refusal held: the
observed-RNA oracle did not beat the cheap prior (delta r -0.037 [-0.086, 0.003]), and frozen
STATE lost to it (delta r -0.226 [-0.266, -0.156]). That is one endpoint, one gate decision
and n = 5 lines; it is not a general validation of the rule.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from typing import Mapping

MIN_REFERENCE_UNITS = 10


@dataclass(frozen=True)
class PhenotypeBridge:
    """How a world-model readout is paired with the decision endpoint in reference data."""

    endpoint: str
    readout: str
    pairing_unit: str
    same_unit: bool
    same_dose: bool
    same_time: bool
    source: str


@dataclass(frozen=True)
class ValueCeiling:
    """Leave-one-context-out reference scores: a perfect forecast versus cheap priors."""

    endpoint: str
    score: str
    oracle: float
    cheap: Mapping[str, float]
    reference_units: int
    minimum_useful_benefit: float

    def __post_init__(self) -> None:
        if not (isfinite(self.minimum_useful_benefit) and self.minimum_useful_benefit > 0):
            raise ValueError("minimum_useful_benefit must be a positive finite number")


@dataclass(frozen=True)
class WorldModelAdmission:
    admitted: bool
    reasons: tuple[str, ...] = ()
    margin: float | None = None
    best_cheap_prior: str | None = None
    notes: tuple[str, ...] = field(default=())

    def payload(self) -> dict[str, object]:
        return {"admitted": self.admitted, "reasons": list(self.reasons), "margin": self.margin,
                "best_cheap_prior": self.best_cheap_prior, "notes": list(self.notes)}


def admit_world_model(bridge: PhenotypeBridge, ceiling: ValueCeiling, *,
                      min_reference_units: int = MIN_REFERENCE_UNITS) -> WorldModelAdmission:
    """Return whether a world model may be evaluated as a decision input for ``ceiling.endpoint``."""

    reasons: list[str] = []
    if bridge.endpoint != ceiling.endpoint:
        reasons.append("BRIDGE_ENDPOINT_MISMATCH")
    if not (bridge.same_unit and bridge.same_dose and bridge.same_time):
        reasons.append("BRIDGE_NOT_SAME_UNIT")
    if ceiling.reference_units < min_reference_units:
        reasons.append("INSUFFICIENT_REFERENCE_UNITS")
    scores = [ceiling.oracle, *ceiling.cheap.values()]
    if not ceiling.cheap or not all(isinstance(s, (int, float)) and isfinite(s) for s in scores):
        reasons.append("CEILING_UNESTIMATED")
        return WorldModelAdmission(False, tuple(reasons))
    best = max(ceiling.cheap, key=lambda name: ceiling.cheap[name])
    margin = float(ceiling.oracle - ceiling.cheap[best])
    if margin < ceiling.minimum_useful_benefit:
        reasons.append("WM_CEILING_BELOW_MUB")
    return WorldModelAdmission(not reasons, tuple(reasons), margin, best)


@dataclass(frozen=True)
class IncrementEstimate:
    """Reference-unit estimate of ``r(prior + X) - r(prior)`` with an interval.

    ``X`` is either a measured early state (the measurement ceiling) or a world-model forecast of
    that state, scored in the domain where the decision is made (its own assay or platform). The
    interval must come from resampling units (e.g. cell lines), not drugs or genes within a unit.
    """

    point: float
    lower: float
    upper: float
    reference_units: int
    domain: str

    def __post_init__(self) -> None:
        values = (self.point, self.lower, self.upper)
        if not all(isinstance(v, (int, float)) and isfinite(v) for v in values):
            raise ValueError("increment estimate must be finite")
        if not self.lower <= self.point <= self.upper:
            raise ValueError("increment estimate requires lower <= point <= upper")


@dataclass(frozen=True)
class MeasureOrPredict:
    action: str
    reasons: tuple[str, ...] = ()

    def payload(self) -> dict[str, object]:
        return {"action": self.action, "reasons": list(self.reasons)}


def plan_measure_or_predict(measurement: IncrementEstimate | None, forecast: IncrementEstimate | None, *,
                            minimum_useful_benefit: float,
                            min_reference_units: int = MIN_REFERENCE_UNITS) -> MeasureOrPredict:
    """Choose between consulting the world model, measuring the early state, or the cheap prior.

    Actions, by name:

    * ``ADMIT_WORLD_MODEL``: the forecast's *lower* bound clears the MUB in the decision's domain;
    * ``MEASURE_EARLY``: the forecast does not, but the measured early state's lower bound does;
    * ``USE_PRIOR``: every evaluated interval lies wholly below the MUB;
    * ``ABSTAIN``: an interval straddles the MUB, so more reference units are needed first.

    A point estimate is never sufficient. Record (2026-10-10,
    ``research/astra/kinetic_horizon_20261010``): on 24 MIX-Seq development lines, prior + 24 h
    measurement gave +0.139 r over a DepMap-scale prior for 5-day PRISM viability, and the
    point-estimate gate chose MEASURE_EARLY. On 48 confirmation lines the increment was -0.021
    [-0.109, +0.078], so the choice was wrong. The development interval, computed post hoc, had
    been [-0.049, +0.298]; this rule would have returned ABSTAIN. The rule is a conservative
    correction motivated by that one failure, not a validated improvement in decisions. In the same
    block, STATE's forecast increment was -0.150 on development lines and -0.091 [-0.182, -0.005] on
    confirmation lines (``WM_TRANSPORT_UNQUALIFIED``).
    """

    if not (isfinite(minimum_useful_benefit) and minimum_useful_benefit > 0):
        raise ValueError("minimum_useful_benefit must be a positive finite number")
    mub = minimum_useful_benefit
    reasons: list[str] = []
    for name, est in (("FORECAST", forecast), ("MEASUREMENT", measurement)):
        if est is not None and est.reference_units < min_reference_units:
            reasons.append(f"INSUFFICIENT_REFERENCE_UNITS_{name}")
    if reasons:
        return MeasureOrPredict("ABSTAIN", tuple(reasons))
    if forecast is None:
        reasons.append("WM_FORECAST_NOT_EVALUATED")
    elif forecast.lower >= mub:
        return MeasureOrPredict("ADMIT_WORLD_MODEL")
    elif forecast.upper < mub:
        reasons.append("WM_TRANSPORT_UNQUALIFIED")
    else:
        reasons.append("FORECAST_INCONCLUSIVE")
    if measurement is not None and measurement.lower >= mub:
        return MeasureOrPredict("MEASURE_EARLY", tuple(reasons))
    if measurement is None:
        reasons.append("MEASUREMENT_NOT_EVALUATED")
    elif measurement.upper < mub:
        reasons.append("WM_CEILING_BELOW_MUB")
    else:
        reasons.append("MEASUREMENT_INCONCLUSIVE")
    inconclusive = {"FORECAST_INCONCLUSIVE", "MEASUREMENT_INCONCLUSIVE"} & set(reasons)
    return MeasureOrPredict("ABSTAIN" if inconclusive else "USE_PRIOR", tuple(reasons))


def realised_fraction(oracle: float, forecast: float, cheap: float) -> float | None:
    """Share of the reference headroom (oracle - cheap) that an actual forecast recovers.

    ``None`` when the headroom is not positive; negative when the forecast is worse than the
    cheap prior. A descriptive quantity for reports, not an admission criterion.
    """

    headroom = oracle - cheap
    if not (isfinite(headroom) and isfinite(forecast)) or headroom <= 0:
        return None
    return float((forecast - cheap) / headroom)
