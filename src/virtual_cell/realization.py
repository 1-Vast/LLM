"""The biological anchor: intervention realisation as a coordinate, not a nominal dose.

File summary
- Path: src/virtual_cell/realization.py
- Purpose: make report sections 31, 42 and 43 executable — model the functional residual
  ``r = g(d; compound, mode, time, context)`` as an explicit coordinate, state exactly what
  its identification buys, and refuse an absolute-scale claim the data cannot support.
- Core points:
  - ``MonotoneRealization`` is occupancy-shaped and therefore monotone decreasing in dose by
    construction; the structural constraint is the main source of identifiability, so it is
    in the model rather than in a comment.
  - A realisation is identified only up to a shared monotone reparameterisation: any monotone
    ``phi`` with ``g -> phi(g)`` and ``V -> V(phi^-1)`` predicts identically. The statement this
    module returns says so, and ``observationally_equivalent`` demonstrates it numerically.
  - A measured functional strength at a declared condition can anchor the scale. Same-drug
    self-combination is only a structural constraint **under a declared
    composition rule**: dose addition gives ``r(d1 + d2)``, independent action gives
    ``r(d1) r(d2)``, and ``self_combination_residual`` reports the gap between them. A non-zero
    gap is not a measurement of the compound; it is how much the rule choice moves the answer for
    this shape, which is why the constraint may only be imposed inside a validated dose window.
  - The four ablations of the direction are declared here with what each one excludes. They are
    declared, not run: a plan that reported them as executed would be claiming a training run
    that never happened.
- Interfaces: `MonotoneRealization`, `ScaleAnchor`, `IdentifiabilityStatement`,
  `self_combination_residual`, `monotone_reparameterisation_demo`, `alignment_disagreement`,
  `ABLATION_ARMS`, `ablation_plan`
- Depends on: (standard library only; no trained model and no dataset is read here)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import exp, isfinite
from typing import Callable, Mapping, Sequence


class ScaleAnchor(str, Enum):
    """What, if anything, fixes the units of the realisation coordinate."""

    NONE = "none"
    MEASURED_FUNCTIONAL_STRENGTH = "measured_functional_strength"
    SELF_COMBINATION = "self_combination"


@dataclass(frozen=True)
class IdentifiabilityStatement:
    """What a caller may claim about ``r`` given the anchors that exist."""

    level: str
    anchors: tuple[ScaleAnchor, ...]
    statement: str
    limitations: tuple[str, ...]

    @property
    def absolute_scale_licensed(self) -> bool:
        return self.level == "scaled" and ScaleAnchor.NONE not in self.anchors


@dataclass(frozen=True)
class MonotoneRealization:
    """Occupancy-shaped residual function for one compound in one context.

    ``residual`` is a model coordinate, not a measured functional percentage.
    Its numerical endpoints encode the assumed untouched and removed limits. It is monotone decreasing in dose by construction, and the declared
    dose window is part of the object: outside it the parameterisation extrapolates, and the
    report requires that failure class to be reported rather than absorbed.
    """

    compound: str
    context_identifier: str
    mode: str
    exposure_hours: float | None
    log_ec50: float
    hill: float = 1.0
    dose_window: tuple[float, float] = (0.0, 1000.0)
    measured_points: int = 0
    source: str = ""
    # A checked dose window permits a structural constraint, not functional units.
    # Dose addition and independent action are different composition assumptions.
    dose_window_validated: bool = False
    composition_rule: str | None = None

    def __post_init__(self) -> None:
        if not isfinite(self.log_ec50):
            raise ValueError("A realisation needs a finite log EC50.")
        if not isfinite(self.hill) or self.hill <= 0.0:
            raise ValueError("A realisation needs a positive Hill coefficient.")
        if not all(isfinite(x) and x >= 0 for x in self.dose_window) or self.dose_window[0] > self.dose_window[1]:
            raise ValueError("The declared dose window is inverted.")

    def occupancy(self, dose: float) -> float:
        if dose <= 0.0:
            return 0.0
        ratio = (dose / exp(self.log_ec50)) ** self.hill
        return ratio / (1.0 + ratio)

    def residual(self, dose: float) -> float:
        """Ordinal residual coordinate; biological units require measurement anchors."""

        return 1.0 - self.occupancy(dose)

    def dose_for_residual(self, target: float) -> float | None:
        """Inverse of ``residual`` inside the declared window, or ``None`` outside it."""

        if not 0.0 < target <= 1.0:
            raise ValueError("A residual target must lie in (0, 1].")
        occupancy = 1.0 - target
        if occupancy <= 0.0:
            return 0.0
        dose = exp(self.log_ec50) * (occupancy / (1.0 - occupancy)) ** (1.0 / self.hill)
        if not self.dose_window[0] <= dose <= self.dose_window[1]:
            return None
        return dose

    def inside_window(self, dose: float) -> bool:
        return self.dose_window[0] <= dose <= self.dose_window[1]

    def identifiability(self, anchors: Sequence[ScaleAnchor]) -> IdentifiabilityStatement:
        """State what these anchors license, and refuse to imply more."""

        granted = tuple(dict.fromkeys(anchors))
        if ScaleAnchor.MEASURED_FUNCTIONAL_STRENGTH in granted:
            return IdentifiabilityStatement(
                level="scaled",
                anchors=granted,
                statement=(
                    "A measured functional strength at a declared condition fixes the scale of r, so "
                    "'a residual fraction of X' may be reported at that condition."
                ),
                limitations=(
                    "The scale transfers only where the same assay, context and time window were measured.",
                ),
            )
        if ScaleAnchor.SELF_COMBINATION in granted:
            limitations = [
                "Self-consistency does not identify biological units: r -> r**2 preserves "
                "multiplicative self-combination while changing the residual percentage.",
                "No functional percentage is licensed without a measured anchor or an "
                "independently validated identifying measurement model.",
            ]
            if not self.dose_window_validated:
                limitations.append("self_combination_anchor_without_validated_dose_window")
            if self.composition_rule not in {"dose_addition", "independent_action"}:
                limitations.append("self_combination_rule_not_declared")
            return IdentifiabilityStatement(
                level="ordinal_only", anchors=granted,
                statement="Same-drug constraints are structural assumptions, not functional measurements.",
                limitations=tuple(limitations),
            )
        return IdentifiabilityStatement(
            level="ordinal_only",
            anchors=granted,
            statement=(
                "Without a scale anchor, g and V are identified only up to a shared monotone "
                "reparameterisation: comparisons of r across conditions are preserved, its units are not."
            ),
            limitations=(
                "No claim of the form 'this compound achieved X percent inhibition' is licensed.",
                "A claim that two conditions are equally inhibited is licensed only ordinally.",
            ),
        )

    def require_absolute_scale(self, anchors: Sequence[ScaleAnchor]) -> IdentifiabilityStatement:
        """Return the statement, refusing a caller who needs units it does not have."""

        statement = self.identifiability(anchors)
        if not statement.absolute_scale_licensed:
            raise ValueError(
                f"Realisation for '{self.compound}' in '{self.context_identifier}' is ordinal-only; "
                "an absolute residual fraction needs measured functional strength or an "
                "independently validated identifying measurement model."
            )
        return statement


def self_combination_residual(
    realization: MonotoneRealization,
    pairs: Sequence[tuple[float, float]],
) -> Mapping[str, object]:
    """How far the two declared composition rules diverge for one realisation.

    Dose addition reads a self-combination of ``d1`` and ``d2`` as the single dose ``d1 + d2``
    and predicts ``r(d1 + d2)``; independent action reads it as two independent chances to act
    and predicts ``r(d1) r(d2)``. The difference is a property of the declared shape, it changes
    sign with the Hill coefficient, and it is exactly what makes the constraint conditional on a
    validated dose window rather than universally true.
    """

    rows = []
    worst = 0.0
    for first, second in pairs:
        total = first + second
        if not all(realization.inside_window(dose) for dose in (first, second, total)):
            rows.append({"doses": [first, second], "residual": None, "reason": "outside_declared_window"})
            continue
        independent_action = realization.residual(first) * realization.residual(second)
        dose_addition = realization.residual(total)
        residual = dose_addition - independent_action
        worst = max(worst, abs(residual))
        rows.append(
            {
                "doses": [first, second],
                "residual_under_dose_addition": dose_addition,
                "residual_under_independent_action": independent_action,
                "rule_gap": residual,
            }
        )
    return {
        "compound": realization.compound,
        "context_identifier": realization.context_identifier,
        "hill": realization.hill,
        "rows": rows,
        "worst_absolute_rule_gap": worst,
        "gap_sign": (
            "dose_addition_leaves_more_function"
            if rows and (rows[0].get("rule_gap") or 0.0) > 0
            else "independent_action_leaves_more_function"
            if rows and rows[0].get("rule_gap") is not None
            else "undetermined"
        ),
        "reading": (
            "Same-drug consistency constrains the declared rule inside its dose window; it does not "
            "identify functional percentages. This gap measures disagreement between assumptions."
        ),
    }


def monotone_reparameterisation_demo(
    realization: MonotoneRealization,
    *,
    doses: Sequence[float],
    phi: Callable[[float], float] | None = None,
    phi_inverse: Callable[[float], float] | None = None,
    response_slope: float = 1.0,
    tolerance: float = 1e-9,
) -> Mapping[str, object]:
    """Demonstrate the monotone-reparameterisation family on a declared dose grid.

    With response ``V(r) = k r`` under the first identification, the second identification writes
    the same response as ``V'(r') = k phi^-1(r')`` evaluated at ``r' = phi(r)``. Every dose in the
    grid then predicts the same number from two different residual coordinates, which is the
    precise sense in which the pair is not identified by the data.
    """

    forward = phi or (lambda value: value**2)
    inverse = phi_inverse or (lambda value: value**0.5)
    rows = []
    agree = True
    for dose in doses:
        first_coordinate = realization.residual(dose)
        second_coordinate = forward(first_coordinate)
        first_response = response_slope * first_coordinate
        second_response = response_slope * inverse(second_coordinate)
        same = abs(first_response - second_response) <= tolerance
        agree = agree and same
        rows.append(
            {
                "dose": dose,
                "residual_under_identification_1": first_coordinate,
                "residual_under_identification_2": second_coordinate,
                "response_under_identification_1": first_response,
                "response_under_identification_2": second_response,
                "responses_agree": same,
            }
        )
    return {
        "identifications_agree_on_the_grid": agree,
        "rows": rows,
        "reading": (
            "Agreement on every declared dose with differing coordinates is the non-identifiability "
            "statement: the data cannot separate these two coordinates, so only ordinal use survives "
            "unless a scale anchor exists."
        ),
    }


@dataclass(frozen=True)
class AlignmentEntry:
    """One condition as two coordinates: the nominal dose and the realised residual."""

    compound: str
    dose: float
    residual: float


def alignment_disagreement(entries: Sequence[AlignmentEntry]) -> Mapping[str, object]:
    """Where nominal-dose alignment and functional alignment order conditions differently.

    This is the measurement behind the anchor: if the two orders agree everywhere on a
    declared panel, dosing by label is harmless there; every inversion is a pair whose
    comparison would change had it been made at functional equivalence.
    """

    by_dose = sorted(range(len(entries)), key=lambda index: (entries[index].dose, entries[index].compound))
    nominal_order = [entries[index].compound for index in by_dose]
    functional = sorted(range(len(entries)), key=lambda index: (-entries[index].residual, entries[index].compound))
    functional_order = [entries[index].compound for index in functional]
    inversions = []
    for first in range(len(entries)):
        for second in range(first + 1, len(entries)):
            left, right = entries[first], entries[second]
            # Agreeing coordinates move in opposite directions: a higher nominal dose must mean a
            # smaller residual. Moving the same way is the disagreement.
            dose_sign = (right.dose > left.dose) - (right.dose < left.dose)
            residual_sign = (right.residual > left.residual) - (right.residual < left.residual)
            if dose_sign * residual_sign > 0:
                inversions.append(
                    {
                        "pair": [left.compound, right.compound],
                        "doses": [left.dose, right.dose],
                        "residuals": [left.residual, right.residual],
                        "note": "the two coordinates order this pair differently",
                    }
                )
    return {
        "conditions": len(entries),
        "order_by_nominal_dose": nominal_order,
        "order_by_realized_residual": functional_order,
        "orders_agree": nominal_order == functional_order,
        "inversions": inversions,
        "reading": (
            "Every inversion is a condition pair that a dose-aligned comparison reads backwards. "
            "The panel is small and declared, so this is a property of these conditions, not a rate."
        ),
    }


ABLATION_ARMS: Mapping[str, str] = {
    "drop_realization": "excludes the explanation that the gain comes from the intermediate variable itself",
    "randomize_realization": (
        "excludes the explanation that the gain comes from extra parameters — the one-hot lesson"
    ),
    "drop_monotonicity": "excludes the explanation that the gain comes from the structural prior",
    "drop_self_consistency": "excludes the explanation that the scale constraint helps",
}


def ablation_plan() -> Mapping[str, object]:
    """The four declared arms, with their execution status stated rather than implied."""

    return {
        "arms": [{"arm": arm, "excludes": reading, "executed": False} for arm, reading in ABLATION_ARMS.items()],
        "executed": False,
        "reading": (
            "Declared, not run: MAESTRO holds no trained realisation model, so reporting any of these "
            "arms as executed would claim a training run that did not happen."
        ),
    }
