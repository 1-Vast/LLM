"""Score the repair catalogue on the frozen real packages, as a declared-model bound.

File summary
- Path: src/evaluation/real_contingent.py
- Purpose: take the contingent-repair instrument off the constructed families and put
  it on the cases the project actually froze, so "what is a correctly typed supplier
  worth here" is a number on real case declarations rather than an illustration.
- Core points:
  - Every case becomes a `DecisionProblem` using only public material: the registered
    actions, their declared per-hypothesis outcomes, their declared costs and
    prerequisites, and the development action each hypothesis proposes.
  - The outcome model is the case author's *declaration* made determinate -- outcome
    `o` with probability 1 for the hypothesis that declares it. It is not a measured
    probability, and nothing here is biological evidence.
  - The repair under test is the one the 2026-09-13 record already measured by hand: a
    supplier whose declared quantity does not satisfy a typed prerequisite discharges
    nothing, and a correctly typed replacement restores the action that depended on it.
  - The certificate is the difference between two exact optima, so it bounds every
    policy restricted to the unrepaired menu, at any search depth.
- Interfaces: `case_problem`, `retyped_repair`, `measure_case`, `measure_package`, `main`
- Depends on: evaluation.cases, evaluation.adaptive_reference, evaluation.contingent
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluation.adaptive_reference import DEFER, AdaptiveAction, DecisionProblem  # noqa: E402
from evaluation.cases import CaseRepository  # noqa: E402
from evaluation.contingent import decisive, repair_catalogue_certificate  # noqa: E402

REPAIR_SOURCE = "repair_catalogue"
WRONG_DECISION_LOSS = 10.0
DEFERRAL_LOSS = 4.0
DEFAULT_REPAIR_PREMIUM = 0.5


def case_problem(
    case,
    *,
    repair_premium: float = DEFAULT_REPAIR_PREMIUM,
    retype_matched_supplier: bool = False,
) -> tuple[DecisionProblem, Mapping[str, object]]:
    """A case as a decision problem, optionally in the counterfactual retyped world.

    With ``retype_matched_supplier`` false this is the case exactly as declared, which
    is the control. With it true, the supplier that a typed prerequisite depends on is
    retyped: no identifier, no record and no cost changes, only the quantity it
    declares, so it no longer discharges the premise and supplies nothing. A correctly
    typed replacement is then registered under the repair source.

    The retyped world is a counterfactual, and it is labelled as one everywhere it is
    reported. It is the manipulation the 2026-09-13 record already ran by hand when it
    measured that retyping only the supplier, changing no name and no record, blocks
    the dependent action in 27 of 27 cases.
    """

    hypotheses = tuple(str(entry["identifier"]) for entry in case.hypotheses)
    proposed = {str(entry["identifier"]): str(entry["development_action"]) for entry in case.hypotheses}
    decisions = tuple(dict.fromkeys((*proposed.values(), DEFER)))
    loss = {
        decision: {h: (0.0 if proposed[h] == decision else WRONG_DECISION_LOSS) for h in hypotheses}
        for decision in decisions
    }
    loss[DEFER] = {h: DEFERRAL_LOSS for h in hypotheses}

    registry = getattr(case, "premise_registry", {}) or {}
    blocked: Mapping[str, object] | None = None
    retyped: set[str] = set()
    if retype_matched_supplier:
        for item in case.actions:
            action = item.action
            for name in action.prerequisites:
                requirement = registry.get(name)
                if requirement is None or not requirement.is_typed:
                    continue
                for candidate in case.actions:
                    if name not in candidate.action.supplies:
                        continue
                    if candidate.action.identifier == action.identifier:
                        continue
                    if candidate.action.quantity.value != requirement.quantity.value:
                        continue
                    retyped.add(candidate.action.identifier)
                    if blocked is None:
                        blocked = {
                            "dependent_action": action.identifier,
                            "premise": name,
                            "requirement": {
                                "quantity": requirement.quantity.value,
                                "entity": requirement.entity,
                                "site": requirement.site,
                                "units": requirement.units,
                                "context_identifier": requirement.context_identifier,
                                "time_hours": requirement.time_hours,
                            },
                            "supplier": candidate.action.identifier,
                            "supplier_quantity": candidate.action.quantity.value,
                            "supplier_cost": float(candidate.action.cost),
                            "counterfactual": "the supplier is retyped; no name, record or cost changes",
                        }
                    break

    actions: list[AdaptiveAction] = []
    for item in case.actions:
        action = item.action
        outcomes = {h: action.expected_outcomes.get(h, "unknown") for h in hypotheses}
        supplies: dict[str, tuple[str, ...]] = {}
        if action.identifier not in retyped:
            for outcome in set(outcomes.values()):
                supplies[outcome] = tuple(action.supplies)
        actions.append(
            AdaptiveAction(
                identifier=action.identifier,
                cost=float(action.cost),
                outcome_model={h: {outcomes[h]: 1.0} for h in hypotheses},
                prerequisites=tuple(action.prerequisites),
                supplies=supplies,
                role="premise_supplier" if action.supplies else "readout",
                source="menu",
            )
        )

    if blocked is not None:
        requirement = registry[str(blocked["premise"])]
        supplier = case.action(str(blocked["supplier"]))
        outcomes = {h: supplier.action.expected_outcomes.get(h, "unknown") for h in hypotheses}
        actions.append(
            AdaptiveAction(
                identifier=f"{supplier.action.identifier}__retyped",
                cost=float(supplier.action.cost) + repair_premium,
                outcome_model={h: {outcomes[h]: 1.0} for h in hypotheses},
                prerequisites=tuple(supplier.action.prerequisites),
                supplies={outcome: (requirement.field,) for outcome in set(outcomes.values())},
                role="premise_supplier",
                source=REPAIR_SOURCE,
            )
        )

    problem = DecisionProblem(
        identifier=case.identifier,
        hypotheses=hypotheses,
        prior={h: 1.0 / len(hypotheses) for h in hypotheses},
        actions=tuple(actions),
        budget=float(case.budget),
        decisions=decisions,
        loss=loss,
        family="frozen real package",
        note="declared outcome model, determinate per hypothesis; not a measured probability",
    )
    problems = problem.validate()
    if problems:
        raise ValueError(f"{case.identifier}: {', '.join(problems)}")
    return problem, (blocked or {})


@dataclass(frozen=True)
class CaseMeasurement:
    """One frozen case's declared-model repair certificate, control and counterfactual."""

    identifier: str
    repair: Mapping[str, object]
    as_declared: Mapping[str, object]
    counterfactual: Mapping[str, object]
    actions_without_a_declared_outcome: int
    individually_decisive_actions: int
    cheapest_decisive_cost: float | None

    def as_row(self) -> Mapping[str, object]:
        return {
            "case": self.identifier,
            "repair": dict(self.repair),
            "as_declared_menu_only": self.as_declared["menu_only_optimum"],
            "as_declared_value": self.as_declared["value_of_the_repair_catalogue"],
            "retyped_menu_only": self.counterfactual["menu_only_optimum"],
            "retyped_closed": self.counterfactual["closed_optimum"],
            "counterfactual_value": self.counterfactual["value_of_the_repair_catalogue"],
            "complete": bool(self.as_declared["complete"] and self.counterfactual["complete"]),
            "actions_without_a_declared_outcome": self.actions_without_a_declared_outcome,
            "individually_decisive_actions": self.individually_decisive_actions,
            "cheapest_decisive_cost": self.cheapest_decisive_cost,
        }


