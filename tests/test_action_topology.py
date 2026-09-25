"""The evidence menu as a graph: analysis results and exactness of the pruned chain search.

File summary
- Path: tests/test_action_topology.py
- Purpose: pin `maestro.topology.ActionTopology` (frontier, steps to executable, capability
  gaps, supply cycles) and prove that pruning the supplier-chain search with it returns
  exactly what the unpruned search returned, on randomly generated menus.
- Core points: assertions here are contract tests, not biological results; each test pins
  one boundary that must not silently move.
- Interfaces: pytest tests only; `reference_chain` is the pre-pruning search, kept verbatim
  as the oracle.
- Depends on: maestro
"""
from __future__ import annotations

import math
import random

import pytest

from maestro import MAESTROAgent
from maestro.models import EvidenceAction, FunctionalInterventionProfile, MeasurementStatus
from maestro.topology import ActionTopology


def _action(name, *, requires=(), supplies=(), cost=1.0, gate=None):
    return EvidenceAction(name, name, cost, ("h",), prerequisites=tuple(requires), supplies=tuple(supplies),
                          interpretation_gate=gate)


def _profile(*measured):
    return FunctionalInterventionProfile("drug", measured_fields={name: MeasurementStatus.MEASURED for name in measured})


def reference_chain(action, profile, actions, depth, visited):
    """The chain search as it was before topological pruning (the oracle)."""

    missing = profile.unmeasured(action.required_premises)
    if not missing:
        return (action,)
    if depth <= 1:
        return None
    outstanding = frozenset(missing)
    suppliers = sorted(
        (c for c in actions if c.cost >= 0 and c.identifier not in visited and frozenset(c.supplies) & outstanding),
        key=lambda c: (c.cost, c.identifier),
    )
    for supplier in suppliers:
        sub = reference_chain(supplier, profile, actions, depth - 1, visited | {supplier.identifier})
        if sub is not None:
            return sub + (action,)
    return None


def test_frontier_steps_gaps_and_cycles_on_a_small_menu():
    actions = (
        _action("run_now"),
        _action("needs_one", requires=("f1",)),
        _action("supplies_f1", supplies=("f1",)),
        _action("needs_two", requires=("f2",), gate="f1"),
        _action("supplies_f2", requires=("f1",), supplies=("f2",)),
        _action("gap", requires=("never_supplied",)),
        _action("loop_a", requires=("fa",), supplies=("fb",)),
        _action("loop_b", requires=("fb",), supplies=("fa",)),
        _action("already", requires=("measured",)),
        _action("refused", cost=-1.0, supplies=("never_supplied",)),
    )
    topology = ActionTopology.build(actions, _profile("measured"))

    assert topology.executable_now == ("run_now", "supplies_f1", "already")
    assert topology.steps_to_executable["needs_one"] == 2
    # needs_two lacks f2 (supplied after f1) and its gate f1: the shortest chain is two suppliers deep.
    assert topology.steps_to_executable["needs_two"] == 2
    assert topology.steps_to_executable["supplies_f2"] == 2
    assert topology.ungrounded == ("gap", "loop_a", "loop_b")
    # A negative-cost action is not a supplier, so the gap stays a gap.
    assert topology.unsupplied_premises == {"gap": ("never_supplied",)}
    assert topology.supply_cycles == (("loop_a", "loop_b"),)
    assert "refused" not in topology.steps_to_executable
    summary = topology.summary()
    assert summary["steps_to_executable"] == {"needs_one": 2, "needs_two": 2, "supplies_f2": 2,
                                              "gap": None, "loop_a": None, "loop_b": None}
    assert topology.within("needs_one", 2) and not topology.within("needs_one", 1)
    assert topology.within("unknown_action", 1)


def test_a_self_supplying_action_is_a_cycle():
    topology = ActionTopology.build((_action("self", requires=("x",), supplies=("x",)),), _profile())
    assert topology.supply_cycles == (("self",),)
    assert topology.ungrounded == ("self",)


def test_a_long_declared_chain_does_not_exhaust_the_recursion_limit():
    length = 5_000
    actions = [_action("a0")] + [_action(f"a{i}", requires=(f"f{i}",)) for i in range(1, length)]
    actions += [_action(f"s{i}", requires=(f"f{i}",), supplies=(f"f{i + 1}",)) for i in range(1, length - 1)]
    actions += [_action("start", supplies=("f1",))]
    topology = ActionTopology.build(actions, _profile())
    # start, s1 .. s(length-2), then a(length-1): length actions in the shortest chain.
    assert topology.steps_to_executable[f"a{length - 1}"] == length
    assert topology.supply_cycles == ()


@pytest.mark.parametrize("seed", range(300))
def test_pruned_search_returns_exactly_what_the_unpruned_search_returned(seed):
    rng = random.Random(seed)
    fields = [f"f{i}" for i in range(rng.randint(3, 7))]
    actions = []
    for index in range(rng.randint(4, 12)):
        requires = rng.sample(fields, rng.randint(0, 2))
        remaining = [name for name in fields if name not in requires]
        gate = rng.choice(remaining) if remaining and rng.random() < 0.2 else None
        actions.append(_action(
            f"a{index}", requires=requires, supplies=rng.sample(fields, rng.randint(0, 2)),
            cost=rng.choice([-1.0, 0.0, 1.0, 1.0, 2.0, 3.0]), gate=gate,
        ))
    if rng.random() < 0.3:
        actions.append(actions[rng.randrange(len(actions))])  # a duplicated identifier
    profile = _profile(*rng.sample(fields, rng.randint(0, 2)))
    agent = MAESTROAgent()
    topology = ActionTopology.build(actions, profile)
    for action in actions:
        for depth in range(0, 7):
            expected = reference_chain(action, profile, tuple(actions), depth, frozenset({action.identifier})) if depth >= 1 else None
            assert agent.executable_chain(action, profile, actions, max_depth=depth) == expected
        # With depth above the node count the search is complete, so reachability matches the graph.
        complete = agent.executable_chain(action, profile, actions, max_depth=len(actions) + 1)
        steps = topology.steps_to_executable.get(action.identifier)
        if action.cost >= 0 and steps is not None:
            assert (complete is not None) == math.isfinite(steps)
            if complete is not None:
                assert len(complete) >= steps
    candidates = [rng.choice(actions) for _ in range(3)]
    expected_step = None
    for candidate in candidates:
        chain = reference_chain(candidate, profile, tuple(actions), 4, frozenset({candidate.identifier}))
        if chain:
            expected_step = chain[0]
            break
    assert agent.next_executable_action(candidates, profile, actions) == expected_step
