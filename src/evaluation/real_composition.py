"""What the composition repair is worth on the frozen real cases, as an exact certificate.

File summary
- Path: src/evaluation/real_composition.py
- Purpose: put the composition operator on the cases the project actually froze. The
  2026-09-13 certificate showed the *retyping* repair is worth 0.000 on `real_v3`; this
  module measures the other repair the framework now has, the composed gated plan, and
  reports where it is worth something, with the negative control that removes it.
- Core points:
  - The re-reading is declared. A case writes its prerequisite as a legality condition:
    without it the readout may not run. The gated reading keeps the same action, cost and
    premise and makes the premise the thing that makes the result interpretable instead,
    so the readout is legal and uninterpretable without it. Nothing else changes.
  - Both optima are exact, so their difference bounds every policy restricted to the
    unrepaired menu at any search depth. The saving is swept, and a zero saving keeps the
    composed object but buys nothing: that is the attribution control.
  - Two different gains are separated: at the shipped budget the composition usually
    saves its declared saving, and below the sequence cost it becomes the only affordable
    deciding route, which is a feasibility gain of a different size.
- Interfaces: `gated_case_problem`, `required_gate_pairs`, `composition_certificate`,
  `minimum_saving`, `measure_package`, `main`
- Depends on: evaluation.cases, evaluation.adaptive_reference, evaluation.composition
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluation.adaptive_reference import DEFER, AdaptiveAction, DecisionProblem, solve_optimal_policy  # noqa: E402
from evaluation.cases import CaseRepository  # noqa: E402
from evaluation.composition import composition_closure, menu_only  # noqa: E402
from maestro.models import CompositionRule  # noqa: E402

WRONG_DECISION_LOSS = 10.0
DEFERRAL_LOSS = 4.0
DEFAULT_BUDGET = 2.0


def required_gate_pairs(case) -> tuple[tuple[str, str], ...]:
    """The (readout, premise) pairs a case declares as a legality precondition.

    Only the first prerequisite is taken, because the registered composition rule is a
    two-component plan: one gate and one readout. A case with several prerequisites is
    therefore reported with the pair that the rule can express and not silently
    reshaped into a longer chain.
    """

    pairs: list[tuple[str, str]] = []
    for item in case.actions:
        action = item.action
        if action.prerequisites:
            pairs.append((action.identifier, action.prerequisites[0]))
    return tuple(pairs)


def gated_case_problem(case, *, budget: float = DEFAULT_BUDGET) -> DecisionProblem:
    """One frozen case under the gated reading, with the same actions, costs and losses.

    The change is exactly one field per readout: the premise moves from ``prerequisites``
    to ``interpretation_gate``, and the declared model that applies while the gate is
    unmeasured returns a qualified ``no_call`` that moves no belief. The declared outcome
    map, the action identifiers, the costs, the hypotheses, the decisions and the loss
    map are the case's own.
    """

    hypotheses = tuple(str(entry["identifier"]) for entry in case.hypotheses)
    proposed = {str(entry["identifier"]): str(entry["development_action"]) for entry in case.hypotheses}
    decisions = tuple(dict.fromkeys((*proposed.values(), DEFER)))
    loss = {
        decision: {h: (0.0 if proposed[h] == decision else WRONG_DECISION_LOSS) for h in hypotheses}
        for decision in decisions
    }
    loss[DEFER] = {h: DEFERRAL_LOSS for h in hypotheses}

    actions: list[AdaptiveAction] = []
    for item in case.actions:
        action = item.action
        declared = {h: action.expected_outcomes.get(h, "unknown") for h in hypotheses}
        gate = action.prerequisites[0] if action.prerequisites else None
        actions.append(
            AdaptiveAction(
                identifier=action.identifier,
                cost=float(action.cost),
                outcome_model={h: {declared[h]: 1.0} for h in hypotheses},
                prerequisites=() if gate else tuple(action.prerequisites),
                supplies={outcome: tuple(action.supplies) for outcome in set(declared.values())},
                role="readout",
                source="menu",
                interpretation_gate=gate,
                uninterpretable_model={h: {"no_call": 1.0} for h in hypotheses} if gate else None,
            )
        )
    return DecisionProblem(
        identifier=f"{case.identifier}@gated",
        hypotheses=hypotheses,
        prior={h: 1.0 / len(hypotheses) for h in hypotheses},
        actions=tuple(actions),
        budget=float(budget),
        decisions=decisions,
        loss=loss,
        family="frozen real package, gated reading",
        note=(
            "Declared re-reading: the case's own prerequisite becomes the interpretation "
            "gate of the same action, at the same cost, with no other field changed."
        ),
    )


@dataclass(frozen=True)
class CompositionCertificate:
    """One case, one budget and one declared saving, with both exact optima."""

    case: str
    budget: float
    saving: float
    menu_optimum: float
    closed_optimum: float
    composed_actions: int
    refused: tuple[str, ...]
    complete: bool

    @property
    def value(self) -> float:
        return self.menu_optimum - self.closed_optimum

    def as_row(self) -> Mapping[str, object]:
        return {
            "case": self.case,
            "budget": self.budget,
            "saving": self.saving,
            "menu_optimum": round(self.menu_optimum, 6),
            "closed_optimum": round(self.closed_optimum, 6),
            "value": round(self.value, 6),
            "composed_actions": self.composed_actions,
            "refused": list(self.refused),
            "complete": self.complete,
        }


def composition_certificate(
    problem: DecisionProblem, *, saving: float, case: str | None = None
) -> CompositionCertificate:
    """The exact value of the composition closure on one declared problem."""

    rule = CompositionRule("shared_plate", saving)
    closed, refused = composition_closure(problem, rule)
    menu_solution = solve_optimal_policy(menu_only(closed))
    closed_solution = solve_optimal_policy(closed)
    return CompositionCertificate(
        case=case or problem.identifier,
        budget=problem.budget,
        saving=saving,
        menu_optimum=menu_solution.expected_loss,
        closed_optimum=closed_solution.expected_loss,
        composed_actions=sum(1 for action in closed.actions if action.is_composed),
        refused=tuple(refused),
        complete=bool(menu_solution.complete and closed_solution.complete),
    )


def minimum_saving(problem: DecisionProblem, *, upper: float = 2.0, step: float = 0.05) -> float | None:
    """The smallest declared saving at which the composition is strictly worth buying.

    The saving is a declared laboratory quantity, so the useful statement is a threshold:
    below it the composed plan is unaffordable or no better, at and above it the repair is
    worth something. ``None`` means no saving in the searched range helps this case, which
    is a result and is reported as one.
    """

    saving = 0.0
    while saving <= upper + 1e-9:
        if composition_certificate(problem, saving=saving).value > 1e-9:
            return round(saving, 6)
        saving = round(saving + step, 6)
    return None


def _median(values: Sequence[float]) -> float | None:
    finite = sorted(values)
    if not finite:
        return None
    middle = len(finite) // 2
    if len(finite) % 2:
        return float(finite[middle])
    return float((finite[middle - 1] + finite[middle]) / 2)


def measure_package(
    directory: Path,
    *,
    budgets: Sequence[float] = (DEFAULT_BUDGET, 1.5, 1.0),
    savings: Sequence[float] = (0.0, 0.5, 1.0),
) -> Mapping[str, object]:
    """Every case at every (budget, saving) cell, with the thresholds that matter."""

    root = Path(directory)
    repository = CaseRepository(root / "public", root / "private")
    cases = [case.public for case, _ in repository.load()]
    cells: list[Mapping[str, object]] = []
    for budget in budgets:
        for saving in savings:
            rows = [
                composition_certificate(gated_case_problem(case, budget=budget), saving=saving, case=case.identifier)
                for case in cases
            ]
            positive = [row for row in rows if row.value > 1e-9]
            cells.append(
                {
                    "budget": budget,
                    "saving": saving,
                    "cases": len(rows),
                    "complete": sum(1 for row in rows if row.complete),
                    "cases_with_a_composed_object": sum(1 for row in rows if row.composed_actions),
                    "cases_where_the_repair_is_worth_something": len(positive),
                    "median_value_where_positive": _median([row.value for row in positive]),
                    "total_value": round(sum(row.value for row in positive), 6),
                    "rows": [row.as_row() for row in rows],
                }
            )
    thresholds = {
        case.identifier: minimum_saving(gated_case_problem(case, budget=DEFAULT_BUDGET))
        for case in cases
        if required_gate_pairs(case)
    }
    finite = [value for value in thresholds.values() if value is not None]
    return {
        "package": root.as_posix(),
        "cases": len(cases),
        "cases_with_a_prerequisite_that_can_be_read_as_a_gate": sum(
            1 for case in cases if required_gate_pairs(case)
        ),
        "cells": cells,
        "minimum_saving_at_the_shipped_budget": {
            "cases_searched": len(thresholds),
            "cases_with_a_threshold_at_or_below_2_0": len(finite),
            "median_threshold": _median(finite),
            "thresholds": thresholds,
        },
        "reading": (
            "The saving is swept because it is a declared laboratory quantity, and the zero "
            "row is the attribution control: with no shared-control saving the composed "
            "object exists and is worth exactly nothing. At the shipped budget the gain is "
            "the saving; below the sequence cost it becomes the loss the menu cannot avoid "
            "because no legal sequence fits. Every number is an exact optimum over the case "
            "author's declarations, not a measured probability."
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    directory = Path(argv[0]) if argv else Path("data/evaluation/cases/real_v3")
    out = Path(argv[1]) if len(argv) > 1 else Path("real_composition_results.json")
    payload = measure_package(directory)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"{payload['package']}: cases={payload['cases']} "
        f"with_a_gate_reading={payload['cases_with_a_prerequisite_that_can_be_read_as_a_gate']}"
    )
    for cell in payload["cells"]:
        print(
            "  budget={budget:>4} saving={saving:>4} worth_something={cases_where_the_repair_is_worth_something:>3} "
            "median_value={median_value_where_positive} total_value={total_value}".format(**cell)
        )
    print(f"written: {out}")
    return 0


if __name__ == "__main__":  # pragma: no cover - direct script execution
    raise SystemExit(main())
