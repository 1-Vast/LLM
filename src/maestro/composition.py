"""Executable action topology, exact budgeted selection, and gated plan composition."""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from itertools import combinations
from typing import Iterable, Mapping, Sequence

from .models import (
    CompositionRule,
    EvidenceAction,
    FunctionalInterventionProfile,
    GatedEvidencePlan,
    MechanismContrast,
)


@dataclass(frozen=True)
class BudgetedEvidencePlan:
    """Current executable actions only; unmet prerequisites remain explicit."""

    actions: tuple[EvidenceAction, ...]
    covered: frozenset[str]
    uncovered: frozenset[str]
    total_cost: float
    waiting_for_prerequisites: tuple[str, ...]
    rejection_reasons: Mapping[str, str] = field(default_factory=dict)


class BudgetedEvidenceSelector:
    """Choose an exact small-set cover without claiming global research utility."""

    def __init__(self, *, maximum_candidates: int = 16):
        self._maximum_candidates = maximum_candidates

    def select(
        self,
        required: frozenset[str],
        actions: Sequence[EvidenceAction],
        profile: FunctionalInterventionProfile,
        budget: float,
        *,
        weights: Mapping[str, float] | None = None,
        action_priorities: Mapping[str, float] | None = None,
    ) -> BudgetedEvidencePlan:
        if budget < 0:
            raise ValueError("Budget must be nonnegative.")
        if not required:
            return BudgetedEvidencePlan((), frozenset(), frozenset(), 0.0, ())
        executable, waiting = self._partition(actions, profile)
        if len(executable) > self._maximum_candidates:
            raise ValueError(
                f"Candidate pool has {len(executable)} actions; maximum is {self._maximum_candidates}."
            )
        weighted = weights or {}
        priorities = action_priorities or {}
        best: tuple[EvidenceAction, ...] = ()
        best_covered: frozenset[str] = frozenset()
        best_cost = 0.0
        for size in range(1, len(executable) + 1):
            for candidate in combinations(executable, size):
                cost = sum(action.cost for action in candidate)
                if cost > budget:
                    continue
                covered = frozenset().union(*(set(action.distinguishes) for action in candidate)) & required
                if self._is_better(candidate, covered, cost, best, best_covered, best_cost, weighted, priorities):
                    best, best_covered, best_cost = candidate, covered, cost
        return BudgetedEvidencePlan(
            actions=best,
            covered=best_covered,
            uncovered=required - best_covered,
            total_cost=best_cost,
            waiting_for_prerequisites=waiting,
        )

    @staticmethod
    def _partition(
        actions: Sequence[EvidenceAction], profile: FunctionalInterventionProfile
    ) -> tuple[tuple[EvidenceAction, ...], tuple[str, ...]]:
        executable: list[EvidenceAction] = []
        waiting: list[str] = []
        for action in actions:
            if action.cost < 0:
                continue
            missing = profile.unmeasured(action.prerequisites)
            if missing:
                waiting.append(f"{action.identifier}: {', '.join(missing)}")
            else:
                executable.append(action)
        return tuple(executable), tuple(waiting)

    @staticmethod
    def _is_better(
        candidate: tuple[EvidenceAction, ...],
        covered: frozenset[str],
        cost: float,
        best: tuple[EvidenceAction, ...],
        best_covered: frozenset[str],
        best_cost: float,
        weights: Mapping[str, float],
        action_priorities: Mapping[str, float],
    ) -> bool:
        score = sum(weights.get(identifier, 1.0) for identifier in covered)
        best_score = sum(weights.get(identifier, 1.0) for identifier in best_covered)
        if score != best_score:
            return score > best_score
        if cost != best_cost:
            return cost < best_cost
        # A bigger set is never preferred at equal coverage and equal cost: extra
        # arms buy redundancy, not information, and must not be rewarded.
        if len(candidate) != len(best):
            return len(candidate) < len(best)
        priority = sum(action_priorities.get(action.identifier, 0.0) for action in candidate)
        best_priority = sum(action_priorities.get(action.identifier, 0.0) for action in best)
        if priority != best_priority:
            return priority > best_priority
        return tuple(action.identifier for action in candidate) < tuple(action.identifier for action in best)


