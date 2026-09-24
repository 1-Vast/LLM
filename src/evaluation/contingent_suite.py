"""Constructed families that decide whether the repair operation is testable at all.

File summary
- Path: src/evaluation/contingent_suite.py
- Purpose: Build the instances on which "check and repair" and "reactive selection"
  can be told apart, measure every policy on them exactly, and record where the
  incumbent family already suffices. Synthetic problems establish algorithm
  behaviour; they are not biological evidence.
- Core points:
  - Every family is a declared finite model. Losses are the framework convention:
    correct decision 0, wrong decision 10, deferral 4, plus the cost of every
    acquired action.
  - `required_depth` reports the smallest depth-limited lookahead that attains the
    exact optimum. A family where no tested depth attains it is the evidence that
    the grammar, not the search budget, was the obstacle.
  - `unsupported_attribution` reports the probability mass on which a policy
    returns a causal attribution without having isolated the cause.
  - The flat family is kept as a control: where the action grammar makes the
    reactive policy optimal, the suite says so instead of hiding it.
- Interfaces: `flat_grammar`, `supplier_choice_binding_budget`, `supplier_ladder`,
  `information_is_not_value`, `false_isolation`, `families`, `run_family`, `main`
- Depends on: evaluation.adaptive_reference, evaluation.contingent
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable, Mapping, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluation.adaptive_reference import (  # noqa: E402
    DEFER,
    AdaptiveAction,
    DecisionProblem,
    Policy,
    information_gain_policy,
    lookahead_policy,
    optimal_policy,
    reactive_prerequisite_policy,
)
from evaluation.contingent import (  # noqa: E402
    ambiguity_aware_repair_policy,
    ambiguity_report,
    evaluate_with_attribution,
    repair_catalogue_certificate,
    required_depth,
)

# Actions that exist only because a repair proposed them carry this source. The
# certificate in `repair_catalogue_certificate` is taken against a problem with
# exactly these removed, which is what turns "repair beats selection" from a
# comparison between two heuristics into a bound on every selection policy.
REPAIR_SOURCE = "repair_catalogue"

HYPOTHESES = ("realised", "not_realised")
LOSS = {
    "continue": {"realised": 0.0, "not_realised": 10.0},
    "revise_intervention": {"realised": 10.0, "not_realised": 0.0},
    DEFER: {"realised": 4.0, "not_realised": 4.0},
}
DECISIONS = ("continue", "revise_intervention", DEFER)


def _problem(
    identifier: str,
    actions: Sequence[AdaptiveAction],
    *,
    budget: float,
    prior: Mapping[str, float] | None = None,
    hypotheses: Sequence[str] = HYPOTHESES,
    loss: Mapping[str, Mapping[str, float]] | None = None,
    decisions: Sequence[str] = DECISIONS,
    family: str = "",
    note: str = "",
) -> DecisionProblem:
    prior = prior or {h: 1.0 / len(hypotheses) for h in hypotheses}
    return DecisionProblem(
        identifier=identifier,
        hypotheses=tuple(hypotheses),
        prior=dict(prior),
        actions=tuple(actions),
        budget=budget,
        decisions=tuple(decisions),
        loss=dict(loss or LOSS),
        family=family,
        note=note,
    )


def _separating(identifier: str, cost: float, **kwargs) -> AdaptiveAction:
    return AdaptiveAction(
        identifier=identifier,
        cost=cost,
        outcome_model={"realised": {"high": 1.0}, "not_realised": {"low": 1.0}},
        **kwargs,
    )


def flat_grammar() -> DecisionProblem:
    """Control: one supplier per premise, unit cost, deterministic declared outcome.

    This mirrors the frozen real-data grammar. On it the reactive policy is
    optimal, and the suite reports that instead of manufacturing a separation.
    """

    return _problem(
        "flat_grammar",
        (_separating("readout_one", 1.0), _separating("readout_two", 1.0)),
        budget=2.0,
        family="flat grammar",
        note="one supplier per premise, unit costs, deterministic declared outcomes",
    )


def supplier_choice_binding_budget() -> DecisionProblem:
    """Several suppliers of one premise at different cost and reliability; budget binds."""

    cheap = AdaptiveAction(
        identifier="cheap_supplier",
        cost=1.0,
        role="premise_supplier",
        outcome_model={h: {"ok": 0.5, "failed": 0.5} for h in HYPOTHESES},
        supplies={"ok": ("premise",)},
    )
    reliable = AdaptiveAction(
        identifier="reliable_supplier",
        cost=2.0,
        role="premise_supplier",
        outcome_model={h: {"ok": 1.0} for h in HYPOTHESES},
        supplies={"ok": ("premise",)},
        source=REPAIR_SOURCE,
    )
    return _problem(
        "supplier_choice_binding_budget",
        (cheap, reliable, _separating("gated_readout", 1.0, prerequisites=("premise",))),
        budget=3.0,
        family="supplier choice under a binding budget",
        note="buying the cheap supplier first leaves too little budget to recover from its failure",
    )


def supplier_ladder(levels: int = 3, *, budget: float = 6.0) -> DecisionProblem:
    """A ladder of suppliers for one premise: the cheap ones fail, the dear ones do not.

    Level i succeeds with probability 1 - 0.5**i and costs i. The optimal policy
    depends on how many failures it has already absorbed, so its value at a state
    is a function of the observed history, and a policy that only looks a fixed
    number of steps ahead cannot price the tail of the ladder.
    """

    actions: list[AdaptiveAction] = []
    for level in range(1, levels + 1):
        failure = 0.5**level
        success = 1.0 - failure
        actions.append(
            AdaptiveAction(
                identifier=f"supplier_level_{level}",
                cost=float(level),
                role="premise_supplier",
                outcome_model={
                    h: {"ok": success, "failed": failure} for h in HYPOTHESES
                },
                supplies={"ok": ("premise",)},
            )
        )
    actions.append(_separating("gated_readout", 1.0, prerequisites=("premise",)))
    return _problem(
        f"supplier_ladder_{levels}",
        tuple(actions),
        budget=budget,
        family="supplier ladder",
        note="n suppliers of one premise, geometrically increasing cost and reliability",
    )


def information_is_not_value() -> DecisionProblem:
    """A cheap, high-entropy readout about an irrelevant hypothesis; the decided one costs more.

    Entropy reduction and decision value are different quantities. A policy that
    maximises information per unit cost buys the confounder first; a policy that
    prices the decision buys the readout that moves it.
    """

    hypotheses = ("candidate", "alternative", "nuisance")
    loss = {
        "continue": {"candidate": 0.0, "alternative": 10.0, "nuisance": 0.0},
        "revise_intervention": {"candidate": 10.0, "alternative": 0.0, "nuisance": 0.0},
        DEFER: {h: 4.0 for h in hypotheses},
    }
    confounder = AdaptiveAction(
        identifier="confounder_readout",
        cost=1.0,
        outcome_model={
            "candidate": {"c1": 0.5, "c2": 0.5},
            "alternative": {"c1": 0.5, "c2": 0.5},
            "nuisance": {"c1": 1.0},
        },
    )
    decisive = AdaptiveAction(
        identifier="decisive_readout",
        cost=2.0,
        outcome_model={
            "candidate": {"cand": 1.0},
            "alternative": {"alt": 1.0},
            "nuisance": {"cand": 0.5, "alt": 0.5},
        },
    )
    return _problem(
        "information_is_not_value",
        (confounder, decisive),
        budget=4.0,
        prior={"candidate": 0.3, "alternative": 0.3, "nuisance": 0.4},
        hypotheses=hypotheses,
        loss=loss,
        family="information is not value",
        note="the cheap readout explains the nuisance hypothesis and leaves the decision where it was",
    )


def false_isolation() -> DecisionProblem:
    """A reading that lowers the expected loss without isolating the cause.

    One cheap reading moves the expected loss of the current best action but
    leaves both explanations compatible; a second reading separates them. A policy
    that stops as soon as the action label stops moving returns an attribution it
    has not isolated, and on this family that costs both credit and loss. The
    readout that isolates is the one to buy first, and it is not the one with the
    larger entropy reduction.
    """

    prior = {"realised": 0.6, "not_realised": 0.4}
    weakening = AdaptiveAction(
        identifier="mode_readout",
        cost=1.0,
        outcome_model={"realised": {"high": 0.8, "low": 0.2}, "not_realised": {"high": 0.4, "low": 0.6}},
    )
    discriminating = AdaptiveAction(
        identifier="realisation_readout",
        cost=1.0,
        outcome_model={"realised": {"high": 1.0}, "not_realised": {"low": 1.0}},
    )
    return _problem(
        "false_isolation",
        (weakening, discriminating),
        budget=2.0,
        prior=prior,
        family="unsupported attribution",
        note="the cheap reading moves the expected loss but leaves both causes compatible",
    )


def repair_cascade(levels: int = 2, *, budget: float | None = None) -> DecisionProblem:
    """A chain of typed premises, each with a cheap fragile and a dear reliable supplier.

    Premise i can only be supplied once premise i-1 is, and the deciding readout
    needs the last premise. The policy therefore has to spend a fixed budget down a
    chain: buying cheap at one level saves a unit now and can cost the whole
    decision later, so the correct choice at level i depends on how much budget is
    left and how many levels remain. That is the structure the frozen real-data
    grammar did not have.
    """

    cheap_cost = 0.5
    reliable_cost = 1.0
    readout_cost = 0.5
    actions: list[AdaptiveAction] = []
    for level in range(1, levels + 1):
        prerequisite = (f"premise_{level - 1}",) if level > 1 else ()
        actions.append(
            AdaptiveAction(
                identifier=f"cheap_supplier_{level}",
                cost=cheap_cost,
                role="premise_supplier",
                prerequisites=prerequisite,
                outcome_model={h: {"ok": 0.5, "failed": 0.5} for h in HYPOTHESES},
                supplies={"ok": (f"premise_{level}",)},
            )
        )
        actions.append(
            AdaptiveAction(
                identifier=f"reliable_supplier_{level}",
                cost=reliable_cost,
                role="premise_supplier",
                prerequisites=prerequisite,
                outcome_model={h: {"ok": 1.0} for h in HYPOTHESES},
                supplies={"ok": (f"premise_{level}",)},
                source=REPAIR_SOURCE,
            )
        )
    actions.append(_separating("gated_readout", readout_cost, prerequisites=(f"premise_{levels}",)))
    total = budget if budget is not None else reliable_cost * levels + readout_cost
    return _problem(
        f"repair_cascade_{levels}",
        tuple(actions),
        budget=total,
        family="repair cascade under a binding budget",
        note="several suppliers per premise, prerequisites chained, budget fixed before the chain is resolvable",
    )


def attribution_is_expensive() -> DecisionProblem:
    """Isolation costs more than the expected loss of deciding without it.

    The prior favours one explanation strongly enough that acting on it beats a
    deferral, and the only measurement that would separate the two costs more than
    the expected loss it removes. Under the loss convention every loss-minimising
    policy then returns a causal attribution it has not isolated, including the
    exact reference. This family exists to price the discipline the framework
    claims: refusing that attribution is not free, and the price is one number.
    """

    prior = {"realised": 0.7, "not_realised": 0.3}
    weakening = AdaptiveAction(
        identifier="mode_readout",
        cost=0.5,
        outcome_model={"realised": {"high": 0.8, "low": 0.2}, "not_realised": {"high": 0.4, "low": 0.6}},
    )
    isolating = AdaptiveAction(
        identifier="isolating_readout",
        cost=3.5,
        outcome_model={"realised": {"high": 1.0}, "not_realised": {"low": 1.0}},
    )
    return _problem(
        "attribution_is_expensive",
        (weakening, isolating),
        budget=4.0,
        prior=prior,
        family="price of the attribution discipline",
        note="isolating the two causes costs more than acting on the prior is expected to lose",
    )


FAMILIES: Mapping[str, Callable[[], DecisionProblem]] = {
    "flat_grammar": flat_grammar,
    "supplier_choice_binding_budget": supplier_choice_binding_budget,
    "supplier_ladder_2": lambda: supplier_ladder(2),
    "supplier_ladder_3": lambda: supplier_ladder(3),
    "repair_cascade_2": lambda: repair_cascade(2),
    "repair_cascade_3": lambda: repair_cascade(3),
    "repair_cascade_4": lambda: repair_cascade(4),
    "information_is_not_value": information_is_not_value,
    "false_isolation": false_isolation,
    "attribution_is_expensive": attribution_is_expensive,
}


def policy_set(problem: DecisionProblem, *, max_depth: int = 5) -> Mapping[str, Policy]:
    """The controls every family is scored against, resource-matched by construction."""

    policies: dict[str, Policy] = {
        "optimal_contingent": optimal_policy(problem),
        "ambiguity_aware_repair": ambiguity_aware_repair_policy,
        "reactive_prerequisite": reactive_prerequisite_policy,
        "information_gain_per_cost": information_gain_policy,
    }
    for depth in range(1, max_depth + 1):
        policies[f"lookahead_{depth}"] = lookahead_policy(depth)
    return policies


def run_family(problem: DecisionProblem, *, max_depth: int = 5) -> Mapping[str, object]:
    """Exact performance of every policy on one family, with what it claimed to know."""

    root_report = ambiguity_report(problem)
    rows = [
        evaluate_with_attribution(policy, problem).as_row(name)
        for name, policy in policy_set(problem, max_depth=max_depth).items()
    ]
    depth = required_depth(problem, max_depth=max_depth)
    return {
        "identifier": problem.identifier,
        "family": problem.family,
        "note": problem.note,
        "hypotheses": list(problem.hypotheses),
        "prior": dict(problem.prior),
        "budget": problem.budget,
        "actions": [
            {"identifier": action.identifier, "cost": action.cost, "role": action.role}
            for action in problem.actions
        ],
        "root_ambiguity": {
            "candidates": list(root_report.candidates),
            "isolating_actions": list(root_report.isolating_actions),
            "cheapest_separating_bundles": [
                {"bundle": list(bundle), "cost": cost}
                for bundle, cost in root_report.separating_bundles[:5]
            ],
            "bundle_search_complete": root_report.complete,
        },
        "required_lookahead_depth": depth,
        "repair_catalogue_certificate": repair_catalogue_certificate(problem, catalogue_source=REPAIR_SOURCE),
        "policies": rows,
    }


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    out = Path(argv[0]) if argv else Path("contingent_suite_results.json")
    payload = {
        "scope": (
            "Constructed finite decision problems. They establish algorithm behaviour "
            "of contingent and ambiguity-aware repair against an exact reference and "
            "resource-matched controls. They are not biological evidence."
        ),
        "loss_convention": "correct 0, wrong 10, deferral 4, plus the cost of every acquired action",
        "families": {name: run_family(builder()) for name, builder in FAMILIES.items()},
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for name, family in payload["families"].items():
        optimal = next(row for row in family["policies"] if row["policy"] == "optimal_contingent")
        aware = next(row for row in family["policies"] if row["policy"] == "ambiguity_aware_repair")
        print(
            f"{name:34s} optimal={optimal['expected_loss']:8.4f} "
            f"ambiguity_aware={aware['expected_loss']:8.4f} "
            f"required_depth={family['required_lookahead_depth']} "
            f"unsupported={aware['unsupported_attribution']:.4f} "
            f"repair_catalogue_value={family['repair_catalogue_certificate']['value_of_the_repair_catalogue']}"
        )
    print(f"written: {out}")
    return 0


if __name__ == "__main__":  # pragma: no cover - direct script execution
    raise SystemExit(main())
