"""Close a declared adaptive problem under the composition rule the controller uses.

File summary
- Path: src/evaluation/composition.py
- Purpose: let the exact reference plan over composed objects, so "the repair added an action" can be separated from "the repair selected better from the same menu".
- Core points:
  - The closure reads one declared rule: a shared-control saving, and a gate that is what makes the readout interpretable.
  - A composed object carries the gate's failing branch itself, so the contingent continuation lives inside the object rather than being assumed by the solver.
  - With a zero saving the closure is still built and buys nothing; that is the negative control for the separation claim.
- Interfaces: `Branch`, `composition_closure`, `menu_only`, `joint_branches`
- Depends on: maestro.models (the single composition rule), evaluation.adaptive_reference
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from maestro.models import CompositionRule

from .adaptive_reference import AdaptiveAction, DecisionProblem


@dataclass(frozen=True)
class Branch:
    """One observation a composed object can return, with how it was produced.

    ``steps`` names the component outcomes in execution order, so a failing gate
    is a branch of length one and a passing gate is a branch of length two. That
    single difference is what lets the object report "the readout was not
    bought", which a bundle that always buys both cannot say.
    """

    label: str
    steps: tuple[tuple[str, str], ...]

    @property
    def bought_readout(self) -> bool:
        return len(self.steps) > 1


def joint_branches(
    gate: AdaptiveAction, readout: AdaptiveAction, gate_field: str
) -> tuple[Branch, ...]:
    """Every observation the composed object can return, ordered deterministically.

    A gate outcome that discharges ``gate_field`` continues into the readout;
    every other gate outcome ends the plan, because buying the readout without
    the premise is exactly the acquisition this plan exists to avoid.
    """

    branches: list[Branch] = []
    readout_outcomes = _readout_outcomes(readout)
    for gate_outcome in gate.supplies:
        if gate_field in gate.supplies[gate_outcome]:
            for readout_outcome in readout_outcomes:
                branches.append(
                    Branch(
                        label=f"{gate_outcome}|{readout_outcome}",
                        steps=((gate.identifier, gate_outcome), (readout.identifier, readout_outcome)),
                    )
                )
        else:
            branches.append(
                Branch(label=f"{gate_outcome}|not_bought", steps=((gate.identifier, gate_outcome),))
            )
    return tuple(branches)


def _readout_outcomes(readout: AdaptiveAction) -> tuple[str, ...]:
    ordered: list[str] = []
    for distribution in readout.outcome_model.values():
        for outcome in distribution:
            if outcome not in ordered:
                ordered.append(outcome)
    return tuple(ordered)


def composition_closure(
    problem: DecisionProblem,
    rule: CompositionRule,
    *,
    source: str = "composed",
) -> tuple[DecisionProblem, tuple[str, ...]]:
    """The problem plus every gated plan admissible under ``rule``, with refusals named.

    Only two-component plans over one interpretation gate are registered. A pair
    that leaves a readout prerequisite undischarged, or whose gate supplies no
    field the readout needs, is refused by name rather than approximated.
    """

    menu = tuple(action for action in problem.actions if action.source != source)
    by_identifier = {action.identifier: action for action in menu}
    refused: list[str] = []
    composed: list[AdaptiveAction] = []
    for readout in menu:
        gate_field = readout.interpretation_gate
        if gate_field is None or not readout.uninterpretable_model:
            continue
        for gate in menu:
            if gate.identifier == readout.identifier or gate.is_composed:
                continue
            if gate_field not in {field for fields in gate.supplies.values() for field in fields}:
                continue
            outstanding = tuple(
                name
                for name in readout.prerequisites
                if not any(name in fields for fields in gate.supplies.values())
            )
            if outstanding:
                refused.append(
                    f"{gate.identifier}+{readout.identifier}:undischarged_premise:"
                    + ",".join(outstanding)
                )
                continue
            branches = joint_branches(gate, readout, gate_field)
            action = _composed_action(problem, rule, gate, readout, branches, by_identifier, source)
            if action is None:
                refused.append(f"{gate.identifier}+{readout.identifier}:no_reachable_branch")
                continue
            composed.append(action)
    closed = DecisionProblem(
        identifier=f"{problem.identifier}+composition",
        hypotheses=problem.hypotheses,
        prior=problem.prior,
        actions=menu + tuple(composed),
        budget=problem.budget,
        decisions=problem.decisions,
        loss=problem.loss,
        family=problem.family,
        note=problem.note,
        attributions=problem.attributions,
        enforce_licensing=problem.enforce_licensing,
    )
    return closed, tuple(refused)


def _composed_action(
    problem: DecisionProblem,
    rule: CompositionRule,
    gate: AdaptiveAction,
    readout: AdaptiveAction,
    branches: Sequence[Branch],
    menu: Mapping[str, AdaptiveAction],
    source: str,
) -> AdaptiveAction | None:
    """Build the composed object with a joint outcome model and declared supplies.

    The object is never gated from the outside: it carries the gate, so running
    it is what measures the premise. For each branch the declared supplies name
    exactly the fields that branch discharges, which is why a failing gate
    discharges the gate's own field and nothing else.
    """

    outcome_model: dict[str, dict[str, float]] = {h: {} for h in problem.hypotheses}
    supplies: dict[str, tuple[str, ...]] = {}
    for branch in branches:
        fields: list[str] = []
        reachable = False
        for hypothesis in problem.hypotheses:
            probability = 1.0
            for identifier, outcome in branch.steps:
                component = menu[identifier]
                probability *= component.outcome_model[hypothesis].get(outcome, 0.0)
            if probability > 0:
                reachable = True
            outcome_model[hypothesis][branch.label] = probability
        if not reachable:
            for hypothesis in problem.hypotheses:
                outcome_model[hypothesis].pop(branch.label, None)
            continue
        for identifier, outcome in branch.steps:
            fields.extend(menu[identifier].supplies.get(outcome, ()))
        supplies[branch.label] = tuple(dict.fromkeys(fields))
    if not supplies:
        return None
    gate_fields = {field for fields in gate.supplies.values() for field in fields}
    prerequisites = tuple(
        dict.fromkeys(
            tuple(gate.prerequisites)
            + tuple(name for name in readout.prerequisites if name not in gate_fields)
        )
    )
    return AdaptiveAction(
        identifier=f"{gate.identifier}+{readout.identifier}",
        cost=rule.composed_cost((gate, readout)),
        outcome_model=outcome_model,
        prerequisites=prerequisites,
        supplies=supplies,
        role="composed_plan",
        source=source,
        composed_from=(gate.identifier, readout.identifier),
    )


def menu_only(problem: DecisionProblem, *, source: str = "composed") -> DecisionProblem:
    """The same problem with the closure removed, for the action-space comparison."""

    return DecisionProblem(
        identifier=f"{problem.identifier}-menu",
        hypotheses=problem.hypotheses,
        prior=problem.prior,
        actions=tuple(action for action in problem.actions if action.source != source),
        budget=problem.budget,
        decisions=problem.decisions,
        loss=problem.loss,
        family=problem.family,
        note=problem.note,
        attributions=problem.attributions,
        enforce_licensing=problem.enforce_licensing,
    )