@dataclass(frozen=True)
class ActionTopology:
    """Supplier graph of one menu under one profile, with its derived structure."""

    open_premises: Mapping[str, tuple[str, ...]]
    suppliers: Mapping[str, tuple[str, ...]]
    steps_to_executable: Mapping[str, float]
    unsupplied_premises: Mapping[str, tuple[str, ...]]
    supply_cycles: tuple[tuple[str, ...], ...]
    order: tuple[str, ...] = field(default=())

    @classmethod
    def build(
        cls, actions: Sequence[EvidenceAction], profile: FunctionalInterventionProfile
    ) -> "ActionTopology":
        """Analyse the menu in O(actions + declared supply edges)."""

        nodes = [action for action in actions if action.cost >= 0]
        order = tuple(dict.fromkeys(action.identifier for action in nodes))
        by_field: dict[str, list[str]] = {}
        for action in nodes:
            for name in action.supplies:
                by_field.setdefault(name, [])
                if action.identifier not in by_field[name]:
                    by_field[name].append(action.identifier)
        open_premises: dict[str, tuple[str, ...]] = {}
        suppliers: dict[str, tuple[str, ...]] = {}
        unsupplied: dict[str, tuple[str, ...]] = {}
        for action in nodes:
            if action.identifier in open_premises:
                continue  # a duplicated identifier is analysed once, as the search sees it
            missing = profile.unmeasured(action.required_premises)
            open_premises[action.identifier] = missing
            suppliers[action.identifier] = tuple(
                dict.fromkeys(supplier for name in missing for supplier in by_field.get(name, ()))
            )
            gaps = tuple(name for name in missing if not by_field.get(name))
            if gaps:
                unsupplied[action.identifier] = gaps
        return cls(
            open_premises=open_premises,
            suppliers=suppliers,
            steps_to_executable=_steps(order, open_premises, suppliers),
            unsupplied_premises=unsupplied,
            supply_cycles=_cycles(order, suppliers),
            order=order,
        )

    @property
    def executable_now(self) -> tuple[str, ...]:
        return tuple(name for name in self.order if self.steps_to_executable[name] == 1)

    @property
    def ungrounded(self) -> tuple[str, ...]:
        """Actions no chain of registered suppliers can make runnable under this profile."""

        return tuple(name for name in self.order if math.isinf(self.steps_to_executable[name]))

    def within(self, identifier: str, depth: int) -> bool:
        """Whether a supplier chain of at most ``depth`` actions could end at this action.

        Unknown identifiers answer ``True``: the bound only prunes what it has analysed.
        """

        steps = self.steps_to_executable.get(identifier)
        return steps is None or steps <= depth

    def summary(self) -> dict[str, object]:
        """A compact, JSON-ready view for the run log and the repair planner."""

        blocked = {
            name: (int(steps) if math.isfinite(steps) else None)
            for name, steps in self.steps_to_executable.items()
            if steps != 1
        }
        return {
            "executable_now": list(self.executable_now),
            "steps_to_executable": {name: blocked[name] for name in self.order if name in blocked},
            "unsupplied_premises": {name: list(fields) for name, fields in self.unsupplied_premises.items()},
            "supply_cycles": [list(component) for component in self.supply_cycles],
        }


def _steps(
    order: Sequence[str],
    open_premises: Mapping[str, tuple[str, ...]],
    suppliers: Mapping[str, tuple[str, ...]],
) -> dict[str, float]:
    """Shortest supplier-chain length to each action, by BFS from the runnable frontier."""

    dependents: dict[str, list[str]] = {name: [] for name in order}
    for name in order:
        for supplier in suppliers[name]:
            dependents[supplier].append(name)
    steps: dict[str, float] = {name: math.inf for name in order}
    queue: deque[str] = deque()
    for name in order:
        if not open_premises[name]:
            steps[name] = 1
            queue.append(name)
    while queue:
        current = queue.popleft()
        for dependent in dependents[current]:
            if math.isinf(steps[dependent]):
                steps[dependent] = steps[current] + 1
                queue.append(dependent)
    return steps


