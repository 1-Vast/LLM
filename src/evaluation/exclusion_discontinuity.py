"""Why the admissible objective credits only exclusion, and never mere information.

File summary
- Path: src/evaluation/exclusion_discontinuity.py
- Purpose: isolate the property of the framework's licensing rule that decides whether a
  repair can be worth anything: `admissible_terminal` admits a non-deferral act only when
  every hypothesis still carrying posterior mass accepts it, so an observation that
  *informs* without *excluding* can never license an attribution, however reliable it is.
- Core points:
  - The family is one declared decision problem with a degenerate menu -- every menu action
    returns the same outcome under every hypothesis, which is what the local releases
    actually contain -- plus one catalogue action whose detection power is a parameter.
  - The grid shows a discontinuity in detection power, not a window in cost: the admissible
    repair value is exactly 0.000 for every power below 1.0 at every cost tested, and jumps
    to its full value at 1.0. The price of admissibility moves the other way, rising with
    detection power and collapsing to 0.000 at 1.0.
  - This refines rather than overturns the 2026-09-15 record. That block measured
    `detection_power_sweep` at 0.9 and recorded 0.000, and explained it by cost arithmetic
    ("expected loss 4.15 against a deferral of 4.00"). The measurement stands; the
    explanation is incomplete, because at a control cost of 0.25 the licensed route
    undercuts the deferral by a wide margin and the value is still exactly 0.000.
  - Nothing here is biological evidence. Every number is a statement about a declared
    finite model.
- Interfaces: `exclusion_family`, `detection_power_cost_grid`, `MENU_SOURCE`,
  `CATALOGUE_SOURCE`, `DEFAULT_POWERS`, `DEFAULT_COSTS`
- Depends on: evaluation.adaptive_reference, evaluation.admissible
"""
from __future__ import annotations

from typing import Mapping, Sequence

from .adaptive_reference import DEFER, AdaptiveAction, DecisionProblem
from .admissible import admissible_certificate, binding_diagnostics, price_of_admissibility

MENU_SOURCE = "menu"
CATALOGUE_SOURCE = "repair_catalogue"

MEDIATED = "mediated_by_target"
NOT_ATTRIBUTABLE = "phenotype_not_target_attributable"
HYPOTHESES: tuple[str, ...] = (MEDIATED, NOT_ATTRIBUTABLE)

CONTINUE = "continue"
REVISE = "revise_attribution"

# The recorded convention, unchanged, so these numbers stay comparable with the
# declared families and with the 2026-09-16 case set.
WRONG = 10.0
DEFERRAL = 4.0
BUDGET = 2.0
MENU_COST = 1.0

DEFAULT_POWERS: tuple[float, ...] = (0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 0.999, 1.0)
DEFAULT_COSTS: tuple[float, ...] = (0.25, 0.5, 1.0, 1.5)

# The three menu actions of the 2026-09-16 case set, as they were declared there: each
# retrieves an already-published value, so its outcome is fixed by the record and the
# declared model is the same under every hypothesis.
_MENU: tuple[tuple[str, str, str], ...] = (
    ("dependency_selectivity_profile", "dependency_selective", "attribution:dependency_selectivity"),
    ("target_abundance_rna", "target_expressed", "abundance:target_rna"),
    ("target_occupancy_estimate", "occupancy_estimated_above_theta", "engagement:scoped_estimate"),
)


def _degenerate(identifier: str, outcome: str, supplies: str) -> AdaptiveAction:
    return AdaptiveAction(
        identifier=identifier,
        cost=MENU_COST,
        outcome_model={hypothesis: {outcome: 1.0} for hypothesis in HYPOTHESES},
        supplies={outcome: (supplies,)},
        role="readout",
        source=MENU_SOURCE,
    )


def exclusion_family(
    detection_power: float,
    control_cost: float = 1.0,
    *,
    identifier: str | None = None,
) -> DecisionProblem:
    """One declared problem whose only informative action has the given detection power.

    ``detection_power`` is the probability that the control returns the outcome its
    hypothesis predicts. At 1.0 each outcome is impossible under one hypothesis, so
    observing it excludes that hypothesis; below 1.0 both hypotheses keep posterior mass
    under either outcome, so neither is ever excluded.
    """

    if not 0.5 <= detection_power <= 1.0:
        raise ValueError("detection power is declared on [0.5, 1.0]")
    if control_cost <= 0.0:
        raise ValueError("a control has a positive cost")
    control = AdaptiveAction(
        identifier="orthogonal_context_control",
        cost=float(control_cost),
        outcome_model={
            MEDIATED: {
                "control_context_resistant": detection_power,
                "control_context_sensitive": 1.0 - detection_power,
            },
            NOT_ATTRIBUTABLE: {
                "control_context_resistant": 1.0 - detection_power,
                "control_context_sensitive": detection_power,
            },
        },
        supplies={
            "control_context_resistant": ("functional:context_control",),
            "control_context_sensitive": ("functional:context_control",),
        },
        role="readout",
        source=CATALOGUE_SOURCE,
    )
    loss = {
        CONTINUE: {MEDIATED: 0.0, NOT_ATTRIBUTABLE: WRONG},
        REVISE: {MEDIATED: WRONG, NOT_ATTRIBUTABLE: 0.0},
        DEFER: {hypothesis: DEFERRAL for hypothesis in HYPOTHESES},
    }
    return DecisionProblem(
        identifier=identifier or f"exclusion_discontinuity_p{detection_power}_c{control_cost}",
        hypotheses=HYPOTHESES,
        prior={hypothesis: 1.0 / len(HYPOTHESES) for hypothesis in HYPOTHESES},
        actions=tuple(_degenerate(*item) for item in _MENU) + (control,),
        budget=BUDGET,
        decisions=(CONTINUE, REVISE, DEFER),
        loss=loss,
        family="exclusion_discontinuity",
        note=(
            "degenerate menu plus one catalogue control of declared detection power; "
            "the menu is degenerate because a retrieval of a published value returns the "
            "same outcome whatever the hypothesis"
        ),
        attributions=(CONTINUE, REVISE),
    )


def detection_power_cost_grid(
    powers: Sequence[float] = DEFAULT_POWERS,
    costs: Sequence[float] = DEFAULT_COSTS,
) -> tuple[Mapping[str, object], ...]:
    """Both certificates across the declared (detection power, control cost) grid."""

    rows: list[Mapping[str, object]] = []
    for power in powers:
        for cost in costs:
            problem = exclusion_family(power, cost)
            invalid = problem.validate()
            if invalid:
                raise ValueError(f"{problem.identifier}: {invalid}")
            certificate = admissible_certificate(problem, catalogue_source=CATALOGUE_SOURCE)
            price = price_of_admissibility(problem)
            diagnostics = binding_diagnostics(problem)
            rows.append(
                {
                    "detection_power": power,
                    "control_cost": cost,
                    "excludes_a_hypothesis": power >= 1.0,
                    "root_bayes_decision": diagnostics["root_bayes_decision"],
                    "root_decision_licensed": diagnostics["root_licensed"],
                    "unconstrained_optimum": price["unconstrained_optimum"],
                    "admissible_optimum": price["admissible_optimum"],
                    "price_of_admissibility": price["price_of_admissibility"],
                    "value_of_the_repair_catalogue_unconstrained": certificate[
                        "value_of_the_repair_catalogue_unconstrained"
                    ],
                    "value_of_the_repair_catalogue_admissible": certificate[
                        "value_of_the_repair_catalogue_admissible"
                    ],
                    "complete": certificate["complete"] and price["complete"],
                }
            )
    return tuple(rows)
