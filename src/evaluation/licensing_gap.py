"""The instance where enforcing the evidence boundary is what makes a repair worth buying.

File summary
- Path: src/evaluation/licensing_gap.py
- Purpose: build the case the whole record has been missing -- one where a correctly
  typed repair changes the decision -- and isolate the mechanism with controls. The
  mechanism is not a richer menu. It is the objective: under the loss convention the
  project has shipped since 2026-09-12, a policy may attribute on the prior, so a
  repair that only unlocks a *licensed* route is worth nothing; make the framework's
  own licensing rule a constraint on the policy class and the same repair is required.
- Core points:
  - Every family is a declared finite model: a skewed prior, a cheap readout that
    moves belief without isolating either explanation, and an isolating readout whose
    premise only a repair can supply. Losses are the framework convention: correct
    decision 0, wrong decision 10, deferral 4, plus the cost of every action.
  - `value_of_the_repair_catalogue_unconstrained` and its admissible twin are both
    reported for every family, so "the repair is worth 0.000 here" and "the repair is
    worth 0.500 here" are statements about the same instance under two objectives.
  - Each separation is paired with the control that removes it: no shared-control
    saving, an already-isolating menu readout, an unreliable gate, and a gate that
    supplies the wrong premise. A certificate that survives none of them would be an
    artifact.
- Interfaces: `licensing_gap`, `FAMILIES`, `run_family`, `gate_cost_sweep`,
  `saving_sweep`, `detection_power_sweep`, `main`
- Depends on: evaluation.adaptive_reference, evaluation.contingent, evaluation.admissible
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable, Mapping, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluation.admissible import (  # noqa: E402
    admissible_certificate,
    admissible_policy,
    admissible_repair_policy,
    admissible_row,
    binding_diagnostics,
    price_of_admissibility,
    sweep,
)
from evaluation.adaptive_reference import (  # noqa: E402
    DEFER,
    AdaptiveAction,
    DecisionProblem,
    information_gain_policy,
    lookahead_policy,
    optimal_policy,
    reactive_prerequisite_policy,
)
from evaluation.contingent import ambiguity_aware_repair_policy  # noqa: E402

REPAIR_SOURCE = "repair_catalogue"
HYPOTHESES = ("realised", "not_realised")
LOSS = {
    "continue": {"realised": 0.0, "not_realised": 10.0},
    "revise_intervention": {"realised": 10.0, "not_realised": 0.0},
    DEFER: {"realised": 4.0, "not_realised": 4.0},
}
DECISIONS = ("continue", "revise_intervention", DEFER)

MODE_READOUT_COST = 0.5


def licensing_gap(
    identifier: str = "licensing_gap",
    *,
    prior: Mapping[str, float] | None = None,
    gate_cost: float = 3.0,
    readout_cost: float = 0.5,
    saving: float = 0.5,
    gate_success: float = 1.0,
    mode_isolating: bool = False,
    composed: bool = False,
    gate_supplies: str = "engagement",
    readout_requires: str = "engagement",
    budget: float = 8.0,
    note: str = "",
) -> DecisionProblem:
    """A skewed contrast where the isolating route is only reachable through a repair.

    The prior favours ``realised`` at 0.7, so attributing on the prior costs 3.000 in
    expectation and deferring costs 4.000: under the shipped objective the cheapest
    thing to do is buy the cheap readout and attribute, which is exactly the practice
    the framework's own boundary forbids. The cheap readout is built so that *every*
    outcome leaves attributing cheaper than deferring (losses 1.139 and 3.578), which
    is what makes the shipped objective blind to a licensed route that costs 3.750:
    the route can only improve a branch the unconstrained policy already decides, and
    it is dearer than the decision it would replace. The isolating readout is legal
    only once its premise is supplied, and no menu action supplies it, so the only
    licensed route is the repair -- whose cost decides whether buying it beats
    deferring at 4.000.
    """

    prior = dict(prior or {"realised": 0.7, "not_realised": 0.3})
    mode_model = (
        {"realised": {"high": 1.0}, "not_realised": {"low": 1.0}}
        if mode_isolating
        else {
            "realised": {"high": 0.30, "low": 0.70},
            "not_realised": {"high": 0.09, "low": 0.91},
        }
    )
    actions: list[AdaptiveAction] = [
        AdaptiveAction(identifier="mode_readout", cost=MODE_READOUT_COST, outcome_model=mode_model),
        AdaptiveAction(
            identifier="realisation_readout",
            cost=readout_cost,
            prerequisites=(readout_requires,),
            outcome_model={"realised": {"high": 1.0}, "not_realised": {"low": 1.0}},
        ),
        AdaptiveAction(
            identifier="engagement_assay",
            cost=gate_cost,
            role="premise_supplier",
            source=REPAIR_SOURCE,
            outcome_model={
                hypothesis: {"ok": gate_success, "failed": 1.0 - gate_success}
                for hypothesis in HYPOTHESES
            },
            supplies={"ok": (gate_supplies,)},
        ),
    ]
    if composed:
        actions.append(
            AdaptiveAction(
                identifier="composed_engagement_and_readout",
                cost=gate_cost + readout_cost - saving,
                source=REPAIR_SOURCE,
                composed_from=("engagement_assay", "realisation_readout"),
                outcome_model={
                    "realised": {"high": gate_success, "failed": 1.0 - gate_success},
                    "not_realised": {"low": gate_success, "failed": 1.0 - gate_success},
                },
            )
        )
    return DecisionProblem(
        identifier=identifier,
        hypotheses=HYPOTHESES,
        prior=prior,
        actions=tuple(actions),
        budget=budget,
        decisions=DECISIONS,
        loss=LOSS,
        family="licensing gap",
        note=note
        or "a skewed contrast, a non-isolating cheap readout, and an isolating route only a repair can buy",
    )


def _replacement(**kwargs) -> DecisionProblem:
    return licensing_gap(
        "licensing_gap_replacement",
        readout_cost=0.5,
        gate_cost=3.25,
        composed=False,
        note="the repair registers a correctly typed supplier of the missing premise",
        **kwargs,
    )


def _composed(saving: float = 0.5, *, identifier: str | None = None, **kwargs) -> DecisionProblem:
    return licensing_gap(
        identifier or f"licensing_gap_composed_saving_{saving:g}",
        readout_cost=1.0,
        gate_cost=3.25,
        saving=saving,
        composed=True,
        note="the repair returns a composed plan that carries a shared-control saving",
        **kwargs,
    )


FAMILIES: Mapping[str, Callable[[], DecisionProblem]] = {
    "licensing_gap_replacement": _replacement,
    "licensing_gap_composed": lambda: _composed(0.5),
    "licensing_gap_composed_no_saving": lambda: _composed(0.0),
    "licensing_gap_menu_already_isolating": lambda: licensing_gap(
        "licensing_gap_menu_already_isolating",
        mode_isolating=True,
        readout_cost=0.5,
        note="control: the cheap menu readout isolates on its own, so there is no gap to repair",
    ),
    "licensing_gap_unreliable_gate": lambda: _composed(
        0.5, identifier="licensing_gap_unreliable_gate", gate_success=0.5
    ),
    "licensing_gap_wrong_premise": lambda: licensing_gap(
        "licensing_gap_wrong_premise",
        readout_cost=0.5,
        gate_supplies="selectivity",
        note="control: the repair supplies a premise the isolating readout does not require",
    ),
}


def policy_rows(problem: DecisionProblem, *, max_depth: int = 3) -> tuple[Mapping[str, object], ...]:
    """Every policy on the same instance, each scored with what it claimed to know."""

    policies: dict[str, object] = {
        "exact_unconstrained": optimal_policy(problem),
        "admissible_reference": admissible_policy(problem),
        "ambiguity_aware_repair": ambiguity_aware_repair_policy,
        "admissible_repair": admissible_repair_policy,
        "reactive_prerequisite": reactive_prerequisite_policy,
        "information_gain_per_cost": information_gain_policy,
    }
    for depth in range(1, max_depth + 1):
        policies[f"lookahead_{depth}"] = lookahead_policy(depth)
    return tuple(
        admissible_row(policy, problem, name).as_row()  # type: ignore[arg-type]
        for name, policy in policies.items()
    )


def run_family(problem: DecisionProblem, *, max_depth: int = 3) -> Mapping[str, object]:
    return {
        "identifier": problem.identifier,
        "family": problem.family,
        "note": problem.note,
        "prior": dict(problem.prior),
        "budget": problem.budget,
        "actions": [
            {
                "identifier": action.identifier,
                "cost": action.cost,
                "source": action.source,
                "prerequisites": list(action.prerequisites),
                "supplies": {outcome: list(fields) for outcome, fields in action.supplies.items()},
                "composed_from": list(action.composed_from),
            }
            for action in problem.actions
        ],
        "binding_diagnostics": binding_diagnostics(problem),
        "price_of_admissibility": price_of_admissibility(problem),
        "repair_catalogue_certificate": admissible_certificate(problem, catalogue_source=REPAIR_SOURCE),
        "policies": list(policy_rows(problem, max_depth=max_depth)),
    }


def gate_cost_sweep(values: Sequence[float] = (1.0, 1.5, 2.0, 2.5, 3.0, 3.25, 3.5, 4.0)) -> tuple:
    return sweep(
        lambda **kwargs: licensing_gap(
            f"licensing_gap_gate_{kwargs['gate_cost']:g}", readout_cost=0.5, composed=False, **kwargs
        ),
        values,
        key="gate_cost",
    )


def saving_sweep(values: Sequence[float] = (0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0)) -> tuple:
    return sweep(lambda **kwargs: _composed(**kwargs), values, key="saving")


def detection_power_sweep(values: Sequence[float] = (1.0, 0.9, 0.75, 0.5, 0.25)) -> tuple:
    return sweep(lambda **kwargs: _composed(0.5, **kwargs), values, key="gate_success")


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    out = Path(argv[0]) if argv else Path("licensing_gap_results.json")
    payload = {
        "scope": (
            "Constructed finite decision problems. They establish algorithm behaviour and "
            "the price of the framework's own evidence boundary; they are not biological "
            "evidence and they are not a measurement on any real development case."
        ),
        "loss_convention": "correct 0, wrong 10, deferral 4, plus the cost of every acquired action",
        "families": {name: run_family(builder()) for name, builder in FAMILIES.items()},
        "sweeps": {
            "gate_cost": list(gate_cost_sweep()),
            "saving": list(saving_sweep()),
            "detection_power": list(detection_power_sweep()),
        },
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for name, family in payload["families"].items():
        certificate = family["repair_catalogue_certificate"]
        prices = family["price_of_admissibility"]
        print(
            f"{name:38s} "
            f"repair_value_unconstrained={certificate['value_of_the_repair_catalogue_unconstrained']:>6} "
            f"repair_value_admissible={certificate['value_of_the_repair_catalogue_admissible']:>6} "
            f"price_of_admissibility={prices['price_of_admissibility']:>6} "
            f"unsupported={prices['unconstrained_unsupported_attribution']:>6}"
        )
    print(f"written: {out}")
    return 0


if __name__ == "__main__":  # pragma: no cover - direct script execution
    raise SystemExit(main())