def _cycles(order: Sequence[str], suppliers: Mapping[str, tuple[str, ...]]) -> tuple[tuple[str, ...], ...]:
    """Strongly connected components that loop: size above one, or a self-supplying action.

    Iterative Tarjan, so a long declared chain cannot exhaust the recursion limit.
    """

    index: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    components: list[tuple[str, ...]] = []
    rank = {name: position for position, name in enumerate(order)}
    counter = 0
    for root in order:
        if root in index:
            continue
        work: list[tuple[str, int]] = [(root, 0)]
        while work:
            node, position = work.pop()
            if position == 0:
                index[node] = low[node] = counter
                counter += 1
                stack.append(node)
                on_stack.add(node)
            successors = suppliers[node]
            if position < len(successors):
                work.append((node, position + 1))
                successor = successors[position]
                if successor not in index:
                    work.append((successor, 0))
                elif successor in on_stack:
                    low[node] = min(low[node], index[successor])
                continue
            if low[node] == index[node]:
                component: list[str] = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    component.append(member)
                    if member == node:
                        break
                if len(component) > 1 or node in suppliers[node]:
                    components.append(tuple(sorted(component, key=rank.__getitem__)))
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])
    return tuple(components)


@dataclass(frozen=True)
class PlanEvaluation:
    """One composed plan with the declared quantities that placed it.

    ``worst_case_residual`` is the number of hypotheses that would still be
    compatible under the readout's least favourable declared outcome. It is a
    worst-declared-case count, not an expected value: the declarations carry no
    probabilities, and inventing them here is exactly the failure the outcome
    layer exists to prevent.

    ``gate_detection_power`` is the gate's *declared* chance of returning a
    qualified, interpretable result. It is the only declared quantity that
    distinguishes two gates which answer the same question at different prices,
    and when it is undeclared the ordering falls back to cost rather than
    guessing.
    """

    plan: GatedEvidencePlan
    worst_case_residual: int
    objective: float
    gate_outcomes: tuple[str, ...]
    readout_outcomes: tuple[str, ...]
    gate_detection_power: float | None = None


def composition_is_legal(plan: GatedEvidencePlan) -> tuple[str, ...]:
    """Every reason this composition is not admissible, named individually.

    A composition is admissible only when the gate is the thing that makes the
    readout interpretable. A pair where the readout's premise is already
    measured, or where the gate supplies nothing the readout needs, is a
    substitution or a discount and is refused by name rather than admitted as a
    plan.
    """

    problems: list[str] = []
    if plan.gate.identifier == plan.readout.identifier:
        problems.append("gate_and_readout_are_the_same_action")
    authorization = plan.authorization()
    discharged = set(plan.gate.supplies)
    if not authorization.premise:
        problems.append("plan_declares_no_premise_to_repair")
    elif authorization.premise not in discharged:
        # An authorization the gate cannot grant is the failure this record
        # exists to make visible: the plan would be composed on a coincidence.
        problems.append("gate_does_not_grant_the_authorized_premise")
    if not discharged:
        problems.append("gate_supplies_nothing")
    if plan.outstanding_prerequisites():
        problems.append(
            "readout_prerequisite_not_discharged_by_gate:" + ",".join(plan.outstanding_prerequisites())
        )
    if not plan.readout.expected_outcomes:
        problems.append("readout_declares_no_expected_outcomes")
    if plan.readout.cost < 0 or plan.gate.cost < 0:
        problems.append("negative_component_cost")
    return tuple(problems)


def unmet_prerequisites(
    actions: Sequence[EvidenceAction], profile: FunctionalInterventionProfile
) -> dict[str, tuple[str, ...]]:
    """Which declared prerequisites each action still lacks, by the profile alone.

    This is the same question :meth:`ContrastCheck` answers, asked here so the
    caller can pass either source. The repair path passes the check's own named
    failures, because a repair directed at anything else is not directed.
    """

    return {
        action.identifier: profile.unmeasured(action.prerequisites)
        for action in actions
    }