def measure_case(case, *, repair_premium: float = DEFAULT_REPAIR_PREMIUM) -> CaseMeasurement:
    declared, _ = case_problem(case, repair_premium=repair_premium, retype_matched_supplier=False)
    counterfactual, repair = case_problem(case, repair_premium=repair_premium, retype_matched_supplier=True)
    undeclared = sum(
        1
        for item in case.actions
        if not any(h in item.action.expected_outcomes for h in declared.hypotheses)
    )
    decisive_singles = [
        action
        for action in counterfactual.actions
        if decisive(counterfactual, (), (action,))
    ]
    return CaseMeasurement(
        identifier=case.identifier,
        repair=repair,
        as_declared=repair_catalogue_certificate(declared, catalogue_source=REPAIR_SOURCE),
        counterfactual=repair_catalogue_certificate(counterfactual, catalogue_source=REPAIR_SOURCE),
        actions_without_a_declared_outcome=undeclared,
        individually_decisive_actions=len(decisive_singles),
        cheapest_decisive_cost=min((action.cost for action in decisive_singles), default=None),
    )


def measure_package(directory: Path, *, repair_premium: float = DEFAULT_REPAIR_PREMIUM) -> Mapping[str, object]:
    root = Path(directory)
    repository = CaseRepository(root / "public", root / "private")
    rows = [measure_case(case.public, repair_premium=repair_premium) for case, _ in repository.load()]
    certified = [row for row in rows if row.as_declared["complete"] and row.counterfactual["complete"]]
    with_repair = [row for row in certified if row.repair]
    positive = [
        row
        for row in with_repair
        if (row.counterfactual["value_of_the_repair_catalogue"] or 0) > 0
    ]
    return {
        "package": root.as_posix(),
        "repair_premium": repair_premium,
        "cases": len(rows),
        "certified": len(certified),
        "cases_needing_a_typed_repair": len(with_repair),
        "cases_where_the_repair_is_worth_something": len(positive),
        "median_counterfactual_value": _median(
            [row.counterfactual["value_of_the_repair_catalogue"] for row in with_repair]
        ),
        "cases_where_the_declared_menu_already_decides_without_a_repair": sum(
            1 for row in certified if (row.as_declared["value_of_the_repair_catalogue"] or 0) == 0
        ),
        "median_individually_decisive_actions_per_retyped_case": _median(
            [float(row.individually_decisive_actions) for row in with_repair]
        ),
        "minimum_individually_decisive_actions_per_retyped_case": min(
            (row.individually_decisive_actions for row in with_repair), default=None
        ),
        "rows": [row.as_row() for row in rows],
        "reading": (
            "The certificate is a bound on every policy restricted to the unrepaired menu. "
            "The as-declared column is the shipped package and is the control; the retyped "
            "column is a counterfactual in which the supplier a typed prerequisite depends "
            "on declares a different quantity, with no name, record or cost changed. Both "
            "are computed from the case author's declared outcomes, so they measure the "
            "declaration, not the biology."
        ),
    }


def _median(values: Sequence[float]) -> float | None:
    finite = sorted(value for value in values if value is not None)
    if not finite:
        return None
    middle = len(finite) // 2
    if len(finite) % 2:
        return float(finite[middle])
    return float((finite[middle - 1] + finite[middle]) / 2)


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    directory = Path(argv[0]) if argv else Path("data/evaluation/cases/real_v3")
    out = Path(argv[1]) if len(argv) > 1 else Path("real_contingent_results.json")
    payload = measure_package(directory)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"{payload['package']}: cases={payload['cases']} certified={payload['certified']} "
        f"needing_a_typed_repair={payload['cases_needing_a_typed_repair']} "
        f"worth_something={payload['cases_where_the_repair_is_worth_something']} "
        f"median_counterfactual_value={payload['median_counterfactual_value']} "
        f"declared_menu_already_decides={payload['cases_where_the_declared_menu_already_decides_without_a_repair']}"
    )
    print(f"written: {out}")
    return 0


if __name__ == "__main__":  # pragma: no cover - direct script execution
    raise SystemExit(main())
