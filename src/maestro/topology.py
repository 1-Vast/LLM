"""The dependency topology of a registered evidence menu under one intervention profile.

File summary
- Path: src/maestro/topology.py
- Purpose: treat the action catalogue as a directed graph and answer, once per round,
  the structural questions planning keeps asking one candidate at a time: which actions
  can run now, how many supplier steps each one is away from running, which premises no
  registered action can ever supply, and where the supply declarations loop.
- Core points:
  - Nodes are registered actions with non-negative cost. An action's open premises are
    its prerequisites and interpretation gate that the profile has not measured. There
    is an edge ``a -> s`` when ``s`` supplies one of ``a``'s open premises.
  - ``steps_to_executable`` is the length of the shortest supplier chain ending at the
    action (1 when it can run now), computed by one multi-source breadth-first search
    over reversed edges from the executable frontier. It matches the chain semantics
    of `MAESTROAgent.executable_chain`, where one supplier resolves one step.
  - It is a lower bound on any chain the depth-bounded search can find, because that
    search additionally forbids revisiting a node. Pruning a supplier whose bound
    exceeds the remaining depth therefore never changes the search's result.
  - ``unsupplied_premises`` is the capability gap: an open premise no registered action
    supplies. An action whose every open premise is unsupplied cannot become runnable
    by buying anything on the menu; only a new capability or a real result helps.
  - ``supply_cycles`` are the strongly connected components (Tarjan) with more than one
    action or a self-loop: declarations under which actions only supply each other.
  - This is structure, not biology: an edge says a declaration names a field, not that
    the measurement would succeed or be informative.
- Interfaces: `ActionTopology`, `ActionTopology.build`, `.steps_to_executable`,
  `.executable_now`, `.ungrounded`, `.unsupplied_premises`, `.supply_cycles`,
  `.within`, `.summary`
- Depends on: maestro.models
"""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Mapping, Sequence

from .models import EvidenceAction, FunctionalInterventionProfile


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