class PlanComposer:
    """Compose registered actions into gated plans a menu-only policy cannot reach.

    The composer is a capability of the controller, not a solver: it enumerates
    a bounded, declared closure and hands the result to the same check the menu
    path uses. It never edits an action, never supplies a field it was not
    declared to supply, and never composes a plan whose readout could be bought
    without its gate.
    """

    def __init__(self, rule: CompositionRule):
        if rule.max_components != 2:
            raise ValueError("Only two-component compositions are registered.")
        self._rule = rule

    @property
    def rule(self) -> CompositionRule:
        return self._rule

    def compose(
        self,
        contrast: MechanismContrast,
        actions: Sequence[EvidenceAction],
        missing: Mapping[str, Iterable[str]],
        *,
        identifiers: frozenset[str] | None = None,
    ) -> tuple[GatedEvidencePlan, ...]:
        """Every admissible gated plan over the catalogue for this contrast.

        ``missing`` names, per action identifier, the prerequisites that action
        still lacks. ``identifiers`` restricts composition to the hypotheses
        still open, so a repair cannot reintroduce an explanation the evidence
        already removed.
        """

        wanted = identifiers if identifiers is not None else contrast.identifiers()
        plans: list[GatedEvidencePlan] = []
        for readout in actions:
            if readout.cost < 0 or not readout.expected_outcomes:
                continue
            if not wanted.issubset(readout.distinguishes):
                continue
            gate_field = readout.interpretation_gate
            if gate_field is None:
                # Composition exists to restore interpretability. A readout with
                # no declared gate has nothing for a plan to restore, and an
                # unmet prerequisite remains the existing single-action repair.
                continue
            outstanding = tuple(dict.fromkeys((gate_field,) + tuple(missing.get(readout.identifier, ()))))
            for gate in actions:
                if gate.identifier == readout.identifier or gate.cost < 0:
                    continue
                if tuple(missing.get(gate.identifier, ())):
                    # The gate must be runnable now; a plan whose first step is
                    # blocked is not a plan, it is an aspiration. Chaining over
                    # the gate's own suppliers is the executable-chain step.
                    continue
                if not set(gate.supplies) & set(outstanding):
                    continue
                plan = GatedEvidencePlan(
                    identifier=f"plan[{gate.identifier}|{readout.identifier}]",
                    gate=gate,
                    readout=readout,
                    rule=self._rule,
                    note=(
                        f"{gate.identifier} measures the interpretation premise; "
                        f"{readout.identifier} is bought only if it passes."
                    ),
                )
                if composition_is_legal(plan):
                    continue
                plans.append(plan)
        return tuple(sorted(plans, key=lambda item: (item.cost, item.identifier)))


def rank_plans(
    plans: Sequence[GatedEvidencePlan],
    contrast: MechanismContrast,
    *,
    cost_weight: float = 0.25,
) -> tuple[PlanEvaluation, ...]:
    """Order composed plans by declared worst case plus weighted cost.

    The ordering is the same robust criterion the evidence planner already uses,
    so a composed plan competes with a menu plan on one scale instead of being
    promoted by a separate rule written for it. Two plans that resolve the same
    residual are separated by the gate's declared detection power before price,
    because an assay that answers the question one time in two is not cheaper
    than one that answers it, it is a different purchase.
    """

    pair = tuple(hypothesis.identifier for hypothesis in contrast.hypotheses)
    order = {identifier: index for index, identifier in enumerate(pair)}
    evaluations: list[PlanEvaluation] = []
    for plan in plans:
        declared = plan.readout.expected_outcomes
        if not set(pair).issubset(declared):
            continue
        outcomes = tuple(dict.fromkeys(declared[name] for name in pair))
        surviving = 1
        for outcome in outcomes:
            count = sum(1 for name in pair if declared[name] == outcome)
            if count == 1:
                # One declared outcome would leave exactly one hypothesis; a
                # plan is scored by the worst branch, so the branch that
                # separates cannot be the one that sets the score.
                continue
            surviving = max(surviving, count)
        evaluations.append(
            PlanEvaluation(
                plan=plan,
                worst_case_residual=surviving,
                objective=surviving + cost_weight * plan.cost,
                gate_outcomes=tuple(sorted(set(plan.gate.expected_outcomes.values()))),
                readout_outcomes=tuple(sorted(set(outcomes))),
                gate_detection_power=plan.gate.detection_power,
            )
        )
    return tuple(
        sorted(
            evaluations,
            key=lambda item: (
                item.worst_case_residual,
                -(item.gate_detection_power if item.gate_detection_power is not None else 0.0),
                item.objective,
                tuple(order.get(name, len(order)) for name in item.plan.readout.distinguishes),
                item.plan.identifier,
            ),
        )
    )
